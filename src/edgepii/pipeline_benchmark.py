"""Measure the combined local filter, including conservative question masking."""

import argparse, json, time, resource
import numpy as np
from .experiment import ROOT
from .prepare import read_jsonl
from .demo import LocalFilter


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--detector", required=True)
    p.add_argument("--relevance", required=True)
    p.add_argument("--repeats", type=int, default=30)
    p.add_argument("--output", required=True)
    a = p.parse_args()
    if a.repeats < 1:
        raise ValueError("positive repeats required")
    f = LocalFilter(a.detector, a.relevance)
    rows = read_jsonl(ROOT / "data/processed/capid_test.jsonl")

    def run(i):
        r = rows[i % len(rows)]
        return f.filter(r["text"], r["question"], "context-aware", 0.9)

    for i in range(5):
        run(i)
    timings = []
    for i in range(a.repeats):
        start = time.perf_counter()
        run(i)
        timings.append((time.perf_counter() - start) * 1000)
    result = dict(
        detector=a.detector,
        relevance=a.relevance,
        device="cpu",
        threads=4,
        batch_size=1,
        warmup=5,
        repeats=a.repeats,
        unit="context and question",
        includes="detection, per-entity relevance, masking, conservative question detection",
        median_ms=float(np.median(timings)),
        p95_ms=float(np.percentile(timings, 95)),
        raw_ms=timings,
        peak_process_rss_mib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024,
        cpu_model=next(
            (
                s.split(":", 1)[1].strip()
                for s in open("/proc/cpuinfo")
                if s.startswith("model name")
            ),
            "unknown",
        ),
    )
    (ROOT / a.output).write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
