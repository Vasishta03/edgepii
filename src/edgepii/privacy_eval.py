"""End-to-end leakage/retention and oracle detector diagnostic on CAPID."""
import argparse,json
from collections import Counter
from .experiment import ROOT
from .prepare import read_jsonl
from .demo import LocalFilter
from .core import privacy_counts,privacy_rates
from .modeling import detect,relevant_probability


def main():
    p=argparse.ArgumentParser();p.add_argument('--detector',required=True);p.add_argument('--relevance',required=True);p.add_argument('--split',choices=['validation','test','reddit'],default='test');p.add_argument('--limit',type=int,default=0);p.add_argument('--threshold',type=float,default=.9);p.add_argument('--output',required=True);a=p.parse_args()
    if not 0<=a.threshold<=1:raise ValueError('threshold out of range')
    f=LocalFilter(a.detector,a.relevance);rows=read_jsonl(ROOT/'data/processed'/f'capid_{a.split}.jsonl');rows=rows[:a.limit] if a.limit else rows
    counts={k:Counter() for k in ['mask_all_detected','context_aware','oracle_spans_context_aware','keep_all','oracle_policy']}
    for r in rows:
        predicted=detect(r,f.detector,f.dt,f.detection_length,f.detection_stride,'cpu')
        def mask(spans):
            result=[]
            for s in spans:
                try:prob=relevant_probability(r,s,f.relevance,f.rt,f.relevance_length,'cpu')
                except ValueError:prob=0.
                if prob<a.threshold:result.append(s)
            return result
        policies=dict(mask_all_detected=predicted,context_aware=mask(predicted),oracle_spans_context_aware=mask(r['spans']),keep_all=[],oracle_policy=[s for s in r['spans'] if s['relevance']==0])
        for name,spans in policies.items():counts[name].update(privacy_counts(r['spans'],spans))
    result=dict(split=a.split,documents=len(rows),threshold=a.threshold,detector=a.detector,relevance=a.relevance,policy_note='Threshold fixed in advance; oracle conditions are diagnostics, not deployable performance.',metrics={k:privacy_rates(v) for k,v in counts.items()})
    (ROOT/a.output).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
