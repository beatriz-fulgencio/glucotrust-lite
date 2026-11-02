from __future__ import annotations

from typing import Literal
from pydantic import BaseModel, ConfigDict, Field
from glucotrust.corpus import Passage

Verdict = Literal["supported", "contradicted", "insufficient"]


class Citation(BaseModel):
    model_config = ConfigDict(extra="forbid")
    passage_id: str
    quote: str = Field(min_length=1)


class Assessment(BaseModel):
    model_config = ConfigDict(extra="forbid")
    verdict: Verdict
    citations: list[Citation]
    explanation: str = Field(min_length=1)


class ValidatedAssessment(Assessment):
    validation_failed: bool = False
    validation_errors: list[str] = Field(default_factory=list)


def normalize_whitespace(text: str) -> str:
    return " ".join(text.split())


def validate_assessment(assessment: Assessment, passages: list[Passage]) -> ValidatedAssessment:
    lookup = {p.passage_id: p for p in passages}
    errors, valid = [], []
    for citation in assessment.citations:
        passage = lookup.get(citation.passage_id)
        if passage is None:
            errors.append(f"Unknown retrieved passage: {citation.passage_id}")
        elif not normalize_whitespace(citation.quote) or normalize_whitespace(citation.quote) not in normalize_whitespace(passage.text):
            errors.append(f"Quote does not match passage: {citation.passage_id}")
        else:
            valid.append(citation)
    if assessment.verdict != "insufficient" and not assessment.citations:
        errors.append("A supported or contradicted verdict requires evidence citations")
    return ValidatedAssessment(
        verdict="insufficient" if errors else assessment.verdict,
        citations=valid,
        explanation="The assessment failed evidence validation; no conclusion can be established." if errors else assessment.explanation,
        validation_failed=bool(errors), validation_errors=errors,
    )
