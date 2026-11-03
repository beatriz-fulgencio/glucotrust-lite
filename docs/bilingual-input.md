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

## Portuguese display button

**Traduzir título e resumo para português** switches the page title, subtitle,
assessment headings and verdict labels to Portuguese. For an existing English
explanation it makes a display-only translation request through the configured
provider, cached for the current result in the browser session. **Show original /
English** restores the original view. Selecting Portuguese input already requests
a Portuguese explanation, so those results do not need another translation.

The original assessment, verdict and citations are retained. Validated source
quotations within the explanation are replaced by protected placeholders before
translation and restored exactly; missing/duplicated placeholders cause translation
to fail safely. A failed translation shows the original explanation and a warning.
Translation may still distort unquoted reasoning and is labeled as automatic.
Static headings require no provider request. Source passages are not translated.

Verification: **92 offline tests passed**, including no reassessment on toggle,
session reuse, exact quote restoration and translation failure. A real local
Qwen summary translation produced Portuguese explanatory text and retained the
protected English source quote. An initial attempt without protection translated
the quotation despite its prompt; the protected implementation addresses that
observed failure. No new classification score is claimed. See the separate
[Portuguese-source feasibility review](portuguese-sources.md) for BVS/LILACS and SciELO.

## Translation retry correction

A failed summary translation previously stayed cached without a retry action.
The title could switch while the summary remained in English, and toggling the
button again reused the failure. The app now offers **Tentar traduzir o resumo
novamente** and clears failed translations when switching back to Portuguese.
Successful translations remain cached; retries do not rerun retrieval or claim
assessment. Quota, configuration and quote-preservation failures now have clearer
Portuguese messages, and sanitized translation failure reasons are logged server-side.

Verification: **94 offline tests passed**. Regression tests cover recovery after
a failed request, quota messaging and retrying through the language toggle.
The live title switch was observed working. A live English assessment completed,
but its summary-translation test was interrupted by a page reload; no successful
live summary translation is claimed from that attempt.

## Mouse-click layout correction

The translation control was the first element at the top of a zero-top-padding
page, overlapping Streamlit's fixed transparent toolbar. Accessibility activation
could toggle it, which did not establish that pointer clicks reached the button.
Following the report that the button could not be clicked, it was moved into a
separate language-controls container **below the custom site header**. Automated
state tests do not establish browser hit-testing; live pointer verification is
recorded separately when available.
