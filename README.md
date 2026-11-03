# GlucoTrust Lite

A small, independent research prototype for assessing diabetes-related claims
against inspectable evidence. It combines biomedical retrieval, structured LLM
assessment, citation validation, and reviewer feedback.

I built it after undergraduate research on personalized blood-glucose forecasting
and clinically meaningful ML errors, to gain practical experience with biomedical
NLP, RAG, source traceability, and human oversight in healthcare AI.

**Educational research only. Not medical advice or a clinical decision system.**

## Demo

[Open the Streamlit demo](https://glucotrust-lite.streamlit.app).
On 2026-11-03, the hosted Groq app rendered and returned supported and
insufficient-evidence assessments in browser checks. These smoke checks are
separate from the local Qwen evaluation below. See the
[dated verification record](docs/demo-verification.md) for exactly which flows
were tested and their limitations. Supported/insufficient results, citation display, literature fallback, and a feedback acknowledgement were observed; the live dosing-block response remains unverified. The local provenance changes in this revision have not been deployed.

## English and Portuguese input

Choose **English** or **Português** in the input-language selector. Portuguese claims use the configured provider to translate the search query into English, then assess the original claim with an explanation in Portuguese. Source passages and exact quotes stay in their original language. The search translation is visible and may introduce errors; it is never treated as evidence. Portuguese input adds a translation request to the selected provider. Use **Traduzir título e resumo para português** to translate the title and assessment summary; original evidence and citations are retained.

The existing scores below describe prompt **2.1.0**, before bilingual support. Prompt **2.2.1** has separate [bilingual smoke checks](docs/bilingual-input.md), not a full new benchmark.

## Features

- MiniLM semantic retrieval over three local passages, with BM25 as an evaluation baseline.
- Ollama and Groq assessment providers, with explicit structured outputs.
- Passage-ID and verbatim-quote validation, plus one bounded citation-repair attempt.
- Optional Europe PMC abstracts/open-access excerpts when local evidence is insufficient.
- Evidence display, archived-source labels, and reviewer feedback saved as JSONL.
- A local guard for common personal insulin-dosing requests.

## Architecture

```text
Claim → MiniLM top 3 → Ollama / Groq assessment → citation validator
                              ↓ if insufficient
                        optional Europe PMC → one reassessment
                                              ↓
                                      evidence UI → feedback
```

The existing Streamlit app calls the shared pipeline in `src/glucotrust`.
Corpus metadata supplies source links; the model returns a verdict, exact quotes,
passage IDs, and explanation. Cache identities include provider, model/settings,
prompt/schema, and evidence fingerprint. Hosted aliases do not expose immutable
weights, so an alias alone cannot guarantee exact model reproducibility.

## Dataset and provenance

The included diabetes subset contains **60 MedQuAD Q&A records / 199 passages**
from eight NIDDK documents. Original URLs were recorded as inaccessible on
2026-11-02; all passages remain archived historical content, unverified as current
guidance. Three separately checked current NIDDK references are linked for narrow
statements; they do not replace archived text or become model evidence.
See [attribution and corpus construction](data/curated/README.md) and the
[scoped source review](docs/source-review.md).

## Evaluation

Fresh local runs on 2026-11-03, against **provisional agent-authored labels**:

| Retrieval | Recall@3, 15 queries | Paraphrases, 8 queries |
|---|---:|---:|
| BM25 | 8/15 (53.3%) | 2/8 (25.0%) |
| MiniLM | 11/15 (73.3%) | 4/8 (50.0%) |

Recall@3 here means at least one annotated gold passage in the top three.
Both methods use the same 199 passages and queries; gold IDs are not exhaustive.

| Qwen, prompt 2.1.0 | Accuracy / label agreement | Macro-F1 | False support | Correct abstention |
|---|---:|---:|---:|---:|
| End to end | 15/18 (83.3%) | 0.832 | 0/12 | 5/6 |
| Oracle evidence | 17/18 (94.4%) | 0.944 | 0/12 | 5/6 |

Model: `qwen3:4b-instruct-2507-q4_K_M`. Both modes had 18/18 available
assessments. Oracle uses gold passages, including empty evidence for five
uncovered claims. Two end-to-end errors were citation downgrades despite retrieval
of gold evidence; both modes misread an unsupported lifetime-prevention claim as
contradicted. Zero observed false support is not evidence of clinical safety.

[Full report](docs/evaluation.md): confusion matrices, separate adversarial
results, errors, historical prompt results, model fingerprint, and reproduction
commands. **Full Groq `openai/gpt-oss-20b` evaluation remains pending credentials**;
local Qwen scores do not describe the hosted model. The separate eight-case challenge set had 4/8 agreement in each setting, exposing additional interpretation errors.

## Safeguards and limitations

- **Supported / contradicted** describe what supplied evidence establishes.
- **Insufficient** means a conclusion cannot be established; it does not prove a claim false.
- **Unavailable** means inference or infrastructure failed, and is counted separately.
- Exact citations establish textual traceability, **not logical support or factual correctness**.
- Small evaluation sets, archived sources, limited literature search, reasoning errors,
  and a limited dosing guard constrain the demonstration. There is no clinician-led
  validation, prospective clinical evaluation, or production healthcare deployment.
- Do not enter personal health information. Hosted claims/evidence go to Groq;
  literature keywords go to Europe PMC. Cloud feedback files may not survive redeployment.

## Local setup

Requires Python 3.12+ and a running Ollama server for local assessment:

```sh
./init.sh
ollama pull qwen3:4b-instruct-2507-q4_K_M
.venv/bin/python -m streamlit run app.py
```

Setup caches pinned MiniLM weights; the curated corpus is included. CPU inference
needs no GPU. Copy settings from `.env.example` as needed; keep `.env`, Streamlit
secrets, feedback, and caches out of Git. Reinstall the package after source edits.

```sh
.venv/bin/python -m pip install '.[dev]'
.venv/bin/python -m pytest -q
.venv/bin/python -m scripts.run_eval  # offline replay of the historical run
```

A GitHub Actions workflow is configured for the offline suite on Python 3.12, without provider credentials or model-weight downloads; its first hosted run is pending. [Bilingual verification](docs/bilingual-input.md): 94 tests passed. See [hosted setup](docs/free-cloud-deployment.md),
[Docker/Ollama deployment](docs/deployment.md), and
[local configuration details](docs/local-setup.md).

## Technical lessons

Retrieval, interpretation, and citation fidelity fail in different ways. Supplying
gold evidence does not guarantee correct reasoning, and a real quotation can be
irrelevant to a conclusion. The useful outcome is an inspectable experiment with
explicit limitations. See [project reflection and next steps](docs/project-reflection.md).

Portuguese literature options: [BVS/LILACS and SciELO feasibility review](docs/portuguese-sources.md). These sources have not been integrated.
