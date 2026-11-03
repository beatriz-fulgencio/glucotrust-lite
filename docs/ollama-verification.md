# Local Ollama migration — 2026-11-02

> Historical verification record. For current evaluation and hosted-demo status, see [evaluation](evaluation.md) and [demo verification](demo-verification.md).

The Anthropic integration has been replaced by Ollama with `qwen3:4b-instruct-2507-q4_K_M`, prompt `2.0.0`. The earlier [verification record](verification.md) describes the previous implementation and remains historical.

## Completed checks

- Regenerated the Python 3.12/macOS ARM dependency lock without Anthropic or its unused SDK dependencies. Installed it into a new temporary environment; all **29 tests passed** and `pip check` found no broken requirements.
- Tested the real Ollama Python client's HTTP serialization and parsing using an offline transport. Tests cover schema transmission, cache reuse and corpus/model-digest invalidation, missing models, connection failure, timeout, malformed output, incomplete generation, citation checks, dosing blocks, UI rendering and feedback.
- Downloaded the selected Qwen model into the existing local Ollama server.
- Ran Streamlit's AppTest against real MiniLM and local Qwen: entered a claim, rendered a supported assessment with evidence, and persisted reviewer feedback to a temporary file. The automatic feedback check is not a human clinical review.
- Checked shell syntax and compiled the application/source/scripts. Recorded retrieval replay preserves BM25 8/15 and MiniLM 11/15 Recall@3.

## Classification evaluation

Development inference completed with fixed prompt/settings. Test inference is complete. The development run agreed with 7/8 provisional labels, with zero false-support outcomes among five non-supported claims; oracle agreement was 6/6. The failed development claim generated mismatched quotes, which the validator downgraded to insufficient. See [development results](../eval/results/dev_qwen_v2.md). Existing labels are provisional AI-authored annotations, not independently reviewed clinical judgments. There is no measured Claude baseline for a quality comparison.


## Frozen test results

Against the 18 provisional test labels, end-to-end agreement was **13/18 (72.2%)**, macro-F1 **0.725**, false support **0/12**, insufficient-label abstention **5/6**, and availability **18/18**. Mean uncached model-reported latency was **10.90 seconds** (excluding retrieval and Python/UI overhead).

Oracle agreement was **8/13 (61.5%)**, macro-F1 **0.509**, with availability **13/13** and mean latency **7.76 seconds**. The oracle subset differs from the full test set, so those percentages are not a paired estimate of retrieval's effect. Macro-F1 uses all three labels even when a subset lacks a label.

Four end-to-end support/contradiction claims were downgraded for missing or invalid citations, and one insufficient-label claim was classified as contradicted. The validator establishes textual traceability, not semantic correctness. Zero observed false support in this small set does not demonstrate safety.

See [test metrics](../eval/results/assessments.md), [full summary including confusion matrices and latency distributions](../eval/results/assessments.summary.json), and [observed failures and review cases](../eval/qwen_error_analysis.md). Raw JSONL outputs preserve prompt/schema, model digest, corpus/label fingerprints, token counts and durations. The prompt was not changed after observing development or test outputs.

Remaining work: independent human annotation/error review, optional Kaggle comparison, project-code license selection, walkthrough recording and publication. There is no claim of clinical efficacy or equivalence to Claude.

The glucose-forecasting case study (`test-13`) returned **insufficient**, without a validation failure: retrieved diabetes-diagnosis material did not establish clinical safety of a forecasting model.
