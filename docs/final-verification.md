# Final local verification — 2026-11-03

Environment: macOS ARM64, Python 3.12.6, existing project virtual environment.
This is a local verification record, not a clean Linux install or completed
GitHub Actions run.

| Check | Actual outcome |
|---|---|
| Baseline `python -m pytest -q` | 67 passed |
| Final `python -m pytest -q` | 75 passed in 7.63 seconds |
| `HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 python -m pytest -q` | 75 passed in 3.40 seconds |
| `python -m pip check` | No broken requirements found |
| `python -m compileall -q app.py src scripts tests` | Exit 0 |
| Real MiniLM/BM25 retrieval | Completed; 15 queries, 8 paraphrases, same 199 passages |
| Real current Qwen original-test run | 36 outcomes, 18 per setting; 35 newly inferred, 1 compatible cache hit |
| Real current Qwen challenge run | 16 outcomes, 8 per setting; separate provisional labels |
| Offline summary reproduction | Both new runs exactly match saved summary JSON |
| Original annotation hashes | All three original annotation-file hashes unchanged |
| Corpus fingerprint | Unchanged: `335471d3abe3b8d04ff1ff53359b82d128b0ed268d7f1198e3c7d91bd51f648c` |
| Missing-key Groq CLI | Exit 2 with an explicit pending message; no output file or metrics created |
| Documentation relative links | No missing targets in README, docs, or artifact index |
| Secret/cache exclusion | Existing ignore rules cover `.env`, Streamlit secrets, caches, runtime and feedback; no Groq-key/private-key patterns found in deliverable files |

New regression coverage includes explicit provider selection, request pacing,
mixed-configuration/digest rejection, empty-evidence oracle handling, separate
validation downgrades, exact challenge quotes and the validator's inability to
prove entailment, and scoped current-reference display without changing assessor
evidence. Streamlit resource caches are cleared in the new UI test so a previous
mock retriever cannot contaminate it.

The GitHub Actions workflow is configured to install CPU dependencies and run the
offline suite on Python 3.12 for pushes and pull requests. It has not been run on
GitHub during this work. [Hosted smoke checks](demo-verification.md) are separate.
The local checkout had no commits or configured remote at inspection; no commit,
push, deployment, or public GitHub publication is claimed.

## Subsequent bilingual change

Prompt 2.2.1 adds explicit English/Portuguese input handling. The expanded offline suite passed 86 tests in 7.29 seconds with model downloads disabled. Earlier 75-test and prompt 2.1.0 observations above remain historical. See [bilingual verification](bilingual-input.md) for the separately recorded smoke checks; this change has not been deployed.
