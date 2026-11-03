# Local setup and configuration

Use Python 3.12+ from the repository root. `./init.sh` creates/reuses `.venv`,
preserves existing `.env` settings, installs dependencies and caches pinned MiniLM.
Use `--skip-model` to defer MiniLM download, `--resolve-deps` to resolve dependencies
instead of the macOS ARM Python 3.12 lock, or `--run` to launch Streamlit afterwards.
Set `PYTHON=/path/to/python3.12` when choosing an interpreter for a new environment.
Setup does not install Ollama or pull Qwen automatically.

Manual setup:

```sh
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install '.[dev]'
cp .env.example .env  # only if it does not already exist
python -m scripts.download_model
ollama pull qwen3:4b-instruct-2507-q4_K_M
streamlit run app.py
```

On macOS ARM/Python 3.12, `requirements.lock.txt` records the tested dependency
versions. Other platforms resolve compatible wheels from `pyproject.toml`.
After changing source files, reinstall using `python -m pip install . --no-deps
--no-build-isolation`. Tests explicitly load `src/`; a stale installed package can
otherwise cause the CLI and tests to execute different versions.

| Variable | Purpose / default |
|---|---|
| `GLUCOTRUST_PROVIDER` | `ollama` or `groq`; default `ollama` |
| `GLUCOTRUST_MODEL` | Ollama model; default `qwen3:4b-instruct-2507-q4_K_M` |
| `GLUCOTRUST_OLLAMA_HOST` | Default `http://localhost:11434` |
| `GLUCOTRUST_GROQ_MODEL` | Default `openai/gpt-oss-20b` |
| `GROQ_API_KEY` | Private hosted credential; never put it in a command argument or Git |
| `GLUCOTRUST_GROQ_REVISION` | Explicit hosted-cache invalidation; default `1` |
| `GLUCOTRUST_TIMEOUT_SECONDS` | Positive request timeout; provider defaults apply |
| `GLUCOTRUST_FEEDBACK_PATH` | Feedback JSONL; default project-local `feedback.jsonl` |

MiniLM is pinned to revision `1110a243fdf4706b3f48f1d95db1a4f5529b4d41`.
Weights and inference caches live in ignored `data/cache/`; embeddings in ignored
`data/curated/*.npz`. Missing/incomplete inference is shown as unavailable rather
than insufficient evidence. Claims stay on the configured Ollama server in local
mode; a remote Ollama URL sends them to that server.

To inspect/rebuild data:

```sh
python -m scripts.download_data
python -m scripts.build_corpus
python -m scripts.check_provenance
```

Rebuilding or checking provenance can change corpus metadata and fingerprints;
preserve the published snapshot when replaying experiments. Current reference
comparisons live separately in `data/curated/current_references.json` and never
replace original records. A Kaggle-copy comparison remains optional and unperformed.
