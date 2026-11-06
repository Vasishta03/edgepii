"""Validation-only policy calibration, with an explicit infeasible outcome."""

import argparse, json
from collections import Counter
from .experiment import ROOT
from .prepare import read_jsonl
from .demo import LocalFilter
from .modeling import detect, relevant_probability
from .core import privacy_counts, privacy_rates


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--detector", required=True)
    p.add_argument("--relevance", required=True)
    p.add_argument("--max-leakage", type=float, default=0.05)
    p.add_argument("--output", required=True)
    a = p.parse_args()
    f = LocalFilter(a.detector, a.relevance)
    rows = read_jsonl(ROOT / "data/processed/capid_validation.jsonl")
    cache = []
    for r in rows:
        preds = detect(
            r, f.detector, f.dt, f.detection_length, f.detection_stride, "cpu"
        )
        for s in preds:
            try:
                s["prob"] = relevant_probability(
                    r, s, f.relevance, f.rt, f.relevance_length, "cpu"
                )
            except ValueError:
                s["prob"] = -1.0
        cache.append((r, preds))
    candidates = []
    for threshold in [0.0, 0.25, 0.5, 0.75, 0.9, 0.95, 0.99, 1.01]:
        c = Counter()
        for r, preds in cache:
            c.update(
                privacy_counts(r["spans"], [s for s in preds if s["prob"] < threshold])
            )
        candidates.append(
            dict(
                threshold=threshold,
                policy="mask-all" if threshold > 1 else "context-aware",
                **privacy_rates(c),
            )
        )
    feasible = [
        c
        for c in candidates
        if c["irrelevant_character_leakage"] is not None
        and c["irrelevant_character_leakage"] <= a.max_leakage
    ]
    chosen = (
        dict(max(feasible, key=lambda c: c["relevant_character_retention"] or 0))
        if feasible
        else None
    )
    if chosen and chosen["policy"] == "mask-all":
        chosen["threshold"] = None
    result = dict(
        split="validation",
        documents=len(rows),
        max_leakage=a.max_leakage,
        status="feasible" if chosen else "infeasible",
        chosen=chosen,
        candidates=candidates,
        note="1.01 is the mask-all-detected diagnostic; no detector can mask entities it misses.",
    )
    (ROOT / a.output).write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
