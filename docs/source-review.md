# Scoped source review — 2026-11-03

The 60 original MedQuAD records / 199 passages, original URLs, and 2026-11-02
reachability metadata are unchanged. The original eight URLs were recorded as
404 on that date; they have not been reclassified as current guidance.

An agent read three current official NIDDK pages and compared their body text
with specific statements. HTTP success alone was not the verification criterion.
This is a content comparison, not clinician review or verification of every
medical statement in a page. The accessible links, date, page sections, scope,
and limitations are recorded separately in
[`current_references.json`](../data/curated/current_references.json).

| Archived passage | Narrow statement | Current reference and content checked |
|---|---|---|
| `5_NIDDK_QA:0000022-1#p1` | Type 2 diabetes can develop during childhood. | [Type 2 Diabetes](https://www.niddk.nih.gov/health-information/diabetes/overview/what-is-diabetes/type-2-diabetes), section “Who is more likely to develop type 2 diabetes?” explicitly includes childhood among possible ages of onset. |
| `5_NIDDK_QA:0000033-6#p1` | Diabetic kidney disease can be present without symptoms. | [Diabetic Kidney Disease](https://www.niddk.nih.gov/health-information/diabetes/overview/preventing-problems/diabetic-kidney-disease), section “How can I tell if I have diabetic kidney disease?” describes absence of symptoms and blood/urine checks. |
| `5_NIDDK_QA:0000035-8#p1` and `0000035-2#p1` | Modest weight loss and physical activity can help prevent or delay type 2 diabetes. | [Preventing Type 2 Diabetes](https://www.niddk.nih.gov/health-information/diabetes/overview/preventing-type-2-diabetes), section “How can I lower my chances of developing type 2 diabetes?” discusses risk reduction and the DPP. |

These checks do not validate an individual diagnosis, universal lifetime
prevention, the historical symptom list, or all old numerical estimates. The
UI preserves the archived badge and broken-link warning and adds clearly scoped
current-reference links. The current pages are **not supplied to the assessor**;
a verdict remains grounded in the displayed archived/research passages.
