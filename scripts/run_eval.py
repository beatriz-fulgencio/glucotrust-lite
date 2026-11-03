"""Live inference is opt-in; replay never instantiates a client or embedding model."""
import argparse
import hashlib
import json
import os
import platform
import statistics
import time
from datetime import datetime, timezone
from importlib.metadata import version
from pathlib import Path

import httpx
from dotenv import load_dotenv

from glucotrust.assess import AssessmentUnavailable, create_assessor, PROMPT_VERSION, SYSTEM_PROMPT
from glucotrust.corpus import fingerprint, load_corpus
from glucotrust.metrics import classification_metrics, recall_at_k
from glucotrust.pipeline import assess_claim
from glucotrust.retrieve import DenseRetriever, EMBEDDING_MODEL, EMBEDDING_REVISION
from glucotrust.literature import EuropePMCLiterature


def read_jsonl(path):
    return [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]


def check_configuration(rows):
    """Reject pooled experiments, including legacy rows with assessor identities."""
    identities = set()
    for row in rows:
        identity = row.get("run", {}).get("identity", {})
        config = row.get("configuration")
        if config is None:
            config = {key: identity.get(key) for key in (
                "provider", "host", "model", "model_digest", "options", "prompt_version", "prompt", "schema")}
            config.update(model=row.get("model"), prompt_version=row.get("prompt_version"))
        identities.add(json.dumps(config, sort_keys=True))
    if len(identities) != 1:
        raise ValueError("Mixed experiment configurations; do not pool providers, models or settings")
    if rows and rows[0].get("configuration"):
        expected = rows[0]["configuration"]["model_identity"]
        for row in rows:
            observed = row.get("run", {}).get("identity", {})
            if observed and any(observed.get(k) != v for k, v in expected.items()):
                raise ValueError("Model identity changed during the experiment; preserve and rerun separately")
            config = row["configuration"]
            for recorded_key, config_key in (("model", "requested_model"), ("options", "generation_options"),
                                              ("prompt_version", "prompt_version")):
                if observed and config_key in config and observed.get(recorded_key) != config[config_key]:
                    raise ValueError("Recorded inference settings differ from the experiment configuration")
            if observed and "prompt_sha256" in config and hashlib.sha256(observed["prompt"].encode()).hexdigest() != config["prompt_sha256"]:
                raise ValueError("Recorded prompt differs from the experiment configuration")
        actual_models = {row["model"] for row in rows if row.get("status") == "assessed"}
        if len(actual_models) > 1:
            raise ValueError("Mixed response models within one experiment")


def summarize(claims, rows):
    claim_ids = [c["claim_id"] for c in claims]
    if len(claim_ids) != len(set(claim_ids)):
        raise ValueError("Duplicate claim IDs")
    if any(row["mode"] not in {"end_to_end", "oracle"} for row in rows):
        raise ValueError("Unexpected evaluation mode")
    oracle_all = bool(rows and rows[0].get("configuration", {}).get("oracle_scope") == "all_claims")
    summary = {}
    for mode in ("end_to_end", "oracle", "end_to_end_gold_subset"):
        subset = [c for c in claims if mode == "end_to_end" or (mode == "oracle" and oracle_all) or c["gold_passage_ids"]]
        source_mode = "end_to_end" if mode == "end_to_end_gold_subset" else mode
        mode_rows = [row for row in rows if row["mode"] == source_mode]
        indexed = {row["claim_id"]: row for row in mode_rows}
        expected = set(claim_ids) if source_mode == "end_to_end" or oracle_all else {c["claim_id"] for c in claims if c["gold_passage_ids"]}
        if len(indexed) != len(mode_rows) or set(indexed) != expected:
            raise ValueError(f"Incomplete, duplicate or unexpected outputs for {mode}")
        selected = [indexed[c["claim_id"]] for c in subset]
        predictions = [r.get("assessment", {}).get("verdict") for r in selected]
        if not subset:
            continue
        metrics = classification_metrics([c["label"] for c in subset], predictions)
        if mode.startswith("end_to_end"):
            metrics["recall_at_3"] = recall_at_k([c["gold_passage_ids"] for c in subset], [r["passage_ids"] for r in selected])
        metrics["validation_downgrades"] = sum(bool(r.get("assessment", {}).get("validation_failed")) for r in selected)
        metrics["model_abstentions_on_insufficient"] = sum(
            c["label"] == "insufficient" and r.get("assessment", {}).get("verdict") == "insufficient"
            and not r.get("assessment", {}).get("validation_failed") for c, r in zip(subset, selected))
        metrics["unavailable_count"] = sum(p is None for p in predictions)
        durations = [r.get("run", {}).get("response", {}).get("total_duration", 0) / 1e9
                     for r in selected if not r.get("run", {}).get("cache_hit")
                     and r.get("run", {}).get("response", {}).get("total_duration")]
        metrics["inference_latency_seconds"] = dict(
            n=len(durations), mean=statistics.mean(durations) if durations else None,
            median=statistics.median(durations) if durations else None,
            max=max(durations) if durations else None)
        summary[mode] = metrics
    return summary


