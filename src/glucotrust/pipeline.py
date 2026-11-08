from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field

from glucotrust.assess import AssessmentUnavailable, PROMPT_VERSION
from glucotrust.retrieve import SearchHit
from glucotrust.literature import LiteratureUnavailable
from glucotrust.validate import ValidatedAssessment, validate_assessment


def is_dosing_request(claim: str) -> bool:
    normalized = " ".join("".join(c for c in unicodedata.normalize("NFD", claim.lower()) if not unicodedata.combining(c)).split())
    if not re.search(r"\b(insulin|insulina|dose|dosage|dosing|doses|dosagem|units|unidades|inject|injetar|aplicar)\b", normalized):
        return False
    # Action verbs alone also occur in scientific claims ("cells take up glucose").
    personal = r"\b(?:(?:should|can|must|could) (?:i|we)|(?:i|we) (?:need|take|inject)|devo|devemos|posso|preciso)\b"
    possession = r"\b(?:my|our|minha|meu|nossa|nosso)\s+(?:insulin|insulina|dose|dosage|dosing|dosagem|units|unidades)\b"
    quantity = (r"\b(?:how much (?:[\w-]+ ){0,4}insulin|how many (?:units|doses)|what (?:dose|dosage)|"
                r"quanto (?:de )?insulina|quantas (?:unidades|doses)|qual (?:e a )?(?:dose|dosagem))\b")
    directive = (r"^(?:please |por favor,? )?(?:recommend|calculate|prescribe|give me|recomende|recomenda|calcule|calcular|prescreva|"
                 r"take|inject|tomar|injetar|aplicar)\b|"
                 r"\b(?:take|inject|tomar|injetar|aplicar)\s+\d")
    return any(re.search(pattern, normalized) for pattern in (personal, possession, quantity, directive))


@dataclass
class ClaimResult:
    claim: str
    status: str
    hits: list[SearchHit]
    assessment: ValidatedAssessment | None
    model: str
    prompt_version: str = PROMPT_VERSION
    message: str = ""
    run: dict = field(default_factory=dict)
    literature: dict = field(default_factory=dict)


def assess_claim(claim: str, retriever, assessor, *, passages=None, literature=None, language="en") -> ClaimResult:
    if language not in {"en", "pt"}:
        raise ValueError("language must be en or pt")
    claim = claim.strip()
    if not claim or len(claim) > 2000:
        raise ValueError("Enter a claim of 1–2,000 characters")
    if is_dosing_request(claim):
        return ClaimResult(claim, "blocked", [], None, assessor.model,
                           message="This prototype cannot provide personal treatment or insulin dosing advice.")
    retrieval_query, translation = claim, {}
    if language == "pt" and passages is None:
        try:
            retrieval_query, translation = assessor.translate_query(claim)
        except AssessmentUnavailable as exc:
            return ClaimResult(claim, "unavailable", [], None, assessor.model, message=str(exc))
        if is_dosing_request(retrieval_query):
            return ClaimResult(claim, "blocked", [], None, assessor.model,
                               message="This prototype cannot provide personal treatment or insulin dosing advice.")

    def finish(result):
        if translation:
            result.run = {**result.run, "query_translation": translation}
        return result

    hits = retriever.search(retrieval_query, k=3) if passages is None else [SearchHit(p, 0.) for p in passages]
    try:
        assessment = assessor.assess(claim, [h.passage for h in hits], **({"language": "pt"} if language == "pt" else {}))
    except AssessmentUnavailable as exc:
        return finish(ClaimResult(claim, "unavailable", hits, None, assessor.model, message=str(exc), run=assessor.last_run))
    validated = validate_assessment(assessment, [h.passage for h in hits])
    run = assessor.last_run
    actual_model = run.get("response", {}).get("model", assessor.model)
    result = ClaimResult(claim, "assessed", hits, validated, actual_model, run=run)
    # Explicit oracle inputs must never trigger an external search.
    if literature is None or passages is not None or validated.verdict != "insufficient":
        return finish(result)
    result.literature = dict(status="searching", local_assessment=validated.model_dump(), local_run=run)
    try:
        found = literature.search(retrieval_query, k=3)
    except LiteratureUnavailable as exc:
        result.literature.update(status="unavailable", note=str(exc))
        return finish(result)
    result.literature.update(queries=found.queries, note=found.note,
                             passages=[h.passage.model_dump(mode="json") for h in found.hits])
    if not found.hits:
        result.literature["status"] = "no_results"
        return finish(result)
    combined = hits + found.hits
    result.hits = combined
    try:
        external = assessor.assess(claim, [h.passage for h in combined], **({"language": "pt"} if language == "pt" else {}))
    except AssessmentUnavailable as exc:
        result.literature.update(status="assessment_unavailable", note=str(exc), failed_run=assessor.last_run)
        return finish(result)
    result.assessment = validate_assessment(external, [h.passage for h in combined])
    result.run = assessor.last_run
    result.model = result.run.get("response", {}).get("model", assessor.model)
    result.literature["status"] = "assessed"
    return finish(result)
