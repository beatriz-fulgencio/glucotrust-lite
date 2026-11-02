"""Reachability is recorded separately from a human content-match attestation."""
import argparse
import csv
import json
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import requests

from glucotrust.corpus import load_corpus, save_corpus


def inspect_url(url):
    try:
        response = requests.get(url, timeout=15, headers={"User-Agent": "GlucoTrust-research-provenance/0.1"})
        return dict(url=url, reachable=response.ok, status=response.status_code, final_url=response.url, error="")
    except requests.RequestException as exc:
        return dict(url=url, reachable=False, status=None, final_url="", error=type(exc).__name__)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", type=Path, default=Path("data/curated/passages.jsonl"))
    parser.add_argument("--verified", type=Path, help="CSV: passage_id,url,content_matches (true only after manual review)")
    args = parser.parse_args()
    passages = load_corpus(args.corpus)
    attestations = {}
    if args.verified:
        with args.verified.open() as handle:
            attestations = {row["passage_id"]: row for row in csv.DictReader(handle)}
    with ThreadPoolExecutor(max_workers=4) as pool:
        checks = {item["url"]: item for item in pool.map(inspect_url, sorted({p.url for p in passages}))}
    today = datetime.now(ZoneInfo("America/Sao_Paulo")).date()
    updated = []
    for passage in passages:
        attestation = attestations.get(passage.passage_id, {})
        verified = (checks[passage.url]["reachable"] and attestation.get("url") == passage.url
                    and attestation.get("content_matches", "").lower() == "true")
        updated.append(passage.model_copy(update={"provenance_status": "url_verified" if verified else "archived_record", "checked_on": today}))
    save_corpus(updated, args.corpus)
    (args.corpus.parent / "provenance_checks.json").write_text(json.dumps({"checked_on": str(today), "checks": list(checks.values())}, indent=2) + "\n")
    print(f"Checked {len(checks)} URLs. Verified {sum(p.provenance_status == 'url_verified' for p in updated)} passages; others remain archived.")


if __name__ == "__main__":
    main()
