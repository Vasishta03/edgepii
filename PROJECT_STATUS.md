# EdgePII project status

**Last validated:** 2026-11-03, Asia/Kolkata

**Execution environment:** CPU-only Intel i9-13900H, four PyTorch threads, 16 GB RAM
**Run state:** 37/37 created training runs have completed metadata; no incomplete run directory exists.

## Completed research

- Source-pinned CAPID and AI4Privacy acquisition, archived licenses, immutable model revisions and SHA-256 manifests.
- Offset-preserving normalization, 20-category harmonization, grouped splits, exclusion records and research-v2 exact-template cleanup.
- MiniLM, DistilBERT and BERT token classifiers with sliding-window inference and strict typed-span evaluation.
- CAPID detector adaptation and balanced contextual-relevance pilots for seeds 42, 43 and 44.
- No-question and rotated-question controls for all nine selected relevance checkpoints.
- Validation-only threshold selection and locked test/Reddit privacy evaluation for all nine model/seed pairs.
- Complete seed-42 pipeline latency/RAM profiling for all three models.
- Reduced research-v2 detector scaling study at 5K and 10K requested documents for all three models.
- Per-type, relevance-class, context-length, exclusion and domain-shift error analysis.
- Exact-template and approximate lexical cross-split near-duplicate audits.
- Verified published CAPID and PII-Bench reference rows, kept separate from reproduced measurements.
- Offline command line demo and plain local web interface, automated tests, final figures, generated manuscript tables and compiled five-page IEEE PDF.
- Current server-process RAM reporting in the web interface, separate from controlled benchmark peak RSS.
- Four checked synthetic presentation examples, an 11-slide editable presentation, and final author information.

## Headline results

| Model | CAPID detector F1, 3-seed pilot | Relevance macro-F1 | 10K AI4Privacy F1 | Seed-42 pipeline median / p95 | Peak RAM |
|---|---:|---:|---:|---:|---:|
| MiniLM | 0.504 ± 0.039 | 0.705 ± 0.018 | 0.9396 | 345 / 623 ms | 585 MiB |
| DistilBERT | 0.729 ± 0.024 | 0.738 ± 0.008 | 0.9573 | 734 / 1127 ms | 870 MiB |
| BERT | 0.771 ± 0.003 | 0.628 ± 0.193 | 0.9592 | 1424 / 2002 ms | 1192 MiB |

BERT relevance seed 43 collapsed to the majority baseline and is retained in all aggregates. Removing the question changes macro-F1 by approximately 0.000 for MiniLM, -0.029 for DistilBERT and -0.014 for BERT across three seeds. DistilBERT has the largest mean dependence signal, but variability prevents a strong contextual-reasoning claim.

The primary 5% irrelevant-character leakage criterion is infeasible for every model/seed because missed detections leak PII even when every detected entity is masked. Under the predeclared detector-floor+5pp diagnostic, retained-test leakage/retention is 0.183/0.454 MiniLM, 0.127/0.478 DistilBERT and 0.096/0.322 BERT. Reddit leakage rises to 0.475, 0.350 and 0.330.

## Research-question answers

**RQ1:** no tested model satisfies every predeclared deployment criterion, so there is no qualifying smallest architecture. MiniLM is fastest but weak on CAPID and long contexts. BERT detects best but is slowest and relevance training is unstable. DistilBERT is the strongest measured accuracy/efficiency compromise.

**RQ2:** increasing usable AI4Privacy training documents from 4,930 to 9,854 improves strict span F1 by 0.0179 MiniLM, 0.0158 DistilBERT and 0.0167 BERT. Training time approximately doubles. Because this reduced matrix uses one seed and fixed epochs, gains combine more data with more optimizer updates.

## Declared limitations

- The three-seed experiments use small pilot subsets; the larger 5K/10K scaling study uses seed 42 only.
- The remaining full original detector matrix is estimated at about 122 additional CPU wall-hours, before CAPID/relevance work. The 25K/full-size and matched-update experiments were not run and are stated as limitations.
- CAPID flat-span normalization excludes 114 train, nine test and 28 Reddit records; local scores are not a reproduction of the published protocol.
- The near-duplicate audit is approximate and lexical, not a semantic-equivalence guarantee. One high-similarity train/validation pair lies outside the first 10K nested training records; none is found for the AI4Privacy test split at the declared threshold.
- Retained-character coverage is a utility proxy. No downstream QA utility, formal privacy guarantee, GPU result or PII-Bench reproduction is claimed.

## Reproducibility

From the repository root:

```bash
bash scripts/finalize_project.sh
```

This checks the environment, completed run states, tests and checksums; regenerates summaries, figures, audits and tables; and compiles the paper twice.

Key deliverables:

- `scripts/run_gui.sh`
- `results/SEED_VARIANCE.md`
- `results/SCALING.md`
- `results/RELEVANCE_CONTROLS.md`
- `results/ADJUSTED_PRIVACY.md`
- `results/ERROR_ANALYSIS.md`
- `results/NEAR_DUPLICATES.md`
- `results/PUBLISHED_REFERENCE.md`
- `paper/ieee/main.pdf`
- `presentation/output/EdgePII_Presentation_2026-11-03.pptx`
- `docs/DEMO_GUIDE.md`

## Authors and presentation state

The paper and presentation list Vasishta Nandipati, Karthikeya Davasam, and Tirth Koradia, Manipal Institute of Technology, Manipal. The local server was revalidated on 2026-11-03 using the BERT identity example. It produced `My passport number is [REDACTED]. I was born on [REDACTED].` and reported current process RSS through `/api/health`.

The PPTX passes package, layout, font, editable native table, editable native chart, and first-party import validation. The paper compiles to five visually checked pages with embedded fonts.
