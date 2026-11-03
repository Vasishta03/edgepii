"""Summarize completed seed-42/43/44 pilot scores without hard-coded values."""
import csv,json,statistics
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
RESULTS=ROOT/'results'
MODELS=('minilm','distilbert','bert')
SEEDS=(42,43,44)
TASKS={
    'ai4privacy_detection':'{model}-pilot-512-s{seed}',
    'capid_detection':'{model}-capid-pilot-s{seed}',
    'balanced_relevance':'{model}-relevance-balanced-pilot-s{seed}',
}

rows=[]
for task,pattern in TASKS.items():
    for model in MODELS:
        scores=[]
        for seed in SEEDS:
            run_id=pattern.format(model=model,seed=seed)
            result=json.loads((RESULTS/f'{run_id}-test.json').read_text())
            scores.append(float(result['metrics']['selection_score']))
        rows.append(dict(
            task=task,model=model,
            seed42=scores[0],seed43=scores[1],seed44=scores[2],
            mean=statistics.mean(scores),sample_sd=statistics.stdev(scores),
            minimum=min(scores),maximum=max(scores),
        ))

with (RESULTS/'seed_variance_summary.csv').open('w',newline='') as handle:
    writer=csv.DictWriter(handle,fieldnames=rows[0].keys())
    writer.writeheader();writer.writerows(rows)

lines=[
    '# Three-seed exploratory pilot summary','',
    'Scores are held-out selection metrics for seeds 42/43/44. SD is the sample standard deviation. These are still small-data pilots.','',
    '| Task | Model | Seed 42 | Seed 43 | Seed 44 | Mean ± SD |','|---|---|---:|---:|---:|---:|',
]
for row in rows:
    lines.append(
        f"| {row['task']} | {row['model']} | {row['seed42']:.4f} | {row['seed43']:.4f} | "
        f"{row['seed44']:.4f} | {row['mean']:.4f} ± {row['sample_sd']:.4f} |"
    )
lines += [
    '',
    'BERT balanced relevance is unstable: seed 43 predicts only the majority class (macro F1 0.4068), while seeds 42 and 44 learn. Report all seeds; do not omit or rerun the collapsed seed.',
]
(RESULTS/'SEED_VARIANCE.md').write_text('\n'.join(lines)+'\n')
print('\n'.join(lines))
