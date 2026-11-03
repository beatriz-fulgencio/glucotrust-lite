# Bilingual deployment import fix — 2026-11-03

The generic retrieval-pipeline TypeError appeared after the bilingual update.
The previous installed package's `assess_claim` signature did not accept
`language`, while the updated form supplied it. Binding the new call against
the prior deployed API reproduces `TypeError: unexpected keyword argument
'language'`. This is the identified compatibility failure; production server
tracebacks were not available to independently confirm the running import path.

The Streamlit entrypoint now puts the repository's `src/` directory first on
its import path, ensuring a fresh process uses the checked-out implementation.
The package version is 0.1.1, and requirements.txt was updated to refresh the
cloud environment. Streamlit documents dependency-file updates and rebuilds in
[Manage your app](https://docs.streamlit.io/deploy/streamlit-community-cloud/manage-your-app).

Unexpected pipeline exceptions now retain server-side tracebacks, and the UI
identifies whether retrieval or assessment failed instead of always suggesting
an embedding download.

Verification: 87 tests passed with Hugging Face/Transformers offline flags,
including a subprocess test outside pytest's src path that places a deliberately
stale package ahead of normal imports, starts app.py, and verifies that the
current source and bilingual API are loaded. This does not claim a successful
hosted assessment after the rebuild.
