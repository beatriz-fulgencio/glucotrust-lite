# Error and uncertainty analysis

Observed retrieval run: 2026-11-02, 199 archived passages, MiniLM and BM25, top 3.
Raw rankings and strict gold IDs: [results/retrieval.json](results/retrieval.json).
These are retrieval errors or questionable retrieval/scoring outcomes, **not observed Claude classification failures**. No live API key was available. Oracle comparison and interpretation/overgeneralization errors from an assessor remain unmeasured.

| Example | Observation | Cause / interpretation | Next check |
|---|---|---|---|
| rq-04: causes of type 2 diabetes | BM25 misses the listed `0000027-3#p1` gold and retrieves `0000027-5#p6`, `0000027-3#p16`, `0000027-3#p2`. Dense finds the gold. | Retrieval: repeated generic question wording gives many chunks similar lexical relevance. | Inspect whether later chunks supply sufficient context; compare claim assessment with oracle p1. |
| rq-08: can the adult-associated form occur in children? | Both methods miss the listed `0000022-1#p1`, but retrieve `0000035-1#p3`, which explicitly says type 2 can occur in childhood. | Questionable scoring: incomplete gold annotations penalize an actually relevant alternative. This is not evidence of a semantic retrieval failure. | Have a reviewer adjudicate all relevant alternative passages in a separately versioned query set. Keep original scores. |
| rq-09: silent early kidney disease | BM25 retrieves neuropathy passages; dense retrieves the listed kidney-symptom gold. | Retrieval: the paraphrase uses renal/silent rather than kidney/no symptoms. | Compare end-to-end and oracle classifications after API configuration. |
| rq-10: immune destruction of insulin-producing cells | BM25 finds the listed `0000027-2#p1`; dense does not. Dense returns `0000027-2#p6`, discussing insulin as an immune trigger, plus generic signaling/glucose passages. | Retrieval/context: the related mechanism may help answer the query, but the concise direct gold is missing. Gold incompleteness is also possible. Dense is not uniformly better. | Review p6 as a possible relevant alternative; do not assume a downstream verdict is wrong. |
| rq-14: tissues stop responding to the glucose-regulating hormone | Both methods miss `0000027-3#p1`. Dense retrieves signaling detail and generic glucose-metabolism passages instead. | Retrieval: background passages can displace the direct insulin-resistance explanation. | Test whether oracle evidence changes the assessment; broad relatedness is not enough for a verdict. |
| rq-15: nerve injury, digestion, arterial pressure | Both miss listed `0000034-7#p1`; dense returns p2/p3 and `0000034-4#p2`, which describe the requested functions. | Questionable scoring: paragraph chunking creates multiple relevant passages. Strict ID Recall@3 underestimates usefulness here. | Expand gold only in a disclosed new annotation version; retain the original benchmark. |
| test-13: low forecasting error establishes clinical safety | Corpus inspection found no forecasting-model validation evidence. Expected label was set to insufficient before any assessor run; actual result is pending. | Missing evidence. Patient-education content cannot establish model safety. | Record actual end-to-end output when a key is available. An unsupported support/contradiction verdict would be an interpretation or overgeneralization failure. |

## How to extend this report after a live run

Use `run_eval --live` on dev claims first, freeze any prompt changes, then run the test set to a new output path. Report the actual model (including fallbacks), prompt version, corpus and label hashes, token usage, and cached/raw outputs. No API cost has been measured yet; do not repeat the plan's per-claim estimate as an observed cost.

For each wrong or questionable classifier output, quote the claim, gold rationale, exact retrieved evidence, model output and validator outcome. Wrong end-to-end/right oracle suggests **retrieval**; wrong in both suggests **interpretation** or **overgeneralization**. A corpus unable to settle the claim indicates **missing evidence**. Multiple causes may apply.

## Threats to validity

- The query gold lists are intentionally small and not exhaustive; observed alternative relevant passages above show strict ID recall is a lower-bound indicator on this set.
- Labels and gold passages were drafted during implementation by an AI assistant and need independent human review. They are provisional annotations, not a manually validated clinical benchmark.
- Contradictions are hand-inverted facts and are simpler than typical misinformation.
- 60 records from eight NIDDK documents make retrieval easier than a broad medical corpus; related chunks and duplicate facts remain even after record-level deduplication.
- The first 60 accepted records in stable source/file order were selected, creating topic and source bias. Later NIDDK documents and other collections were logged but not selected.
- Single annotation process, 15 retrieval queries and 18 classification claims provide no basis for general clinical-accuracy claims. Dev/test claims overlap in underlying topics and sources even though claim texts are disjoint.
- All original URLs returned HTTP 404 on 2026-11-02. Source metadata is preserved, but content is archived and may contain obsolete statistics, recommendations and insurance information.
- Exact quotation validation establishes textual traceability, not whether the quote entails the claim, whether the explanation is correct, or whether a medical assertion is current.
