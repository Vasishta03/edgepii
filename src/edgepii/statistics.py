"""Paired document-bootstrap comparisons; independent of model libraries."""

import argparse, json, random
from collections import Counter
from pathlib import Path
from .core import span_counts, prf
from .prepare import ROOT, read_jsonl


def interval(values, alpha=0.05):
    values = sorted(values)
    return [
        values[int((len(values) - 1) * alpha / 2)],
        values[int((len(values) - 1) * (1 - alpha / 2))],
    ]


def paired_bootstrap(gold, pred_a, pred_b, repeats=2000, seed=42):
    """Resample documents jointly; micro F1 difference A minus B."""
    if not gold or repeats < 1:
        raise ValueError("nonempty gold and positive repeats required")
    ids = [r["id"] for r in gold]
    if set(ids) != set(pred_a) or set(ids) != set(pred_b):
        raise ValueError("prediction IDs must exactly match gold IDs")
    ca = [span_counts(r["spans"], pred_a[r["id"]]) for r in gold]
    cb = [span_counts(r["spans"], pred_b[r["id"]]) for r in gold]
    rng = random.Random(seed)
    deltas = []
    for _ in range(repeats):
        a = Counter()
        b = Counter()
        for i in rng.choices(range(len(gold)), k=len(gold)):
            a.update(ca[i])
            b.update(cb[i])
        deltas.append(prf(a)["f1"] - prf(b)["f1"])
    return dict(
        difference_f1=prf(sum(ca, Counter()))["f1"] - prf(sum(cb, Counter()))["f1"],
        ci95=interval(deltas),
        documents=len(gold),
        bootstrap_repeats=repeats,
        seed=seed,
    )


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--gold", required=True)
    p.add_argument("--a", required=True)
    p.add_argument("--b", required=True)
    p.add_argument("--output", required=True)
    a = p.parse_args()
    gold = read_jsonl(a.gold)
    pa = {r["id"]: r["spans"] for r in read_jsonl(a.a)}
    pb = {r["id"]: r["spans"] for r in read_jsonl(a.b)}
    # Pilot files may be prefixes; only compare identical ID populations.
    if set(pa) != set(pb):
        raise ValueError("different evaluation populations")
    gold = [r for r in gold if r["id"] in pa]
    result = paired_bootstrap(gold, pa, pb)
    Path(a.output).write_text(json.dumps(result, indent=2) + "\n")
    print(result)


if __name__ == "__main__":
    main()
