# EdgePII: continuation guide for ChatGPT (from Claude session, 2026-10-27)

Read `CONTINUATION_CLAUDE.md` first: it holds the full mandate, verified data/model revisions,
cautions and completion standard. This file only records what changed in the Claude session.

## Local GUI completion (2026-11-03)

A dependency-free local web interface is available through `bash scripts/run_gui.sh` and opens at
`http://127.0.0.1:7860`. It supports MiniLM, DistilBERT and BERT, both masking policies, the
validation-selected seed-42 thresholds, four synthetic examples, protected context and question output, per-entity
relevance decisions and measured model summaries. Only one model pair remains in memory at a time. Prompts are not
logged or saved, and no external API is used. Browser checks covered the default and responsive layouts plus live
inference through all three model choices. The corrected suite passes 33 tests and all 38 pinned checksums still pass.

## Final Codex completion audit (2026-10-29)

Read `PROJECT_STATUS.md` first; it supersedes historical next-step lists below. All 37 created training runs have
completed metadata. The six missing seed-43/44 question controls completed with `RELEVANCE_CONTROLS_DONE` and are
summarized in `results/RELEVANCE_CONTROLS.md`. The project now includes per-type/length/relevance error analysis,
CAPID exclusion-bias reporting, approximate lexical near-duplicate auditing, three final figures, verified published
reference rows, a measured compute estimate, and `scripts/finalize_project.sh` for one-command regeneration.

The complete original detector matrix is estimated from measured timings at about 131 CPU wall-hours, with about
122 hours still unrun before CAPID/relevance work. The 25K/full-size, larger-seed and matched-update experiments are
therefore declared limitations rather than implied completed work. The IEEE draft is updated and compiled; only
author/institution/supervisor details require user input.

## Codex seed-variance queue (started 2026-10-28)

The validation-only threshold rule was frozen in `docs/PROTOCOL.md` before the new seed test evaluations. The 5%
irrelevant-character leakage target remains the primary criterion. If the detector's mask-all floor makes it
infeasible, a secondary diagnostic threshold maximizes validation relevant-character retention subject to a budget
of `mask-all floor + 5 percentage points`; thresholds are model/seed-specific and the full Pareto curve is reported.

`scripts/generate_seed_pilot_configs.py` generated 18 configs for seeds 43 and 44. These replicate the complete pilot
chain for every model: 512-document AI4Privacy detector, 128-document CAPID adaptation initialized from the matching
seed's detector, and 128-document/eight-epoch balanced relevance model. A verification script confirmed that the
configs differ from seed 42 only in `seed`, `run_id`, and the corresponding CAPID initializer. This is more complete
than reusing the seed-42 detector for both new seeds.

The sequential queue `scripts/run_seed_pilots.sh` started at 07:30 IST on 2026-10-28. Its authoritative progress log
is `logs/seed-pilots-s43-s44.log`; per-run logs and `metadata.json` remain authoritative. At launch,
`minilm-pilot-512-s43` completed and benchmarked successfully, and the queue advanced to
`minilm-capid-pilot-s43`. The queue stops on the first error, refuses existing incomplete run
directories, skips completed training and benchmarks, and ends with `SEED_PILOTS_DONE`. Do not start another copy
while this queue is active. If it is interrupted, inspect the final log line and run metadata; completed items can be
skipped safely, but training runs are not optimizer-resumable and an incomplete run directory must be preserved for
diagnosis before assigning a new run ID.

**Completion update:** the queue finished at 14:23 IST with `SEED_PILOTS_DONE`; all 18 new runs completed and were
benchmarked. `results/SEED_VARIANCE.md` and `results/seed_variance_summary.csv` are generated from all three seeds.
Balanced relevance mean ± sample SD: MiniLM 0.7055 ± 0.0178, DistilBERT 0.7383 ± 0.0084, BERT 0.6278 ± 0.1926.
BERT seed 43 collapsed to the majority-class baseline (0.4068), while seeds 42/44 learned; retain this run and report
the instability rather than rerunning or excluding it. Three-seed CAPID detector F1: MiniLM 0.5039 ± 0.0386,
DistilBERT 0.7290 ± 0.0238, BERT 0.7708 ± 0.0029.

## Adjusted privacy evaluation and reduced scaling (2026-10-28)

`edgepii.calibrate_adjusted` implements the frozen protocol using every decision-changing validation threshold and
records the Pareto curve, primary 5% feasibility, detector mask-all floor, and the secondary floor+5pp operating
point. `edgepii.privacy_eval_locked` reads the saved calibration artifact and evaluates that exact policy without
reselecting on held-out data. Tests cover infeasibility, tie-breaking and Pareto filtering.

