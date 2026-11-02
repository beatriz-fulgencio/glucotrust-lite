"""Bounded Europe PMC search; model knowledge never becomes evidence."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date
from html.parser import HTMLParser
import xml.etree.ElementTree as ET

import httpx

from glucotrust.corpus import Passage
from glucotrust.retrieve import BM25Retriever, SearchHit

API = "https://www.ebi.ac.uk/europepmc/webservices/rest"
STOP = set("a an the is are was were be been being of for to in on at by with and or not no never every all can cannot could may might must should does do did means proves safe unsafe safety claim prediction predictions zone zode".split())


class LiteratureUnavailable(RuntimeError):
    pass


class _Text(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []

    def handle_data(self, data):
        self.parts.append(data)


def plain_text(html: str) -> str:
    parser = _Text()
    parser.feed(html)
    return " ".join(" ".join(parser.parts).split())


def search_terms(claim: str) -> list[str]:
    # Strip conclusions/negation: search for the topic, not a desired verdict.
    words = re.findall(r"[a-zA-Z][a-zA-Z0-9-]*", claim.lower())
    return list(dict.fromkeys(w for w in words if w not in STOP and len(w) > 1))[:8]


@dataclass
class LiteratureResult:
    hits: list[SearchHit] = field(default_factory=list)
    queries: list[str] = field(default_factory=list)
    note: str = ""


class EuropePMCLiterature:
    def __init__(self, client=None):
        self.client = client

    def search(self, claim: str, k: int = 3) -> LiteratureResult:
        if self.client is not None:
            return self._search(self.client, claim, k)
        with httpx.Client(timeout=10, follow_redirects=False,
                          headers={"User-Agent": "GlucoTrust-Lite/0.1 (research prototype)"}) as client:
            return self._search(client, claim, k)

    @staticmethod
    def _get(client, path, **kwargs):
        # Never follow model-provided URLs or provider redirects.
        with client.stream("GET", API + path, **kwargs) as response:
            response.raise_for_status()
            data = bytearray()
            for chunk in response.iter_bytes():
                data.extend(chunk)
                if len(data) > 2_000_000:
                    raise LiteratureUnavailable("Literature response exceeded the size limit.")
            return bytes(data)

    def _search(self, client, claim, k):
        words = search_terms(claim)
        if not words:
            return LiteratureResult(note="No searchable literature terms in the claim.")
        queries = []
        try:
            import json
            records = []
            for joiner in (" AND ", " OR "):
                query = "TITLE_ABS:(" + joiner.join(f'"{w}"' for w in words) + ") AND (SRC:MED OR SRC:PMC)"
                queries.append(query)
                payload = json.loads(self._get(client, "/search", params={
                    "query": query, "format": "json", "resultType": "core", "pageSize": 5}))
                records = payload["resultList"]["result"]
                if not isinstance(records, list) or any(not isinstance(r, dict) for r in records):
                    raise ValueError("Invalid search records")
                if records:
                    break
            passages, seen, unavailable_fulltext = [], set(), 0
            for record in records:
                source, identifier = record.get("source", ""), str(record.get("id", ""))
                if source not in {"MED", "PMC"} or not re.fullmatch(r"(?:PMC)?\d+", identifier):
                    continue
                doc_id = f"europepmc:{source}:{identifier}"
                if doc_id in seen:
                    continue
                seen.add(doc_id)
                blocks = [("abstract", plain_text(record.get("abstractText") or ""))]
                pmcid = record.get("pmcid", "")
                if record.get("isOpenAccess") == "Y" and re.fullmatch(r"PMC\d+", pmcid):
                    try:
                        raw = self._get(client, f"/{pmcid}/fullTextXML")
                        if b"<!ENTITY" in raw.upper():
                            raise ValueError("XML entity declaration")
                        root = ET.fromstring(raw)
                        blocks += [("full_text", " ".join("".join(node.itertext()).split()))
                                   for node in root.findall(".//body//p") + root.findall(".//body//tr")]
                    except (httpx.HTTPError, ET.ParseError, ValueError, LiteratureUnavailable):
                        unavailable_fulltext += 1  # Abstract remains usable and visibly labeled.
                title = plain_text(record.get("title", "Untitled publication"))
                year = record.get("pubYear", "year unavailable")
                for block_index, (kind, text) in enumerate(blocks):
                    tokens = text.split()
                    if len(tokens) < 8:
                        continue
                    for offset in range(0, len(tokens), 180):
                        passages.append(Passage(
                            passage_id=f"{doc_id}#{kind}-{block_index}-{offset}", doc_id=doc_id, qid=identifier,
                            source=f"Europe PMC · {source}:{identifier} · {year} · {kind.replace('_', ' ')}",
                            source_type="research", url=f"https://europepmc.org/article/{source}/{identifier}",
                            focus=title, qtype=kind, question=title, text=" ".join(tokens[offset:offset+180]),
                            provenance_status="retrieved", checked_on=date.today()))
            hits = BM25Retriever(passages).search(claim, k=k) if passages else []
            note = "Literature search completed." if hits else "No usable literature passages found."
            if unavailable_fulltext:
                note += " Some full texts were unavailable; abstracts were used where available."
            return LiteratureResult(hits, queries, note)
        except (httpx.HTTPError, ValueError, KeyError, TypeError, LiteratureUnavailable) as exc:
            raise LiteratureUnavailable(f"Literature search unavailable ({type(exc).__name__}); local assessment retained.") from exc
