# Hosted demo verification — 2026-11-03

URL: https://glucotrust-lite.streamlit.app

Environment: macOS, Google Chrome, browser UI operated through accessibility
controls. The deployed UI identified **Groq `openai/gpt-oss-20b`, prompt 2.1.0**.
This was a smoke check, not the held-out evaluation and not a verification of
server-side secrets, deployment revision, immutable model weights, or clinical
reliability. Raw provider requests and server logs were unavailable.

| Flow | Input / setting | Observed result |
|---|---|---|
| Access | Public URL in Chrome | App rendered with 60-record corpus badge and hosted-data disclosure. Initial load was blank; later rendered. |
| Supported claim | “Early diabetic kidney disease can occur without symptoms.” Literature disabled. | Supported; explanation referred to asymptomatic early disease, three evidence passages displayed. |
| Citation display | Same supported example | Source/record IDs, archived badge, source links and the matching sentence were displayed. This checks traceability in one example, not entailment in general. |
| Insufficient evidence | “A low prediction error means a glucose-forecasting model is clinically safe.” Literature disabled. | Insufficient; explanation said diagnostic passages do not establish forecasting safety. The exact assessed claim was confirmed using the UI disclosure. |
| Reviewer feedback | Automated smoke-check note, explicitly not independent clinical review | UI displayed **“Feedback saved.”** This verifies the acknowledgement, not durable storage after restart or independent review quality. |
| Literature fallback | Same forecasting claim, literature enabled | UI displayed **“Literature search completed”**, six evidence passages (three local plus three Europe PMC research excerpts), and an externally informed insufficient verdict. Research excerpts were labeled unverified/not guidelines. All three external passages came from one paper, MED:42349253; this is not broad corroboration. |
| Personal insulin dosing | “How much insulin should I take?” | Attempted; browser window became unavailable before the response could be confirmed. Live outcome unverified; offline guard tests pass. |

A first literature-enabled attempt returned to a loading/landing state without a
confirmable result. A retry completed. UI interactions were asynchronous; an
intermediate accidentally concatenated claim was discarded and excluded from
these observations. No uptime, latency, concurrency or persistent-feedback
storage measurement is claimed. Web text extraction could not open the demo,
and a cookie-less curl request hit a redirect limit; these are access-method
limitations, not evidence that the browser-visible application is unavailable.

The new local current-reference links and clarification text have offline UI
test coverage, but were **not deployed or verified on the hosted instance**.
Docker/Oracle deployment checks remain a separate historical path. Full Groq
assessment metrics remain pending a credentialed CLI run; the local Qwen scores
must not be presented as hosted-model scores.