def report(summary):
    lines = ["# Claim evaluation", "", "Exploratory label agreement. Unavailable outcomes count as incorrect and never as abstention.",
             "False support denominator: all gold non-supported cases, including unavailable outcomes.",
             "Abstention counts final insufficient verdicts; validation downgrades are also counted separately.", "",
             "| Mode | Metric | Result |", "|---|---|---|"]
    for mode, metrics in summary.items():
        for name, value in metrics.items():
            if isinstance(value, dict) and "rate" in value:
                percent = f"{value['rate']:.1%}" if value["rate"] is not None else "N/A"
                lines.append(f"| {mode} | {name} | {value['n']}/{value['total']} ({percent}) |")
        lines.append(f"| {mode} | macro-F1 | {metrics['macro_f1']:.3f} |")
        for key in ("validation_downgrades", "model_abstentions_on_insufficient", "unavailable_count"):
            lines.append(f"| {mode} | {key} | {metrics[key]} |")
    for mode, metrics in summary.items():
        lines += ["", f"## {mode}: confusion matrix", "", "Rows: gold; columns: prediction.", "",
                  "| Gold | supported | contradicted | insufficient | unavailable |", "|---|---|---|---|---|"]
        for label, values in zip(metrics["confusion_labels"][:3], metrics["confusion_matrix"][:3]):
            lines.append("| " + " | ".join([label] + list(map(str, values))) + " |")
    return "\n".join(lines) + "\n"


