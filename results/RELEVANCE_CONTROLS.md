# Question-dependence controls

Gold-span relevance controls on 64 retained CAPID test documents. No-question macro-F1 is a scored degraded-input ablation; rotated-question outputs are sensitivity diagnostics only because no counterfactual labels exist.

| Model | Normal macro-F1 | No-question macro-F1 | No-question delta | Removed-question flip rate | Permuted-question flip rate |
|---|---:|---:|---:|---:|---:|
| MiniLM | 0.705 ± 0.018 | 0.705 ± 0.019 | -0.000 ± 0.007 | 0.085 ± 0.036 | 0.060 ± 0.015 |
| DistilBERT | 0.738 ± 0.008 | 0.709 ± 0.034 | -0.029 ± 0.035 | 0.098 ± 0.010 | 0.067 ± 0.023 |
| BERT | 0.628 ± 0.193 | 0.614 ± 0.179 | -0.014 ± 0.020 | 0.043 ± 0.040 | 0.045 ± 0.039 |

A negative no-question delta indicates worse performance after removing the question. Probability and decision changes alone show dependence, not correct counterfactual reasoning.
