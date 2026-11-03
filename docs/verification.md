# Implementation verification — 2026-11-02

> Historical verification record. For current evaluation and hosted-demo status, see [evaluation](evaluation.md) and [demo verification](demo-verification.md).

- Python 3.12 virtual environment created and pinned dependencies installed. `pip check`: no broken requirements.
- A separate source copy and clean virtual environment under `/private/tmp` installed from `requirements.lock.txt` plus a regular local package install. All **21 tests passed** there, and recorded evaluation replay reproduced the published retrieval counts without model or API access.
- Real CPU MiniLM search ran on all 15 retrieval queries: 11/15 strict gold-ID hits; BM25: 8/15. Paraphrased subset: 4/8 and 2/8. Raw rankings and scoring caveats are included in `eval/`.
- Pinned MedQuAD ZIP downloaded, all scanned XML checksums verified, and corpus regenerated. All 199 passages matched the included snapshot after excluding the later URL-check date.
- Eight original source URLs were checked over the network; all returned 404. All 199 passages remain archived records.
- The actual Streamlit application ran with the real corpus and MiniLM through Streamlit's AppTest harness: no UI exceptions, three evidence panels, and a clear missing-key status. Successful verdict/quote/feedback rendering is covered separately with a mocked assessor. This does not claim a completed live browser/API assessment.
- The installed Anthropic SDK serialized structured-output, explicit-effort and beta-fallback fields and parsed a mocked HTTP response correctly. No live Anthropic calls were made.
- Python compilation checks completed. Secrets, raw downloads, model caches and reviewer logs are ignored by Git.

Pending: an Anthropic key and live classification/oracle runs, independent human annotation review, Kaggle-copy comparison, code-license selection, walkthrough recording and publication. Expected case-study labels and provisional annotations are not reported as observed model results.

## Subsequent migration

The bullets above describe the original implementation. See [local Ollama verification](ollama-verification.md) for the replacement, current checks and observed classification results. An Anthropic key is no longer required.
