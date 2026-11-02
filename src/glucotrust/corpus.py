from __future__ import annotations

import hashlib
import json
from datetime import date
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class Passage(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    passage_id: str = Field(min_length=1)
    doc_id: str
    qid: str
    source: str
    source_type: Literal["dataset", "research"] = "dataset"
    url: str
    focus: str
    qtype: str
    question: str
    text: str = Field(min_length=1)
    provenance_status: Literal["url_verified", "archived_record", "retrieved"] = "archived_record"
    checked_on: date | None = None

    @field_validator("url")
    @classmethod
    def safe_url(cls, value: str) -> str:
        if value and not value.startswith(("https://", "http://")):
            raise ValueError("Source URL must use HTTP(S)")
        return value


def load_corpus(path: str | Path) -> list[Passage]:
    passages = [Passage.model_validate_json(line) for line in Path(path).read_text().splitlines() if line.strip()]
    ids = [p.passage_id for p in passages]
    if not passages or len(ids) != len(set(ids)):
        raise ValueError("Corpus must be nonempty with unique passage IDs")
    return passages


def save_corpus(passages: list[Passage], path: str | Path) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("".join(p.model_dump_json() + "\n" for p in passages))


def fingerprint(passages: list[Passage]) -> str:
    payload = [p.model_dump(mode="json") for p in passages]
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
