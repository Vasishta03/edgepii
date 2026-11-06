#!/usr/bin/env bash
# Rebuild final summaries, figures and the IEEE PDF from frozen measured artifacts.
set -euo pipefail
cd "$(dirname "$0")/.."
export PYTHONPATH="$PWD/src"
export PIP_CACHE_DIR="$PWD/.cache/pip"
py=.venv/bin/python

"$py" -m pip check
"$py" - <<'PY'
import glob,json,os
paths=glob.glob('artifacts/runs/*/metadata.json')
bad=[(os.path.basename(os.path.dirname(p)),json.load(open(p)).get('status')) for p in paths if json.load(open(p)).get('status')!='completed']
if bad: raise SystemExit(f'Non-completed runs: {bad}')
print(f'Verified {len(paths)} completed run metadata files')
PY
"$py" -m pytest -q
"$py" scripts/check_integrity.py
"$py" scripts/summarize.py > logs/final-summarize.log
"$py" scripts/summarize_seed_pilots.py > logs/final-seed-summary.log
"$py" scripts/summarize_adjusted_privacy.py > logs/final-privacy-summary.log
"$py" scripts/summarize_scaling.py > logs/final-scaling-summary.log
"$py" scripts/summarize_relevance_controls.py > logs/final-relevance-controls-summary.log
"$py" scripts/final_analysis.py > logs/final-analysis.log
"$py" scripts/audit_near_duplicates.py > logs/final-near-duplicate-audit.log
"$py" scripts/estimate_compute.py > logs/compute-estimate-measured.log
"$py" scripts/paper_tables.py > logs/final-paper-tables.log
(
  cd paper/ieee
  pdflatex -interaction=nonstopmode -halt-on-error main.tex > ../../logs/paper-pass1.log
  pdflatex -interaction=nonstopmode -halt-on-error main.tex > ../../logs/paper-pass2.log
)
test -s paper/ieee/main.pdf
echo "FINALIZATION_DONE $(date --iso-8601=seconds)"