`scripts/run_adjusted_privacy_queue.sh` completed all nine model/seed pairs and ended with
`ADJUSTED_PRIVACY_DONE`. It evaluated the validation-locked policy on the full retained test and Reddit splits;
the earlier fixed-.9 files are preserved. The primary 5% target was infeasible for all nine pairs. Under the
predeclared floor+5pp diagnostic, three-seed mean +/- sample SD test leakage/retention was MiniLM
0.1827 +/- 0.0257 / 0.4544 +/- 0.0176, DistilBERT 0.1271 +/- 0.0359 / 0.4775 +/- 0.0694, and BERT
0.0956 +/- 0.0077 / 0.3216 +/- 0.1288. Reddit leakage was much higher: 0.4755, 0.3503 and 0.3299 respectively.
These are diagnostic trade-offs, not privacy guarantees. See `results/ADJUSTED_PRIVACY.md` and
`results/adjusted_privacy_summary.csv`.

The reduced scaling queue completed all six runs at 04:35 IST on 2026-10-29 with `REDUCED_SCALING_DONE`; no run
failed. It used seed 42 and the complete 4,349-document research-v2 test split. At 5K requested / 4,930 usable
training documents, strict span F1 was 0.9217 MiniLM, 0.9414 DistilBERT and 0.9425 BERT. At 10K requested / 9,854
usable documents it was 0.9396, 0.9573 and 0.9592. Training time approximately doubled with data size. The
authoritative table is `results/SCALING.md` and machine-readable data is `results/scaling_summary.csv`.

Post-run validation passed: 27 tests, all 38 pinned checksums and research-v2 split checksums. The manuscript table
generator now consumes the measured multiseed, scaling, pipeline and adjusted-privacy summaries. The updated
three-page IEEE draft compiles successfully to `paper/ieee/main.pdf`. It concludes that no candidate satisfies all
prespecified criteria, while DistilBERT is the strongest measured accuracy/efficiency compromise.

## Codex verification and continuation (2026-10-27)

Claude's stage-2 work was independently checked before any new experiment was started. The queue ended with
`STAGE2_DONE`, no `FAIL` marker was present, every named run had completed metadata, all 38 pinned integrity
checks passed, and the saved BERT run source matched `src/edgepii` except for cache files. Exact evidence is in
`results/CLAUDE_SESSION_VERIFICATION.md`. The mounted `.git` path is not a functional repository, so Git history
could not provide an additional audit.

The relevance collapse also occurs on the 128-document training subset, not only validation/test. Codex added a
declared repair family for all three backbones: balanced cross-entropy weights computed only from the 754 training
entities (508 irrelevant / 246 relevant), eight epochs, unchanged seed/data/learning rate, and validation macro-F1
checkpoint selection. Original runs remain untouched.

Completed repair result so far:

| run | best validation macro F1 | held-out macro F1 | status |
|---|---:|---:|---|
| `minilm-relevance-balanced-pilot-s42` | 0.6804 | 0.7241 | completed |
| `distilbert-relevance-balanced-pilot-s42` | 0.7028 | 0.7471 | completed |
| `bert-relevance-balanced-pilot-s42` | 0.6892 | 0.7158 | completed |

MiniLM's repaired held-out improvement over collapsed MiniLM is 0.3173 macro F1 (paired document bootstrap 95%
CI [0.2663, 0.3659]). Its 0.0390 difference over the original DistilBERT pilot has CI [-0.0116, 0.0868], so the
pilot does not establish superiority. The repaired MiniLM end-to-end pipeline is 344.5 ms median / 622.8 ms p95,
585.0 MiB peak RSS. At threshold .9 it has 27.62% irrelevant-character leakage and 65.42% relevant-character
retention. Validation calibration is still infeasible at 5% leakage because mask-all detector misses leave a
13.53% character-leakage floor.

The repaired DistilBERT run completed in 3,231.6 training seconds (3,546.1 wall seconds), selecting epoch 5. Its
held-out macro F1 is 0.7471. The paired gain over original DistilBERT is 0.0620, CI [0.0115, 0.1125]. Its 0.0230
advantage over repaired MiniLM has CI [-0.0206, 0.0669], so it is not established with one seed. Relevance-only CPU
inference is 643.9 ms median / 982.8 ms p95 with 674.9 MiB peak RSS. Its no-question macro F1 drops to 0.6954 and
10.47% of decisions flip, whereas MiniLM slightly improves without the question (0.7278 versus 0.7241; 7.85% flips).
Therefore DistilBERT currently has stronger evidence of question use; MiniLM's score must not be described as
demonstrated context-aware reasoning.