class PacedClient(httpx.Client):
    """Pace every hosted HTTP request, including citation repair. No automatic retries."""
    def __init__(self, interval):
        super().__init__()
        self.interval = interval
        self.last_request = None

    def post(self, *args, **kwargs):
        if self.last_request is not None:
            time.sleep(max(0, self.interval - (time.monotonic() - self.last_request)))
        self.last_request = time.monotonic()
        return super().post(*args, **kwargs)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--claims", type=Path, default=Path("eval/claims_test.jsonl"))
    parser.add_argument("--outputs", type=Path, default=Path("eval/results/assessments.jsonl"))
    parser.add_argument("--provider", choices=("ollama", "groq"), help="Defaults to GLUCOTRUST_PROVIDER, then ollama")
    parser.add_argument("--language", choices=("en", "pt"), default="en", help="Input language; Portuguese uses English search translation")
    parser.add_argument("--model", help="Explicit provider-specific model identifier")
    parser.add_argument("--request-interval", type=float, default=60, help="Groq minimum seconds between HTTP requests (default 60)")
    parser.add_argument("--report-dir", type=Path, help="New directory for replay reports; replay otherwise only prints")
    parser.add_argument("--live", action="store_true", help="Run model inference; use a new output filename")
    parser.add_argument("--literature", action="store_true", help="Enable Europe PMC only in live end-to-end mode")
    args = parser.parse_args()
    if args.report_dir and args.report_dir.exists():
        parser.error("Report directory already exists; choose a new path")
    if args.literature and not args.live:
        parser.error("--literature requires --live")
    if not args.live and (args.provider or args.model):
        parser.error("Replay uses recorded identities; --provider/--model require --live")
    if not 0 <= args.request_interval < float("inf"):
        parser.error("--request-interval must be finite and nonnegative")
    claims = read_jsonl(args.claims)
    if not claims or len({c["claim_id"] for c in claims}) != len(claims):
        parser.error("Claims must be nonempty with unique IDs")
    passages = load_corpus("data/curated/passages.jsonl")
    lookup = {p.passage_id: p for p in passages}
    unknown = {pid for c in claims for pid in c["gold_passage_ids"] if pid not in lookup}
    if unknown:
        raise ValueError(f"Unknown gold passage IDs: {unknown}")
    labels_hash = hashlib.sha256(args.claims.read_bytes()).hexdigest()
    corpus_hash = fingerprint(passages)
    if args.live:
        if any(p.exists() for p in (args.outputs, args.outputs.with_suffix(".summary.json"), args.outputs.with_suffix(".md"))):
            parser.error("Output already exists; use a new --outputs path to preserve previous runs")
        load_dotenv()
        provider = args.provider or os.getenv("GLUCOTRUST_PROVIDER", "ollama").strip().lower()
        paced = PacedClient(args.request_interval) if provider == "groq" else None
        assessor = create_assessor(provider=provider, **({"model": args.model} if args.model else {}),
                                   **({"client": paced} if paced else {}))
        # Fail before creating an experiment if credentials/model/server are missing.
        try:
            model_identity = assessor._model_identity()
        except AssessmentUnavailable as exc:
            if paced:
                paced.close()
            parser.exit(2, f"Evaluation pending: {exc}\nNo inference outputs or metrics were created.\n")
        configuration = dict(provider=provider, requested_model=assessor.model, model_identity=model_identity,
                             generation_options=assessor.generation_options, prompt_version=PROMPT_VERSION,
                             prompt_sha256=hashlib.sha256(SYSTEM_PROMPT.encode()).hexdigest(),
                             embedding_model=EMBEDDING_MODEL, embedding_revision=EMBEDDING_REVISION, k=3,
                             language=args.language, literature=args.literature, oracle_scope="all_claims", corpus_hash=corpus_hash,
                             labels_hash=labels_hash, request_interval=args.request_interval if paced else 0,
                             python=platform.python_version(), packages={p: version(p) for p in (
                                 "sentence-transformers", "numpy", "torch", "ollama", "httpx", "scikit-learn")})
        retriever = DenseRetriever(passages)
        rows = []
        args.outputs.parent.mkdir(parents=True, exist_ok=True)
        try:
            with args.outputs.open("x") as handle:
                for mode in ("end_to_end", "oracle"):
                    for claim in claims:
                        # An empty gold set is deliberate empty evidence, not a skipped case.
                        gold = [lookup[pid] for pid in claim["gold_passage_ids"]] if mode == "oracle" else None
                        result = assess_claim(claim["claim"], retriever, assessor, passages=gold,
                            literature=EuropePMCLiterature() if args.literature and mode == "end_to_end" else None, language=args.language)
                        row = dict(claim_id=claim["claim_id"], mode=mode, status=result.status,
                                   assessment=result.assessment.model_dump() if result.assessment else {},
                                   passage_ids=[h.passage.passage_id for h in result.hits], model=result.model,
                                   prompt_version=PROMPT_VERSION, labels_hash=labels_hash, corpus_hash=corpus_hash,
                                   message=result.message, run=result.run, literature=result.literature,
                                   configuration=configuration, created_at=datetime.now(timezone.utc).isoformat())
                        handle.write(json.dumps(row) + "\n")
                        handle.flush()
                        rows.append(row)
                        print(f"{mode} {claim['claim_id']}: {result.status} {row['assessment'].get('verdict', '')}", flush=True)
                        if provider == "groq" and result.status == "unavailable" and "usage limit" in result.message:
                            parser.exit(2, "Groq quota reached. Partial results retained; no aggregate reported. Retry later with a new path.\n")
        finally:
            if paced:
                paced.close()
    else:
        rows = read_jsonl(args.outputs)
    if any(row.get("labels_hash") != labels_hash or row.get("corpus_hash") != corpus_hash for row in rows):
        raise ValueError("Recorded outputs do not match these labels/corpus; preserve the original run inputs")
    check_configuration(rows)
    summary = summarize(claims, rows)
    markdown = report(summary)
    if args.report_dir:
        args.report_dir.mkdir(parents=True, exist_ok=False)
        prefix = args.report_dir / args.outputs.stem
    else:
        prefix = args.outputs if args.live else None
    if prefix:
        with prefix.with_suffix(".summary.json").open("x") as handle:
            handle.write(json.dumps(summary, indent=2) + "\n")
        with prefix.with_suffix(".md").open("x") as handle:
            handle.write(markdown)
    print(markdown)


if __name__ == "__main__":
    main()
