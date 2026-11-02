from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from pathlib import Path

from glucotrust.corpus import Passage

COLLECTIONS = ("5_NIDDK_QA", "4_MPlus_Health_Topics_QA", "7_SeniorHealth_QA", "9_CDC_QA")
DIABETES = re.compile(r"\b(diabet(?:es|ic)|hypoglyc(?:emia|aemia)|hyperglyc(?:emia|aemia))\b", re.I)


def normalize(text: str) -> str:
    return " ".join(text.split())


def relevant(focus: str, question: str) -> bool:
    return bool(DIABETES.search(focus + " " + question))


def parse_xml(path: Path) -> list[dict]:
    root = ET.parse(path).getroot()
    def content(node):
        return "" if node is None else "".join(node.itertext()).strip()
    return [dict(
        doc_id=f"{path.parent.name}:{root.get('id', path.stem)}",
        qid=f"{path.parent.name}:{pair.find('Question').get('qid')}",
        source=root.get("source", path.parent.name), url=root.get("url", ""),
        focus=content(root.find("Focus")), qtype=pair.find("Question").get("qtype", ""),
        question=content(pair.find("Question")), answer=content(pair.find("Answer")),
    ) for pair in root.findall(".//QAPair") if pair.find("Question") is not None]


def chunk_answer(answer: str, words: int = 150) -> list[str]:
    """Preserve paragraph boundaries where possible; split oversized paragraphs."""
    chunks, current = [], ""
    for paragraph in re.split(r"\n\s*\n", answer.strip()):
        tokens = paragraph.split()
        for start in range(0, len(tokens), words):
            part = " ".join(tokens[start:start + words])
            if current and len((current + " " + part).split()) > words:
                chunks.append(current)
                current = ""
            current = (current + "\n\n" + part).strip()
    if current:
        chunks.append(current)
    return chunks


def build_corpus(root: Path, limit: int = 60) -> tuple[list[Passage], list[dict]]:
    if not 40 <= limit <= 80:
        raise ValueError("Select 40–80 Q&A records")
    passages, log, selected = [], [], []
    for collection in COLLECTIONS:
        for path in sorted((root / collection).glob("*.xml")):
            for record in parse_xml(path):
                answer = normalize(record["answer"])
                if not relevant(record["focus"], record["question"]):
                    reason = "focus_and_question_not_diabetes"
                elif not answer:
                    reason = "empty_answer"
                elif any(len(set(answer.lower().split()) & old) / max(1, len(set(answer.lower().split()) | old)) >= .92 for old in selected):
                    reason = "near_duplicate_answer"
                elif len(selected) >= limit:
                    reason = "record_limit"
                else:
                    reason = "included"
                    selected.append(set(answer.lower().split()))
                    metadata = {k: v for k, v in record.items() if k != "answer"}
                    for index, text in enumerate(chunk_answer(record["answer"]), 1):
                        passages.append(Passage(**metadata, passage_id=f"{record['qid']}#p{index}", text=text))
                log.append({"qid": record["qid"], "file": str(path.relative_to(root)), "question": record["question"], "reason": reason})
    if len(selected) < 40:
        raise ValueError(f"Only {len(selected)} relevant records; supply the original MedQuAD collections")
    return passages, log
