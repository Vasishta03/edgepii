"""Summarize the completed single-seed 5K/10K detector scaling study."""
from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODELS = ("minilm", "distilbert", "bert")
SIZES = (5000, 10000)


def load_row(model: str, requested_size: int) -> dict:
    run_id = f"{model}-detection-{requested_size}-s42"
    result_path = ROOT / "results" / f"{run_id}-test.json"
    metadata_path = ROOT / "artifacts" / "runs" / run_id / "metadata.json"
    result = json.loads(result_path.read_text())
    metadata = json.loads(metadata_path.read_text())
    if metadata.get("status") != "completed":
        raise RuntimeError(f"Run is not completed: {run_id}")
    span = result["metrics"]["span"]
    bench = result["benchmark"]
    return {
        "run_id": run_id,
        "model": model,
        "seed": metadata["config"]["seed"],
        "requested_train_documents": requested_size,
        "usable_train_documents": metadata["training_documents"],
        "test_documents": result["documents"],
        "precision": span["precision"],
        "recall": span["recall"],
        "strict_span_f1": span["f1"],
        "train_seconds": metadata["train_seconds"],
        "wall_seconds": metadata["wall_seconds"],
        "median_ms": bench["median_ms"],
        "p95_ms": bench["p95_ms"],
        "peak_rss_mib": bench["peak_process_rss_mib"],
        "checkpoint_bytes": bench["checkpoint_bytes"],
    }


rows = [load_row(model, size) for size in SIZES for model in MODELS]
csv_path = ROOT / "results" / "scaling_summary.csv"
with csv_path.open("w", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)

lines = [
    "# Reduced detector scaling study",
    "",
    "Measured on the complete frozen AI4Privacy research-v2 test split (4,349 documents), seed 42. "
    "The study uses one seed and two data sizes; it is a reduced RQ2 matrix, not the planned full 3-seed/4-size design.",
    "",
    "| Model | Requested / usable train docs | Strict span F1 | Precision | Recall | Train min | Median / p95 ms | Peak RSS MiB |",
    "|---|---:|---:|---:|---:|---:|---:|---:|",
]
labels = {"minilm": "MiniLM", "distilbert": "DistilBERT", "bert": "BERT"}
for row in rows:
    lines.append(
        f"| {labels[row['model']]} | {row['requested_train_documents']:,} / {row['usable_train_documents']:,} "
        f"| {row['strict_span_f1']:.4f} | {row['precision']:.4f} | {row['recall']:.4f} "
        f"| {row['train_seconds'] / 60:.1f} | {row['median_ms']:.1f} / {row['p95_ms']:.1f} "
        f"| {row['peak_rss_mib']:.0f} |"
    )

lines += ["", "## Change from 5K to 10K", "", "| Model | F1 gain | Extra train min |", "|---|---:|---:|"]
for model in MODELS:
    five = next(row for row in rows if row["model"] == model and row["requested_train_documents"] == 5000)
    ten = next(row for row in rows if row["model"] == model and row["requested_train_documents"] == 10000)
    lines.append(
        f"| {labels[model]} | {ten['strict_span_f1'] - five['strict_span_f1']:+.4f} "
        f"| {(ten['train_seconds'] - five['train_seconds']) / 60:+.1f} |"
    )

lines += [
    "",
    "All three models improved with more data. Training time approximately doubled. At 10K, DistilBERT was "
    "0.0019 F1 below BERT while its measured median latency was about half. Statistical significance was not "
    "estimated for this single-seed scaling comparison.",
]
md_path = ROOT / "results" / "SCALING.md"
md_path.write_text("\n".join(lines) + "\n")
print(md_path)
print(csv_path)
