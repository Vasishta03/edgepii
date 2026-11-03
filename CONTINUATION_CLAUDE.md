# EdgePII continuation handoff

## Final status (2026-10-29)

Use `PROJECT_STATUS.md` as the authoritative current handoff. All 37 created training runs are complete, all nine
balanced relevance checkpoints have question controls, and the reduced 5K/10K scaling matrix, locked privacy
evaluation, error analysis, exclusion audit, approximate near-duplicate audit, verified reference table and compiled
IEEE paper are present. Run `bash scripts/finalize_project.sh` to regenerate and validate deliverables. Historical
queues below are retained only for provenance. The only external blocker is the student's author/institution/
supervisor information.

## Historical seed queue (completed 2026-10-28)

Codex froze the validation-only threshold rule in `docs/PROTOCOL.md`, generated and verified 18 seed-43/44 pilot
configs, and started `scripts/run_seed_pilots.sh` sequentially at 07:30 IST. Unlike the earlier suggestion to reuse
the seed-42 AI4Privacy detector, this queue replicates the complete chain per seed: AI4Privacy detector, CAPID
adaptation initialized from that same seed, and balanced relevance. Monitor `logs/seed-pilots-s43-s44.log` and each
run's `metadata.json`; completion is marked by `SEED_PILOTS_DONE`. Do not launch a second queue while it is active.
The first run, `minilm-pilot-512-s43`, completed and benchmarked successfully; the queue then advanced to
`minilm-capid-pilot-s43`. Tests were 24/24 and all 38 integrity checks passed immediately before launch.

**Completion:** the queue ended at 14:23 IST with `SEED_PILOTS_DONE`; all 18 runs completed and were benchmarked.
Generated summaries are `results/SEED_VARIANCE.md` and `results/seed_variance_summary.csv`. BERT relevance seed 43
collapsed (0.4068), producing 0.6278 ± 0.1926 across three seeds; keep it as measured evidence of instability.
MiniLM relevance is 0.7055 ± 0.0178 and DistilBERT 0.7383 ± 0.0084. CAPID detector F1 is 0.5039 ± 0.0386,
0.7290 ± 0.0238 and 0.7708 ± 0.0029 respectively. Tests remain 24/24 and all integrity checks pass.

The adjusted-threshold queue completed all nine model/seed pairs with `ADJUSTED_PRIVACY_DONE`. New modules
`edgepii.calibrate_adjusted` and `edgepii.privacy_eval_locked` implement the frozen validation-only floor+5pp
diagnostic and locked full-test/Reddit evaluation. The 5% primary target was infeasible for every pair. The
authoritative aggregate is `results/ADJUSTED_PRIVACY.md`; Reddit leakage is substantially higher than retained-test
leakage, and all adjusted values remain diagnostics rather than privacy guarantees.

The reduced scaling queue completed all six 5K/10K seed-42 runs at 04:35 IST on 2026-10-29 with no failures. At
10K requested / 9,854 usable documents, strict span F1 is 0.9396 MiniLM, 0.9573 DistilBERT and 0.9592 BERT. See
`results/SCALING.md` and `results/scaling_summary.csv`. Post-run tests are 27/27 and all pinned/research-v2 checksums
pass. The measured tables and paper were regenerated; `paper/ieee/main.pdf` compiles successfully as a three-page
draft. It makes no smallest-qualifying-model or privacy-guarantee claim; DistilBERT is described as the best measured
practical compromise.

## Latest Codex work (2026-10-27)

Read `CONTINUATION_CHATGPT.md` and `results/CLAUDE_SESSION_VERIFICATION.md` for the exact post-Claude audit and
repair table. Claude's stage-2 queue, completed statuses, reported metrics and all 38 pinned checksums were verified.
The original MiniLM and BERT relevance models were also evaluated on their training subset and still predicted only
the majority class, confirming training collapse rather than validation-only overfitting.

Codex added training-only balanced relevance loss, tests, three separate eight-epoch repair configs, paired
relevance bootstrap statistics, a generic pipeline evaluator, a skip-completed repair queue, learning-curve
generation, and question-dependence controls. The controls now include removing the question (a valid degraded-input
ablation) and rotating it (sensitivity only; CAPID has no counterfactual labels).

`minilm-relevance-balanced-pilot-s42` is complete: validation macro F1 0.6804, held-out macro F1 0.7241. Its
repaired pipeline measured 344.5 ms median / 622.8 ms p95 and 585.0 MiB peak RSS. Threshold .9 produced 27.62%
irrelevant-character leakage and 65.42% relevant-character retention. The 5% validation leakage constraint remains
infeasible because detector misses create a 13.53% mask-all floor. These are still one-seed, 128-document exploratory
results.

