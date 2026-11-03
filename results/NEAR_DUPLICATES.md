# Approximate near-duplicate audit

Threshold: delexicalized word-trigram Jaccard ≥ 0.80.

| Dataset | Holdout | Train docs | Holdout docs | Matches | Maximum similarity |
|---|---|---:|---:|---:|---:|
| ai4privacy | ai4privacy_validation | 34801 | 4347 | 1 | 0.917 |
| ai4privacy | ai4privacy_test | 34801 | 4349 | 0 | 0.724 |
| capid | capid_validation | 1813 | 180 | 0 | 0.198 |
| capid | capid_test | 1813 | 191 | 0 | 0.136 |
| capid | capid_reddit | 1813 | 122 | 0 | 0.067 |

The report stores IDs and scores only, without copying source text. SimHash is used only to generate candidate pairs; reported Jaccard values are exact for those candidates.

This is an approximate lexical audit, not a semantic-equivalence guarantee. It can miss semantically similar paraphrases and candidate pairs missed by SimHash.

AI4Privacy validation matches inside the first 10,000 nested training records: 0. Therefore the measured reduced 5K/10K scaling runs were not exposed to the identified high-similarity training record.
