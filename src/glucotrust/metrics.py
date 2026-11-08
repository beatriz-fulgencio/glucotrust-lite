"""Compute retrieval and evidence-classification evaluation metrics."""
from __future__ import annotations

from sklearn.metrics import accuracy_score, confusion_matrix, f1_score

LABELS = ["supported", "contradicted", "insufficient"]


def rate(n: int, total: int) -> dict:
    return {"n": n, "total": total, "rate": n / total if total else None}


def recall_at_k(gold: list[list[str]], predictions: list[list[str]], k: int = 3) -> dict:
    if len(gold) != len(predictions):
        raise ValueError("Gold and prediction lengths differ")
    pairs = [(g, p) for g, p in zip(gold, predictions) if g]
    return rate(sum(bool(set(g) & set(p[:k])) for g, p in pairs), len(pairs))


def classification_metrics(labels: list[str], predictions: list[str | None]) -> dict:
    if len(labels) != len(predictions) or not labels:
        raise ValueError("Provide equally sized, nonempty labels and predictions")
    if any(label not in LABELS for label in labels) or any(p not in LABELS + [None] for p in predictions):
        raise ValueError("Unknown classification label")
    predicted = [p if p is not None else "unavailable" for p in predictions]
    available = [(g, p) for g, p in zip(labels, predictions) if p is not None]
    non_support = [(g, p) for g, p in zip(labels, predictions) if g != "supported"]
    insufficient = [(g, p) for g, p in zip(labels, predictions) if g == "insufficient"]
    non_insufficient = [(g, p) for g, p in zip(labels, predictions) if g != "insufficient"]
    return dict(
        accuracy=rate(sum(g == p for g, p in zip(labels, predictions)), len(labels)),
        macro_f1=float(f1_score(labels, predicted, labels=LABELS, average="macro", zero_division=0)),
        confusion_matrix=confusion_matrix(labels, predicted, labels=LABELS + ["unavailable"]).tolist(),
        confusion_labels=LABELS + ["unavailable"],
        false_support=rate(sum(p == "supported" for _, p in non_support), len(non_support)),
        abstention=rate(sum(p == "insufficient" for _, p in insufficient), len(insufficient)),
        over_abstention=rate(sum(p == "insufficient" for _, p in non_insufficient), len(non_insufficient)),
        availability=rate(len(available), len(labels)),
        available_accuracy=float(accuracy_score(*zip(*available))) if available else None,
    )
