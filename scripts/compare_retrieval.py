import argparse
import json
import hashlib
from pathlib import Path

from glucotrust.corpus import fingerprint, load_corpus
from glucotrust.metrics import recall_at_k
from glucotrust.retrieve import BM25Retriever, DenseRetriever, EMBEDDING_MODEL, EMBEDDING_REVISION


def main():
    parser = argparse.ArgumentParser(description="Compare BM25 and dense Recall@3")
    parser.add_argument("--queries", type=Path, default=Path("eval/retrieval_queries.jsonl"))
    parser.add_argument("--bm25-only", action="store_true")
    args = parser.parse_args()
    passages = [p for p in load_corpus("data/curated/passages.jsonl") if p.source_type == "dataset"]
    queries = [json.loads(line) for line in args.queries.read_text().splitlines() if line.strip()]
    retrievers = {"bm25": BM25Retriever(passages)}
    if not args.bm25_only:
        retrievers["dense"] = DenseRetriever(passages)
    rows = []
    for query in queries:
        row = dict(query)
        for name, retriever in retrievers.items():
            row[name] = [hit.passage.passage_id for hit in retriever.search(query["query"])]
        rows.append(row)
    summary = {name: {subset: recall_at_k([row["gold_passage_ids"] for row in rows if subset == "overall" or row.get("paraphrased")],
                                        [row[name] for row in rows if subset == "overall" or row.get("paraphrased")])
                      for subset in ("overall", "paraphrased")} for name in retrievers}
    output = dict(corpus_hash=fingerprint(passages), queries_hash=hashlib.sha256(args.queries.read_bytes()).hexdigest(),
                  embedding_model=EMBEDDING_MODEL, embedding_revision=EMBEDDING_REVISION, summary=summary, queries=rows)
    Path("eval/results").mkdir(parents=True, exist_ok=True)
    suffix = "_bm25" if args.bm25_only else ""
    Path(f"eval/results/retrieval{suffix}.json").write_text(json.dumps(output, indent=2) + "\n")
    lines = ["# Retrieval comparison", "", "| Method | Subset | Recall@3 |", "|---|---|---|"]
    for name, subsets in summary.items():
        for subset, value in subsets.items():
            lines.append(f"| {name} | {subset} | {value['n']}/{value['total']} ({value['rate']:.1%}) |")
    lines.extend(["", "## Disagreements", ""])
    disagreements = [row for row in rows if "dense" in row and row["bm25"] != row["dense"]]
    for row in disagreements:
        b = bool(set(row["gold_passage_ids"]) & set(row["bm25"]))
        d = bool(set(row["gold_passage_ids"]) & set(row["dense"]))
        lines.append(f"- {row['query_id']}: {row['query']} BM25 hit: {b}; dense hit: {d}. Different rankings are not necessarily errors; review raw passage IDs in retrieval.json.")
    Path(f"eval/results/retrieval{suffix}.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
