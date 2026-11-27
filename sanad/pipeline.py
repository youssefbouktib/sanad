"""The full Sanad pipeline: retrieve -> gate -> screen -> generate -> verify."""
from __future__ import annotations

from dataclasses import dataclass, field

from . import generate as gen
from .guard import check_citations, screen
from .ingest import Chunk, load_dir
from .retrievers import BM25, Dense, Hybrid, top_k

ABSTAIN_MSG = {
    "en": "I couldn't find this in the documents.",
    "fr": "Je n'ai pas trouvé cette information dans les documents.",
    "ar": "لم أجد هذه المعلومة في الوثائق.",
}


@dataclass
class Answer:
    question: str
    text: str
    status: str                      # answered | abstained_gate | abstained_llm | retrieval_only
    hits: list[tuple[Chunk, float]]
    quarantined: list[Chunk] = field(default_factory=list)
    citations: dict = field(default_factory=dict)
    labels: dict = field(default_factory=dict)
    latency_s: float | None = None
    tokens: int | None = None
    best: float | None = None        # best cosine similarity seen by the gate
    retrieved: int = 0               # passages found before screening


class Sanad:
    def __init__(self, folders, retriever: str = "hybrid", max_chars: int = 700, dense_model: str | None = None):
        folders = [folders] if isinstance(folders, (str, bytes)) or not hasattr(folders, "__iter__") else folders
        self.chunks = [c for f in folders for c in load_dir(f, max_chars=max_chars)]
        if not self.chunks:
            raise ValueError(f"No .md/.txt/.pdf documents found in {folders}")
        self.retrievers = {"bm25": BM25(self.chunks)}
        if retriever in ("dense", "hybrid"):
            dense = Dense(self.chunks, **({"model_name": dense_model} if dense_model else {}))
            self.retrievers["dense"] = dense
            self.retrievers["hybrid"] = Hybrid(self.retrievers["bm25"], dense)
        self.default = retriever

    def retrieve(self, q: str, k: int = 4, retriever: str | None = None, allowed: set[str] | None = None):
        return top_k(self.retrievers[retriever or self.default], q, k=k, allowed=allowed)

    def best_cosine(self, q: str, allowed: set[str] | None = None) -> float | None:
        """Max cosine similarity to any permitted chunk — used by the abstention gate."""
        if "dense" not in self.retrievers:
            return None
        hits = top_k(self.retrievers["dense"], q, k=1, allowed=allowed)
        return hits[0][1] if hits else None

    def ask(self, q: str, k: int = 4, retriever: str | None = None, gate: float = 0.25,
            quarantine: bool = True, allowed: set[str] | None = None, lang: str = "en") -> Answer:
        # Over-fetch so quarantined chunks can be replaced by the next clean ones (backfill).
        hits = self.retrieve(q, k=k + 3, retriever=retriever, allowed=allowed)

        # 1. Gate: if nothing is even semantically close, don't pay for an LLM call.
        best = self.best_cosine(q, allowed)
        n = min(len(hits), k)
        if not hits or (best is not None and best < gate):
            return Answer(q, ABSTAIN_MSG.get(lang, ABSTAIN_MSG["en"]), "abstained_gate", hits[:k],
                          best=best, retrieved=n)

        # 2. Screen retrieved text for instructions aimed at the model.
        quarantined = []
        if quarantine:
            hits, quarantined = screen(hits)
        hits = hits[:k]

        if not gen.llm_available():
            return Answer(q, "(no LLM configured: showing retrieved evidence only)", "retrieval_only",
                          hits, quarantined, best=best, retrieved=n)

        # 3. Generate, then 4. verify citations.
        out = gen.generate(q, hits, lang)
        if out["abstained"]:
            return Answer(q, ABSTAIN_MSG.get(lang, ABSTAIN_MSG["en"]), "abstained_llm", hits, quarantined,
                          latency_s=out["latency_s"], tokens=out["tokens"], best=best, retrieved=n)
        return Answer(q, out["answer"], "answered", hits, quarantined,
                      citations=check_citations(out["answer"], out["labels"]), labels=out["labels"],
                      latency_s=out["latency_s"], tokens=out["tokens"], best=best, retrieved=n)
