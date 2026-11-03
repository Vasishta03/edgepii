"""Evaluate every original CAPID document by unique annotated value/type.

This is a project-defined metric, NOT CAPID's published evaluator. It includes
unmatchable gold strings as false negatives and preserves overlapping annotations.
It avoids implying that the flat-BIO retained subset covers the entire benchmark.
"""
import argparse,json
from collections import Counter
from .experiment import ROOT
from .prepare import read_jsonl
from .demo import LocalFilter
from .modeling import detect
from .core import prf


def main():
    p=argparse.ArgumentParser();p.add_argument('--detector',required=True);p.add_argument('--split',choices=['test','reddit'],default='test');p.add_argument('--output',required=True);a=p.parse_args()
    groups=json.loads((ROOT/'configs/labels.json').read_text());mapping={n:k for k,values in groups.items() for n in values}
    f=LocalFilter(a.detector);rows=read_jsonl(ROOT/'data/raw/capid/data'/f'{a.split}.jsonl');counts=Counter();details=[]
    for i,r in enumerate(rows):
        gold={(value,mapping[s['type']]) for value,s in r['piis'].items()}
        spans=detect(dict(text=r['context']),f.detector,f.dt,f.detection_length,f.detection_stride,'cpu')
        pred={(r['context'][s['start']:s['end']],s['label']) for s in spans}
        c=Counter(tp=len(gold&pred),fp=len(pred-gold),fn=len(gold-pred));counts.update(c)
        details.append(dict(source_row=i,**c))
    result=dict(split=a.split,documents=len(rows),metric='exact_unique_value_and_harmonized_type',metrics=prf(counts),per_document_counts=details,note='Full original file, overlapping and unmatchable annotations included. Not the published CAPID evaluator; not character-span F1 or privacy leakage.')
    (ROOT/a.output).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='per_document_counts'},indent=2))
if __name__=='__main__':main()