New reproducibility/support files:

- `scripts/run_relevance_repairs.sh`: skip-completed sequential repair queue.
- `scripts/evaluate_model_pipeline.sh`: generic evaluation for any detector/relevance pair.
- `src/edgepii/relevance_statistics.py`: paired document bootstrap for relevance macro-F1.
- `scripts/plot_relevance_learning.py`: measured validation-learning curves.
- relevance controls now include a no-question ablation plus rotated-question probability/decision sensitivity.

Run all tests and integrity checks before resuming. Never delete a completed run. The exact next command is
`bash scripts/evaluate_model_pipeline.sh distilbert distilbert-relevance-balanced-pilot-s42`; this produces the still
missing DistilBERT privacy, combined pipeline, calibration, and native-coverage artifacts. Then run
`.venv/bin/python -m edgepii.experiment --config configs/bert-relevance-balanced-pilot-s42.json`, benchmark it, run
paired relevance comparisons and the generic pipeline evaluation. `scripts/run_relevance_repairs.sh` can perform the
training/benchmark sequence safely because it skips MiniLM and DistilBERT now that they are complete. Regenerate the
learning curve and measured summary afterward.

## Claude session 2 (2026-10-27): stage 3 queue

Added `scripts/run_stage3.sh` (idempotent, logs `FAIL ...` and continues, ends with `STAGE3_DONE` in `logs/stage3.log`):
1. `evaluate_model_pipeline.sh distilbert distilbert-relevance-balanced-pilot-s42` (privacy, pipeline, controls,
   calibration, native coverage). Codex's earlier controls file was copied to
   `results/distilbert-balanced-pilot-s42-relevance-controls.codex-original.json` before regeneration; diff the two to confirm determinism.
2. `run_relevance_repairs.sh` → trains + benchmarks `bert-relevance-balanced-pilot-s42` (≈2 h CPU expected).
3. Paired relevance bootstraps: BERT-balanced vs original BERT, vs DistilBERT-balanced, vs MiniLM-balanced.
4. `evaluate_model_pipeline.sh bert bert-relevance-balanced-pilot-s42`.
5. `plot_relevance_learning.py`, `summarize.py`.

STAGE3_STATUS: **completed 2026-10-28, no FAIL lines, `STAGE3_DONE` present.** The regenerated DistilBERT controls file
is byte-identical to Codex's copy (deterministic). All values below are one-seed, 64-test-doc exploratory pilots; JSON is authoritative.

| relevance (balanced) | val macro F1 | test macro F1 | no-question | permuted-q | train s | pipeline median/p95 ms | pipeline peak RSS MiB |
|---|---:|---:|---:|---:|---:|---:|---:|
| MiniLM | 0.6804 | 0.7241 | 0.7278 | 0.7122 | 1546 | 344.5 / 622.8 | 585.0 |
| DistilBERT | 0.7028 | 0.7471 | 0.6954 | 0.7365 | 3232 | 733.7 / 1126.9 | 870.3 |
| BERT | 0.6892 | 0.7158 | 0.7098 | 0.7039 | 5223 | 1424.2 / 2002.1 | 1191.6 |

Baselines on the same 382 entities: majority 0.4068, gold-type-only 0.5736. BERT relevance-only inference: 1014 / 1654 ms, 843 MiB.

Paired document bootstrap (2000 reps, seed 42), BERT-balanced minus:
original BERT +0.3089 [0.2586, 0.3594] (repair works); DistilBERT-balanced −0.0313 [−0.0798, 0.0183];
MiniLM-balanced −0.0083 [−0.0579, 0.0436]. **No pair of repaired relevance models is reliably different.**

**Finding: the fixed 0.9 threshold isn't comparable across models.** Repaired BERT never outputs a probability ≥0.9
(0/382 test entities; 132 are ≥0.5), so at 0.9 its "context-aware" policy is mask-all: char leakage 0.0724, retention 0.1078.
MiniLM (115/382 ≥0.9) gives leakage 0.2762 / retention 0.6542, and DistilBERT (140/382) gives 0.2517 / 0.7120. Don't present the 0.9 privacy
numbers as a model ranking. Thresholds must be chosen per model **on validation only**.
Validation calibration at max leakage 5% is **infeasible for all three**, because detector misses set mask-all leakage floors:
MiniLM 13.53%, DistilBERT 5.63%, BERT 6.19%.

