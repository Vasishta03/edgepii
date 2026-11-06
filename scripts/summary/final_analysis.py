"""Generate error analysis and final figures from frozen measured artifacts."""
from __future__ import annotations
import numpy as np
import matplotlib.pyplot as plt
import matplotlib

import csv
import json
import os
import statistics
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
os.environ["MPLCONFIGDIR"] = str(ROOT / ".cache" / "matplotlib")

matplotlib.use("Agg")

plt.rcParams["pdf.fonttype"] = 42
plt.rcParams["ps.fonttype"] = 42

MODELS = ("minilm", "distilbert", "bert")
SEEDS = (42, 43, 44)
LABELS = {"minilm": "MiniLM", "distilbert": "DistilBERT", "bert": "BERT"}


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def prf(tp: int, fp: int, fn: int) -> dict:
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / \
        (precision + recall) if precision + recall else 0.0
    return {"precision": precision, "recall": recall, "f1": f1, "tp": tp, "fp": fp, "fn": fn}


def mean_sd(values: list[float]) -> dict:
    return {"mean": statistics.mean(values), "sample_sd": statistics.stdev(values) if len(values) > 1 else 0.0}


gold_docs = read_jsonl(ROOT / "data" / "processed" / "capid_test.jsonl")[:64]
gold_by_id = {row["id"]: row for row in gold_docs}
types = sorted({span["label"] for row in gold_docs for span in row["spans"]})
lengths = sorted(len(row["text"]) for row in gold_docs)
q1, q2 = lengths[len(lengths) // 3], lengths[2 * len(lengths) // 3]


def bucket(length: int) -> str:
    if length <= q1:
        return "short"
    if length <= q2:
        return "medium"
    return "long"


detection_seed_rows = []
per_type_seed = defaultdict(list)
length_seed = defaultdict(list)
for model in MODELS:
    for seed in SEEDS:
        predictions = read_jsonl(
            ROOT / "results" / f"{model}-capid-pilot-s{seed}-test-predictions.jsonl")
        pred_by_id = {row["id"]: row["spans"] for row in predictions}
        if set(pred_by_id) != set(gold_by_id):
            raise RuntimeError(
                f"Prediction population mismatch: {model} seed {seed}")
        for label in types:
            tp = fp = fn = 0
            for doc_id, gold in gold_by_id.items():
                g = {(s["start"], s["end"], s["label"])
                     for s in gold["spans"] if s["label"] == label}
                p = {(s["start"], s["end"], s["label"])
                     for s in pred_by_id[doc_id] if s["label"] == label}
                tp += len(g & p)
                fp += len(p - g)
                fn += len(g - p)
            result = prf(tp, fp, fn)
            per_type_seed[(model, label)].append(result["f1"])
            detection_seed_rows.append(
                {"model": model, "seed": seed, "group": "type", "value": label, **result})
        for name in ("short", "medium", "long"):
            tp = fp = fn = 0
            for doc_id, gold in gold_by_id.items():
                if bucket(len(gold["text"])) != name:
                    continue
                g = {(s["start"], s["end"], s["label"]) for s in gold["spans"]}
                p = {(s["start"], s["end"], s["label"])
                     for s in pred_by_id[doc_id]}
                tp += len(g & p)
                fp += len(p - g)
                fn += len(g - p)
            result = prf(tp, fp, fn)
            length_seed[(model, name)].append(result["f1"])
            detection_seed_rows.append(
                {"model": model, "seed": seed, "group": "length", "value": name, **result})

relevance = {}
for model in MODELS:
    seed_metrics = []
    for seed in SEEDS:
        rows = read_jsonl(
            ROOT / "results" / f"{model}-relevance-balanced-pilot-s{seed}-test-predictions.jsonl")
        gold = [int(row["gold"]) for row in rows]
        pred = [int(row["probability"] >= 0.5) for row in rows]
        confusion = Counter((g, p) for g, p in zip(gold, pred))
        class_metrics = {}
        for cls, name in ((0, "irrelevant"), (1, "relevant")):
            tp = confusion[(cls, cls)]
            fp = sum(confusion[(g, cls)] for g in (0, 1) if g != cls)
            fn = sum(confusion[(cls, p)] for p in (0, 1) if p != cls)
            class_metrics[name] = prf(tp, fp, fn)
        seed_metrics.append({"seed": seed, "entities": len(rows), "confusion": {
                            f"gold{g}_pred{p}": confusion[(g, p)] for g in (0, 1) for p in (0, 1)}, "classes": class_metrics})
    relevance[model] = seed_metrics

relevance_summary = {}
for model, seed_metrics in relevance.items():
    relevance_summary[model] = {}
    for class_name in ("irrelevant", "relevant"):
        relevance_summary[model][class_name] = {
            metric: mean_sd([seed["classes"][class_name][metric]
                            for seed in seed_metrics])
            for metric in ("precision", "recall", "f1")
        }

exclusions = read_jsonl(ROOT / "data" / "processed" / "exclusions.jsonl")
excluded = {row["id"]: row["reason"]
            for row in exclusions if row["id"].startswith("capid-")}
exclusion_reasons = Counter(excluded.values())
raw_label_docs = Counter()
excluded_label_docs = Counter()
split_totals = Counter()
split_excluded = Counter()
for split in ("train", "test", "reddit"):
    raw_rows = read_jsonl(ROOT / "data" / "raw" /
                          "capid" / "data" / f"{split}.jsonl")
    for index, row in enumerate(raw_rows):
        doc_id = f"capid-{split}-{index}"
        labels = {annotation.get("type", "UNKNOWN")
                  for annotation in row.get("piis", {}).values()}
        split_totals[split] += 1
        for label in labels:
            raw_label_docs[label] += 1
        if doc_id in excluded:
            split_excluded[split] += 1
            for label in labels:
                excluded_label_docs[label] += 1

exclusion_rows = []
for label in sorted(raw_label_docs):
    exclusion_rows.append({
        "native_label": label,
        "raw_documents_with_label": raw_label_docs[label],
        "excluded_documents_with_label": excluded_label_docs[label],
        "document_exclusion_rate": excluded_label_docs[label] / raw_label_docs[label],
    })
with (ROOT / "results" / "exclusion_bias.csv").open("w", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=list(exclusion_rows[0]))
    writer.writeheader()
    writer.writerows(exclusion_rows)

research_alignment = {}
for size in (5000, 10000):
    by_model = {}
    for model in MODELS:
        path = ROOT / "artifacts" / "runs" / \
            f"{model}-detection-{size}-s42" / "training_exclusions.jsonl"
        by_model[model] = sorted(row["id"] for row in read_jsonl(path))
    research_alignment[str(size)] = {
        "excluded_count": len(by_model["minilm"]),
        "identical_exclusion_ids_across_models": by_model["minilm"] == by_model["distilbert"] == by_model["bert"],
        "excluded_ids_sha256": __import__("hashlib").sha256("\n".join(by_model["minilm"]).encode()).hexdigest(),
    }
(ROOT / "results" / "research_alignment_audit.json").write_text(
    json.dumps(research_alignment, indent=2) + "\n")

per_type_summary = {
    model: {label: mean_sd(per_type_seed[(model, label)]) for label in types}
    for model in MODELS
}
length_summary = {
    model: {name: mean_sd(length_seed[(model, name)])
            for name in ("short", "medium", "long")}
    for model in MODELS
}
report = {
    "scope": "CAPID retained test prefix used by three-seed pilots (64 documents)",
    "length_bucket_character_boundaries": {"short_max": q1, "medium_max": q2},
    "detection_per_type": per_type_summary,
    "detection_by_document_length": length_summary,
    "relevance_confusion_and_class_metrics": relevance,
    "relevance_class_summary": relevance_summary,
    "capid_exclusions": {
        "by_reason": dict(exclusion_reasons),
        "by_raw_split": {split: {"raw": split_totals[split], "excluded_during_normalization": split_excluded[split]} for split in ("train", "test", "reddit")},
        "per_label_csv": "results/exclusion_bias.csv",
    },
    "research_token_boundary_alignment": research_alignment,
    "cautions": [
        "Per-type and length results are exploratory because they use 64 retained test documents.",
        "Exclusion rates are record-level associations; a label in an excluded record is not necessarily the cause of exclusion.",
        "Reddit domain shift is reported separately in results/ADJUSTED_PRIVACY.md.",
    ],
}
(ROOT / "results" / "error_analysis.json").write_text(json.dumps(report, indent=2) + "\n")

lines = [
    "# Error analysis",
    "",
    "Exploratory analysis on the frozen 64-document retained CAPID test prefix across seeds 42/43/44.",
    "",
    "## Strict typed span F1 by PII type (mean ± sample SD)",
    "",
    "| Type | MiniLM | DistilBERT | BERT |",
    "|---|---:|---:|---:|",
]
for label in types:
    values = [per_type_summary[m][label] for m in MODELS]
    lines.append(f"| {label} | " + " | ".join(
        f"{v['mean']:.3f} ± {v['sample_sd']:.3f}" for v in values) + " |")
lines += [
    "",
    "## Detection by context length",
    "",
    f"Buckets use character length: short ≤ {q1}, medium ≤ {q2}, long > {q2}.",
    "",
    "| Bucket | MiniLM | DistilBERT | BERT |",
    "|---|---:|---:|---:|",
]
for name in ("short", "medium", "long"):
    values = [length_summary[m][name] for m in MODELS]
    lines.append(f"| {name.title()} | " + " | ".join(
        f"{v['mean']:.3f} ± {v['sample_sd']:.3f}" for v in values) + " |")
lines += [
    "",
    "## Relevance errors by class",
    "",
    "| Model | Irrelevant recall | Relevant recall | Relevant F1 |",
    "|---|---:|---:|---:|",
]
for model in MODELS:
    irrelevant = relevance_summary[model]["irrelevant"]["recall"]
    relevant_recall = relevance_summary[model]["relevant"]["recall"]
    relevant_f1 = relevance_summary[model]["relevant"]["f1"]
    lines.append(
        f"| {LABELS[model]} | {irrelevant['mean']:.3f} ± {irrelevant['sample_sd']:.3f} "
        f"| {relevant_recall['mean']:.3f} ± {relevant_recall['sample_sd']:.3f} "
        f"| {relevant_f1['mean']:.3f} ± {relevant_f1['sample_sd']:.3f} |"
    )
lines += [
    "",
    "## Exclusion audit",
    "",
    "| Raw split | Documents | Excluded during normalization |",
    "|---|---:|---:|",
]
for split in ("train", "test", "reddit"):
    lines.append(
        f"| {split} | {split_totals[split]} | {split_excluded[split]} |")
lines += ["", "Exclusion reasons:", ""]
for reason, count in exclusion_reasons.most_common():
    lines.append(f"- {count}: {reason}")
lines += [
    "",
    "Per-label record exclusion associations are in `results/exclusion_bias.csv`. A label appearing in an excluded record is not necessarily the cause of exclusion.",
    "",
    "## Interpretation",
    "",
    "- MiniLM records zero mean exact F1 for APPEARANCE and BELIEF and near-zero EDUCATION performance. These categories are absent from AI4Privacy supervision, so the small CAPID adaptation must learn them; the analysis shows association, not a proven cause.",
    "- MiniLM's sharp degradation on long contexts occurs despite sliding-window inference, so it cannot be explained by silent tail truncation. Model capacity, adaptation data and boundary errors remain plausible contributors.",
    "- BERT relevance variability is dominated by the retained seed-43 majority-class collapse. Excluding it would hide a reproducibility failure.",
    "- Reddit has a markedly different type distribution and writing style; every model's leakage rises substantially in `results/ADJUSTED_PRIVACY.md`. The present experiment does not isolate which shift causes the loss.",
    "",
    "The analysis remains exploratory because the multiseed pilots use only 64 retained CAPID test documents.",
]
(ROOT / "results" / "ERROR_ANALYSIS.md").write_text("\n".join(lines) + "\n")

# Figure 1: reduced scaling quality and training cost.
scale_rows = list(csv.DictReader(
    (ROOT / "results" / "scaling_summary.csv").open()))
fig, axes = plt.subplots(1, 2, figsize=(9, 3.5))
for model in MODELS:
    rows = sorted((r for r in scale_rows if r["model"] == model), key=lambda r: int(
        r["requested_train_documents"]))
    x = [int(r["usable_train_documents"]) for r in rows]
    axes[0].plot(x, [float(r["strict_span_f1"])
                 for r in rows], marker="o", label=LABELS[model])
    axes[1].plot(x, [float(r["train_seconds"]) / 60 for r in rows],
                 marker="o", label=LABELS[model])
axes[0].set(xlabel="Usable training documents",
            ylabel="Strict typed span F1", ylim=(0.90, 0.97))
axes[1].set(xlabel="Usable training documents",
            ylabel="Training time (minutes)")
for ax in axes:
    ax.grid(alpha=0.25)
axes[0].legend(frameon=False)
fig.tight_layout()
fig.savefig(ROOT / "figures" / "scaling_quality_cost.png", dpi=220)
fig.savefig(ROOT / "figures" / "scaling_quality_cost.pdf")
plt.close(fig)

# Figure 2: per-type mean F1 heatmap.
matrix = np.array([[per_type_summary[m][label]["mean"]
                  for label in types] for m in MODELS])
fig, ax = plt.subplots(figsize=(11, 3.2), constrained_layout=True)
image = ax.imshow(matrix, aspect="auto", vmin=0, vmax=1, cmap="viridis")
ax.set_yticks(range(len(MODELS)), [LABELS[m] for m in MODELS])
ax.set_xticks(range(len(types)), types, rotation=55, ha="right")
fig.colorbar(image, ax=ax, label="Mean strict span F1")
fig.savefig(ROOT / "figures" / "capid_per_type_f1.png", dpi=220)
fig.savefig(ROOT / "figures" / "capid_per_type_f1.pdf")
plt.close(fig)

# Figure 3: validation-locked leakage/retention operating points.
privacy_rows = list(csv.DictReader(
    (ROOT / "results" / "adjusted_privacy_summary.csv").open()))
fig, ax = plt.subplots(figsize=(5.5, 4))
markers = {"test": "o", "reddit": "s"}
for row in privacy_rows:
    ax.errorbar(
        float(row["leakage_mean"]), float(row["retention_mean"]),
        xerr=float(row["leakage_sample_sd"]), yerr=float(row["retention_sample_sd"]),
        marker=markers[row["split"]], capsize=3, linestyle="none",
        label=f"{LABELS[row['model']]} ({row['split']})",
    )
ax.axvline(0.05, color="black", linestyle="--",
           linewidth=1, label="Primary leakage target")
ax.set(xlabel="Irrelevant-character leakage",
       ylabel="Relevant-character retention", xlim=(0, 0.6), ylim=(0, 0.7))
ax.grid(alpha=0.25)
ax.legend(fontsize=7, ncol=2, frameon=False)
fig.tight_layout()
fig.savefig(ROOT / "figures" / "privacy_tradeoff.png", dpi=220)
fig.savefig(ROOT / "figures" / "privacy_tradeoff.pdf")
plt.close(fig)

print(ROOT / "results" / "ERROR_ANALYSIS.md")
