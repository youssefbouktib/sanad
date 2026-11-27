"""Defences around the generator: injection screening and citation validation."""
from __future__ import annotations

import re

from .ingest import Chunk

# Heuristic patterns for instructions aimed at the model, in EN / FR / AR.
# A heuristic catches the obvious cases only: it is ONE layer, not the security boundary.
INJECTION_PATTERNS = [
    r"ignore (all |any )?(the )?(previous|prior|above) (instructions|rules)",
    r"disregard (the|your) (instructions|system prompt)",
    r"you are now", r"system prompt", r"reveal (the |your )?(password|secret|key|prompt)",
    r"send (it|them|the \w+|your \w+) to", r"\b\S+@\S+\.\w+\b.*(password|mot de passe)",
    r"ignore[rz]? (toutes |les )?(les )?instructions", r"oublie[rz]? (tes|vos|les) (consignes|instructions)",
    r"تجاهل (جميع |كل )?(التعليمات|الأوامر)", r"انس (التعليمات|الأوامر)",
]
_INJ = re.compile("|".join(INJECTION_PATTERNS), re.IGNORECASE)


def looks_like_injection(text: str) -> bool:
    return bool(_INJ.search(text))


def screen(hits: list[tuple[Chunk, float]]) -> tuple[list[tuple[Chunk, float]], list[Chunk]]:
    """Split hits into (kept, quarantined)."""
    kept, quarantined = [], []
    for c, s in hits:
        (quarantined.append(c) if looks_like_injection(c.text) else kept.append((c, s)))
    return kept, quarantined


CITE = re.compile(r"\[(S\d+)\]")


def check_citations(answer: str, labels: dict[str, Chunk]) -> dict:
    """Every [S#] must refer to a source we actually supplied. Uncited answers are flagged too."""
    cited = CITE.findall(answer)
    return {
        "cited": sorted(set(cited)),
        "invalid": sorted({c for c in cited if c not in labels}),
        "uncited": not cited,
    }