`distilbert-relevance-balanced-pilot-s42` is also complete: validation macro F1 0.7028 (epoch 5 selected), held-out
macro F1 0.7471, relevance-only 643.9 ms median / 982.8 ms p95 and 674.9 MiB inference RSS. Its paired improvement
over original DistilBERT is 0.0620, CI [0.0115, 0.1125]; its 0.0230 difference over repaired MiniLM has CI
[-0.0206, 0.0669]. Removing the question lowers DistilBERT to 0.6954 but slightly improves MiniLM to 0.7278, so only
DistilBERT currently shows a material question-ablation penalty. Keep this limitation prominent.

**Update 2026-10-28 (Claude session 2):** BERT balanced repair, DistilBERT/BERT pipeline evals and all bootstraps are complete; see `CONTINUATION_CHATGPT.md` "Claude session 2" for results and the next steps.
Inspect each run's `metadata.json`; never infer completion from the directory. Do not claim a smallest model or context-aware MiniLM winner.

## User mandate
This is an 8-credit minor project. Work only in `/home/pixie/Documents/manipal/minor_proj`. Professional, reproducible implementation; no invented results. Primary RQ: smallest tested encoder satisfying quality/resource constraints. Secondary RQ: training data size versus accuracy/generalization/cost. Compare MiniLM-L6-H384, DistilBERT-base-uncased and BERT-base-uncased; use AI4Privacy PII-200K English and CAPID. IEEE-style manuscript after validated experiments. Distillation/quantization are optional.

## Current project state
The project was empty at start. Source, tests, pinned download scripts, configs, offline demo, training, inference, benchmarks, leakage metrics and bootstrap comparison are implemented. Check `results/results.csv`, `results/experiment_registry.jsonl`, `artifacts/runs/*/metadata.json` and `logs/` for actual execution status. Do not infer completion from a config or a directory alone. A completed checkpoint may be from an early epoch if a later epoch failed; require metadata status=completed.

### Verified data
- CAPID revision `e14c93de9c72c2a0f1ecf32c5655b60402754131`, MIT repository license. Raw: 2,107 training / 200 test / 150 Reddit. After strict flat-span validation: 1,813 train / 180 validation / 191 test / 122 Reddit.
- AI4Privacy revision `7c22e6816b8fc24b7781e9f4e22016c698842dd0`, **custom license**; both license files archived. English file contains 43,501 rows. Frozen v1 split: 34,805 train / 4,347 validation / 4,349 test. Not 43K training examples.
- CAPID uses `context`, `question`, `piis` string keys with `type` and string `relevance`. Exact match all occurrences; no fuzzy repair. Audit exclusions: 128 overlap, 20 missing string, three textual relevance values. `results/data_audit.json` and `data/processed/exclusions.jsonl` are authoritative.
- PII-Bench relevant paper is arXiv:2502.18545, not similarly named newer datasets. **No dataset access verified, no downloaded data, no reproduced result.**

### Models/environment
- MiniLM is `nreimers/MiniLM-L6-H384-uncased`, revision `3276f0fac9d818781d7a1327b3ff818fc4e643c0`. It retains every second layer of L12; do not call it an official independently distilled six-layer Microsoft release.
- DistilBERT: `distilbert/distilbert-base-uncased` revision `12040accade4e8a0f71eabdb258fecc2e7e948be`.
- BERT: `google-bert/bert-base-uncased` revision `86b5e0934494bd15c9632b12f734a8a67f723594`.
- All three vocabulary SHA-256 values match. Model/file manifests have exact byte checksums.
- Project-local `.venv`: Python 3.13.5, CPU PyTorch 2.8.0+cpu, transformers 4.57.1. Successful packages frozen in requirements.lock.txt. CPU Intel i9-13900H, 16 GB RAM, no detected NVIDIA GPU. Other applications use much of the RAM; run large models sequentially.
- Primary PyPI timed out; HTTPS Tsinghua PyPI mirror worked. Backbones and datasets are already downloaded. No further network is needed for training/inference. Git metadata mount is read-only; no Git commits were created.

