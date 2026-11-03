# Evaluation — 2026-11-03

> This report measures prompt **2.1.0**. Subsequent bilingual support uses **2.2.1**; these scores do not evaluate that changed prompt or Portuguese translation. See [bilingual verification](bilingual-input.md).

This is an exploratory evaluation of an educational prototype, not clinical
validation. All labels are provisional agent-authored annotations. The original
held-out files are unchanged; neither prompt nor retrieval settings were tuned
during this evaluation. Independent human/clinician adjudication remains absent.

## Setup and experiment identity

- Corpus: 60 MedQuAD records, **199 archived passages**, eight original NIDDK documents.
- Retrieval set: **15 queries**, including **8 paraphrases**; identical corpus,
  query set, top-3 cutoff and annotations for BM25 and MiniLM.
- Original assessment set: **18 test claims**, six per label; eight separate dev
  claims were not used to tune this run. Topic/source overlap limits independence.
- End to end: top three MiniLM passages plus the existing assessor/validator.
- Oracle: supplied annotated passages for all 18 claims, including **empty evidence
  for five claims with no gold passages**. Empty-evidence abstention is easier
  than interpreting retrieved distractors. The older runner omitted those cases.
- Literature fallback disabled in all reported classification runs. Scores do not
  describe the app's default literature-enabled behavior.
- Separate challenge set: eight cases, fixed before its inference run; six
  insufficient, one contradicted, one supported control. Gold IDs designate the
  deliberately supplied challenge context, including irrelevant evidence. Never
  pooled with the original test set. [Rationale review](adversarial-review.md).

| Configuration | Value |
|---|---|
| Provider / model | Ollama / `qwen3:4b-instruct-2507-q4_K_M` |
| Model digest | `0edcdef34593eac1aa2be9c7d06c432dcf81945adca5eca2f27662c18f168ba0` |
| Prompt | `2.1.0`, one bounded citation repair; unchanged for both datasets |
| Prompt SHA-256 | `1370469ef5b2a18a39781c7ac970d94f86d8e5179023b9764329946b6aab4b5c` |
| Generation | temperature 0; context 16,384; max generated tokens 1,800 |
| Embedding model | `sentence-transformers/all-MiniLM-L6-v2`, CPU cosine |
| Embedding revision | `1110a243fdf4706b3f48f1d95db1a4f5529b4d41` |
| Corpus fingerprint | `335471d3abe3b8d04ff1ff53359b82d128b0ed268d7f1198e3c7d91bd51f648c` |
| Original test SHA-256 | `fe7ac6ddcb9bc1fd0a65c870f29642fed28b6863124e4970e7a2150ad4969493` |
| Environment | macOS ARM64, Python 3.12.6; package versions recorded per result |

Raw records retain full prompt/schema, model identity, generation settings,
passages IDs, final validation outcome, model responses, repair responses,
timestamps, corpus/label fingerprints and cache status. One of the 36 original
assessment outcomes reused a configuration-compatible cache entry; 35 were newly
inferred. No incompatible historical prompt cache was reused. Temperature zero
and a pinned digest do not guarantee identical generation on another runtime.

## Retrieval

The existing function calls its metric Recall@3. It measures **query-level hit
rate**: at least one annotated gold ID in the top three. It does not measure the
fraction of all relevant passages retrieved. Gold IDs are incomplete.

| Method | All queries (N=15) | Paraphrases (N=8) |
|---|---:|---:|
| BM25 | 8/15 (53.3%) | 2/8 (25.0%) |
| MiniLM | 11/15 (73.3%) | 4/8 (50.0%) |

Fresh results reproduce the historical table. [Raw rankings and metadata](../eval/results/2026-11-03-retrieval/retrieval.json).
Examples (all full IDs/ranks are in that file):

| Query | BM25 top result | MiniLM top result | Annotated hit within top 3 |
|---|---|---|---|
| rq-04: causes of type 2 diabetes | `0000027-5#p6` | `0000027-3#p1` | BM25 no; MiniLM yes |
| rq-09: renal damage silent at first | `0000034-7#p2` (nerve/autonomic context) | `0000033-6#p1` (early kidney symptoms) | BM25 no; MiniLM yes |
| rq-10: defense system destroying insulin-producing cells | `0000034-7#p2` | `0000027-3#p12` | BM25 yes, rank 3; MiniLM no |

IDs in this table omit the common `5_NIDDK_QA:` prefix. MiniLM's misses can contain
alternative relevant material. These small-set results do not establish a general
advantage or clinical reliability.

