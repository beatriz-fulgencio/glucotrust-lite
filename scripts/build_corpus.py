import argparse
import hashlib
import json
from pathlib import Path

import pandas as pd

from glucotrust.corpus import save_corpus
from glucotrust.ingest import build_corpus


def main():
    parser = argparse.ArgumentParser(description="Curate original MedQuAD XML (40–80 Q&A records)")
    parser.add_argument("--raw", type=Path, default=Path("data/raw/MedQuAD-master"))
    parser.add_argument("--limit", type=int, default=60)
    parser.add_argument("--output", type=Path, default=Path("data/curated/passages.jsonl"))
    args = parser.parse_args()
    passages, log = build_corpus(args.raw, args.limit)
    save_corpus(passages, args.output)
    pd.DataFrame(log).to_csv(args.output.parent / "curation_log.csv", index=False)
    files = sorted({row["file"] for row in log})
    manifest = {name: hashlib.sha256((args.raw / name).read_bytes()).hexdigest() for name in files}
    (args.output.parent / "input_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"Saved {len(passages)} passages from {len({p.qid for p in passages})} records. All initially archived; run provenance checks separately.")


if __name__ == "__main__":
    main()
