# Published reference values

These values were verified from the cited arXiv tables on 2026-10-29. They are **published references**, not locally reproduced results, and remain separate from EdgePII measurements.

## CAPID

CAPID Table 2 evaluates 200 test samples with a hybrid token/character span metric. Type and relevance accuracy are conditioned on correctly matched spans. Its fine-tuned Llama-3.1-8B reports span F1 0.9603 and relevance accuracy 0.9306; Llama-3.2-3B reports 0.9608 and 0.9306. Table 3 reports Reddit span F1/relevance accuracy of 0.8159/0.7994 for Llama-3.1-8B and 0.7973/0.7195 for Llama-3.2-3B.

EdgePII instead reports strict exact typed spans on a retained flat-span subset and gold-span relevance macro-F1. Direct numerical ranking against CAPID's published table is invalid.

## PII-Bench

PII-Bench v2 describes 2,842 samples spanning seven broad PII types and 55 fine-grained categories. Section 4.4 reports query-related exact F1 of 0.627 for naive GPT-4o, 0.716 with self-consistency, and 0.710 for Qwen-2.5-72B with Auto-CoT on PII-single.

The PII-Bench dataset was not accessed or reproduced in this project. Its task, prompts, metric and population differ from EdgePII, so these values are context only.

Machine-readable rows and protocol notes are in `results/published_reference.csv`.
