# Free demo: Streamlit Community Cloud and Groq

This option serves the Streamlit app on Community Cloud and sends assessments
to Groq's hosted `openai/gpt-oss-20b` model. No Ollama server, GPU VM, or downloaded
Qwen model is required for hosted assessments. MiniLM retrieval still runs on the
app server against the included curated corpus.

Groq's [Free tier](https://console.groq.com/docs/billing-faqs) has
[usage limits](https://console.groq.com/docs/rate-limits). Stay on the Free tier;
no paid provider fallback is configured. The app reports quota errors as
assessment unavailable. Citation repair and literature reassessment can each
consume additional calls. Community Cloud can sleep when unused and needs time
to wake; this is a demo deployment, not an uptime commitment.

## Prepare the accounts

1. Sign up or sign in at [GroqCloud](https://console.groq.com/login), then create
   a project API key on the API Keys page. Keep the account on the Free tier.
2. Sign in to [Streamlit Community Cloud](https://share.streamlit.io/) using the
   GitHub account that owns the app repository.
3. Put the application source in a GitHub repository. A private repository keeps
   source visibility separate from the public app; grant Streamlit access only
   as needed. Include `app.py`, `assets/`, `src/`, `pyproject.toml`,
   `requirements.txt`, `.streamlit/config.toml`, and `data/curated/` with its
   attribution. Do not upload local caches, feedback, `.env`, actual
   `.streamlit/secrets.toml`, `runtime/`, or SSH/cloud credentials.

`requirements.txt` installs the local package and CPU-only Torch on Linux x86-64.
Select **Python 3.12** when deploying. The macOS lock file is not used by this
deployment. Initial semantic retrieval downloads the pinned MiniLM model.

## Configure and publish

Create an app in Community Cloud using the repository, branch, and `app.py` as
the entry point. In Advanced settings, choose Python 3.12 and add these secrets:

```toml
GLUCOTRUST_PROVIDER = "groq"
GLUCOTRUST_GROQ_MODEL = "openai/gpt-oss-20b"
GROQ_API_KEY = "your-private-key"
GLUCOTRUST_TIMEOUT_SECONDS = 60
```

The template is also in `.streamlit/secrets.toml.example`. Enter the actual key
directly in the platform's secret store, rather than committing it to GitHub.
See [Community Cloud secret management](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/secrets-management).

For a local preflight, copy the template to the gitignored
`.streamlit/secrets.toml`, replace the key there, and run:

```sh
.venv/bin/python -m streamlit run app.py
```

Community Cloud supplies the public `https://...streamlit.app` URL. Once the app
starts, verify an evidence-supported claim with literature search off, an
insufficient-evidence claim with search on, and feedback saving. Confirm the
page discloses that claims and evidence are sent to Groq. Verify a dosing
request is blocked without inference.

## Behavior and limits

- Groq uses strict structured output, followed by the same Pydantic and exact
  quote/ID validator as the local provider. One bounded citation-repair attempt
  is retained. Failed citations cannot create a supported verdict.
- API authentication, rate limits, refusals, malformed responses, timeouts, and
  truncated generations remain unavailable outcomes, separate from insufficient
  evidence. No automatic paid fallback or unbounded retry is enabled.
- Hosted caches are isolated by provider/model, prompt, generation settings,
  schema, claim and passage fingerprint, and UTC date. Set
  `GLUCOTRUST_GROQ_REVISION` to invalidate the hosted deployment's cache manually.
  Hosted aliases have no local model digest, so exact weight reproducibility
  cannot be inferred from the alias alone.
- Feedback and caches on Community Cloud are not durable storage. They may be
  lost after restarts or redeployments. Do not treat this file as a permanent
  reviewer database.
- Existing Qwen evaluation scores do not describe this hosted model. Assess its
  behavior independently before making comparisons or reliability claims.
- To run locally with Ollama again, remove the hosted secrets or set
  `GLUCOTRUST_PROVIDER = "ollama"` and use the original setup instructions.

## Verification status

The adapter and UI pass 67 offline tests, including HTTP request serialization,
provider selection, cache isolation metadata, key exclusion from cache files,
bounded citation repair, and quota/error handling. On 2026-11-02, a live MiniLM
retrieval and Groq assessment for the public corpus example “Early diabetic
kidney disease can occur without symptoms” returned supported with one exact
validated citation and no validation errors. This is a deployment smoke check,
not a model evaluation or evidence of clinical reliability. The private GitHub
deployment repository is prepared; the public Community Cloud deployment still
requires completing its account connection and app setup.
