"""Paired document-bootstrap comparisons for relevance classifiers."""
import argparse,json,random
from collections import defaultdict
from pathlib import Path
from sklearn.metrics import f1_score
from .prepare import read_jsonl


def _group(rows):
    grouped=defaultdict(list)
    seen=set()
    for row in rows:
        key=(row['id'],row['start'],row['end'])
        if key in seen:raise ValueError('duplicate relevance prediction key')
        seen.add(key)
        grouped[row['id']].append((row['start'],row['end'],int(row['gold']),int(row['probability']>=.5)))
    return {key:sorted(values) for key,values in grouped.items()}


def paired_relevance_bootstrap(rows_a,rows_b,repeats=2000,seed=42):
    a,b=_group(rows_a),_group(rows_b)
    if not a or repeats<1:raise ValueError('nonempty predictions and positive repeats required')
    if set(a)!=set(b):raise ValueError('prediction document IDs must match')
    ids=sorted(a)
    for doc_id in ids:
        gold_a=[x[:3] for x in a[doc_id]];gold_b=[x[:3] for x in b[doc_id]]
        if gold_a!=gold_b:raise ValueError('entity keys and gold labels must match')

    def score(sample,grouped):
        gold=[];pred=[]
        for doc_id in sample:
            gold.extend(x[2] for x in grouped[doc_id]);pred.extend(x[3] for x in grouped[doc_id])
        return float(f1_score(gold,pred,labels=[0,1],average='macro',zero_division=0))

    point=score(ids,a)-score(ids,b);rng=random.Random(seed);deltas=[]
    for _ in range(repeats):
        sample=rng.choices(ids,k=len(ids));deltas.append(score(sample,a)-score(sample,b))
    deltas.sort();lo=deltas[int((len(deltas)-1)*.025)];hi=deltas[int((len(deltas)-1)*.975)]
    return dict(difference_macro_f1=point,ci95=[lo,hi],documents=len(ids),entities=sum(len(a[i]) for i in ids),bootstrap_repeats=repeats,seed=seed)


def main():
    p=argparse.ArgumentParser();p.add_argument('--a',required=True);p.add_argument('--b',required=True);p.add_argument('--output',required=True);p.add_argument('--repeats',type=int,default=2000);p.add_argument('--seed',type=int,default=42);args=p.parse_args()
    result=paired_relevance_bootstrap(read_jsonl(args.a),read_jsonl(args.b),args.repeats,args.seed)
    Path(args.output).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))


if __name__=='__main__':main()
