"""Indexing path, step 1: load documents and split them into chunks with metadata."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

SUPPORTED = {".md", ".txt", ".pdf"}


@dataclass
class Chunk:
    id: str              # stable id: "<doc>#<n>"
    doc: str             # file name
    text: str
    section: str = ""    # nearest heading
    page: int | None = None
    lang: str = "?"
    meta: dict = field(default_factory=dict)


_FR = {"le", "la", "les", "des", "est", "une", "pour", "dans", "sont", "avec", "du", "aux"}
_EN = {"the", "is", "are", "and", "for", "with", "must", "to", "of", "in", "be", "by"}


def detect_lang(text: str) -> str:
    """Tiny heuristic detector: good enough for routing/stats, not a real language-ID model."""
    if len(re.findall(r"[؀-ۿ]", text)) > len(text) * 0.2:
        return "ar"
    words = re.findall(r"[a-zà-ÿ']+", text.lower())
    fr, en = sum(w in _FR for w in words), sum(w in _EN for w in words)
    return "fr" if fr > en else "en" if en else "?"


def _read(path: Path) -> list[tuple[str, int | None]]:
    """Return (text, page) pairs. PDFs keep page numbers so we can cite them."""
    if path.suffix.lower() == ".pdf":
        from pypdf import PdfReader
        return [(p.extract_text() or "", i + 1) for i, p in enumerate(PdfReader(str(path)).pages)]
    return [(path.read_text(encoding="utf-8"), None)]


def chunk_text(text: str, max_chars: int = 700, overlap: int = 1) -> list[tuple[str, str]]:
    """Split on headings and blank lines, then pack paragraphs up to max_chars.

    - Headings are kept with the text they introduce (a chunk never loses its context).
    - `overlap` paragraphs are repeated at the start of the next chunk of the same section,
      so a rule that crosses a boundary is still found.
    Returns (section, chunk_text) pairs.
    """
    section, paras, out = "", [], []
    blocks = [b.strip() for b in re.split(r"\n\s*\n", text) if b.strip()]

    def flush():
        if paras:
            body = "\n\n".join(paras)
            out.append((section, f"{section}\n{body}".strip() if section else body))

    for b in blocks:
        heading = re.match(r"^#{1,6}\s+(.*)", b)
        if heading:
            flush()
            section, paras = heading.group(1).strip(), []
            rest = b.split("\n", 1)[1].strip() if "\n" in b else ""
            if rest:
                paras.append(rest)
            continue
        if paras and sum(map(len, paras)) + len(b) > max_chars:
            flush()
            paras = paras[-overlap:] if overlap else []
        paras.append(b)
    flush()
    return out


def load_dir(folder: str | Path, max_chars: int = 700) -> list[Chunk]:
    chunks: list[Chunk] = []
    for path in sorted(Path(folder).rglob("*")):
        if path.suffix.lower() not in SUPPORTED:
            continue
        n = 0
        for text, page in _read(path):
            for section, body in chunk_text(text, max_chars=max_chars):
                chunks.append(Chunk(id=f"{path.name}#{n}", doc=path.name, text=body,
                                    section=section, page=page, lang=detect_lang(body)))
                n += 1
    return chunks
