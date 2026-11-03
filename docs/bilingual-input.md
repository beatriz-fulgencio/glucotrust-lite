# English and Portuguese input

Select **English** or **Português** in the claim form. Interface controls remain
English. For Portuguese input, the selected Ollama or Groq model first translates
the claim into English for MiniLM retrieval and Europe PMC search. The original
Portuguese claim is passed to the assessor, with an explicit Portuguese response
language. Evidence passages and exact quotations remain unchanged, typically in
English. The visible search translation is also stored with the result/feedback.

Translation is a retrieval aid, never an evidence passage. It can distort meaning,
negation or quantities; inspect the displayed translation. Portuguese requires one
additional provider request before retrieval. A translation failure returns
unavailable, not insufficient evidence. Oracle inputs bypass search translation.

The dosing guard handles common English and Portuguese personal dosing requests,
including accents. It runs before translation, retrieval and assessment. It is
still a limited heuristic rather than a comprehensive medical-content classifier.

Prompt 2.2.1 separates response-language cache identities. Previous 2.1.0 results
remain preserved and must not be described as measurements of bilingual support.

## Verification

Final prompt **2.2.1** Portuguese smoke checks returned supported for the asymptomatic-kidney-disease example and insufficient for the forecasting-safety example, in both end-to-end and oracle modes. All four explanations were in Portuguese (with source language retained where quoted), and none failed citation validation. Raw outputs are in [`portuguese-2.2.1.jsonl`](../eval/results/2026-11-03-bilingual-smoke/portuguese-2.2.1.jsonl).

The final 2.2.1 English check also returned supported and insufficient for the same examples in both modes, with no citation failures; see [`english-2.2.1.jsonl`](../eval/results/2026-11-03-bilingual-smoke/english-2.2.1.jsonl). These eight outcomes cover only two distinct claims in two languages.

The offline suite passes **86 tests** with model downloads disabled. New tests
cover Portuguese UI selection, original-claim preservation, English search terms
for both retrieval paths, both providers' structured translation requests,
translation failure and bilingual dosing blocks.

Initial local Qwen prompt 2.2.0 smoke checks returned the expected verdicts for
both Portuguese examples (end to end and oracle) but wrote explanations in English.
Those observations are retained in `eval/results/2026-11-03-bilingual-smoke/portuguese.*`.
This prompted an explicit response-language field and prompt 2.2.1; initial English
smoke checks are also retained separately. These are two public examples per
language, not a representative bilingual benchmark. Groq serialization is tested
offline; live hosted behavior has not been verified for this change.

```sh
python -m pip install . --no-deps --no-build-isolation
python -m scripts.run_eval --live --provider ollama --language pt --claims eval/smoke/claims_pt.jsonl --outputs eval/results/bilingual-next/portuguese.jsonl
python -m scripts.run_eval --live --provider ollama --language en --claims eval/smoke/claims_en.jsonl --outputs eval/results/bilingual-next/english.jsonl
```

Use unused output paths. The same language option works with `--provider groq`;
configure credentials privately and retain the default hosted pacing. A full
bilingual evaluation, including independent translation/label review, is pending.
The local changes have not been deployed to the hosted demo.
