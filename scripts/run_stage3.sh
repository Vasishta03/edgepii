#!/usr/bin/env bash
# Stage 3: DistilBERT balanced pipeline eval, BERT balanced relevance repair + benchmark,
# paired relevance bootstraps, BERT pipeline eval, figures/summary. Skips finished outputs.
set -uo pipefail
cd "$(dirname "$0")/.."
export PYTHONPATH="$PWD/src"
py=.venv/bin/python
[ -f results/distilbert-balanced-pilot-s42-validation-calibration.json ] || bash scripts/evaluate_model_pipeline.sh distilbert distilbert-relevance-balanced-pilot-s42 || echo "FAIL distilbert pipeline eval"
bash scripts/run_relevance_repairs.sh || echo "FAIL relevance repairs"
pred() { echo "results/$1-test-predictions.jsonl"; }
boot() { [ -f "results/$3.json" ] || $py -m edgepii.relevance_statistics --a "$(pred $1)" --b "$(pred $2)" --output "results/$3.json" || echo "FAIL boot $3"; }
if [ -f "$(pred bert-relevance-balanced-pilot-s42)" ]; then
  boot bert-relevance-balanced-pilot-s42 bert-relevance-pilot-s42 bert-balanced-minus-original-relevance-bootstrap
  boot bert-relevance-balanced-pilot-s42 distilbert-relevance-balanced-pilot-s42 bert-balanced-minus-distilbert-balanced-relevance-bootstrap
  boot bert-relevance-balanced-pilot-s42 minilm-relevance-balanced-pilot-s42 bert-balanced-minus-minilm-balanced-relevance-bootstrap
  [ -f results/bert-balanced-pilot-s42-validation-calibration.json ] || bash scripts/evaluate_model_pipeline.sh bert bert-relevance-balanced-pilot-s42 || echo "FAIL bert pipeline eval"
fi
$py scripts/plot_relevance_learning.py || echo "FAIL plot"
$py scripts/summarize.py > logs/summary.log 2>&1 || echo "FAIL summarize"
echo STAGE3_DONE
