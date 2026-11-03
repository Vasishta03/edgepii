"""Generate manuscript tables from measured artifacts; no hard-coded scores."""
from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "paper" / "ieee" / "tables" / "results.tex"
LABELS = {"minilm": "MiniLM", "distilbert": "DistilBERT", "bert": "BERT"}


def csv_rows(name: str) -> list[dict]:
    with (ROOT / "results" / name).open(newline="") as handle:
        return list(csv.DictReader(handle))


seed_rows = csv_rows("seed_variance_summary.csv")
scale_rows = csv_rows("scaling_summary.csv")
privacy_rows = csv_rows("adjusted_privacy_summary.csv")

lines = [
    r"\begin{table}[t]",
    r"\centering",
    r"\caption{Three-seed exploratory pilots (mean $\pm$ sample SD). Detection is strict typed span F1; relevance is macro-F1.}",
    r"\label{tab:multiseed}",
    r"\begin{tabular}{lrrr}",
    r"\toprule",
    r"Model & AI4P det. & CAPID det. & Relevance \\",
    r"\midrule",
]
for model in LABELS:
    values = {}
    for task in ("ai4privacy_detection", "capid_detection", "balanced_relevance"):
        row = next(r for r in seed_rows if r["model"] == model and r["task"] == task)
        values[task] = f"{float(row['mean']):.3f} $\\pm$ {float(row['sample_sd']):.3f}"
    lines.append(
        f"{LABELS[model]} & {values['ai4privacy_detection']} & {values['capid_detection']} & "
        f"{values['balanced_relevance']} \\\\"
    )
lines += [r"\bottomrule", r"\end{tabular}", r"\end{table}", ""]

lines += [
    r"\begin{table*}[t]",
    r"\centering",
    r"\caption{Reduced AI4Privacy research-v2 scaling study, seed 42, complete 4,349-document test split. Training documents are requested/usable.}",
    r"\label{tab:scaling}",
    r"\begin{tabular}{lrrrrrr}",
    r"\toprule",
    r"Model & Train docs & P & R & F1 & Train min & Median/p95 ms \\",
    r"\midrule",
]
for row in scale_rows:
    lines.append(
        f"{LABELS[row['model']]} & {int(row['requested_train_documents']):,}/{int(row['usable_train_documents']):,} & "
        f"{float(row['precision']):.3f} & {float(row['recall']):.3f} & {float(row['strict_span_f1']):.3f} & "
        f"{float(row['train_seconds']) / 60:.1f} & {float(row['median_ms']):.1f}/{float(row['p95_ms']):.1f} \\\\"
    )
lines += [r"\bottomrule", r"\end{tabular}", r"\end{table*}", ""]

lines += [
    r"\begin{table}[t]",
    r"\centering",
    r"\caption{Seed-42 end-to-end CAPID pilot pipeline resources on CPU.}",
    r"\label{tab:pipeline}",
    r"\begin{tabular}{lrrr}",
    r"\toprule",
    r"Model & Median ms & p95 ms & RSS MiB \\",
    r"\midrule",
]
for model in LABELS:
    data = json.loads((ROOT / "results" / f"{model}-balanced-pilot-s42-pipeline-benchmark.json").read_text())
    lines.append(
        f"{LABELS[model]} & {data['median_ms']:.0f} & {data['p95_ms']:.0f} & "
        f"{data['peak_process_rss_mib']:.0f} \\\\"
    )
lines += [r"\bottomrule", r"\end{tabular}", r"\end{table}", ""]

lines += [
    r"\begin{table}[t]",
    r"\centering",
    r"\caption{Validation-locked floor+5pp diagnostic (three-seed mean $\pm$ SD). Leak is irrelevant-character leakage; Ret. is relevant-character retention. The 5\% primary target was infeasible.}",
    r"\label{tab:privacy}",
    r"\begin{tabular}{llrr}",
    r"\toprule",
    r"Split & Model & Leak & Ret. \\",
    r"\midrule",
]
for split in ("test", "reddit"):
    for model in LABELS:
        row = next(r for r in privacy_rows if r["split"] == split and r["model"] == model)
        lines.append(
            f"{split.title()} & {LABELS[model]} & {float(row['leakage_mean']):.3f} $\\pm$ "
            f"{float(row['leakage_sample_sd']):.3f} & {float(row['retention_mean']):.3f} $\\pm$ "
            f"{float(row['retention_sample_sd']):.3f} \\\\"
        )
    if split == "test":
        lines.append(r"\midrule")
lines += [r"\bottomrule", r"\end{tabular}", r"\end{table}"]

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text("\n".join(lines) + "\n")
print(OUT)
