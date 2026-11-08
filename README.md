# GlucoTrust Lite

A small, independent research prototype for assessing diabetes-related claims
against inspectable evidence. It combines biomedical retrieval, structured LLM
assessment, citation validation, and reviewer feedback, with English and Portuguese input.

I built it after undergraduate research on personalized blood-glucose forecasting
and clinically meaningful ML errors, to gain practical experience with biomedical
NLP, RAG, source traceability, and human oversight in healthcare AI.

**Educational research only. Not medical advice or a clinical decision system.**

New to the code? Start with the [code review guide and Mermaid diagrams](docs/code-review-guide.md).

## Live demo

[Open GlucoTrust Lite](https://glucotrust-lite.streamlit.app).
The demo uses **Groq `openai/gpt-oss-20b`**; local Ollama is also supported.
Browser checks on 2026-11-03 observed assessments, citations, literature fallback,
feedback acknowledgement, and title switching. Live summary translation, dosing
blocking, and mouse clicks after the latest relocation remain unverified.
See [deployment](docs/demo-verification.md) and [bilingual verification](docs/bilingual-input.md).

## English and Portuguese

1. Choose **English** or **Português** in **Input language / Idioma da afirmação**.
2. Enter a claim and select **Assess claim →**. Portuguese claims use an English
   search translation; the assessor receives the original claim and is asked to
   explain its result in Portuguese. The search translation is inspectable.
3. To translate the page title and assessment summary, use **Traduzir título e
   resumo para português**, located **below the GlucoTrust Lite header**.
   **Show original / English** restores the original view.

Summary translation adds a provider request and is reused for the current result.
Failures retain the original and offer **Tentar traduzir o resumo novamente**;
retrying does not rerun assessment. The button was moved to avoid toolbar overlap.
Source passages and validated quotations retain their original language.
Translation can introduce errors. Bilingual smoke checks cover only two distinct
claims and do not establish reliability.

## Features and architecture

- MiniLM semantic retrieval over the top three local passages; BM25 evaluation baseline.
- Ollama and Groq structured assessment with passage-ID and exact-quote validation.
- One bounded citation-repair attempt and optional Europe PMC literature fallback.
- Archived-source labels, scoped current-reference links, and reviewer feedback JSONL.
- A guard for common English and Portuguese personal insulin-dosing requests.
- Shared web-app limits: six assessment/translation operations per minute and
  one in flight, configurable through [local settings](docs/local-setup.md).

```text
Original claim → English search query → MiniLM top 3 → Ollama / Groq → citation validator
                                                              ↓ if insufficient
                                                       optional Europe PMC
                                                              ↓
                                                   one reassessment → evidence UI
                                                                        ↓
                                                      optional summary translation / review
```

The shared pipeline lives in `src/glucotrust`. Cache identities include provider,
model/settings, prompt/schema, response language, and evidence fingerprint.
Hosted model aliases limit exact reproducibility.

## Dataset and provenance

The **60 MedQuAD records / 199 passages** come from eight NIDDK documents whose
original URLs were recorded as inaccessible on 2026-11-02. They remain archived,
unverified as current guidance. Three separately checked current references
support narrow statements; they do not replace model evidence.
See [attribution](data/curated/README.md) and [source review](docs/source-review.md).

**Portuguese-source candidates:** BVS/LILACS requires an API key; SciELO metadata
access worked, but Portuguese search/full-text retrieval remains unvalidated.
Neither is integrated. [Feasibility review](docs/portuguese-sources.md).

## Evaluation

Recorded on 2026-11-03 against **provisional agent-authored labels**:

| Retrieval | Recall@3, 15 queries | Paraphrases, 8 queries |
|---|---:|---:|
| BM25 | 8/15 (53.3%) | 2/8 (25.0%) |
| MiniLM | 11/15 (73.3%) | 4/8 (50.0%) |

Both methods use the same 199 passages and queries. Recall@3 means at least one
annotated gold passage in the top three; gold IDs are not exhaustive.

| Qwen, prompt 2.1.0 | Accuracy / label agreement | Macro-F1 | False support | Correct abstention |
|---|---:|---:|---:|---:|
| End to end | 15/18 (83.3%) | 0.832 | 0/12 | 5/6 |
| Oracle evidence | 17/18 (94.4%) | 0.944 | 0/12 | 5/6 |

Model: `qwen3:4b-instruct-2507-q4_K_M`. Both modes had 18/18 available outcomes.
Oracle supplies annotated evidence, including empty evidence for five uncovered
claims. Two end-to-end errors were citation downgrades despite retrieving gold
evidence; both modes misclassified an unsupported lifetime-prevention claim as
contradicted. The separate eight-case challenge set had 4/8 agreement in each mode.

These scores describe **prompt 2.1.0**, before bilingual **2.2.1** support.
They do not evaluate the current prompt, summary translation, literature fallback,
or the hosted Groq model. **Full Groq evaluation remains pending credentials.**
See the [evaluation report](docs/evaluation.md) for confusion matrices, errors,
configuration fingerprints, raw results, and exact reproduction commands.

## Safeguards and limitations

Verdicts describe supplied evidence. Insufficient does not mean false;
infrastructure failures are separate. Exact citations establish traceability,
**not logical support or factual correctness**. Zero false support does not establish safety.

Limits include small provisional datasets, archived sources, reasoning/translation
errors, limited search, and a heuristic dosing guard. There is no clinician-led
validation, prospective clinical evaluation, or production healthcare deployment.
Do not enter personal health information: hosted claims/evidence go to Groq,
keywords to Europe PMC. Cloud feedback may be lost after redeployment.

## Local setup and tests

Requires Python 3.12+ and a running Ollama server for local assessment:

```sh
./init.sh
ollama pull qwen3:4b-instruct-2507-q4_K_M
.venv/bin/python -m streamlit run app.py
```

Setup caches MiniLM; the curated corpus is included. Keep secrets, feedback,
and caches out of Git. Reinstall the package after source edits.

```sh
.venv/bin/python -m pip install '.[dev]'
.venv/bin/python -m pytest -q
.venv/bin/python -m scripts.run_eval  # offline replay of the historical run
```

**135 offline tests passed.** GitHub Actions is configured for Python 3.12 without
provider credentials or model-weight downloads; its outcome is unverified.
See [hosted setup](docs/free-cloud-deployment.md), [Docker deployment](docs/deployment.md),
and [local configuration](docs/local-setup.md).

## Technical lessons

Retrieval, interpretation, and citation fidelity fail in different ways. Gold
evidence does not guarantee correct reasoning, and a real quotation can be
irrelevant to a conclusion. This project makes those failures inspectable.
See [project reflection and next steps](docs/project-reflection.md).
