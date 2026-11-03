# EdgePII

EdgePII is a local research prototype for detecting personally identifiable information and estimating whether each detected entity is relevant to a task question. It compares MiniLM-L6-H384, DistilBERT-base-uncased, and BERT-base-uncased under the same preprocessing and evaluation protocol.

The project uses AI4Privacy PII-200K for larger-scale detector training and a retained CAPID subset for contextual detection and relevance experiments. Published CAPID and PII-Bench values are kept separate from reproduced results. The PII-Bench dataset was not obtained or reproduced.

## Main findings

Three-seed exploratory CAPID pilots used 64 test documents per seed.

| Model | CAPID strict span F1 | Relevance macro F1 | Pipeline median / p95 | Peak RSS |
|---|---:|---:|---:|---:|
| MiniLM | 0.504 +/- 0.039 | 0.705 +/- 0.018 | 345 / 623 ms | 585 MiB |
| DistilBERT | 0.729 +/- 0.024 | 0.738 +/- 0.008 | 734 / 1127 ms | 870 MiB |
| BERT | 0.771 +/- 0.003 | 0.628 +/- 0.193 | 1424 / 2002 ms | 1192 MiB |

No tested model satisfies every declared deployment criterion. MiniLM is cheapest but its CAPID detector is much weaker. BERT detects best but has the highest resource cost and unstable relevance training. DistilBERT is the strongest measured accuracy and efficiency compromise.

The original 5% irrelevant-character leakage target is infeasible for every model and seed. Missed detector spans remain visible even when every detected entity is masked. This system is a research prototype, not a privacy guarantee.

Increasing usable AI4Privacy training data from 4,930 to 9,854 documents improved strict span F1 by 0.0158 to 0.0179 while training time approximately doubled. The scaling study used one seed and two data sizes, so it is reported as limited evidence.

## Local demo

From the repository root:

```bash
bash scripts/run_gui.sh
```

Open `http://127.0.0.1:7860`.

The page supports all three models, conservative masking, optional context-aware retention, synthetic examples, detected entities, inference time, and current server-process RAM. Use BERT with `Mask all detected` for the prepared presentation examples. See `docs/DEMO_GUIDE.md`.

The task question does not ask the system to generate an answer. In context-aware mode, it helps the relevance classifier decide which detected entities may be needed for the task. In mask-all mode, every detected entity is removed regardless of the question. The question is still scanned for PII.

## Setup

```bash
python3 -m venv .venv
export PIP_CACHE_DIR="$PWD/.cache/pip"
.venv/bin/pip install torch==2.8.0 --index-url https://download.pytorch.org/whl/cpu
.venv/bin/pip install -r requirements.txt
export PYTHONPATH="$PWD/src"
python3 scripts/fetch_data.py
python3 scripts/fetch_models.py
PYTHONPATH=src .venv/bin/python -m edgepii.prepare
.venv/bin/python -m pytest -q
```

Downloads are pinned by revision and checksum. Raw data and model checkpoints are excluded from Git because they are large and must be fetched from their original sources.

## Reproduce the final analysis

```bash
bash scripts/finalize_project.sh
```

This validates completed runs, runs tests and checksum checks, regenerates summaries and figures, rebuilds manuscript tables, and compiles the IEEE paper.

For a single configured experiment:

```bash
export PYTHONPATH="$PWD/src"
.venv/bin/python -m edgepii.experiment --config configs/minilm-pilot-512-s42.json
.venv/bin/python -m edgepii.benchmark --run minilm-pilot-512-s42 --limit 64
```

Run directories are immutable. Repeating an experiment requires a new `run_id`.

## Important files

- `docs/PROTOCOL.md`: experiment and threshold protocol
- `docs/SOURCES_AND_LICENSES.md`: sources, revisions, and licenses
- `docs/DEMO_GUIDE.md`: checked presentation examples
- `PROJECT_STATUS.md`: final project status and limitations
- `results/SEED_VARIANCE.md`: three-seed pilot summary
- `results/SCALING.md`: 5K and 10K detector scaling study
- `results/ADJUSTED_PRIVACY.md`: validation-locked privacy analysis
- `results/ERROR_ANALYSIS.md`: per-type and context-length failures
- `paper/ieee/main.pdf`: compiled IEEE-style paper
- `presentation/output/EdgePII_Presentation_2026-11-03.pptx`: presentation deck

## Repository layout

- `src/edgepii`: preprocessing, modeling, evaluation, statistics, demo, and web server
- `configs`: label mapping and experiment configurations
- `scripts`: acquisition, queues, summaries, validation, and paper generation
- `tests`: unit and integration tests
- `results`: machine-readable outputs and research summaries
- `figures`: plots generated from measured results
- `paper`: IEEE source and compiled PDF
- `presentation`: editable PPTX build source and final deck

## Limitations

CAPID experiments use a retained flat-span subset and are not a reproduction of the official protocol. AI4Privacy is synthetic. The multi-seed experiments are small pilots, while the reduced scaling study uses one seed. Character retention is not downstream answer quality. No formal privacy guarantee, regulatory claim, GPU benchmark, full-data matrix, or PII-Bench reproduction is made.

## Authors

Vasishta Nandipati, Karthikeya Davasam, and Tirth Koradia

Manipal Institute of Technology, Manipal
