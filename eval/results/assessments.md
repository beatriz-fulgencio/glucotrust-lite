# Claim evaluation

Exploratory only. Unavailable outcomes count as incorrect for all-claim accuracy and never count as abstention.

| Mode | Metric | Result |
|---|---|---|
| end_to_end | accuracy | 13/18 (72.2%) |
| end_to_end | false_support | 0/12 (0.0%) |
| end_to_end | abstention | 5/6 (83.3%) |
| end_to_end | over_abstention | 4/12 (33.3%) |
| end_to_end | availability | 18/18 (100.0%) |
| end_to_end | recall_at_3 | 11/13 (84.6%) |
| end_to_end | macro-F1 | 0.725 |
| end_to_end | mean inference latency (seconds) | 10.90 |
| oracle | accuracy | 8/13 (61.5%) |
| oracle | false_support | 0/7 (0.0%) |
| oracle | abstention | 0/1 (0.0%) |
| oracle | over_abstention | 4/12 (33.3%) |
| oracle | availability | 13/13 (100.0%) |
| oracle | macro-F1 | 0.509 |
| oracle | mean inference latency (seconds) | 7.76 |
