# Reduced detector scaling study

Measured on the complete frozen AI4Privacy research-v2 test split (4,349 documents), seed 42. The study uses one seed and two data sizes; it is a reduced RQ2 matrix, not the planned full 3-seed/4-size design.

| Model | Requested / usable train docs | Strict span F1 | Precision | Recall | Train min | Median / p95 ms | Peak RSS MiB |
|---|---:|---:|---:|---:|---:|---:|---:|
| MiniLM | 5,000 / 4,930 | 0.9217 | 0.9123 | 0.9313 | 22.2 | 13.0 / 23.6 | 527 |
| DistilBERT | 5,000 / 4,930 | 0.9414 | 0.9327 | 0.9503 | 48.1 | 32.9 / 55.5 | 710 |
| BERT | 5,000 / 4,930 | 0.9425 | 0.9350 | 0.9500 | 85.8 | 65.1 / 115.2 | 866 |
| MiniLM | 10,000 / 9,854 | 0.9396 | 0.9289 | 0.9506 | 42.7 | 13.1 / 21.2 | 528 |
| DistilBERT | 10,000 / 9,854 | 0.9573 | 0.9503 | 0.9643 | 96.5 | 30.7 / 63.6 | 706 |
| BERT | 10,000 / 9,854 | 0.9592 | 0.9533 | 0.9651 | 174.0 | 57.4 / 107.2 | 935 |

## Change from 5K to 10K

| Model | F1 gain | Extra train min |
|---|---:|---:|
| MiniLM | +0.0179 | +20.5 |
| DistilBERT | +0.0158 | +48.4 |
| BERT | +0.0167 | +88.1 |

All three models improved with more data. Training time approximately doubled. At 10K, DistilBERT was 0.0019 F1 below BERT while its measured median latency was about half. Statistical significance was not estimated for this single-seed scaling comparison.
