from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

from glucotrust.pipeline import ClaimResult


def save_feedback(result: ClaimResult, correct: bool, note: str = "", path: str | Path = "feedback.jsonl") -> None:
    if result.assessment is None:
        raise ValueError("Only completed assessments accept correctness feedback")
    record = dict(claim=result.claim, verdict=result.assessment.verdict,
                  passage_ids=[h.passage.passage_id for h in result.hits],
                  model=result.model, prompt_version=result.prompt_version,
                  validation_failed=result.assessment.validation_failed,
                  correct=correct, note=note[:4000], literature=result.literature, timestamp=datetime.now(timezone.utc).isoformat())
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(target, os.O_APPEND | os.O_CREAT | os.O_WRONLY, 0o600)
    try:
        os.write(descriptor, (json.dumps(record, ensure_ascii=False) + "\n").encode())
    finally:
        os.close(descriptor)
