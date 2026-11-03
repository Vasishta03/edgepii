#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
export PYTHONPATH="$PWD/src"
for model in minilm distilbert bert; do
  run="${model}-pilot-512-s42"
  .venv/bin/python -m edgepii.experiment --config "configs/$run.json" > "logs/$run.log" 2>&1
  .venv/bin/python -m edgepii.benchmark --run "$run" --limit 64 > "logs/$run-test.log" 2>&1
done
for run in minilm-pilot-128-s42 minilm-capid-pilot-s42 minilm-relevance-pilot-s42; do
  .venv/bin/python -m edgepii.experiment --config "configs/$run.json" > "logs/$run.log" 2>&1
  .venv/bin/python -m edgepii.benchmark --run "$run" --limit 64 > "logs/$run-test.log" 2>&1
done
