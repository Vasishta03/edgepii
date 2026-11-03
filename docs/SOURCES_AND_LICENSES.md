# Sources and licensing evidence

Verified 2026-10-27. Downloaded sources remain local; they are ignored by version control. This repository does not relicense third-party data or pretrained weights.

| Source | Evidence | Treatment |
|---|---|---|
| CAPID | https://github.com/MariaPonomarenko38/CAPID ; revision e14c93de9c72c2a0f1ecf32c5655b60402754131 | Repository LICENSE.md is MIT; preserve it and provenance. Reddit-derived content may have separate provenance considerations; do not assume repository licensing resolves every underlying content right. |
| AI4Privacy PII-200K | https://huggingface.co/datasets/ai4privacy/pii-masking-200k ; revision 7c22e6816b8fc24b7781e9f4e22016c698842dd0 | Custom license, not a generic CC license. Both LICENSE and license.md are archived because wording differs. Individual/nonprofit use is covered in their stated eligibility; redistribution and commercial reuse require checking the actual terms. |
| MiniLM-L6 | https://huggingface.co/nreimers/MiniLM-L6-H384-uncased | Model card declares MIT, describes alternate-layer extraction from L12. Card archived, no standalone license file in this repository. |
| DistilBERT | https://huggingface.co/distilbert/distilbert-base-uncased | LICENSE and card archived with pinned revision. |
| BERT-base | https://huggingface.co/google-bert/bert-base-uncased | LICENSE and card archived with pinned revision. |

CAPID paper: https://arxiv.org/abs/2602.10074 and https://aclanthology.org/2026.eacl-srw.23/ . Source schema is context, question, and piis mapping from strings to type/relevance. Official file counts: train 2,107; test 200; Reddit 150. Consult results/data_audit.json for retained counts.

PII-Bench relevant to this project is *PII-Bench: Evaluating Query-Aware Privacy Protection Systems*, https://arxiv.org/abs/2502.18545 . It is not the similarly named 2026 multi-source PIIBench. Dataset access and license have **not** been verified and no PII-Bench data has been downloaded. No reproduced PII-Bench results exist.

Published metrics are intentionally not transcribed yet: their exact tables, definitions and evaluation populations need extraction and review. results/published_reference.csv is separate from measured results.csv. Never fill missing measurements with paper numbers.
