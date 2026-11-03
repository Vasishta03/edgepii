"""Deterministic training and validation; never selects models on test scores."""
import argparse, csv, hashlib, json, os, platform, random, resource, sys, time, shutil
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
for key,sub in [('HF_HOME','hf'),('TORCH_HOME','torch'),('MPLCONFIGDIR','matplotlib'),('XDG_CACHE_HOME','xdg')]:
    os.environ.setdefault(key,str(ROOT/'.cache'/sub))
os.environ.setdefault('TOKENIZERS_PARALLELISM','false')
os.environ.setdefault('HF_HUB_OFFLINE','1')
import numpy as np
import torch
import torch.nn.functional as F
from torch.utils.data import DataLoader
from transformers import AutoTokenizer, AutoModelForTokenClassification, AutoModelForSequenceClassification, DataCollatorForTokenClassification, DataCollatorWithPadding
from sklearn.metrics import accuracy_score, f1_score
from .core import span_counts,prf
from .prepare import read_jsonl,write_jsonl
from .modeling import detection_features,relevance_feature,detect,relevant_probability


def seed_all(seed,threads):
    random.seed(seed);np.random.seed(seed);torch.manual_seed(seed);torch.set_num_threads(threads)
    if torch.cuda.is_available():torch.cuda.manual_seed_all(seed)
    torch.use_deterministic_algorithms(True)


def load_model(task,path,labels,device):
    cls=AutoModelForTokenClassification if task=='detection' else AutoModelForSequenceClassification
    model=cls.from_pretrained(str(path),local_files_only=True,num_labels=len(labels),id2label=dict(enumerate(labels)),label2id={v:i for i,v in enumerate(labels)})
    return model.to(device)


def relevance_class_weights(features, mode, device):
    """Return training-only loss weights and the observed class counts.

    Balanced weights follow n_samples / (n_classes * class_count).  Validation
    and test labels never influence training weights.
    """
    counts=Counter(int(feature['labels']) for feature in features)
    if set(counts) != {0, 1}:
        raise ValueError('relevance training data must contain both classes')
    if mode=='none':
        return None,dict(sorted(counts.items()))
    if mode!='balanced':
        raise ValueError('class_weighting must be none or balanced')
    total=sum(counts.values());classes=len(counts)
    weights=torch.tensor([total/(classes*counts[i]) for i in range(classes)],dtype=torch.float32,device=device)
    return weights,dict(sorted(counts.items()))


def evaluate(model,tokenizer,records,cfg,device):
    model.eval();predictions=[]
    if cfg['task']=='detection':
        counts=Counter(); untyped=Counter(); per_type={}
        for r in records:
            pred=detect(r,model,tokenizer,cfg['max_length'],cfg['stride'],device)
            counts.update(span_counts(r['spans'],pred));untyped.update(span_counts(r['spans'],pred,False))
            for label in {s['label'] for s in r['spans']+pred}:
                per_type.setdefault(label,Counter()).update(span_counts([s for s in r['spans'] if s['label']==label],[s for s in pred if s['label']==label]))
            predictions.append(dict(id=r['id'],spans=pred))
        metrics=dict(span=prf(counts),untyped_span=prf(untyped),per_type={k:prf(v) for k,v in sorted(per_type.items())})
        metrics['selection_score']=metrics['span']['f1']
    else:
        gold=[];pred=[];probs=[]
        for r in records:
            for span in r['spans']:
                prob=relevant_probability(r,span,model,tokenizer,cfg['max_length'],device)
                gold.append(span['relevance']);pred.append(int(prob>=.5));probs.append(prob)
                predictions.append(dict(id=r['id'],start=span['start'],end=span['end'],gold=span['relevance'],probability=prob))
        metrics=dict(accuracy=float(accuracy_score(gold,pred)),macro_f1=float(f1_score(gold,pred,labels=[0,1],average='macro',zero_division=0)),entities=len(gold))
        metrics['selection_score']=metrics['macro_f1']
    return metrics,predictions


def registry(record):
    with (ROOT/'results/experiment_registry.jsonl').open('a') as f:f.write(json.dumps(record)+'\n')


