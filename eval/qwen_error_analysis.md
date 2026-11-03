# Observed Qwen failures and review cases

These outcomes use prompt 2.0.0 and provisional, AI-authored labels. Categories below are inferences from the recorded passages and outputs, not clinical adjudications. No test-based prompt tuning was performed.

## dev-07 — end_to_end

People with prediabetes can delay type 2 diabetes through modest weight loss and physical activity.

Provisional label: **supported**. Observed verdict: **insufficient**.

Citation-fidelity failure: the generated assessment failed exact evidence validation. The validator downgraded the original verdict; this is not a model-originated abstention. Quote does not match passage: 5_NIDDK_QA:0000035-8#p1; Quote does not match passage: 5_NIDDK_QA:0000022-2#p1; Quote does not match passage: 5_NIDDK_QA:0000035-10#p2.

Annotated gold passage retrieved: **no**.

Retrieved passage IDs: `5_NIDDK_QA:0000035-8#p1`, `5_NIDDK_QA:0000022-2#p1`, `5_NIDDK_QA:0000035-10#p2`.

## test-04 — end_to_end

Insulin resistance contributes to type 2 diabetes.

Provisional label: **supported**. Observed verdict: **insufficient**.

Citation-fidelity failure: the generated assessment failed exact evidence validation. The validator downgraded the original verdict; this is not a model-originated abstention. Quote does not match passage: 5_NIDDK_QA:0000027-3#p1.

Annotated gold passage retrieved: **yes**.

Retrieved passage IDs: `5_NIDDK_QA:0000027-3#p3`, `5_NIDDK_QA:0000027-3#p1`, `5_NIDDK_QA:0000027-3#p2`.

## test-07 — end_to_end

Type 1 diabetes occurs because the immune system leaves insulin-producing beta cells undamaged.

Provisional label: **contradicted**. Observed verdict: **insufficient**.

Citation-fidelity failure: the generated assessment failed exact evidence validation. The validator downgraded the original verdict; this is not a model-originated abstention. Quote does not match passage: 5_NIDDK_QA:0000027-2#p1.

Annotated gold passage retrieved: **yes**.

Retrieved passage IDs: `5_NIDDK_QA:0000027-2#p1`, `5_NIDDK_QA:0000027-2#p6`, `5_NIDDK_QA:0000027-2#p8`.

## test-09 — end_to_end

Every person with diabetic nerve damage has noticeable symptoms.

Provisional label: **contradicted**. Observed verdict: **insufficient**.

Citation-fidelity failure: the generated assessment failed exact evidence validation. The validator downgraded the original verdict; this is not a model-originated abstention. Quote does not match passage: 5_NIDDK_QA:0000034-1#p1.

Annotated gold passage retrieved: **yes**.

Retrieved passage IDs: `5_NIDDK_QA:0000034-3#p1`, `5_NIDDK_QA:0000034-1#p1`, `5_NIDDK_QA:0000034-6#p1`.

## test-10 — end_to_end

The kidneys are located inside the bladder.

Provisional label: **contradicted**. Observed verdict: **insufficient**.

Citation-fidelity failure: the generated assessment failed exact evidence validation. The validator downgraded the original verdict; this is not a model-originated abstention. A supported or contradicted verdict requires evidence citations.

Annotated gold passage retrieved: **yes**.

Retrieved passage IDs: `5_NIDDK_QA:0000033-2#p1`, `5_NIDDK_QA:0000033-2#p2`, `5_NIDDK_QA:0000033-3#p2`.

## test-17 — end_to_end

The Diabetes Prevention Program proves that its lifestyle intervention prevents every future case of type 2 diabetes for life.

Provisional label: **insufficient**. Observed verdict: **contradicted**.

Interpretation failure relative to the provisional label: the explanation treats lack of support for universal/lifelong prevention as proof of contradiction. Under the frozen prompt, missing support alone requires insufficient evidence. Recorded explanation: The claim states that the Diabetes Prevention Program proves its lifestyle intervention prevents every future case of type 2 diabetes for life. However, the evidence only shows that the lifestyle intervention can delay or prevent type 2 diabetes in high-risk individuals, and that a 5-7% weight loss slows development of the disease. The phrase 'every future case' and 'for life' is not supported by the passage, which does not claim universal or lifelong prevention. Therefore, the claim is overgeneralized and not fully supported by the evidence.

Annotated gold passage retrieved: **yes**.

Retrieved passage IDs: `5_NIDDK_QA:0000022-2#p2`, `5_NIDDK_QA:0000022-2#p5`, `5_NIDDK_QA:0000022-2#p1`.

## test-03 — oracle

