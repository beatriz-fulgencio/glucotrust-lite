# Project reflection

## Why I built it

I wanted practical experience with evidence-grounded LLMs, biomedical retrieval,
and source traceability after researching trustworthy AI challenges in healthcare.
My undergraduate work on personalized blood-glucose forecasting made me interested
in clinically meaningful errors: a small aggregate prediction error does not, on
its own, establish that dangerous events are detected. This prototype explores
how to make the evidence and limits of an AI assessment inspectable.

## Skills I developed

- Semantic retrieval and embeddings, compared against a transparent BM25 baseline.
- Biomedical NLP and retrieval-augmented inference with a bounded Europe PMC fallback.
- Structured LLM outputs, exact-quote validation, and source traceability.
- Evaluation of unsupported claims, abstention, and unavailable inference.
- Reproducible experiment records with model, prompt, corpus, and label identities.
- Human-in-the-loop assessment through reviewer feedback; feedback is not itself clinical validation.

## What the experiments taught me

MiniLM retrieved an annotated passage for 11/15 queries versus BM25's 8/15,
and for 4/8 paraphrases versus 2/8. The sample is small and the gold IDs are
incomplete, so this does not establish general superiority or clinical reliability.

The historical Qwen run exposed invalid quotations and confusion between missing
support and contradiction. The [evaluation report](evaluation.md) separates that
prompt from the current prompt and separates retrieval errors from interpretation
and citation failures. Oracle evidence does not guarantee correct reasoning.

The central lesson is that **citation integrity and evidential support are different**.
A quotation can occur verbatim in an existing passage while having no logical
bearing on the claimed conclusion. An offline counterexample demonstrates that
boundary; separate adversarial cases probe it using the same assessor. No extra
verification model was added. Zero observed false support on a small set cannot
establish safety, and a prompt change alone cannot justify a reliability claim.

## Limitations

Evaluation sets are small and manually specified, with provisional agent-authored
labels awaiting independent human review. Sources include archived medical
material. LLM reasoning can be wrong despite valid citations. Literature search
is bounded and is not a systematic review. There has been no clinician-led
validation, prospective clinical evaluation, or production healthcare deployment.
This is a research and learning demonstration, not a medical decision system.

## Next steps

1. Build a larger independently annotated biomedical evaluation with adjudicated disagreements.
2. Evaluate evidence entailment more deeply, including population and individual applicability.
3. Monitor source freshness and statement applicability systematically.
