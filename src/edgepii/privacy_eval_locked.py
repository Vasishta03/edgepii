"""Evaluate a validation-locked privacy policy on held-out CAPID splits."""

import argparse, hashlib, json
from collections import Counter
from pathlib import Path
from .experiment import ROOT
from .prepare import read_jsonl
from .demo import LocalFilter
from .core import privacy_counts, privacy_rates
from .modeling import detect, relevant_probability


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--calibration", required=True)
    parser.add_argument(
        "--criterion", choices=["primary", "adjusted"], default="adjusted"
    )
    parser.add_argument("--split", choices=["test", "reddit"], required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    calibration_path = ROOT / args.calibration
    calibration = json.loads(calibration_path.read_text())
    selection = calibration[args.criterion]
    if selection["status"] != "feasible" or not selection["chosen"]:
        raise ValueError(f"{args.criterion} calibration is infeasible")
    chosen = selection["chosen"]
    detector = calibration["detector"]
    relevance = calibration["relevance"]
    filt = LocalFilter(detector, relevance)
    rows = read_jsonl(ROOT / "data/processed" / f"capid_{args.split}.jsonl")
    counts = {
        name: Counter()
        for name in [
            "mask_all_detected",
            "locked_policy",
            "oracle_spans_locked_policy",
            "keep_all",
            "oracle_policy",
        ]
    }
    for record in rows:
        predicted = detect(
            record,
            filt.detector,
            filt.dt,
            filt.detection_length,
            filt.detection_stride,
            "cpu",
        )

        def selected_mask(spans):
            if chosen["policy"] == "mask-all-detected":
                return spans
            masked = []
            for span in spans:
                try:
                    prob = relevant_probability(
                        record,
                        span,
                        filt.relevance,
                        filt.rt,
                        filt.relevance_length,
                        "cpu",
                    )
                except ValueError:
                    prob = -1.0
                if prob < chosen["threshold"]:
                    masked.append(span)
            return masked

        policies = dict(
            mask_all_detected=predicted,
            locked_policy=selected_mask(predicted),
            oracle_spans_locked_policy=selected_mask(record["spans"]),
            keep_all=[],
            oracle_policy=[span for span in record["spans"] if span["relevance"] == 0],
        )
        for name, masked in policies.items():
            counts[name].update(privacy_counts(record["spans"], masked))
    result = dict(
        split=args.split,
        documents=len(rows),
        criterion=args.criterion,
        calibration_file=str(Path(args.calibration)),
        calibration_sha256=hashlib.sha256(calibration_path.read_bytes()).hexdigest(),
        validation_operating_point=chosen,
        detector=detector,
        relevance=relevance,
        policy_note="Threshold/policy selected on validation only. Primary feasibility remains separate from the adjusted diagnostic.",
        metrics={name: privacy_rates(value) for name, value in counts.items()},
    )
    (ROOT / args.output).write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