Diabetic neuropathy may cause tingling or numbness in the hands and feet.

Provisional label: **supported**. Observed verdict: **insufficient**.

Citation-fidelity failure: the generated assessment failed exact evidence validation. The validator downgraded the original verdict; this is not a model-originated abstention. Quote does not match passage: 5_NIDDK_QA:0000034-1#p1.

Annotated gold passage retrieved: **yes**.

Retrieved passage IDs: `5_NIDDK_QA:0000034-1#p1`.

## test-04 — oracle

Insulin resistance contributes to type 2 diabetes.

Provisional label: **supported**. Observed verdict: **insufficient**.

Citation-fidelity failure: the generated assessment failed exact evidence validation. The validator downgraded the original verdict; this is not a model-originated abstention. Quote does not match passage: 5_NIDDK_QA:0000027-3#p1.

Annotated gold passage retrieved: **yes**.

Retrieved passage IDs: `5_NIDDK_QA:0000027-3#p1`.

## test-07 — oracle

Type 1 diabetes occurs because the immune system leaves insulin-producing beta cells undamaged.

Provisional label: **contradicted**. Observed verdict: **insufficient**.

Citation-fidelity failure: the generated assessment failed exact evidence validation. The validator downgraded the original verdict; this is not a model-originated abstention. Quote does not match passage: 5_NIDDK_QA:0000027-2#p1.

Annotated gold passage retrieved: **yes**.

Retrieved passage IDs: `5_NIDDK_QA:0000027-2#p1`.

## test-10 — oracle

The kidneys are located inside the bladder.

Provisional label: **contradicted**. Observed verdict: **insufficient**.

Citation-fidelity failure: the generated assessment failed exact evidence validation. The validator downgraded the original verdict; this is not a model-originated abstention. Quote does not match passage: 5_NIDDK_QA:0000033-2#p1.

Annotated gold passage retrieved: **yes**.

Retrieved passage IDs: `5_NIDDK_QA:0000033-2#p1`.

## test-17 — oracle

The Diabetes Prevention Program proves that its lifestyle intervention prevents every future case of type 2 diabetes for life.

Provisional label: **insufficient**. Observed verdict: **contradicted**.

Interpretation failure relative to the provisional label: the explanation treats lack of support for universal/lifelong prevention as proof of contradiction. Under the frozen prompt, missing support alone requires insufficient evidence. Recorded explanation: The claim states that the Diabetes Prevention Program proves its lifestyle intervention prevents every future case of type 2 diabetes for life. However, the evidence shows that the intervention can delay or prevent type 2 diabetes and that modest weight loss delays onset by an average of 4 years over ten years, not that it prevents every case for life. The use of 'every' and 'for life' is not supported by the passages, which describe only a delay in onset, not complete prevention or lifelong prevention. Therefore, the claim is overgeneralized and not fully supported by the evidence.

Annotated gold passage retrieved: **yes**.

Retrieved passage IDs: `5_NIDDK_QA:0000022-2#p1`, `5_NIDDK_QA:0000035-8#p1`.

## dev-01 — end_to_end

Diabetes involves elevated blood glucose.

Provisional label: **supported**. Observed verdict: **supported**.

Retrieval/scoring review: the model agreed with the label despite missing all annotated gold IDs. Inspect alternative evidence and annotation completeness before attributing the result to correct reasoning.

Annotated gold passage retrieved: **no**.

Retrieved passage IDs: `5_NIDDK_QA:0000027-3#p8`, `5_NIDDK_QA:0000027-3#p11`, `5_NIDDK_QA:0000035-1#p1`.

## test-01 — end_to_end

Type 2 diabetes can develop during childhood.

Provisional label: **supported**. Observed verdict: **supported**.

Retrieval/scoring review: the model agreed with the label despite missing all annotated gold IDs. Inspect alternative evidence and annotation completeness before attributing the result to correct reasoning.

Annotated gold passage retrieved: **no**.

Retrieved passage IDs: `5_NIDDK_QA:0000035-1#p3`, `5_NIDDK_QA:0000022-3#p3`, `5_NIDDK_QA:0000027-3#p14`.

## test-03 — end_to_end

Diabetic neuropathy may cause tingling or numbness in the hands and feet.

Provisional label: **supported**. Observed verdict: **supported**.

Retrieval/scoring review: the model agreed with the label despite missing all annotated gold IDs. Inspect alternative evidence and annotation completeness before attributing the result to correct reasoning.

Annotated gold passage retrieved: **no**.

Retrieved passage IDs: `5_NIDDK_QA:0000034-9#p2`, `5_NIDDK_QA:0000034-6#p1`, `5_NIDDK_QA:0000034-3#p2`.

