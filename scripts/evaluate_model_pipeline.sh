#!/usr/bin/env bash
# Evaluate one completed detector/relevance pair without retraining either model.
set -euo pipefail
cd "$(dirname "$0")/.."
export PYTHONPATH="$PWD/src"

if [ "$#" -lt 1 ] || [ "$#" -gt 2 ]; then
  echo "usage: $0 MODEL [RELEVANCE_RUN_ID]" >&2
  exit 2
fi

model="$1"
relevance_run="${2:-${model}-relevance-pilot-s42}"
detector_run="${model}-capid-pilot-s42"
detector="artifacts/runs/${detector_run}/checkpoint"
relevance="artifacts/runs/${relevance_run}/checkpoint"
prefix="${model}-${relevance_run#${model}-relevance-}"

for metadata in "artifacts/runs/${detector_run}/metadata.json" "artifacts/runs/${relevance_run}/metadata.json"; do
  python3 -c 'import json,sys; assert json.load(open(sys.argv[1]))["status"]=="completed", sys.argv[1]' "$metadata"
done

.venv/bin/python -m edgepii.privacy_eval \
  --detector "$detector" --relevance "$relevance" --split test --limit 64 \
  --threshold .9 --output "results/${prefix}-privacy-pilot.json" \
  > "logs/${prefix}-privacy-pilot.log" 2>&1
.venv/bin/python -m edgepii.pipeline_benchmark \
  --detector "$detector" --relevance "$relevance" \
  --output "results/${prefix}-pipeline-benchmark.json" \
  > "logs/${prefix}-pipeline-benchmark.log" 2>&1
.venv/bin/python -m edgepii.relevance_controls \
  --checkpoint "$relevance" --output "results/${prefix}-relevance-controls.json" \
  > "logs/${prefix}-relevance-controls.log" 2>&1
.venv/bin/python -m edgepii.calibrate \
  --detector "$detector" --relevance "$relevance" \
  --output "results/${prefix}-validation-calibration.json" \
  > "logs/${prefix}-validation-calibration.log" 2>&1
for split in test reddit; do
  .venv/bin/python -m edgepii.capid_native_eval \
    --detector "$detector" --split "$split" \
    --output "results/${model}-capid-full-${split}.json" \
    > "logs/${model}-capid-full-${split}.log" 2>&1
done