def validate_config(cfg):
    for key in ['epochs','train_size','batch_size','gradient_accumulation','threads']:
        if not isinstance(cfg[key],int) or cfg[key]<1:raise ValueError(f'{key} must be a positive integer')
    if cfg['task'] not in ('detection','relevance'):raise ValueError('unsupported task')
    if not 8<=cfg['max_length']<=512:raise ValueError('max_length outside supported range')
    if not 0<=cfg['stride']<cfg['max_length']-2:raise ValueError('invalid stride')
    if cfg['learning_rate']<=0:raise ValueError('learning rate must be positive')
    if cfg.get('validation_size') is not None and cfg['validation_size']<1:raise ValueError('validation_size must be positive or null')
    weighting=cfg.get('class_weighting','none')
    if weighting not in ('none','balanced'):raise ValueError('class_weighting must be none or balanced')
    if cfg['task']!='relevance' and weighting!='none':raise ValueError('class weighting is supported only for relevance')


_ACTIVE_OUT=None

def main():
    global _ACTIVE_OUT
    parser=argparse.ArgumentParser();parser.add_argument('--config',required=True);args=parser.parse_args()
    cfg=json.loads(Path(args.config).read_text());validate_config(cfg);run_id=cfg['run_id'];out=ROOT/'artifacts/runs'/run_id
    if Path(run_id).name!=run_id or run_id in ('.','..'):raise ValueError('run_id must be a plain directory name')
    out.mkdir(parents=True,exist_ok=False)
    _ACTIVE_OUT=out
    registry(dict(run_id=run_id,status='initializing',config=cfg))
    (out/'config.json').write_text(json.dumps(cfg,indent=2)+'\n')
    seed_all(cfg['seed'],cfg['threads']);device=cfg.get('device','cpu')
    if device=='cuda' and not torch.cuda.is_available():raise RuntimeError('CUDA requested but unavailable')
    source=ROOT/cfg.get('initialize_from',f"artifacts/backbones/{cfg['model']}")
    tokenizer=AutoTokenizer.from_pretrained(str(source),local_files_only=True,use_fast=True)
    if not tokenizer.is_fast:raise ValueError('offset-aware fast tokenizer required')
    labels=json.loads((ROOT/'data/processed/labels.json').read_text()) if cfg['task']=='detection' else ['irrelevant','relevant']
    model=load_model(cfg['task'],source,labels,device)
    data_root=ROOT/cfg.get('data_dir','data/processed')
    train=read_jsonl(data_root/f"{cfg['dataset']}_train.jsonl")
    validation=read_jsonl(data_root/f"{cfg['dataset']}_validation.jsonl")
    if cfg['train_size']>len(train):raise ValueError('requested training size exceeds available train split')
    train=train[:cfg['train_size']];validation=validation[:cfg.get('validation_size') or len(validation)]
    features=[];rejected=[]
    for r in train:
        try:
            new=detection_features(r,tokenizer,{v:i for i,v in enumerate(labels)},cfg['max_length'],cfg['stride']) if cfg['task']=='detection' else [relevance_feature(r,s,tokenizer,cfg['max_length']) for s in r['spans']]
            features.extend(new)
        except ValueError as e:rejected.append(dict(id=r['id'],reason=str(e)))
    if not features:raise ValueError('no usable training features')
    write_jsonl(out/'training_exclusions.jsonl',rejected)
    collator=DataCollatorForTokenClassification(tokenizer) if cfg['task']=='detection' else DataCollatorWithPadding(tokenizer)
    loader=DataLoader(features,batch_size=cfg['batch_size'],shuffle=True,collate_fn=collator,generator=torch.Generator().manual_seed(cfg['seed']))
    class_weights=None;class_counts=None
    if cfg['task']=='relevance':
        class_weights,class_counts=relevance_class_weights(features,cfg.get('class_weighting','none'),device)
    optimizer=torch.optim.AdamW(model.parameters(),lr=cfg['learning_rate'],weight_decay=cfg['weight_decay'])
    shutil.copytree(ROOT/'src/edgepii',out/'source/edgepii',ignore=shutil.ignore_patterns('__pycache__'))
    shutil.copy2(ROOT/'requirements.lock.txt',out/'requirements.lock.txt')
    codehash=hashlib.sha256(b''.join(p.read_bytes() for p in sorted((ROOT/'src/edgepii').glob('*.py')))).hexdigest()
    metadata=dict(run_id=run_id,status='running',started_utc=datetime.now(timezone.utc).isoformat(),config=cfg,code_sha256=codehash,python=sys.version,torch=torch.__version__,platform=platform.platform(),parameters=sum(p.numel() for p in model.parameters()),training_documents=len(train)-len(rejected),training_features=len(features),training_class_counts=class_counts,class_weights=class_weights.tolist() if class_weights is not None else None,validation_documents=len(validation),processed_sha256={p.stem:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(data_root.glob('*_*.jsonl'))})
    registry(metadata);(out/'metadata.json').write_text(json.dumps(metadata,indent=2)+'\n')
    best=-1.;history=[];train_seconds=0.;start=time.perf_counter()
    if device=='cuda':torch.cuda.reset_peak_memory_stats()
    try:
        for epoch in range(cfg['epochs']):
            model.train();loss_sum=0.;epoch_start=time.perf_counter();optimizer.zero_grad(set_to_none=True)
            accum=cfg['gradient_accumulation']
            for i,batch in enumerate(loader):
                batch={k:v.to(device) for k,v in batch.items()}
                if cfg['task']=='relevance' and class_weights is not None:
                    labels_batch=batch.pop('labels')
                    loss=F.cross_entropy(model(**batch).logits,labels_batch,weight=class_weights)
                else:
                    loss=model(**batch).loss
                if not torch.isfinite(loss):raise RuntimeError('nonfinite loss')
                # Last accumulation group may have fewer microbatches.
                group_size=min(accum,len(loader)-(i//accum)*accum)
                (loss/group_size).backward();loss_sum+=float(loss.detach())
                if (i+1)%accum==0 or i+1==len(loader):
                    torch.nn.utils.clip_grad_norm_(model.parameters(),1.0);optimizer.step();optimizer.zero_grad(set_to_none=True)
            if device=='cuda':torch.cuda.synchronize()
            train_seconds+=time.perf_counter()-epoch_start
            metrics,predictions=evaluate(model,tokenizer,validation,cfg,device)
            row=dict(epoch=epoch+1,loss=loss_sum/len(loader),validation=metrics,train_seconds=train_seconds)
            history.append(row);print(json.dumps(row),flush=True)
            (out/'history.json').write_text(json.dumps(history,indent=2)+'\n')
            if metrics['selection_score']>best:
                best=metrics['selection_score'];model.save_pretrained(out/'checkpoint');tokenizer.save_pretrained(out/'checkpoint')
                (out/'validation_metrics.json').write_text(json.dumps(metrics,indent=2)+'\n');write_jsonl(out/'validation_predictions.jsonl',predictions)
        finish=dict(metadata,status='completed',train_seconds=train_seconds,wall_seconds=time.perf_counter()-start,peak_process_rss_mib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024,peak_cuda_allocated_mib=torch.cuda.max_memory_allocated()/2**20 if device=='cuda' else None,best_validation_score=best)
        (out/'metadata.json').write_text(json.dumps(finish,indent=2)+'\n');registry(finish)
        fields=['run_id','status','task','model','dataset','phase','seed','requested_train_size','training_documents','parameters','best_validation_score','train_seconds','wall_seconds','peak_process_rss_mib','peak_cuda_allocated_mib']
        path=ROOT/'results/results.csv';exists=path.exists()
        with path.open('a',newline='') as f:
            writer=csv.DictWriter(f,fieldnames=fields)
            if not exists:writer.writeheader()
            row={k:finish.get(k,cfg.get(k)) for k in fields};row['requested_train_size']=cfg['train_size'];writer.writerow(row)
    except BaseException as e:
        raise

if __name__=='__main__':
    try:main()
    except BaseException as error:
        if _ACTIVE_OUT is not None:
            path=_ACTIVE_OUT/'metadata.json'
            failed=json.loads(path.read_text()) if path.exists() else {'run_id':_ACTIVE_OUT.name}
            failed.update(status='failed',error=repr(error))
            path.write_text(json.dumps(failed,indent=2)+'\n');registry(failed)
        raise
