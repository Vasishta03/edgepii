#!/usr/bin/env bash
# Reproduce the declared balanced-loss relevance repair pilots sequentially.
set -euo pipefail
cd "$(dirname "$0")/.."
export PYTHONPATH="$PWD/src"

is_complete() {
  local run_id="$1"
  local metadata="artifacts/runs/${run_id}/metadata.json"
  [ -f "$metadata" ] && python3 -c \
    'import json,sys; raise SystemExit(json.load(open(sys.argv[1])).get("status")!="completed")' \
    "$metadata"
}

for model in minilm distilbert bert; do
  run_id="${model}-relevance-balanced-pilot-s42"
  config="configs/${run_id}.json"
  if is_complete "$run_id"; then
    echo "SKIP completed ${run_id}"
  elif [ -e "artifacts/runs/${run_id}" ]; then
    echo "REFUSE existing incomplete run: ${run_id}" >&2
    exit 1
  else
    echo "TRAIN ${run_id}"
    .venv/bin/python -m edgepii.experiment --config "$config" \
      > "logs/${run_id}.log" 2>&1
  fi

  if [ ! -f "results/${run_id}-test.json" ]; then
    echo "BENCHMARK ${run_id}"
    .venv/bin/python -m edgepii.benchmark --run "$run_id" --limit 64 \
      > "logs/${run_id}-test.log" 2>&1
  fi
done
