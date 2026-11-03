"""Summarize question-dependence controls for all balanced relevance checkpoints."""
from __future__ import annotations

import csv
import json
import statistics
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODELS = ("minilm", "distilbert", "bert")
SEEDS = (42, 43, 44)
LABELS = {"minilm": "MiniLM", "distilbert": "DistilBERT", "bert": "BERT"}
rows = []
for model in MODELS:
    for seed in SEEDS:
        path = ROOT / "results" / f"{model}-balanced-pilot-s{seed}-relevance-controls.json"
        data = json.loads(path.read_text())
        normal = data["metrics"]["normal_question"]["macro_f1"]
        no_question = data["metrics"]["no_question"]["macro_f1"]
        rows.append({
            "model": model,
            "seed": seed,
            "documents": data["documents"],
            "entities": data["entities"],
            "normal_macro_f1": normal,
            "no_question_macro_f1": no_question,
            "no_question_delta": no_question - normal,
            "removed_probability_change": data["question_sensitivity"]["removed"]["mean_absolute_probability_change"],
            "removed_decision_flip_rate": data["question_sensitivity"]["removed"]["decision_flip_rate"],
            "permuted_probability_change": data["question_sensitivity"]["permuted"]["mean_absolute_probability_change"],
            "permuted_decision_flip_rate": data["question_sensitivity"]["permuted"]["decision_flip_rate"],
        })

with (ROOT / "results" / "relevance_controls_summary.csv").open("w", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
    writer.writeheader(); writer.writerows(rows)

def mean_sd(values):
    return statistics.mean(values), statistics.stdev(values)

lines = [
    "# Question-dependence controls",
    "",
    "Gold-span relevance controls on 64 retained CAPID test documents. No-question macro-F1 is a scored degraded-input ablation; rotated-question outputs are sensitivity diagnostics only because no counterfactual labels exist.",
    "",
    "| Model | Normal macro-F1 | No-question macro-F1 | No-question delta | Removed-question flip rate | Permuted-question flip rate |",
    "|---|---:|---:|---:|---:|---:|",
]
for model in MODELS:
    selected = [row for row in rows if row["model"] == model]
    metrics = []
    for key in ("normal_macro_f1", "no_question_macro_f1", "no_question_delta", "removed_decision_flip_rate", "permuted_decision_flip_rate"):
        mean, sd = mean_sd([row[key] for row in selected]); metrics.append(f"{mean:.3f} ± {sd:.3f}")
    lines.append(f"| {LABELS[model]} | " + " | ".join(metrics) + " |")
lines += [
    "",
    "A negative no-question delta indicates worse performance after removing the question. Probability and decision changes alone show dependence, not correct counterfactual reasoning.",
]
(ROOT / "results" / "RELEVANCE_CONTROLS.md").write_text("\n".join(lines) + "\n")
print(ROOT / "results" / "RELEVANCE_CONTROLS.md")