## Original claim results

“Accuracy” means agreement with the provisional evidence-relative labels.
Macro-F1 always averages the three verdict labels. Unavailable outcomes count as
incorrect, contribute false negatives, and never count as evidence abstention.
False-support denominator is all gold non-supported claims, not only successful
inference. Here all outcomes were available.

| Setting | Accuracy | Macro-F1 | False support | Correct abstention on insufficient | Unavailable |
|---|---:|---:|---:|---:|---:|
| End to end | 15/18 (83.3%) | 0.832 | 0/12 | 5/6 (83.3%) | 0/18 |
| Oracle, all claims | 17/18 (94.4%) | 0.944 | 0/12 | 5/6 (83.3%) | 0/18 |

End-to-end gold-ID hit rate for the 13 gold-bearing claims was **11/13**.
On that same 13-claim subset, end-to-end agreement was **10/13** and oracle
agreement **12/13**. The two remaining end-to-end errors had retrieved gold
passages but failed citation validation, so the oracle difference is not evidence
that the retriever simply missed their facts. Evidence amount/composition and
citation generation also differ. The other five claims supply no evidence in
oracle mode. No causal improvement or general reliability claim follows.

Confusion matrices: rows are gold, columns are predictions. S=supported,
C=contradicted, I=insufficient, U=unavailable.

| End to end | S | C | I | U |
|---|---:|---:|---:|---:|
| S | 6 | 0 | 0 | 0 |
| C | 0 | 4 | 2 | 0 |
| I | 0 | 1 | 5 | 0 |

| Oracle | S | C | I | U |
|---|---:|---:|---:|---:|
| S | 6 | 0 | 0 | 0 |
| C | 0 | 6 | 0 | 0 |
| I | 0 | 1 | 5 | 0 |

There were **two validation downgrades** end to end and none in oracle mode.
All five correct insufficient-label outcomes in each mode were model-originated
abstentions, not validator downgrades. Unavailable inference and a technically
invalid citation are also distinct failure mechanisms.

## Separate adversarial results and false-support audit

| Setting | Accuracy | Macro-F1 | False support | Correct insufficient abstention | Unavailable |
|---|---:|---:|---:|---:|---:|
| End to end | 4/8 (50.0%) | 0.333 | 0/7 | 3/6 (50.0%) | 0/8 |
| Supplied challenge evidence (oracle) | 4/8 (50.0%) | 0.333 | 0/7 | 3/6 (50.0%) | 0/8 |

Both confusion matrices were identical:

| Gold | S | C | I | U |
|---|---:|---:|---:|---:|
| S | 0 | 0 | 1 | 0 |
| C | 0 | 1 | 0 | 0 |
| I | 0 | 3 | 3 | 0 |

There were **zero observed false-support cases**, separately 0/12 on the original
set and 0/7 on the challenge set in each mode. Consequently evidence relevance,
citation validity and unsupported reasoning for *observed false-support cases*
are **not applicable**, rather than assumed successful. These denominators must
not be pooled across repeated contexts or interpreted as a safety guarantee.

The challenge set still exposed semantic errors with technically valid citations:

| Case | Observed failure | Evidence and citation review |
|---|---|---|
| test-07, end to end | Contradicted → insufficient | Relevant annotated beta-cell evidence was retrieved. The quote still mismatched after repair; validator downgraded it. Oracle returned contradicted. |
| test-10, end to end | Contradicted → insufficient | Relevant anatomy evidence was retrieved. Model omitted required citations, including after repair. Oracle returned contradicted. |
| test-17, both | Insufficient → contradicted | Relevant DPP evidence and technically valid quotations. Explanation says the lifetime guarantee is not established, then assigns contradiction. Reasoning exceeds the source's bounded study result. |
| adv-02/05, both | Insufficient → contradicted | Relevant DPP evidence, valid quotations, but no individual lifetime guarantee or unlimited external validity. Oracle adv-02's explanation ends mid-sentence despite valid JSON and a reported stop completion. |
| adv-06, both | Insufficient → contradicted | Relevant prediabetes definition, valid quote; the source cannot determine the unspecified individual's diagnostic category. Label boundary merits independent review. |
| adv-08, both | Supported → insufficient | Valid childhood-onset quote, but model refuses the bounded meta-statement about absence of an individual diagnosis. This positive control also needs adjudication. |

