"""Fresh-process checkpoint evaluation and batch-one latency measurement."""
import argparse,json,resource,time,platform
from pathlib import Path
import numpy as np
import torch
from transformers import AutoTokenizer
from .experiment import ROOT,load_model,seed_all,evaluate
from .prepare import read_jsonl,write_jsonl
from .modeling import detect,relevant_probability


def main():
    p=argparse.ArgumentParser();p.add_argument('--run',required=True);p.add_argument('--split',choices=['validation','test','reddit'],default='test');p.add_argument('--limit',type=int,default=0);p.add_argument('--repeats',type=int,default=30);p.add_argument('--warmup',type=int,default=5);a=p.parse_args()
    out=ROOT/'artifacts/runs'/a.run;cfg=json.loads((out/'config.json').read_text());seed_all(cfg['seed'],cfg['threads']);device=cfg['device']
    rows=read_jsonl(ROOT/cfg.get('data_dir','data/processed')/f"{cfg['dataset']}_{a.split}.jsonl");rows=rows[:a.limit] if a.limit else rows
    if not rows or a.repeats<1:raise ValueError('nonempty evaluation and repeats required')
    tokenizer=AutoTokenizer.from_pretrained(out/'checkpoint',local_files_only=True)
    labels=json.loads((ROOT/'data/processed/labels.json').read_text()) if cfg['task']=='detection' else ['irrelevant','relevant']
    model=load_model(cfg['task'],out/'checkpoint',labels,device);model.eval()
    def infer(r):
        if cfg['task']=='detection':return detect(r,model,tokenizer,cfg['max_length'],cfg['stride'],device)
        return [relevant_probability(r,s,model,tokenizer,cfg['max_length'],device) for s in r['spans']]
    if device=='cuda':torch.cuda.reset_peak_memory_stats()
    for i in range(a.warmup):infer(rows[i%len(rows)])
    timings=[]
    for i in range(a.repeats):
        r=rows[i%len(rows)]
        if device=='cuda':torch.cuda.synchronize()
        start=time.perf_counter();infer(r)
        if device=='cuda':torch.cuda.synchronize()
        timings.append((time.perf_counter()-start)*1000)
    metrics,predictions=evaluate(model,tokenizer,rows,cfg,device)
    result=dict(run_id=a.run,phase=cfg['phase'],split=a.split,documents=len(rows),metrics=metrics,benchmark=dict(device=device,threads=cfg['threads'],batch_size=1,unit='document (all windows/entities)',includes='tokenization, model forward, decoding; excludes loading and disk IO',warmup=a.warmup,repeats=a.repeats,median_ms=float(np.median(timings)),p95_ms=float(np.percentile(timings,95)),mean_ms=float(np.mean(timings)),raw_ms=timings,peak_process_rss_mib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024,peak_cuda_allocated_mib=torch.cuda.max_memory_allocated()/2**20 if device=='cuda' else None,platform=platform.platform(),checkpoint_bytes=sum(p.stat().st_size for p in (out/'checkpoint').glob('*') if p.is_file())))
    dest=ROOT/'results'/f'{a.run}-{a.split}.json';dest.write_text(json.dumps(result,indent=2)+'\n');write_jsonl(ROOT/'results'/f'{a.run}-{a.split}-predictions.jsonl',predictions)
    print(json.dumps(result,indent=2))
if __name__=='__main__':main()
