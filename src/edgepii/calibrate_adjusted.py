"""Validation-only exact threshold selection with detector-floor accounting."""
import argparse,json,math
from collections import Counter
from .experiment import ROOT
from .prepare import read_jsonl
from .demo import LocalFilter
from .modeling import detect,relevant_probability
from .core import privacy_counts,privacy_rates


def choose(candidates,budget):
    feasible=[c for c in candidates if c['irrelevant_character_leakage'] is not None and c['irrelevant_character_leakage']<=budget]
    if not feasible:return None
    return dict(max(feasible,key=lambda c: (c['relevant_character_retention'] or 0.,-(c['irrelevant_character_leakage'] or 0.),c['threshold'] if c['threshold'] is not None else math.inf)))


def select_operating_points(candidates,mask_all,primary_budget=.05,headroom=.05):
    floor=mask_all['irrelevant_character_leakage']
    if floor is None:raise ValueError('validation set has no irrelevant characters')
    all_candidates=[*candidates,mask_all]
    primary_chosen=choose(all_candidates,primary_budget) if floor<=primary_budget else None
    adjusted_budget=min(1.,floor+headroom)
    adjusted_chosen=choose(all_candidates,adjusted_budget)
    return dict(
        mask_all_floor=floor,
        primary=dict(budget=primary_budget,status='feasible' if primary_chosen else 'infeasible',chosen=primary_chosen),
        adjusted=dict(headroom=headroom,budget=adjusted_budget,status='feasible' if adjusted_chosen else 'infeasible',chosen=adjusted_chosen),
    )


def pareto(candidates):
    result=[]
    for candidate in candidates:
        leak=candidate['irrelevant_character_leakage'];retain=candidate['relevant_character_retention']
        dominated=any(
            other['irrelevant_character_leakage']<=leak and other['relevant_character_retention']>=retain and
            (other['irrelevant_character_leakage']<leak or other['relevant_character_retention']>retain)
            for other in candidates if other is not candidate
        )
        if not dominated:result.append(candidate)
    return sorted(result,key=lambda c:(c['threshold'] is None,c['threshold'] or 0.))


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--detector',required=True);parser.add_argument('--relevance',required=True)
    parser.add_argument('--primary-budget',type=float,default=.05);parser.add_argument('--headroom',type=float,default=.05)
    parser.add_argument('--output',required=True);args=parser.parse_args()
    if not 0<=args.primary_budget<=1 or not 0<=args.headroom<=1:raise ValueError('budgets must be in [0,1]')

    filt=LocalFilter(args.detector,args.relevance)
    rows=read_jsonl(ROOT/'data/processed/capid_validation.jsonl');cache=[];probabilities=[]
    for record in rows:
        predictions=detect(record,filt.detector,filt.dt,filt.detection_length,filt.detection_stride,'cpu')
        for span in predictions:
            try:prob=relevant_probability(record,span,filt.relevance,filt.rt,filt.relevance_length,'cpu')
            except ValueError:prob=-1.
            span['prob']=prob;probabilities.append(prob)
        cache.append((record,predictions))

    thresholds={0.,1.}
    thresholds.update(math.nextafter(prob,1.) for prob in probabilities if 0<=prob<1.)
    candidates=[]
    for threshold in sorted(thresholds):
        counts=Counter()
        for record,predictions in cache:
            counts.update(privacy_counts(record['spans'],[span for span in predictions if span['prob']<threshold]))
        candidates.append(dict(threshold=threshold,policy='context-aware',**privacy_rates(counts)))
    mask_counts=Counter()
    for record,predictions in cache:mask_counts.update(privacy_counts(record['spans'],predictions))
    mask_all=dict(threshold=None,policy='mask-all-detected',**privacy_rates(mask_counts))
    selection=select_operating_points(candidates,mask_all,args.primary_budget,args.headroom)
    curve=pareto([*candidates,mask_all])
    result=dict(
        split='validation',documents=len(rows),detector=args.detector,relevance=args.relevance,
        rule='maximize validation relevant-character retention under leakage budget; ties: lower leakage, then higher threshold',
        **selection,pareto_curve=curve,
        note='Primary 5% criterion remains authoritative. Adjusted floor+headroom point is an exploratory diagnostic, not a privacy guarantee.',
    )
    (ROOT/args.output).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))


if __name__=='__main__':main()
