# Before a final research claim

The current outputs are exploratory pilot experiments. A working pipeline is not evidence that either research question is answered.

- [x] Immutable dataset/model revisions and SHA-256 manifests.
- [x] Local environment and pinned successful package versions.
- [x] Real schema validation and explicit exclusion records.
- [x] Document-level train/validation/test separation.
- [x] Common label mapping with native labels retained.
- [x] Exact typed/untyped span metrics and per-type output.
- [x] Oracle relevance distinguished from end-to-end privacy filtering.
- [x] Tests for offsets, overlaps, windows, leakage, split isolation, bootstrap pairing.
- [x] CPU/CUDA timing implementation with synchronized CUDA measurement support.
- [x] Independently verify the Claude stage-2 queue, run statuses, metrics and pinned data/model integrity.
- [x] Diagnose the MiniLM/BERT relevance majority collapse on both training and validation examples.
- [x] Complete the declared balanced-loss/eight-epoch relevance repair for all three backbones and three seeds.
- [x] Run no-question and rotated-question dependence diagnostics for every selected balanced relevance checkpoint.
- [x] Review CAPID exclusions by reason, split and associated PII label; preserve the record-level caveat.
- [x] Remove four shared AI4Privacy delexicalized templates into research-v2; preserve pilot split v1.
- [x] Run exact-template and approximate lexical near-duplicate audits; explicitly retain the lack of a semantic-equivalence guarantee.
- [x] Token-boundary exclusions match across all backbones for pilots and the completed 5K/10K research subsets.
- [x] Freeze final quality/resource criteria and the validation-only threshold rule before held-out evaluation.
- [x] Complete the declared reduced detector matrix: all three backbones at 5K/10K, seed 42, full held-out split.
- [ ] Full detector runs: three backbones, 5K/10K/25K/all train, three seeds.
- [ ] Matched-update sensitivity experiment for data-size interpretation.
- [x] Complete CAPID adaptation and balanced relevance pilots for all three backbones and seeds 42/43/44.
- [x] Complete retained held-out CAPID/Reddit privacy evaluation with validation-locked thresholds and seed variance; paired model bootstraps remain seed-42 diagnostics.
- [x] Validate threshold feasibility for all nine pilot model/seed pairs; lock on validation before test/Reddit.
- [x] Combined-process resource profiling for each seed-42 complete pilot pipeline.
- [x] Explicitly limit utility claims to the retained-character proxy; no downstream QA result is claimed.
- [x] Keep GPU/VRAM results absent because no GPU environment was available.
- [x] Complete structured error analysis by type, relevance class, document length, exclusions and source domain.
- [x] Verify selected CAPID and PII-Bench tables/protocols into `published_reference.csv`; keep them separate from reproduced results.
- [x] Generate IEEE manuscript tables from measured CSV/JSON artifacts and compile/inspect the PDF; author/institution placeholders require user details.

PII-Bench access remains unverified. It is optional related work, not a required dataset dependency for completing CAPID experiments.
