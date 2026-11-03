#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
export PYTHONPATH="$PWD/src"
detector=artifacts/runs/minilm-capid-pilot-s42/checkpoint
relevance=artifacts/runs/minilm-relevance-pilot-s42/checkpoint
.venv/bin/python -m edgepii.privacy_eval --detector "$detector" --relevance "$relevance" --split test --limit 64 --threshold .9 --output results/minilm-privacy-pilot.json > logs/minilm-privacy-pilot.log 2>&1
.venv/bin/python -m edgepii.pipeline_benchmark --detector "$detector" --relevance "$relevance" --output results/minilm-pipeline-benchmark.json > logs/minilm-pipeline-benchmark.log 2>&1
.venv/bin/python -m edgepii.relevance_controls --checkpoint "$relevance" --output results/minilm-relevance-controls.json > logs/minilm-relevance-controls.log 2>&1
.venv/bin/python -m edgepii.calibrate --detector "$detector" --relevance "$relevance" --output results/minilm-validation-calibration.json > logs/minilm-validation-calibration.log 2>&1
for split in test reddit; do
  .venv/bin/python -m edgepii.capid_native_eval --detector "$detector" --split "$split" --output "results/minilm-capid-full-$split.json" > "logs/minilm-capid-full-$split.log" 2>&1
done
.venv/bin/python -m edgepii.demo --detector "$detector" --relevance "$relevance" --text 'My name is Alice and I live in London.' --question 'What museums can I visit?' --policy context-aware > results/demo-example.json
.venv/bin/python scripts/summarize.py > logs/summary.log
