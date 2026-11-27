"""Three retrievers behind one interface: BM25 (lexical), Dense (embeddings), Hybrid (RRF)."""
from __future__ import annotations

import hashlib
import math
import re
import unicodedata
from collections import Counter
from pathlib import Path

import numpy as np

from .ingest import Chunk


def normalize(text: str) -> str:
    """Lowercase + strip accents and Arabic diacritics (é->e, تَقْدِيم->تقديم)."""
    text = unicodedata.normalize("NFKD", text.lower())
    return "".join(c for c in text if not unicodedata.combining(c))


def tokenize(text: str) -> list[str]:
    return [t for t in re.findall(r"\w+", normalize(text)) if len(t) > 1]


class BM25:
    """Okapi BM25 with the usual defaults (k1=1.5, b=0.75) and a non-negative IDF."""
    name = "bm25"

    def __init__(self, chunks: list[Chunk], k1: float = 1.5, b: float = 0.75):
        self.chunks, self.k1, self.b = chunks, k1, b
        self.docs = [Counter(tokenize(c.text)) for c in chunks]
        self.lens = [sum(d.values()) for d in self.docs]
        self.avg = sum(self.lens) / max(len(self.lens), 1)
        df = Counter(t for d in self.docs for t in d)
        n = len(self.docs)
        self.idf = {t: math.log(1 + (n - f + 0.5) / (f + 0.5)) for t, f in df.items()}

    def scores(self, query: str) -> np.ndarray:
        q = tokenize(query)
        out = np.zeros(len(self.docs))
        for i, (d, L) in enumerate(zip(self.docs, self.lens)):
            for t in q:
                if t in d:
                    tf = d[t]
                    out[i] += self.idf[t] * tf * (self.k1 + 1) / (tf + self.k1 * (1 - self.b + self.b * L / self.avg))
        return out


class Dense:
    """Multilingual sentence embeddings. Vectors are L2-normalised, so cosine = dot product."""
    name = "dense"
    DEFAULT_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

    def __init__(self, chunks: list[Chunk], model_name: str = DEFAULT_MODEL, cache_dir: str = ".sanad_cache"):
        from sentence_transformers import SentenceTransformer
        self.chunks = chunks
        self.model = SentenceTransformer(model_name)
        texts = [c.text for c in chunks]
        key = hashlib.sha1((model_name + "\x00".join(texts)).encode()).hexdigest()[:16]
        cache = Path(cache_dir) / f"{key}.npy"
        if cache.exists():                      # don't re-embed an unchanged collection
            self.V = np.load(cache)
        else:
            self.V = self.model.encode(texts, normalize_embeddings=True, batch_size=32)
            cache.parent.mkdir(exist_ok=True)
            np.save(cache, self.V)

    def scores(self, query: str) -> np.ndarray:
        return self.V @ self.model.encode([query], normalize_embeddings=True)[0]


class Hybrid:
    """Weighted score fusion: cosine + alpha * (BM25 / max BM25).

    Reciprocal Rank Fusion was tried first and dropped Recall@1 from 0.89 (dense alone) to 0.61 on the
    benchmark: on cross-language queries BM25 only matches incidental tokens (numbers, short words), and
    under RRF a single lexical rank is enough to reorder the top results. A small alpha keeps BM25 as a
    tie-breaker for exact terms and identifiers. alpha=0.1 is the largest value in the sweep that did not
    lower recall for any question type.
    """
    name = "hybrid"

    def __init__(self, bm25: BM25, dense: Dense, alpha: float = 0.1):
        self.bm25, self.dense, self.alpha, self.chunks = bm25, dense, alpha, bm25.chunks

    def scores(self, query: str) -> np.ndarray:
        b = self.bm25.scores(query)
        b = b / b.max() if b.max() > 0 else b
        return self.dense.scores(query) + self.alpha * b


def top_k(retriever, query: str, k: int = 4, allowed: set[str] | None = None) -> list[tuple[Chunk, float]]:
    """Rank and return the top-k chunks. `allowed` = doc names this user may read:
    forbidden chunks are dropped before top-k is cut, so they can never reach the prompt."""
    s = retriever.scores(query)
    idx = [i for i in np.argsort(s)[::-1] if allowed is None or retriever.chunks[i].doc in allowed]
    return [(retriever.chunks[i], float(s[i])) for i in idx[:k]]
