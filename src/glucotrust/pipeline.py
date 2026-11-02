from __future__ import annotations

import re
from dataclasses import dataclass, field

from glucotrust.assess import AssessmentUnavailable, PROMPT_VERSION
from glucotrust.retrieve import SearchHit
from glucotrust.literature import LiteratureUnavailable
from glucotrust.validate import ValidatedAssessment, validate_assessment


def is_dosing_request(claim: str) -> bool:
    return bool(re.search(r"\b(insulin|dose|dosage|dosing|units|inject)\b", claim, re.I) and re.search(
        r"\b(how (?:much|many)|should (?:i|we)|my|recommend|calculate|prescribe|give me|what (?:dose|dosage)|take|inject)\b", claim, re.I))


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


def assess_claim(claim: str, retriever, assessor, *, passages=None, literature=None) -> ClaimResult:
    claim = claim.strip()
    if not claim or len(claim) > 2000:
        raise ValueError("Enter a claim of 1–2,000 characters")
    if is_dosing_request(claim):
        return ClaimResult(claim, "blocked", [], None, assessor.model,
                           message="This prototype cannot provide personal treatment or insulin dosing advice.")
    hits = retriever.search(claim, k=3) if passages is None else [SearchHit(p, 0.) for p in passages]
    try:
        assessment = assessor.assess(claim, [h.passage for h in hits])
    except AssessmentUnavailable as exc:
        return ClaimResult(claim, "unavailable", hits, None, assessor.model, message=str(exc), run=assessor.last_run)
    validated = validate_assessment(assessment, [h.passage for h in hits])
    run = assessor.last_run
    actual_model = run.get("response", {}).get("model", assessor.model)
    result = ClaimResult(claim, "assessed", hits, validated, actual_model, run=run)
    # Explicit oracle inputs must never trigger an external search.
    if literature is None or passages is not None or validated.verdict != "insufficient":
        return result
    result.literature = dict(status="searching", local_assessment=validated.model_dump(), local_run=run)
    try:
        found = literature.search(claim, k=3)
    except LiteratureUnavailable as exc:
        result.literature.update(status="unavailable", note=str(exc))
        return result
    result.literature.update(queries=found.queries, note=found.note,
                             passages=[h.passage.model_dump(mode="json") for h in found.hits])
    if not found.hits:
        result.literature["status"] = "no_results"
        return result
    combined = hits + found.hits
    result.hits = combined
    try:
        external = assessor.assess(claim, [h.passage for h in combined])
    except AssessmentUnavailable as exc:
        result.literature.update(status="assessment_unavailable", note=str(exc), failed_run=assessor.last_run)
        return result
    result.assessment = validate_assessment(external, [h.passage for h in combined])
    result.run = assessor.last_run
    result.model = result.run.get("response", {}).get("model", assessor.model)
    result.literature["status"] = "assessed"
    return result
