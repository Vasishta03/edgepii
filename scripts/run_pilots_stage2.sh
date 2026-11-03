#!/usr/bin/env bash
# Stage 2 pilots: MiniLM pipeline eval, then DistilBERT/BERT CAPID + relevance pilots.
# Skips runs whose metadata already says completed; continues past failures (logged).
set -uo pipefail
cd "$(dirname "$0")/.."
export PYTHONPATH="$PWD/src"
done_run() { grep -q '"status": *"completed"' "artifacts/runs/$1/metadata.json" 2>/dev/null; }
[ -f results/minilm-privacy-pilot.json ] || bash scripts/evaluate_pipeline_pilot.sh || echo "FAIL minilm pipeline eval"
for run in distilbert-capid-pilot-s42 bert-capid-pilot-s42 distilbert-relevance-pilot-s42 bert-relevance-pilot-s42; do
  done_run "$run" || .venv/bin/python -m edgepii.experiment --config "configs/$run.json" > "logs/$run.log" 2>&1 || { echo "FAIL train $run"; continue; }
  [ -f "results/$run-test.json" ] || .venv/bin/python -m edgepii.benchmark --run "$run" --limit 64 > "logs/$run-test.log" 2>&1 || echo "FAIL test $run"
done
.venv/bin/python scripts/summarize.py > logs/summary.log 2>&1 || echo "FAIL summarize"
echo STAGE2_DONE
