"""Live runs are opt-in. Default replay never instantiates a client or embedding model."""
import argparse
import hashlib
import json
import statistics
from pathlib import Path

from dotenv import load_dotenv

from glucotrust.assess import OllamaAssessor, PROMPT_VERSION
from glucotrust.corpus import fingerprint, load_corpus
from glucotrust.metrics import classification_metrics, recall_at_k
from glucotrust.pipeline import assess_claim
from glucotrust.retrieve import DenseRetriever
from glucotrust.literature import EuropePMCLiterature


def read_jsonl(path):
    return [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]


def summarize(claims, rows):
    claim_ids = [c["claim_id"] for c in claims]
    if len(claim_ids) != len(set(claim_ids)):
        raise ValueError("Duplicate claim IDs")
    summary = {}
    for mode in ("end_to_end", "oracle"):
        subset = [c for c in claims if mode != "oracle" or c["gold_passage_ids"]]
        mode_rows = [row for row in rows if row["mode"] == mode]
        indexed = {row["claim_id"]: row for row in mode_rows}
        if len(indexed) != len(mode_rows) or set(indexed) != {c["claim_id"] for c in subset}:
            raise ValueError(f"Incomplete, duplicate or unexpected outputs for {mode}")
        predictions = [indexed[c["claim_id"]].get("assessment", {}).get("verdict") for c in subset]
        summary[mode] = classification_metrics([c["label"] for c in subset], predictions)
        if mode == "end_to_end":
            summary[mode]["recall_at_3"] = recall_at_k([c["gold_passage_ids"] for c in subset], [indexed[c["claim_id"]]["passage_ids"] for c in subset])
        durations = [r.get("run", {}).get("response", {}).get("total_duration", 0) / 1e9
                     for r in mode_rows if not r.get("run", {}).get("cache_hit")
                     and r.get("run", {}).get("response", {}).get("total_duration")]
        summary[mode]["inference_latency_seconds"] = dict(
            n=len(durations), mean=statistics.mean(durations) if durations else None,
            median=statistics.median(durations) if durations else None,
            max=max(durations) if durations else None)
    return summary


def report(summary):
    lines = ["# Claim evaluation", "", "Exploratory only. Unavailable outcomes count as incorrect for all-claim accuracy and never count as abstention.", "", "| Mode | Metric | Result |", "|---|---|---|"]
    for mode, metrics in summary.items():
        for name, value in metrics.items():
            if isinstance(value, dict) and "rate" in value:
                percent = f"{value['rate']:.1%}" if value["rate"] is not None else "N/A"
                lines.append(f"| {mode} | {name} | {value['n']}/{value['total']} ({percent}) |")
        lines.append(f"| {mode} | macro-F1 | {metrics['macro_f1']:.3f} |")
        latency = metrics.get("inference_latency_seconds", {})
        if latency.get("n"):
            lines.append(f"| {mode} | mean inference latency (seconds) | {latency['mean']:.2f} |")
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--claims", type=Path, default=Path("eval/claims_test.jsonl"))
    parser.add_argument("--outputs", type=Path, default=Path("eval/results/assessments.jsonl"))
    parser.add_argument("--live", action="store_true", help="Run model inference; labels must already exist")
    parser.add_argument("--literature", action="store_true", help="Allow Europe PMC fallback in live end-to-end mode; oracle stays local")
    args = parser.parse_args()
    if args.literature and not args.live:
        parser.error("--literature requires --live")
    claims = read_jsonl(args.claims)
    passages = load_corpus("data/curated/passages.jsonl")
    lookup = {p.passage_id: p for p in passages}
    unknown = {pid for c in claims for pid in c["gold_passage_ids"] if pid not in lookup}
    if unknown:
        raise ValueError(f"Unknown gold passage IDs: {unknown}")
    labels_hash = hashlib.sha256(args.claims.read_bytes()).hexdigest()
    corpus_hash = fingerprint(passages)
    if args.live:
        if args.outputs.exists():
            parser.error("Output already exists; use a new --outputs path to preserve previous runs")
        load_dotenv()
        assessor = OllamaAssessor()
        retriever = DenseRetriever(passages)
        rows = []
        args.outputs.parent.mkdir(parents=True, exist_ok=True)
        with args.outputs.open("x") as handle:
            for mode in ("end_to_end", "oracle"):
                for claim in claims:
                    if mode == "oracle" and not claim["gold_passage_ids"]:
                        continue
                    gold = [lookup[pid] for pid in claim["gold_passage_ids"]] if mode == "oracle" else None
                    result = assess_claim(claim["claim"], retriever, assessor, passages=gold,
                                          literature=EuropePMCLiterature() if args.literature and mode == "end_to_end" else None)
                    row = dict(claim_id=claim["claim_id"], mode=mode, status=result.status,
                               assessment=result.assessment.model_dump() if result.assessment else {},
                               passage_ids=[h.passage.passage_id for h in result.hits], model=result.model,
                               prompt_version=PROMPT_VERSION, labels_hash=labels_hash, corpus_hash=corpus_hash,
                               message=result.message, run=result.run, literature=result.literature)
                    handle.write(json.dumps(row) + "\n")
                    handle.flush()
                    rows.append(row)
    else:
        if not args.outputs.exists():
            retrieval_path = Path("eval/results/retrieval.json")
            if not retrieval_path.exists():
                parser.exit(2, "No recorded results. Run scripts.compare_retrieval first.\n")
            recorded = json.loads(retrieval_path.read_text())
            dataset_hash = fingerprint([p for p in passages if p.source_type == "dataset"])
            if recorded["corpus_hash"] != dataset_hash:
                raise ValueError("Retrieval outputs do not match the corpus")
            query_path = Path("eval/retrieval_queries.jsonl")
            if recorded.get("queries_hash") != hashlib.sha256(query_path.read_bytes()).hexdigest():
                raise ValueError("Recorded retrieval outputs do not match these query annotations")
            lines = ["# Recorded evaluation status", "", "| Method | Subset | Recall@3 |", "|---|---|---|"]
            for name in recorded["summary"]:
                for subset in ("overall", "paraphrased"):
                    selected = [r for r in recorded["queries"] if subset == "overall" or r["paraphrased"]]
                    value = recall_at_k([r["gold_passage_ids"] for r in selected], [r[name] for r in selected])
                    lines.append(f"| {name} | {subset} | {value['n']}/{value['total']} ({value['rate']:.1%}) |")
            lines.extend(["", "Claim classification, oracle comparison, and the case-study verdict: **pending local inference run**.",
                          "Start Ollama, pull the configured model, review the provisional labels, then run with --live.",
                          "No classification accuracy, false-support, or abstention scores are fabricated."])
            markdown = "\n".join(lines) + "\n"
            Path("eval/results/status.md").write_text(markdown)
            print(markdown)
            return
        rows = read_jsonl(args.outputs)
    if any(row.get("labels_hash") != labels_hash or row.get("corpus_hash") != corpus_hash for row in rows):
        raise ValueError("Recorded outputs do not match these labels/corpus; preserve the original run inputs")
    summary = summarize(claims, rows)
    args.outputs.with_suffix(".summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    markdown = report(summary)
    args.outputs.with_suffix(".md").write_text(markdown)
    print(markdown)


if __name__ == "__main__":
    main()
