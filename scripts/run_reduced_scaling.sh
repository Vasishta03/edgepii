#!/usr/bin/env bash
# Reduced RQ2 matrix: 5K then 10K, all three backbones, seed 42.
set -euo pipefail
cd "$(dirname "$0")/.."
export PYTHONPATH="$PWD/src"
py=.venv/bin/python

is_complete() {
  local run_id="$1" metadata="artifacts/runs/${run_id}/metadata.json"
  [ -f "$metadata" ] && python3 -c \
    'import json,sys; raise SystemExit(json.load(open(sys.argv[1])).get("status")!="completed")' \
    "$metadata"
}

for size in 5000 10000; do
  for model in minilm distilbert bert; do
    run_id="${model}-detection-${size}-s42"
    if is_complete "$run_id"; then
      echo "SKIP completed ${run_id}"
    elif [ -e "artifacts/runs/${run_id}" ]; then
      echo "REFUSE existing incomplete run: ${run_id}" >&2
      exit 1
    else
      echo "TRAIN ${run_id} $(date --iso-8601=seconds)"
      "$py" -m edgepii.experiment --config "configs/${run_id}.json" \
        > "logs/${run_id}.log" 2>&1
    fi
    if [ -f "results/${run_id}-test.json" ]; then
      echo "SKIP benchmark ${run_id}"
    else
      echo "BENCHMARK ${run_id} $(date --iso-8601=seconds)"
      "$py" -m edgepii.benchmark --run "$run_id" \
        > "logs/${run_id}-test.log" 2>&1
    fi
  done
done
echo "REDUCED_SCALING_DONE $(date --iso-8601=seconds)"
