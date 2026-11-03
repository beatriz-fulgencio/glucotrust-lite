# Adversarial annotation review — 2026-11-03

Eight candidate cases in [`claims_adversarial.jsonl`](../eval/claims_adversarial.jsonl)
are separate from the original test set. Labels/rationales were fixed before their
inference run. No prompt, retrieval model, or original test annotation was tuned
on these cases. An agent checked every tempting quotation against its supplied
archived passage. These quotes are **stimuli, not recorded model output**.

At the author's request, an additional web-assisted rationale check used the
sources below. This review did not change frozen labels or rerun the model.
It is agent review using external sources, not independent human/clinician review.
External pages were not added to the evaluation evidence.

| Case | Candidate label | Review of the evidence boundary |
|---|---|---|
| adv-01 | insufficient | General asymptomatic kidney disease does not determine one person's kidney status. [NIDDK kidney disease](https://www.niddk.nih.gov/health-information/diabetes/overview/preventing-problems/diabetic-kidney-disease) discusses absent symptoms and diagnostic checks. |
| adv-02 | insufficient | Population-level risk reduction cannot establish an individual lifetime guarantee. [NIDDK prevention](https://www.niddk.nih.gov/health-information/diabetes/overview/preventing-type-2-diabetes) describes reduced risk and possible prevention/delay, without that guarantee. |
| adv-03 | insufficient | Glucose-metabolism text does not evaluate forecasting safety or missed hypoglycemia. [Wolff et al., 2025](https://journals.sagepub.com/doi/10.1089/dia.2025.0074), accessible abstract, reports that the lowest-RMSE model in its experiment performed poorly at glycemic-event prediction. This supports the rationale for testing the distinction, not a verdict from the supplied passage. |
| adv-04 | insufficient | Bladder anatomy has no logical bearing on a forecasting algorithm's hypoglycemia detection. This is a deliberately irrelevant exact quote. |
| adv-05 | insufficient | A study population and follow-up period do not establish applicability to every population and future decade. [NIDDK prevention](https://www.niddk.nih.gov/health-information/diabetes/overview/preventing-type-2-diabetes) is appropriately bounded. |
| adv-06 | insufficient | Above-normal glucose without test values does not establish which diagnostic category applies to an individual. [NIDDK tests](https://www.niddk.nih.gov/health-information/professionals/clinical-tools-patient-management/diabetes/diabetes-prediabetes) distinguishes diagnostic tests and confirmation. |
| adv-07 | contradicted | The archived passage explicitly includes people with no symptoms. The [current NIDDK neuropathy page](https://www.niddk.nih.gov/health-information/diabetes/overview/preventing-problems/nerve-damage-diabetic-neuropathies/what-is-diabetic-neuropathy) also discusses unnoticed mild nerve damage. |
| adv-08 | supported | Bounded positive control: childhood onset is explicit, and the general passage contains no individual child's diagnosis. [NIDDK type 2 diabetes](https://www.niddk.nih.gov/health-information/diabetes/overview/what-is-diabetes/type-2-diabetes) confirms possible childhood onset. |

The label boundary is debatable for invalid guarantees: an annotator could treat
some universal formulations as contradicted by counterexamples, while this task
reserves contradiction for directly incompatible facts in the supplied evidence.
In adv-01/02/06, the target interpretation is a missing individual assessment.
Adv-08 also includes a meta-statement about what a passage cannot diagnose.
These cases require independent adjudication before use as a benchmark. Their
50% agreement is a diagnostic observation against provisional labels, not a
medical accuracy estimate.

An offline test deliberately supplies a supported verdict with adv-04's exact
anatomy quote. Citation validation accepts it. This demonstrates a validator
boundary; it is never counted as an observed model false-support case.
