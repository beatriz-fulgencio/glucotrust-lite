# Corpus provenance

Original: [abachaa/MedQuAD](https://github.com/abachaa/MedQuAD), revision `577bd37b96c02d1833b2c9eed2de9f96964e96cb`.

The corpus is an adaptation: diabetes-focused filtering on Focus/Question, deterministic record selection, whitespace normalization, paragraph chunking and added provenance metadata. It contains 60 Q&A records / 199 passages from eight original NIDDK documents. `input_manifest.json` records SHA-256 checksums for every scanned XML; `curation_log.csv` records decisions for every scanned Q&A. Removed-answer collections are excluded.

Record-level near-duplicate detection uses >=0.92 Jaccard similarity over lowercase answer-word sets. This transparent heuristic does not remove every repeated fact across chunks or distinct longer answers.

All source URLs returned 404 in `provenance_checks.json` on 2026-11-02. Every passage is `archived_record`; none is presented as current guidance. `checked_on` records a URL check, not medical review. A reachable URL alone can never produce `url_verified`: a passage-specific manual content-match attestation is also required by `scripts.check_provenance`.

The original XML is the provenance authority. A Kaggle copy was not downloaded or compared; no claim of equivalence is made.

## Attribution

MedQuAD is distributed under [Creative Commons Attribution 4.0 International](https://creativecommons.org/licenses/by/4.0/). See the [original license](https://github.com/abachaa/MedQuAD/blob/master/LICENSE.txt) and [dataset README](https://github.com/abachaa/MedQuAD/blob/master/readme.txt). No endorsement by the creators or NIH is implied. The data is supplied without warranties; the license terms apply.

Asma Ben Abacha and Dina Demner-Fushman. **A Question-Entailment Approach to Question Answering.** BMC Bioinformatics 20, 511 (2019). [doi:10.1186/s12859-019-3119-4](https://doi.org/10.1186/s12859-019-3119-4).
