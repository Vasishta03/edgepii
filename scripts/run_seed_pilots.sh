#!/usr/bin/env bash
# Sequentially reproduce the entire pilot chain for seeds 43 and 44.
set -euo pipefail
cd "$(dirname "$0")/.."
export PYTHONPATH="$PWD/src"
py=.venv/bin/python

is_complete() {
  local run_id="$1"
  local metadata="artifacts/runs/${run_id}/metadata.json"
  [ -f "$metadata" ] && python3 -c \
    'import json,sys; raise SystemExit(json.load(open(sys.argv[1])).get("status")!="completed")' \
    "$metadata"
}

run_one() {
  local run_id="$1"
  local config="configs/${run_id}.json"
  if is_complete "$run_id"; then
    echo "SKIP completed ${run_id}"
  elif [ -e "artifacts/runs/${run_id}" ]; then
    echo "REFUSE existing incomplete run: ${run_id}" >&2
    exit 1
  else
    echo "TRAIN ${run_id} $(date --iso-8601=seconds)"
    "$py" -m edgepii.experiment --config "$config" \
      > "logs/${run_id}.log" 2>&1
  fi

  if [ -f "results/${run_id}-test.json" ]; then
    echo "SKIP benchmark ${run_id}"
  else
    echo "BENCHMARK ${run_id} $(date --iso-8601=seconds)"
    "$py" -m edgepii.benchmark --run "$run_id" --limit 64 \
      > "logs/${run_id}-test.log" 2>&1
  fi
}

for seed in 43 44; do
  for model in minilm distilbert bert; do
    run_one "${model}-pilot-512-s${seed}"
    run_one "${model}-capid-pilot-s${seed}"
    run_one "${model}-relevance-balanced-pilot-s${seed}"
  done
done

echo "SEED_PILOTS_DONE $(date --iso-8601=seconds)"
