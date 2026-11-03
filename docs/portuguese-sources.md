# Portuguese biomedical sources — feasibility check, 2026-11-03

Two relevant complements to Europe PMC are **BVS/LILACS** and **SciELO**.
Neither is integrated into GlucoTrust by this change; Europe PMC remains the
existing automated fallback. Research publication coverage is not a guarantee
of evidential support or current clinical guidance.

| Source | Fit | Technical findings and limits |
|---|---|---|
| BVS / LILACS, BIREME/PAHO/WHO | Regional health literature, including Brazilian/Portuguese material; a strong subject-matter fit. | [Official bibliographic API specification](https://github.com/bireme/api-docs/blob/main/apis/bibliographic-en.yaml) documents `https://api.bvsalud.org/bibliographic/v1/search/`, query/filter/pagination parameters and an **apikey header**. An unauthenticated one-record diabetes search returned **403** here, so usable authenticated search was not verified. |
| SciELO | Open-access journal literature across disciplines, including health; collection and article language must be checked. | [Official ArticleMeta documentation](https://github.com/scieloorg/articles_meta/blob/master/docs/source/index.rst) and [official Python client](https://github.com/scieloorg/articlemetaapi/blob/master/articlemeta/client.py) document metadata/identifier retrieval. Both the one-identifier endpoint and its article-record endpoint returned **200 with valid JSON** without credentials. This establishes metadata access, not a working diabetes search or Portuguese full-text extraction. |

The [LILACS landing page](https://lilacs.bvsalud.org/) displayed a maintenance
notice and directs searches to the [BVS Regional Portal](https://pesquisa.bvsalud.org/portal/?lang=pt).
The [Brazilian Ministry of Health's BVS description](https://bvsms.saude.gov.br/o-que-e-a-bvs-ms/)
explains access to regional/international health information and LILACS.
[SciELO's official home](https://www.scielo.org/) provides a Portuguese interface
and journal collections including Brazil and Public Health.

## Actual endpoint probes

No credentials, patient information or model requests were sent in these probes.

```text
GET https://api.bvsalud.org/bibliographic/v1/search/?q=diabetes&count=1&format=json
→ 403 without an API key (the specification requires a key)

GET https://articlemeta.scielo.org/api/v1/article/identifiers/?collection=scl&limit=1
→ 200; JSON contained meta and one objects entry

GET https://articlemeta.scielo.org/api/v1/article/?collection=scl&code=S0100-879X1998000800002
→ 200; article metadata JSON
```

The randomly selected SciELO record was an English-language 1998 article, not a
diabetes source. It was used only to check the API contract; it was not added to
the corpus or represented as Portuguese evidence. The browser text-fetch tool
could not open the SciELO/BVS search pages. No full-text retrieval or language
coverage measurement was completed.

## Recommendation

BVS/LILACS is the strongest conceptual next source for Portuguese health
literature, conditional on obtaining API access and testing actual Portuguese
abstracts. SciELO is a practical alternative for a small metadata-to-passage pilot
because its metadata endpoint worked here. ArticleMeta is an identifier/metadata
service, not a proven replacement for Europe PMC's topic-search endpoint.

Before adding either provider, verify search access, Portuguese abstract/full-text
availability, per-article reuse permissions, stable source IDs and URLs, bounded
request behavior, and deduplication against Europe PMC. Use original Portuguese
passages for exact citation validation; translated summaries remain display text.
A small independently reviewed retrieval set would be needed before claiming
better Portuguese evidence coverage. This is feasibility research, not a new
feature or a measured reliability improvement.
