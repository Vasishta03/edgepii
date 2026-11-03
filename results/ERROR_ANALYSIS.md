# Error analysis

Exploratory analysis on the frozen 64-document retained CAPID test prefix across seeds 42/43/44.

## Strict typed span F1 by PII type (mean ± sample SD)

| Type | MiniLM | DistilBERT | BERT |
|---|---:|---:|---:|
| AGE | 0.573 ± 0.045 | 0.647 ± 0.020 | 0.593 ± 0.042 |
| APPEARANCE | 0.000 ± 0.000 | 0.754 ± 0.055 | 0.917 ± 0.000 |
| BELIEF | 0.000 ± 0.000 | 0.785 ± 0.091 | 0.854 ± 0.019 |
| DATETIME | 0.787 ± 0.071 | 0.906 ± 0.015 | 0.960 ± 0.035 |
| DEMOGRAPHIC | 0.422 ± 0.050 | 0.705 ± 0.023 | 0.768 ± 0.019 |
| EDUCATION | 0.074 ± 0.128 | 0.640 ± 0.039 | 0.716 ± 0.033 |
| FINANCE | 0.559 ± 0.047 | 0.677 ± 0.103 | 0.762 ± 0.022 |
| HEALTH | 0.615 ± 0.047 | 0.812 ± 0.038 | 0.793 ± 0.011 |
| ID | 0.427 ± 0.081 | 0.582 ± 0.112 | 0.878 ± 0.107 |
| LOCATION | 0.588 ± 0.015 | 0.584 ± 0.035 | 0.651 ± 0.042 |
| NAME | 0.450 ± 0.213 | 0.852 ± 0.034 | 0.760 ± 0.023 |
| OCCUPATION | 0.571 ± 0.052 | 0.739 ± 0.095 | 0.819 ± 0.016 |
| ORGANIZATION | 0.544 ± 0.044 | 0.837 ± 0.015 | 0.817 ± 0.022 |
| RELATIONSHIP | 0.440 ± 0.120 | 0.615 ± 0.034 | 0.632 ± 0.072 |
| SEXUAL_ORIENTATION | 0.698 ± 0.116 | 0.909 ± 0.008 | 0.929 ± 0.017 |

## Detection by context length

Buckets use character length: short ≤ 410, medium ≤ 605, long > 605.

| Bucket | MiniLM | DistilBERT | BERT |
|---|---:|---:|---:|
| Short | 0.588 ± 0.075 | 0.758 ± 0.022 | 0.752 ± 0.028 |
| Medium | 0.567 ± 0.018 | 0.707 ± 0.033 | 0.751 ± 0.015 |
| Long | 0.348 ± 0.024 | 0.720 ± 0.031 | 0.811 ± 0.018 |

## Relevance errors by class

| Model | Irrelevant recall | Relevant recall | Relevant F1 |
|---|---:|---:|---:|
| MiniLM | 0.808 ± 0.067 | 0.608 ± 0.087 | 0.599 ± 0.029 |
| DistilBERT | 0.803 ± 0.042 | 0.692 ± 0.068 | 0.651 ± 0.019 |
| BERT | 0.872 ± 0.112 | 0.456 ± 0.396 | 0.433 ± 0.376 |

## Exclusion audit

| Raw split | Documents | Excluded during normalization |
|---|---:|---:|
| train | 2107 | 114 |
| test | 200 | 9 |
| reddit | 150 | 28 |

Exclusion reasons:

- 128: overlapping entities cannot be represented by flat BIO
- 20: CAPID annotation absent from context
- 2: invalid literal for int() with base 10: 'high'
- 1: invalid literal for int() with base 10: 'low'

Per-label record exclusion associations are in `results/exclusion_bias.csv`. A label appearing in an excluded record is not necessarily the cause of exclusion.

## Interpretation

- MiniLM records zero mean exact F1 for APPEARANCE and BELIEF and near-zero EDUCATION performance. These categories are absent from AI4Privacy supervision, so the small CAPID adaptation must learn them; the analysis shows association, not a proven cause.
- MiniLM's sharp degradation on long contexts occurs despite sliding-window inference, so it cannot be explained by silent tail truncation. Model capacity, adaptation data and boundary errors remain plausible contributors.
- BERT relevance variability is dominated by the retained seed-43 majority-class collapse. Excluding it would hide a reproducibility failure.
- Reddit has a markedly different type distribution and writing style; every model's leakage rises substantially in `results/ADJUSTED_PRIVACY.md`. The present experiment does not isolate which shift causes the loss.

The analysis remains exploratory because the multiseed pilots use only 64 retained CAPID test documents.
