# Claim evaluation

Exploratory label agreement. Unavailable outcomes count as incorrect and never as abstention.
False support denominator: all gold non-supported cases, including unavailable outcomes.
Abstention counts final insufficient verdicts; validation downgrades are also counted separately.

| Mode | Metric | Result |
|---|---|---|
| end_to_end | accuracy | 15/18 (83.3%) |
| end_to_end | false_support | 0/12 (0.0%) |
| end_to_end | abstention | 5/6 (83.3%) |
| end_to_end | over_abstention | 2/12 (16.7%) |
| end_to_end | availability | 18/18 (100.0%) |
| end_to_end | recall_at_3 | 11/13 (84.6%) |
| end_to_end | macro-F1 | 0.832 |
| end_to_end | validation_downgrades | 2 |
| end_to_end | model_abstentions_on_insufficient | 5 |
| end_to_end | unavailable_count | 0 |
| oracle | accuracy | 17/18 (94.4%) |
| oracle | false_support | 0/12 (0.0%) |
| oracle | abstention | 5/6 (83.3%) |
| oracle | over_abstention | 0/12 (0.0%) |
| oracle | availability | 18/18 (100.0%) |
| oracle | macro-F1 | 0.944 |
| oracle | validation_downgrades | 0 |
| oracle | model_abstentions_on_insufficient | 5 |
| oracle | unavailable_count | 0 |
| end_to_end_gold_subset | accuracy | 10/13 (76.9%) |
| end_to_end_gold_subset | false_support | 0/7 (0.0%) |
| end_to_end_gold_subset | abstention | 0/1 (0.0%) |
| end_to_end_gold_subset | over_abstention | 2/12 (16.7%) |
| end_to_end_gold_subset | availability | 13/13 (100.0%) |
| end_to_end_gold_subset | recall_at_3 | 11/13 (84.6%) |
| end_to_end_gold_subset | macro-F1 | 0.576 |
| end_to_end_gold_subset | validation_downgrades | 2 |
| end_to_end_gold_subset | model_abstentions_on_insufficient | 0 |
| end_to_end_gold_subset | unavailable_count | 0 |

## end_to_end: confusion matrix

Rows: gold; columns: prediction.

| Gold | supported | contradicted | insufficient | unavailable |
|---|---|---|---|---|
| supported | 6 | 0 | 0 | 0 |
| contradicted | 0 | 4 | 2 | 0 |
| insufficient | 0 | 1 | 5 | 0 |

## oracle: confusion matrix

Rows: gold; columns: prediction.

| Gold | supported | contradicted | insufficient | unavailable |
|---|---|---|---|---|
| supported | 6 | 0 | 0 | 0 |
| contradicted | 0 | 6 | 0 | 0 |
| insufficient | 0 | 1 | 5 | 0 |

## end_to_end_gold_subset: confusion matrix

Rows: gold; columns: prediction.

| Gold | supported | contradicted | insufficient | unavailable |
|---|---|---|---|---|
| supported | 6 | 0 | 0 | 0 |
| contradicted | 0 | 4 | 2 | 0 |
| insufficient | 0 | 1 | 0 | 0 |