No challenge verdict failed citation validation. Adv-03 (forecasting accuracy
versus missed hypoglycemia) and adv-04 (irrelevant anatomy quotation) returned
insufficient in both modes. This does not establish robust entailment checking.
An explicit **constructed** adv-04 supported response passes the existing
validator in an offline test: its ID and quote are real, its inference is invalid.
That counterexample is not a model result and is excluded from all metrics.

[Machine-readable case audit](../eval/results/2026-11-03-qwen-prompt-2.1/case_audit.json),
[original summary](../eval/results/2026-11-03-qwen-prompt-2.1/test.summary.json),
[challenge summary](../eval/results/2026-11-03-qwen-prompt-2.1/adversarial.summary.json).

## Provider consistency and historical runs

Groq credentials were absent from environment, `.env`, and local Streamlit
secrets. The full hosted-model evaluation is **pending**, not scored as unavailable
or replaced by local-model scores. The live UI exposed `openai/gpt-oss-20b`, prompt
2.1.0 in smoke checks; those observations are not an 18-claim evaluation.

The runner now accepts `--provider ollama|groq` and `--model`, defaulting to existing
provider configuration. It reuses the assessor abstraction and compatible cache
identity, paces every hosted request (including citation repair), and stops on
quota exhaustion while preserving partial rows without a misleading aggregate.
The default 60-second interval is conservative pacing, not a guarantee of fitting
every account's token/day limits. No automatic retry loop is used.

Original files remain untouched. The historical Qwen **prompt 2.0.0** run had
13/18 accuracy, macro-F1 0.725, false support 0/12 and abstention 5/6 end to end;
its gold-bearing-only oracle run had 8/13 accuracy and macro-F1 0.509. These
are different prompt/protocol configurations, not replicates to average. Current
results alone cannot attribute a quality improvement to citation repair.
[Historical replay, including a matched subset](../eval/results/2026-11-03-historical-replay/assessments.summary.json).

## Reproduction

From the repository root, using Python 3.12+ and the included corpus snapshot:

```sh
python -m pip install '.[dev]'
python -m scripts.download_model
python -m scripts.compare_retrieval --output-dir eval/results/retrieval-reproduction-01

# Offline metric replay; no clients, embeddings, or inference instantiated:
python -m scripts.run_eval --outputs eval/results/2026-11-03-qwen-prompt-2.1/test.jsonl
python -m scripts.run_eval --claims eval/claims_adversarial.jsonl --outputs eval/results/2026-11-03-qwen-prompt-2.1/adversarial.jsonl
python -m scripts.run_eval  # historical prompt 2.0.0 replay

# Actual current-model inference; Ollama must be running:
ollama pull qwen3:4b-instruct-2507-q4_K_M
python -m scripts.run_eval --live --provider ollama --model qwen3:4b-instruct-2507-q4_K_M --outputs eval/results/qwen-reproduction-01/test.jsonl
python -m scripts.run_eval --live --provider ollama --model qwen3:4b-instruct-2507-q4_K_M --claims eval/claims_adversarial.jsonl --outputs eval/results/qwen-reproduction-01/adversarial.jsonl

# Pending hosted-model evaluation: set GROQ_API_KEY privately in the environment or .env first.
python -m scripts.run_eval --live --provider groq --model openai/gpt-oss-20b --request-interval 60 --outputs eval/results/groq-reproduction-01/test.jsonl
python -m scripts.run_eval --live --provider groq --model openai/gpt-oss-20b --request-interval 60 --claims eval/claims_adversarial.jsonl --outputs eval/results/groq-reproduction-01/adversarial.jsonl

python -m pytest -q
```

Choose unused paths for each inference/retrieval run; outputs are never
overwritten. Replay prints without modifying old artifacts; `--report-dir NEW_DIR`
saves fresh replay reports. `--literature` explicitly opts into a different live
experiment; oracle stays on supplied evidence. Do not compare those scores as
local-only runs. Corpus/label mismatches and mixed configurations are rejected.

The included assessment cache is ignored; one can move `data/cache/assessments`
aside to force uncached inference. Pinned corpus/model/prompt/configuration and
replay enable auditing, not a promise of bit-identical new generation.

## Limits of the findings

Small non-independent datasets, incomplete retrieval judgments, provisional
agent-authored labels, ambiguous contradiction/insufficiency boundaries,
archived sources, and one run per configuration limit conclusions. There is no
independent manual clinical annotation, clinician-led validation, prospective
clinical evaluation, systematic literature review, or production healthcare
validation. The central finding is a visible distinction between source tracing
and semantic reasoning quality, not a measured guarantee of correctness.
