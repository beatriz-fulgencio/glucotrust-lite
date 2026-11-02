from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from rank_bm25 import BM25Okapi

from glucotrust.corpus import Passage, fingerprint

EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_REVISION = "1110a243fdf4706b3f48f1d95db1a4f5529b4d41"


@dataclass(frozen=True)
class SearchHit:
    passage: Passage
    score: float


def tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


def ranked(passages: list[Passage], scores, k: int) -> list[SearchHit]:
    if k < 1:
        raise ValueError("k must be positive")
    order = np.argsort(-np.asarray(scores), kind="stable")[:k]
    return [SearchHit(passages[i], float(scores[i])) for i in order]


class BM25Retriever:
    def __init__(self, passages: list[Passage]):
        if not passages:
            raise ValueError("Empty corpus")
        self.passages = passages
        self.index = BM25Okapi([tokenize(p.question + " " + p.text) for p in passages])

    def search(self, query: str, k: int = 3) -> list[SearchHit]:
        return ranked(self.passages, self.index.get_scores(tokenize(query)), k)


class DenseRetriever:
    def __init__(self, passages: list[Passage], cache_dir: str | Path = "data/curated", encoder=None, model_name: str = EMBEDDING_MODEL):
        if not passages:
            raise ValueError("Empty corpus")
        self.passages = passages
        if encoder is None:
            from sentence_transformers import SentenceTransformer
            local = Path(cache_dir).parent / "cache/all-MiniLM-L6-v2"
            location = str(local) if model_name == EMBEDDING_MODEL and (local / "modules.json").exists() else model_name
            encoder = SentenceTransformer(location, device="cpu", cache_folder=str(Path(cache_dir).parent / "cache/models"),
                                          revision=EMBEDDING_REVISION if location == EMBEDDING_MODEL else None)
        self.encoder = encoder
        import hashlib
        key = hashlib.sha256((model_name + EMBEDDING_REVISION + fingerprint(passages)).encode()).hexdigest()
        cache = Path(cache_dir) / f"embeddings-{key}.npz"
        if cache.exists():
            with np.load(cache, allow_pickle=False) as data:
                self.embeddings = data["embeddings"]
        else:
            self.embeddings = np.asarray(encoder.encode([p.question + "\n" + p.text for p in passages], normalize_embeddings=True), dtype=np.float32)
            cache.parent.mkdir(parents=True, exist_ok=True)
            np.savez_compressed(cache, embeddings=self.embeddings)
        norms = np.linalg.norm(self.embeddings, axis=1, keepdims=True)
        self.embeddings = self.embeddings / np.maximum(norms, 1e-12)

    def search(self, query: str, k: int = 3) -> list[SearchHit]:
        vector = np.asarray(self.encoder.encode([query], normalize_embeddings=True), dtype=np.float32)[0]
        vector /= max(float(np.linalg.norm(vector)), 1e-12)
        return ranked(self.passages, self.embeddings @ vector, k)
