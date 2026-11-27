"""Streamlit front end.  Run:  streamlit run app.py"""
from __future__ import annotations

import os
import re
from pathlib import Path

import streamlit as st

import ui
from sanad import Sanad
from sanad import generate as gen
from sanad.ingest import detect_lang

ROOT = Path(__file__).parent
CORPUS, ATTACKS, UPLOADS = ROOT / "data/corpus", ROOT / "data/attacks", ROOT / "data/uploads"

st.set_page_config(page_title="Sanad: answers with sources", page_icon="📖", layout="wide")
st.markdown(ui.CSS, unsafe_allow_html=True)

EXAMPLES = [
    "When do capstone project submissions close?",
    "Quelle est la date limite pour rendre le projet ?",
    "كم ثمن الغرفة في السكن الجامعي؟",
    "Are smartwatches allowed in the exam room?",
    "What is the penalty for submitting the project late?",
    "What does the capstone FAQ say about the deadline?",
]
SEARCH_MODES = {"hybrid": "Meaning + keywords", "dense": "Meaning only", "bm25": "Keywords only"}


@st.cache_resource(show_spinner="Opening the documents for the first time…")
def get_engine(folders: tuple[str, ...], mtime: float) -> Sanad:  # mtime refreshes the index after uploads
    return Sanad(list(folders), retriever="hybrid")


def folder_mtime(folders):
    return max((p.stat().st_mtime for f in folders for p in Path(f).rglob("*") if p.is_file()), default=0)


# ---------------- Sidebar ----------------
with st.sidebar:
    st.markdown("### Documents")
    with_attacks = st.toggle("Add tricky documents", help="Adds a forum post hiding instructions for the assistant, "
                                                          "and an old email that gives a different deadline.")
    files = st.file_uploader("Add your own files", type=["md", "txt", "pdf"], accept_multiple_files=True)
    if files:
        UPLOADS.mkdir(parents=True, exist_ok=True)
        for f in files:
            (UPLOADS / Path(f.name).name).write_bytes(f.getbuffer())
    folders = [str(CORPUS)] + ([str(ATTACKS)] if with_attacks else []) + ([str(UPLOADS)] if UPLOADS.exists() else [])

    engine = get_engine(tuple(folders), folder_mtime(folders))
    docs = sorted({c.doc for c in engine.chunks})
    allowed = set(st.multiselect("Documents this user can open", docs, default=docs,
                                 help="Sanad never reads a document the user isn't allowed to open."))

    st.markdown("### Search")
    retriever = st.radio("Search by", list(SEARCH_MODES), format_func=SEARCH_MODES.get)
    k = st.slider("Passages to read", 1, 8, 3)
    gate = st.slider("Minimum relevance", 0.0, 0.8, 0.25, 0.05,
                     help="Below this score, Sanad says the documents don't cover the question, without asking the model.")
    quarantine = st.toggle("Block hidden instructions", value=True,
                           help="Removes passages that try to give orders to the assistant.")

    st.markdown("### Model")
    if gen.llm_available():
        st.success(f"Connected to {os.environ['SANAD_MODEL']}")
    else:
        st.warning("No model connected. Sanad will show the matching passages only.")
    st.caption(f"{len(docs)} documents, {len(engine.chunks)} passages")

# ---------------- Main ----------------
st.markdown(ui.hero(), unsafe_allow_html=True)
tab_ask, tab_bench, tab_how = st.tabs(["Ask", "Benchmark", "How it works"])

with tab_ask:
    q = st.text_input("Your question", key="q", placeholder="Ask about deadlines, exams, the library, housing…",
                      label_visibility="collapsed")
    cols = st.columns(3)
    for i, ex in enumerate(EXAMPLES):
        cols[i % 3].button(ex, key=f"ex{i}", use_container_width=True,
                           on_click=st.session_state.update, kwargs={"q": ex})

    if q:
        lang = detect_lang(q)
        thinking = st.empty()
        thinking.markdown(ui.reading(gen.llm_available()), unsafe_allow_html=True)
        try:
            a = engine.ask(q, k=k, retriever=retriever, gate=gate, quarantine=quarantine,
                           allowed=allowed or set(), lang=lang)
        except Exception as e:  # provider down, bad key, timeout…
            thinking.empty()
            st.error(f"The model didn't respond ({type(e).__name__}). Check that Ollama is running, then ask again.")
            st.stop()
        thinking.empty()

        st.markdown(ui.chain(a, lang, quarantine), unsafe_allow_html=True)
        left, right = st.columns([5, 6], gap="large")
        with left:
            st.markdown('<h4 class="side">Answer</h4>' + ui.answer_card(a, lang), unsafe_allow_html=True)
        with right:
            title = "Closest passages (not relevant enough to use)" if a.status == "abstained_gate" else "Passages Sanad read"
            st.markdown(f'<h4 class="side">{title}</h4>' + ui.source_cards(a), unsafe_allow_html=True)

with tab_bench:
    st.markdown("#### How well Sanad finds and uses evidence")
    st.caption("Regenerate with `python -m sanad.evaluate --llm --attacks`.")
    report, chart = ROOT / "results/report.md", ROOT / "results/retrieval_chart.png"
    if chart.exists():
        st.image(str(chart), width=650)
    if report.exists():
        st.markdown(re.sub(r"^# .*\n", "", report.read_text(encoding="utf-8")))
    else:
        st.info("No benchmark yet. Run `python -m sanad.evaluate` in the project folder to create one.")

with tab_how:
    st.markdown("""
#### From question to answer
1. **Search**: the question is compared with every passage by meaning (multilingual embeddings) and by keywords (BM25). Only documents the user can open are searched.
2. **Relevance check**: if no passage is close enough, Sanad says so right away and the model is never asked.
3. **Safety screen**: passages that try to give orders to the assistant ("ignore previous instructions…") are blocked.
4. **Answer**: the model may use only the passages it was given, must cite them as S1, S2…, must say when the documents don't cover the question, and must point out contradictions.
5. **Check**: citations to passages that weren't provided, or answers with no citation, are flagged.

#### Why these choices
- Meaning search finds a French answer to an English question; keyword search catches exact codes and names.
- Refusing early saves time and money; refusing inside the model catches the rest.
- Instructions alone can't stop a malicious document, so the app also controls what the model sees and gives it no ability to act.
""")
