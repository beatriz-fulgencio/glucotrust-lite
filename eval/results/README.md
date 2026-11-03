# Experiment artifacts

See [the evaluation report](../../docs/evaluation.md) for setup, interpretation,
limitations and exact commands. Raw JSONL includes responses and configuration;
summary JSON includes counts, denominators and confusion matrices.

| Path | Experiment |
|---|---|
| `2026-11-03-retrieval/` | Fresh BM25 versus pinned MiniLM, identical 199 passages and 15 queries |
| `2026-11-03-qwen-prompt-2.1/test.*` | Current local Qwen, 18 original test claims in each mode |
| `2026-11-03-qwen-prompt-2.1/adversarial.*` | Same configuration, separate eight-case provisional challenge set |
| `2026-11-03-qwen-prompt-2.1/case_audit.json` | Agent review of recorded errors and explicit empty false-support case lists |
| `2026-11-03-historical-replay/` | Offline reproduction of prompt 2.0.0, plus a matched gold-bearing subset |
| `groq_pending.json` | Full hosted evaluation pending local credentials; no fabricated metrics |

Original `assessments.*`, `dev_qwen_v2.*`, `retrieval*` and historical reports are
preserved. They describe their recorded configurations, not the current prompt
or Groq. New live runs require unused output paths. Replay prints by default;
`--report-dir` writes to a new directory without modifying previous reports.
Caches, credentials and reviewer feedback are ignored and do not belong here.

`2026-11-03-bilingual-smoke/` contains separate prompt 2.2.0 and 2.2.1 smoke checks. They must not be pooled with the 2.1.0 evaluation or treated as a bilingual benchmark.
