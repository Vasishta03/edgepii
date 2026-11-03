# Three-seed exploratory pilot summary

Scores are held-out selection metrics for seeds 42/43/44. SD is the sample standard deviation. These are still small-data pilots.

| Task | Model | Seed 42 | Seed 43 | Seed 44 | Mean ± SD |
|---|---|---:|---:|---:|---:|
| ai4privacy_detection | minilm | 0.5793 | 0.5654 | 0.5294 | 0.5581 ± 0.0258 |
| ai4privacy_detection | distilbert | 0.7861 | 0.7202 | 0.7282 | 0.7448 ± 0.0360 |
| ai4privacy_detection | bert | 0.8189 | 0.8103 | 0.8377 | 0.8223 ± 0.0140 |
| capid_detection | minilm | 0.5484 | 0.4813 | 0.4819 | 0.5039 ± 0.0386 |
| capid_detection | distilbert | 0.7339 | 0.7032 | 0.7500 | 0.7290 ± 0.0238 |
| capid_detection | bert | 0.7687 | 0.7696 | 0.7740 | 0.7708 ± 0.0029 |
| balanced_relevance | minilm | 0.7241 | 0.7038 | 0.6886 | 0.7055 ± 0.0178 |
| balanced_relevance | distilbert | 0.7471 | 0.7376 | 0.7304 | 0.7383 ± 0.0084 |
| balanced_relevance | bert | 0.7158 | 0.4068 | 0.7607 | 0.6278 ± 0.1926 |

BERT balanced relevance is unstable: seed 43 predicts only the majority class (macro F1 0.4068), while seeds 42 and 44 learn. Report all seeds; do not omit or rerun the collapsed seed.