## Commands
```bash
cd /home/pixie/Documents/manipal/minor_proj
export PYTHONPATH="$PWD/src"
export PIP_CACHE_DIR="$PWD/.cache/pip"
.venv/bin/python -m pytest -q
python3 scripts/check_integrity.py
.venv/bin/python -m edgepii.experiment --config configs/CHOSEN_RUN.json
.venv/bin/python -m edgepii.benchmark --run CHOSEN_RUN --limit 64
```
Existing run directories are deliberately not overwritten. Change `run_id` in a copied config for a rerun. A fresh full pilot sequence is `bash scripts/run_pilots.sh`; do not rerun the entire script over completed IDs. Choose remaining commands individually. Training is not optimizer-resumable; checkpoints are inference/fine-tuning weights, not full optimizer/RNG snapshots.

## Required next research work
1. Finish/inspect the pilot queue. Primary detector pilots use 512 requested documents, 3 epochs, seed 42, max length 128, validation/test prefixes of 64. Label these **exploratory pilots** everywhere. MiniLM's initial run had 504 usable training documents, validation F1 0.5659 and test F1 0.5793; use JSON for authoritative values.
2. Complete MiniLM size-128 pilot, CAPID detection adaptation, relevance pilot, privacy evaluation and combined pipeline benchmark. DistilBERT/BERT CAPID/relevance configs exist but require their detector pilots first.
3. Read `docs/PROTOCOL.md`. AI4Privacy lacks several CAPID categories, so zero-shot transfer alone cannot answer contextual detection RQ1. Final comparison must include CAPID-adapted detectors and relevance classifiers for all backbones.
4. A clean research-v2 is now created at `data/research`, with 34,801 AI4Privacy training documents; pilot v1 remains unchanged. `results/template_audit.json` identifies four AI4Privacy training documents sharing delexicalized templates with validation/test. None is in the first 512 pilot training documents. Those four records are removed from research-v2, and research configs select `data_dir=data/research`. Integrity checks cover both versions. Semantic near-duplicate audit is still needed.
5. Audit exclusions and class coverage. Flat BIO drops nested CAPID records, so reported metrics are on retained subsets and cannot be equated with published CAPID numbers. `edgepii.capid_native_eval` now provides full-file exact value/type coverage, including overlapping and absent gold strings; it is a custom diagnostic, NOT the official CAPID metric. An overlapping span model remains a future option.
6. Run three seeds and full-size matrix after estimating CPU cost. Configs exist for 5K,10K,25K,34,801 × models × seeds 42/43/44, plus full CAPID adaptation/relevance for every model and seed. Research max length 256 differs from pilots. No full matrix result is claimed.
7. Freeze final thresholds/budgets using validation only. `edgepii.calibrate` can explicitly report infeasible. Keep test data out of checkpoint/threshold selection. Add matched-update scaling control.
8. Evaluate all CAPID test and Reddit retained examples; paired bootstrap, per-type errors, seed variance. `edgepii.statistics` compares paired strict span F1. `edgepii.privacy_eval` reports mask-all, context-aware, oracle-span and oracle-policy conditions separately.
9. Record end-to-end pipeline memory/latency (`edgepii.pipeline_benchmark`), not only component costs. CPU measurements are real; GPU/VRAM values must remain absent until actually measured.
10. Generate tables/figures with `scripts/summarize.py`. Draft manuscript must distinguish pilot findings from unanswered RQs. Add published reference table values only after verifying source tables and definitions. No downstream QA utility has been measured; character retention is only a proxy.

## Scientific/implementation cautions
- Split groups by normalized text; training subsets are nested by stable ID ordering.
- Native labels preserved, harmonized into 20 types / 41 BIO tags. Mapping is a documented design choice, not a statement that corpora annotate the same scope.
- Training tokens crossing annotation boundaries reject their whole document; exclusions are logged per run. Same vocabulary does not by itself prove identical tokenizer configurations; compare accepted IDs before final comparisons.
- Sliding-window inference aggregates logits by absolute offsets; no silent tail truncation.
- Relevance uses an entity-centered crop. Very long question/entity inputs raise explicit errors; deployment masks on relevance preprocessing failure.
- Demo defaults to mask-all-detected, and also masks detected PII in the question. Relevance is not disclosure authorization. Missed PII can leak.
- Resource measurements are process peaks, not model-only RAM. Timing depends on background CPU load. Repeat in a controlled environment before claiming strict deployment compliance.
- No certainty about user account credits; never invent a remaining balance.

## Completion standard
A completed software pipeline plus a few pilots is NOT a completed 8-credit research project. Final deliverables require validated multiseed comparisons, honest limitations, reproducible artifacts and a manuscript whose claims follow the actual evidence. Continue from current outputs rather than rebuilding the project.
