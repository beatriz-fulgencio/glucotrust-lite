"""Compare a user-supplied Kaggle CSV against the included original XML records."""
import argparse
import json
from pathlib import Path

import pandas as pd

from glucotrust.ingest import normalize, parse_xml


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv", type=Path)
    parser.add_argument("--question-column", default="question")
    parser.add_argument("--answer-column", default="answer")
    parser.add_argument("--raw", type=Path, default=Path("data/raw/MedQuAD-master"))
    args = parser.parse_args()
    copy = pd.read_csv(args.csv).fillna("")
    for column in (args.question_column, args.answer_column):
        if column not in copy.columns:
            parser.error(f"Missing column {column!r}; available: {list(copy.columns)}")
    index = {}
    for _, row in copy.iterrows():
        index.setdefault(normalize(str(row[args.question_column])).lower(), set()).add(normalize(str(row[args.answer_column])))
    log = pd.read_csv("data/curated/curation_log.csv")
    included = log[log.reason == "included"]
    rows = []
    for file, group in included.groupby("file"):
        records = {r["qid"]: r for r in parse_xml(args.raw / file)}
        for qid in group.qid:
            record = records[qid]
            answers = index.get(normalize(record["question"]).lower(), set())
            status = "exact_normalized_match" if normalize(record["answer"]) in answers else "answer_differs" if answers else "question_missing"
            rows.append(dict(qid=qid, status=status))
    output = dict(csv_name=args.csv.name, note="Text comparison only; Kaggle provenance is not inferred.",
                  counts=pd.Series([row["status"] for row in rows]).value_counts().to_dict(), records=rows)
    Path("eval/results/kaggle_comparison.json").write_text(json.dumps(output, indent=2) + "\n")
    print(json.dumps(output["counts"], indent=2))


if __name__ == "__main__":
    main()
