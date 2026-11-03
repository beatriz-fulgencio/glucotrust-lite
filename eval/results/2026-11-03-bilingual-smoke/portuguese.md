# Claim evaluation

Exploratory label agreement. Unavailable outcomes count as incorrect and never as abstention.
False support denominator: all gold non-supported cases, including unavailable outcomes.
Abstention counts final insufficient verdicts; validation downgrades are also counted separately.

| Mode | Metric | Result |
|---|---|---|
| end_to_end | accuracy | 2/2 (100.0%) |
| end_to_end | false_support | 0/1 (0.0%) |
| end_to_end | abstention | 1/1 (100.0%) |
| end_to_end | over_abstention | 0/1 (0.0%) |
| end_to_end | availability | 2/2 (100.0%) |
| end_to_end | recall_at_3 | 1/1 (100.0%) |
| end_to_end | macro-F1 | 0.667 |
| end_to_end | validation_downgrades | 0 |
| end_to_end | model_abstentions_on_insufficient | 1 |
| end_to_end | unavailable_count | 0 |
| oracle | accuracy | 2/2 (100.0%) |
| oracle | false_support | 0/1 (0.0%) |
| oracle | abstention | 1/1 (100.0%) |
| oracle | over_abstention | 0/1 (0.0%) |
| oracle | availability | 2/2 (100.0%) |
| oracle | macro-F1 | 0.667 |
| oracle | validation_downgrades | 0 |
| oracle | model_abstentions_on_insufficient | 1 |
| oracle | unavailable_count | 0 |
| end_to_end_gold_subset | accuracy | 1/1 (100.0%) |
| end_to_end_gold_subset | false_support | 0/0 (N/A) |
| end_to_end_gold_subset | abstention | 0/0 (N/A) |
| end_to_end_gold_subset | over_abstention | 0/1 (0.0%) |
| end_to_end_gold_subset | availability | 1/1 (100.0%) |
| end_to_end_gold_subset | recall_at_3 | 1/1 (100.0%) |
| end_to_end_gold_subset | macro-F1 | 0.333 |
| end_to_end_gold_subset | validation_downgrades | 0 |
| end_to_end_gold_subset | model_abstentions_on_insufficient | 0 |
| end_to_end_gold_subset | unavailable_count | 0 |

## end_to_end: confusion matrix

Rows: gold; columns: prediction.

| Gold | supported | contradicted | insufficient | unavailable |
|---|---|---|---|---|
| supported | 1 | 0 | 0 | 0 |
| contradicted | 0 | 0 | 0 | 0 |
| insufficient | 0 | 0 | 1 | 0 |

## oracle: confusion matrix

Rows: gold; columns: prediction.

| Gold | supported | contradicted | insufficient | unavailable |
|---|---|---|---|---|
| supported | 1 | 0 | 0 | 0 |
| contradicted | 0 | 0 | 0 | 0 |
| insufficient | 0 | 0 | 1 | 0 |

## end_to_end_gold_subset: confusion matrix

Rows: gold; columns: prediction.

| Gold | supported | contradicted | insufficient | unavailable |
|---|---|---|---|---|
| supported | 1 | 0 | 0 | 0 |
| contradicted | 0 | 0 | 0 | 0 |
| insufficient | 0 | 0 | 0 | 0 |
