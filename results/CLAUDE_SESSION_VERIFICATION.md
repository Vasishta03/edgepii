# Verification of the Claude continuation session

Verified locally on 2026-10-27 before continuing the experiments. This record distinguishes checks performed in the current session from claims copied from a handoff document.

## Repository and artifact checks

- `logs/stage2.log` ends with `STAGE2_DONE` and contains no `FAIL` marker.
- Every stage-2 run named in `CONTINUATION_CHATGPT.md` has `status: completed` in its own `metadata.json`.
- The source snapshot stored with `bert-relevance-pilot-s42` matches the current `src/edgepii` tree except for Python cache files. This supports Claude's statement that it did not edit source code.
- `scripts/check_integrity.py` verified all 38 pinned source/model/split checksums, including the research-v2 files.
- The stage-2 queue script exists at `scripts/run_pilots_stage2.sh` and skips completed run IDs.
- Git history could not be used as an independent audit because the mounted `.git` path is not a functional repository in this workspace.

## Recomputed artifact findings

All values below were read from the saved prediction/evaluation artifacts; they are exploratory seed-42 pilots on the same 64-document retained CAPID test prefix.

| Task | MiniLM | DistilBERT | BERT-base |
|---|---:|---:|---:|
| CAPID detector strict typed span F1 | 0.5484 | 0.7339 | 0.7687 |
| Original relevance macro F1 | 0.4068 | 0.6851 | 0.4068 |

The original MiniLM and BERT relevance predictions are degenerate: both predict zero relevant entities among 382 gold-span examples. MiniLM probabilities span 0.2867--0.3014 and BERT probabilities span 0.2696--0.2781. DistilBERT probabilities span 0.053--0.869 and it predicts both classes. Re-evaluation on the 128-document training subset showed the same majority-only behavior for MiniLM and BERT, ruling out a validation-only failure.

Paired document bootstrap results support a pilot difference between DistilBERT and MiniLM detection (F1 difference 0.1855, 95% CI [0.1306, 0.2438]). BERT's 0.0348 F1 advantage over DistilBERT has a 95% CI of [-0.0051, 0.0748], so this pilot does not establish that BERT is better.

## Declared relevance repair

The repair is a separate experiment family: eight epochs and inverse-frequency loss weights computed only from the 754 training entities (508 irrelevant, 246 relevant), applied identically to all three models. The original runs are retained unchanged.

The completed MiniLM repair reached validation macro F1 0.6804 and held-out macro F1 0.7241. Its paired difference from the original MiniLM run is 0.3173 (95% document-bootstrap CI [0.2663, 0.3659]). Its 0.0390 difference from the original DistilBERT pilot has CI [-0.0116, 0.0868], so it is not a reliable superiority result. These comparisons still omit training-seed variability.

At threshold 0.9, the repaired MiniLM pipeline trades privacy for retention: irrelevant-character leakage is 0.2762 and relevant-character retention is 0.6542. Combined CPU latency is 344.5 ms median / 622.8 ms p95 with 585.0 MiB peak RSS. Validation calibration remains infeasible at the declared 5% leakage target because detector misses leave a mask-all floor of 13.53% irrelevant-character leakage.

Question rotation changed only 7.59% of MiniLM entity decisions and had a median absolute probability effect of 0.00063. This is a dependence warning, not a counterfactual accuracy result, because CAPID does not supply new labels for rotated questions. A no-question ablation has been added for subsequent evaluations.

The repaired DistilBERT run subsequently completed, selecting epoch 5 at validation macro F1 0.7028. Held-out macro F1 is 0.7471. The paired improvement over original DistilBERT is 0.0620 (95% CI [0.0115, 0.1125]); its 0.0230 difference over repaired MiniLM has CI [-0.0206, 0.0669]. Removing the question lowers DistilBERT macro F1 to 0.6954 and flips 10.47% of decisions. Removing it from MiniLM slightly increases macro F1 to 0.7278 and flips 7.85%, so the MiniLM repair has not demonstrated meaningful question-aware behavior.

## Interpretation boundary

No smallest satisfactory model is established. All results above use one seed, tiny training subsets, a retained CAPID population and CPU measurements affected by the local environment. Published CAPID and PII-Bench values remain separate; no PII-Bench dataset access is claimed.