## What the Claude session did
1. Verified all six stage-1 pilots finished with `metadata.json` status=completed:
   minilm/distilbert/bert-pilot-512-s42, minilm-pilot-128-s42, minilm-capid-pilot-s42,
   minilm-relevance-pilot-s42. Values are in `results/results.csv` and `results/*-test.json`.
2. Added `scripts/run_pilots_stage2.sh` (skips completed runs, continues past failures and logs `FAIL ...`):
   - `scripts/evaluate_pipeline_pilot.sh` → MiniLM privacy eval, pipeline benchmark, relevance controls,
     validation calibration, CAPID native diagnostic (test+reddit), demo example, summarize.
   - distilbert/bert CAPID pilots and distilbert/bert relevance pilots, each followed by a 64-doc test benchmark.
   - `scripts/summarize.py` at the end. Queue log: `logs/stage2.log` (ends with `STAGE2_DONE`).
3. No source code, data, configs or existing runs were modified.

## Stage-2 status
All finished with no `FAIL` lines; `scripts/summarize.py` regenerated `results/results.csv`, `measured_summary.csv`
and `MEASURED.md`. Exploratory pilots, seed 42, 64 test docs, CPU 4 threads, batch 1 (the JSON files hold the authoritative values):

| run | train docs | val | test | median / p95 ms | peak RSS MiB (infer) |
|---|---|---|---|---|---|
| minilm-capid-pilot | 125 | 0.539 | span F1 0.548 | see json | see json |
| distilbert-capid-pilot | 125 | 0.722 | span F1 0.734 | 91 / 148 | 628 |
| bert-capid-pilot | 125 | 0.736 | span F1 0.769 | 174 / 282 | 789 |
| minilm-relevance-pilot | 128 | 0.401 | macro F1 0.407 | 181 / 297 | 514 |
| distilbert-relevance-pilot | 128 | 0.641 | macro F1 0.685 (acc 0.720) | 514 / 834 | 667 |
| bert-relevance-pilot | 128 | 0.401 | macro F1 0.407 | 1072 / 1688 | 833 |

**Important finding: relevance collapse:** MiniLM and BERT relevance pilots predict a nearly constant probability
(MiniLM 0.287–0.301, BERT 0.270–0.278 across all 382 test entities; none ≥0.5), so they predict the majority class only.
Their identical 0.407 macro F1 is a degenerate result, not a learned one. DistilBERT spreads 0.05–0.87.
Probable causes to investigate (not verified): 128 training docs too few, learning rate/epochs, class imbalance.
Check `logs/{minilm,bert}-relevance-pilot-s42.log` loss curves before the full relevance runs. Consider class weighting or more
epochs, applied identically to all three models and chosen on validation only.

MiniLM pipeline (`results/minilm-*.json`): end-to-end median 259 ms / p95 399 ms, peak RSS 578 MiB. Privacy eval (thr 0.9):
context-aware equals mask-all (irrelevant-entity leakage 0.218, relevant-char retention 0.196) because relevance collapsed.
Leakage there comes from missed detections. Validation calibration at max leakage 0.05: **infeasible**.
`minilm-capid-full-{test,reddit}.json` hold the native coverage diagnostic. The DistilBERT/BERT pipeline eval has NOT been run yet.

## Historical next steps after Claude session 2 (completed or superseded by the 2026-10-29 status above)
Pilot stage is now complete for all three backbones (AI4Privacy detector, CAPID detector, balanced relevance, pipeline).
Remaining work to finish the 8-credit project, in order:
1. `.venv/bin/python -m pytest -q` and `python3 scripts/check_integrity.py` first.
2. **Threshold protocol (no test peeking):** the 5% budget is infeasible. Declare *before looking at test* a
   validation-only rule, e.g. "the lowest threshold whose validation leakage ≤ mask-all floor + 5 pp", or report the
   full validation leakage/retention curve per model (already in `results/*-balanced-pilot-s42-validation-calibration.json`
   `candidates`). Then rerun `edgepii.privacy_eval` on test with each model's chosen threshold (new output names; keep the 0.9 files).
   Write the rule into `docs/PROTOCOL.md` before running it.
3. **Seed variance (most important for credibility):** copy the `*-capid-pilot-s42` and `*-relevance-balanced-pilot-s42`
   configs to s43/s44 (change only `run_id` and `seed`; CAPID detectors keep `initialize_from` the s42 AI4Privacy pilot unless
   you also rerun those). Estimated CPU: ≈3 h per seed for the three relevance models, ≈10 min for the CAPID detectors.
   Report mean ± sd and per-seed bootstraps.
