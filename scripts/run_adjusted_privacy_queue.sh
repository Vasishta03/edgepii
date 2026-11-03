#!/usr/bin/env bash
# Calibrate each completed seed on validation, then evaluate its locked diagnostic policy.
set -euo pipefail
cd "$(dirname "$0")/.."
export PYTHONPATH="$PWD/src"
py=.venv/bin/python

for seed in 42 43 44; do
  for model in minilm distilbert bert; do
    detector="artifacts/runs/${model}-capid-pilot-s${seed}/checkpoint"
    relevance="artifacts/runs/${model}-relevance-balanced-pilot-s${seed}/checkpoint"
    prefix="${model}-balanced-s${seed}-adjusted"
    calibration="results/${prefix}-validation-calibration.json"
    if [ ! -f "$calibration" ]; then
      echo "CALIBRATE ${model} seed ${seed} $(date --iso-8601=seconds)"
      "$py" -m edgepii.calibrate_adjusted --detector "$detector" --relevance "$relevance" \
        --primary-budget .05 --headroom .05 --output "$calibration" \
        > "logs/${prefix}-validation-calibration.log" 2>&1
    else
      echo "SKIP calibration ${model} seed ${seed}"
    fi
    for split in test reddit; do
      output="results/${prefix}-${split}-privacy.json"
      if [ ! -f "$output" ]; then
        echo "EVALUATE ${model} seed ${seed} ${split} $(date --iso-8601=seconds)"
        "$py" -m edgepii.privacy_eval_locked --calibration "$calibration" --criterion adjusted \
          --split "$split" --output "$output" > "logs/${prefix}-${split}-privacy.log" 2>&1
      else
        echo "SKIP evaluation ${model} seed ${seed} ${split}"
      fi
    done
  done
done
echo "ADJUSTED_PRIVACY_DONE $(date --iso-8601=seconds)"
