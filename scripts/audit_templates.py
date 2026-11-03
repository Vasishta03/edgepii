"""Audit exact delexicalized-template overlap without changing frozen splits."""
import json,sys,re,hashlib
from collections import defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from edgepii.prepare import read_jsonl

def template(r):
 text=r['text']
 for s in sorted(r['spans'],key=lambda x:x['start'],reverse=True):text=text[:s['start']]+' <'+s['label']+'> '+text[s['end']:]
 return hashlib.sha256(' '.join(text.casefold().split()).encode()).hexdigest()
report={}
for dataset in ['ai4privacy','capid']:
 splits={s:read_jsonl(ROOT/'data/processed'/f'{dataset}_{s}.jsonl') for s in ['train','validation','test']}
 keys={s:{template(r) for r in rows} for s,rows in splits.items()}
 report[dataset]={f'{a}_{b}_shared_templates':len(keys[a]&keys[b]) for a,b in [('train','validation'),('train','test'),('validation','test')]}
 report[dataset]['test_documents_with_train_template']=sum(template(r) in keys['train'] for r in splits['test'])
 report[dataset]['affected_training_ids']=[r['id'] for r in splits['train'] if template(r) in (keys['validation']|keys['test'])]
 report[dataset]['affected_pilot_training_ids']=[r['id'] for r in splits['train'][:512] if template(r) in (keys['validation']|keys['test'])]
 report[dataset]['note']='Exact delexicalized template equality only; not semantic near-duplicate detection.'
(ROOT/'results/template_audit.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