4. **Data-size RQ (reduced matrix, stated as a limitation):** `*-detection-5000-s42` for all three models, then 10000
   (≈0.5/1.1/2+ h each by `compute_estimate.json`; research max length 256 makes this slower). Seeds 43/44 at 5000 if time allows.
   Use a GPU (Kaggle/Colab) for 25000/34801, and record the GPU and VRAM only if they were measured.
5. `scripts/summarize.py`, `scripts/paper_tables.py`, update `paper/ieee/main.tex` (pilot tables plus the threshold finding and the
   question-ablation limitation: only DistilBERT shows a material no-question drop), compile with local pdflatex, then inspect the PDF.
6. Answer the primary RQ honestly. Current pilot evidence: MiniLM is the cheapest pipeline (≈2× faster, ≈2× less RAM than
   DistilBERT; ≈4× faster than BERT) with statistically indistinguishable relevance F1. But its detector is much weaker
   (CAPID span F1 0.548 vs 0.734/0.769; AI4Privacy 0.579 vs 0.786/0.819), and it doesn't use the question. No "smallest
   adequate model" claim until steps 2–4 hold up.

## Older next steps (Claude session 1, partly done)
1. Check `logs/stage2.log` for `FAIL` lines; inspect the matching `logs/<run>.log`. Rerun a failed run only
   after deleting its *incomplete* `artifacts/runs/<run>` dir (never delete a completed one), or copy the
   config with a new `run_id`.
2. (After fixing relevance collapse) run the same pipeline evaluation for DistilBERT and BERT: copy `scripts/evaluate_pipeline_pilot.sh`,
   swap the `minilm` paths/output names for `distilbert`/`bert`.
3. Paired bootstrap on the CAPID pilots (`python -m edgepii.statistics --help`).
4. Full research matrix (`configs/*-detection-{5000,10000,25000,34801}-s{42,43,44}.json`, then
   `*-capid-full-*`, `*-relevance-full-*`). Estimate ≈161 CPU hours for the detectors alone
   (`results/compute_estimate.json`). Not feasible on this laptop in one go. Suggested cut, to be stated
   as a limitation: all models at 5K and 10K × 3 seeds; full size seed 42 only. Or use a GPU (Colab/Kaggle):
   the code supports CUDA, and VRAM is only reported when it is actually measured.
   Run sequentially (16 GB RAM, other apps use much of it, swap was full on 2026-10-27).
5. Calibrate thresholds on validation only (`edgepii.calibrate`), then final test + Reddit eval.
6. `scripts/summarize.py`, `scripts/paper_tables.py`, update `paper/ieee/main.tex`, compile with local pdflatex.
   Keep everything labelled "exploratory pilot" until the multi-seed results exist.

## Commands
```bash
cd /home/pixie/Documents/manipal/minor_proj
export PYTHONPATH="$PWD/src"
.venv/bin/python -m pytest -q
python3 scripts/check_integrity.py
bash scripts/run_pilots_stage2.sh > logs/stage2.log 2>&1   # idempotent
```

## Final deliverables pass (2026-11-03)

- Added current server-process RSS to the GUI through `/api/health`. This is live inference-server memory, not training RAM and not the controlled pipeline peak-RSS benchmark.
- Simplified the web page to plain HTML with a short header, direct labels, no footer or promotional tagline, and an explanation of what the task question does in each masking policy.
- Added four checked synthetic examples and `docs/DEMO_GUIDE.md`. The recommended presentation setting is BERT with `Mask all detected`. The identity example produces exactly: `My passport number is [REDACTED]. I was born on [REDACTED].`
- Rewrote and compiled the IEEE-style paper with the final authors: Vasishta Nandipati, Karthikeya Davasam, and Tirth Koradia, Manipal Institute of Technology, Manipal. The final PDF is five pages and was visually checked page by page. Fonts are embedded and there are no Type 3 fonts.
- Created `presentation/output/EdgePII_Presentation_2026-11-03.pptx`. It contains 11 slides, three editable native tables, and three editable native charts. Package integrity, layout, font, native object, and first-party import checks all pass with zero findings.
- Replaced the long README with a plain project summary, results, setup, reproduction commands, limitations, deliverables, and authors.
- GitHub upload is the only external step still pending. The saved GitHub CLI tokens are expired, and the mounted empty `.git` directory is read-only. Use an in-folder alternate Git directory for the local commit, then reauthenticate `gh` before creating and pushing the remote repository. Do not commit raw data, generated research splits, caches, environments, or the 9.8 GB of model checkpoints.
