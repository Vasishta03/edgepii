#!/usr/bin/env bash
# Complete no-question and rotated-question controls for balanced relevance seeds 43/44.
set -euo pipefail
cd "$(dirname "$0")/.."
export PYTHONPATH="$PWD/src"
py=.venv/bin/python

for seed in 43 44; do
  for model in minilm distilbert bert; do
    run_id="${model}-relevance-balanced-pilot-s${seed}"
    checkpoint="artifacts/runs/${run_id}/checkpoint"
    output="results/${model}-balanced-pilot-s${seed}-relevance-controls.json"
    log="logs/${model}-balanced-pilot-s${seed}-relevance-controls.log"
    python3 -c 'import json,sys; assert json.load(open(sys.argv[1]))["status"]=="completed"' \
      "artifacts/runs/${run_id}/metadata.json"
    if [ -f "$output" ]; then
      echo "SKIP ${output}"
    else
      echo "CONTROL ${run_id} $(date --iso-8601=seconds)"
      "$py" -m edgepii.relevance_controls --checkpoint "$checkpoint" --output "$output" > "$log" 2>&1
    fi
  done
done
echo "RELEVANCE_CONTROLS_DONE $(date --iso-8601=seconds)"
