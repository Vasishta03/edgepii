"""Update planning estimates from the measured 5K/10K research runs."""
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
rows = []
for model in ["minilm", "distilbert", "bert"]:
    measured = []
    for size in (5000, 10000):
        path = ROOT / "artifacts" / "runs" / f"{model}-detection-{size}-s42" / "metadata.json"
        metadata = json.loads(path.read_text())
        if metadata["status"] != "completed":
            raise RuntimeError(f"Incomplete basis run: {path}")
        measured.append((metadata["training_documents"], metadata["train_seconds"], metadata["wall_seconds"], metadata["run_id"]))
    train_seconds_per_usable_document = sum(seconds for _, seconds, _, _ in measured) / sum(size for size, _, _, _ in measured)
    wall_seconds_per_usable_document = sum(seconds for _, _, seconds, _ in measured) / sum(size for size, _, _, _ in measured)
    measured_by_requested = {5000: measured[0], 10000: measured[1]}
    usable_ratio = sum(item[0] for item in measured) / 15000
    for requested in (5000, 10000, 25000, 34801):
        basis = measured_by_requested.get(requested)
        usable = basis[0] if basis else round(requested * usable_ratio)
        rows.append({
            "model": model,
            "requested_train_size": requested,
            "estimated_usable_documents": usable,
            "three_epoch_training_hours": (basis[1] if basis else train_seconds_per_usable_document * usable) / 3600,
            "wall_hours": (basis[2] if basis else wall_seconds_per_usable_document * usable) / 3600,
            "status": "measured" if basis else "linear_extrapolation",
            "basis_runs": [item[3] for item in measured],
        })
report = {
    "status": "5K/10K measured; 25K/full linear extrapolation",
    "caveats": "Extrapolations use observed research-v2 CPU time per usable document. They exclude CAPID adaptation, relevance, privacy evaluation and failures, and can change with thermals/background load.",
    "estimates": rows,
    "full_original_three_seed_detector_matrix_wall_hours_estimate": 3 * sum(row["wall_hours"] for row in rows),
    "remaining_after_completed_5K_10K_seed42_wall_hours_estimate": 3 * sum(row["wall_hours"] for row in rows) - sum(row["wall_hours"] for row in rows if row["status"] == "measured"),
}
(ROOT / "results" / "compute_estimate.json").write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps(report, indent=2))
