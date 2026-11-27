"""Visual layer for the Sanad app: styles, the reading robot, the evidence chain and source cards."""
from __future__ import annotations

import html
import re

INK, MAJORELLE, PAPER, MINT, SAFFRON, POMEGRANATE = "#16203A", "#2C4BC7", "#F4F6FB", "#2F8A68", "#E2A13B", "#C23B3B"

ZELLIGE = (
    "url(\"data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='56' height='56' viewBox='0 0 56 56'>"
    "<g fill='none' stroke='%232C4BC7' stroke-opacity='.08' stroke-width='1.2'>"
    "<rect x='16' y='16' width='24' height='24'/><rect x='16' y='16' width='24' height='24' transform='rotate(45 28 28)'/>"
    "<circle cx='28' cy='28' r='5'/></g></svg>\")"
)

CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,400;12..96,500;12..96,700;12..96,800&family=Reem+Kufi:wght@700&family=IBM+Plex+Sans+Arabic:wght@400;600&display=swap');
:root {{ --ink:{INK}; --maj:{MAJORELLE}; --paper:{PAPER}; --mint:{MINT}; --saffron:{SAFFRON}; --pom:{POMEGRANATE}; --line:#D7DDEC; }}
.stApp {{ background: var(--paper); }}
.stApp, .stMarkdown, .stMarkdown p, label, .stTextInput input, .stButton button, .stTabs button, h1, h2, h3 {{
  font-family: 'Bricolage Grotesque', 'IBM Plex Sans Arabic', system-ui, sans-serif; color: var(--ink); }}
.block-container {{ padding-top: 1.6rem; max-width: 1180px; }}
header[data-testid="stHeader"] {{ background: transparent; }}
[dir="rtl"], .ar {{ font-family: 'IBM Plex Sans Arabic', sans-serif; }}

/* hero */
.hero {{ display:flex; align-items:center; justify-content:space-between; gap:2rem; padding:1.6rem 2rem 1.4rem;
  background: #fff {ZELLIGE}; background-size:56px; border-radius:26px; border:1px solid var(--line); margin-bottom:1.4rem; }}
.hero .mark {{ font-family:'Reem Kufi', sans-serif; font-size:4.2rem; line-height:1; color:var(--maj); margin:0 0 .4rem; }}
.hero h1 {{ font-size:1.9rem; font-weight:800; line-height:1.15; letter-spacing:-.02em; margin:0 0 .5rem; max-width:22ch; padding:0; }}
.hero p {{ font-size:1.05rem; line-height:1.5; max-width:52ch; margin:0; opacity:.78; }}
.hero-bot svg {{ width:170px; height:auto; }}

/* question box + examples */
.stTextInput input {{ font-size:1.15rem !important; padding:.9rem 1.1rem !important; border-radius:16px !important;
  border:2px solid var(--line) !important; background:#fff !important; }}
.stTextInput input:focus {{ border-color: var(--maj) !important; box-shadow: 0 0 0 4px rgba(44,75,199,.15) !important; }}
.main .stButton button, [data-testid="stMain"] .stButton button {{ border-radius:999px; border:1.5px solid var(--line); background:#fff;
  font-size:.88rem; padding:.35rem .9rem; transition: border-color .15s, color .15s; }}
[data-testid="stMain"] .stButton button p {{ white-space:normal; overflow:visible; text-overflow:clip; line-height:1.3; }}
[data-testid="stMain"] .stButton button {{ height:100%; min-height:2.6rem; }}
[data-baseweb="tag"] {{ background: var(--maj) !important; }}
[data-baseweb="tab-highlight"] {{ background: var(--maj) !important; }}
[data-baseweb="tab"][aria-selected="true"] p {{ color: var(--maj) !important; }}
[data-testid="stMain"] .stButton button:hover {{ border-color: var(--maj); color: var(--maj); }}
[data-testid="stMain"] .stButton button:focus-visible {{ outline:3px solid var(--maj); outline-offset:2px; }}

/* evidence chain: the one animated moment, played on every answer */
.chain {{ display:flex; align-items:stretch; margin:1.2rem 0 1.4rem; }}
.node {{ flex:1; min-width:0; background:#fff; border:2px solid var(--line); border-radius:16px; padding:.7rem .8rem;
  animation: light .45s ease both; }}
.node b {{ display:flex; align-items:center; gap:.45rem; font-size:.95rem; }}
.node small {{ display:block; margin-top:.2rem; font-size:.8rem; line-height:1.35; opacity:.75; }}
.dot {{ width:11px; height:11px; border-radius:50%; background:var(--line); flex:none; }}
.link {{ flex:0 0 26px; align-self:center; height:3px; background:var(--line); position:relative; overflow:hidden; }}
.link::after {{ content:""; position:absolute; inset:0; background:var(--maj); transform-origin:left; animation: fill .35s ease both;
  animation-delay: inherit; }}
.link.off::after {{ display:none; }}
.s-ok {{ border-color: rgba(47,138,104,.45); }} .s-ok .dot {{ background:var(--mint); }}
.s-warn {{ border-color: rgba(226,161,59,.6); background:#FFF9EE; }} .s-warn .dot {{ background:var(--saffron); }}
.s-hold {{ border-color: var(--maj); background:#F0F3FD; }} .s-hold .dot {{ background:var(--maj); }}
.s-stop {{ border-color: var(--pom); background:#FDF2F2; }} .s-stop .dot {{ background:var(--pom); box-shadow:0 0 0 0 rgba(194,59,59,.5);
  animation: ring 1.2s ease-out 2; animation-delay: inherit; }}
.s-skip {{ opacity:.38; border-style:dashed; }}
@keyframes light {{ from {{ opacity:0; transform: translateY(6px); }} to {{ opacity:1; transform:none; }} }}
@keyframes fill {{ from {{ transform: scaleX(0); }} to {{ transform: scaleX(1); }} }}
@keyframes ring {{ to {{ box-shadow: 0 0 0 10px rgba(194,59,59,0); }} }}

/* answer */
.answer {{ background:#fff; border-radius:20px; padding:1.3rem 1.4rem; border:1px solid var(--line); border-left:6px solid var(--mint); }}
.answer.abstain {{ border-left-color: var(--maj); }} .answer.plain {{ border-left-color: var(--saffron); }}
.answer .text {{ font-size:1.22rem; line-height:1.6; }}
.answer .foot {{ margin-top:.8rem; font-size:.82rem; opacity:.65; }}
.cite {{ display:inline-block; background:var(--maj); color:#fff; font-size:.72rem; font-weight:700; border-radius:7px;
  padding:1px 7px; margin:0 2px; vertical-align:2px; }}
.flag {{ margin-top:.7rem; font-size:.85rem; padding:.45rem .7rem; border-radius:10px; background:#FDF2F2; color:var(--pom); }}
h4.side {{ font-size:1rem; font-weight:700; margin:0 0 .6rem; }}

/* sources */
.src {{ background:#fff; border:1px solid var(--line); border-radius:14px; padding:.75rem .95rem; margin-bottom:.7rem; }}
.src.cited {{ border:2px solid var(--maj); }}
.src-head {{ display:flex; gap:.5rem; align-items:baseline; flex-wrap:wrap; font-size:.82rem; }}
.src-head .doc {{ font-weight:700; }} .src-head .sec {{ opacity:.6; }}
.bar {{ height:5px; border-radius:5px; background:#E8ECF6; margin:.5rem 0 .55rem; overflow:hidden; }}
.bar i {{ display:block; height:100%; background:var(--maj); border-radius:5px; }}
.src-body {{ font-size:.92rem; line-height:1.55; }}
.src.blocked {{ border:2px solid var(--pom);
  background: repeating-linear-gradient(-45deg, #fff 0 12px, #FDF2F2 12px 24px); }}
.src.blocked .why {{ color:var(--pom); font-weight:700; font-size:.85rem; margin-bottom:.35rem; }}

/* the reading robot */
.reader {{ display:flex; flex-direction:column; align-items:center; padding:1.2rem 0 .6rem; }}
.reader svg {{ width:210px; height:auto; }}
.reader .say {{ position:relative; height:1.6em; width:100%; text-align:center; font-weight:600; font-size:1.02rem; }}
.reader .say span {{ position:absolute; left:0; right:0; opacity:0; animation: say 7.5s infinite; }}
.reader .say span:nth-child(2) {{ animation-delay: 2.5s; }} .reader .say span:nth-child(3) {{ animation-delay: 5s; }}
@keyframes say {{ 0%,4% {{ opacity:0; transform:translateY(4px); }} 8%,30% {{ opacity:1; transform:none; }} 34%,100% {{ opacity:0; }} }}
.bot .eyes {{ animation: scan 1.3s ease-in-out infinite alternate; }}
.bot .flip {{ transform-box: view-box; transform-origin: 100px 130px; animation: flip 1.9s ease-in-out infinite; }}
.bot .bulb {{ animation: bulb 1s steps(2) infinite; }}
.bot .glyph {{ opacity:0; animation: rise 2.4s ease-out infinite; }}
.bot .glyph.g2 {{ animation-delay: .8s; }} .bot .glyph.g3 {{ animation-delay: 1.6s; }}
.bot.idle .eyes {{ animation: blink 4s infinite; transform-box: fill-box; transform-origin:center; }}
.bot.idle .flip, .bot.idle .glyph {{ display:none; }} .bot.idle .bulb {{ animation:none; }}
@keyframes scan {{ from {{ transform: translate(-4px, 2px); }} to {{ transform: translate(4px, 2px); }} }}
@keyframes flip {{ 0%,15% {{ transform: scaleX(1); }} 85%,100% {{ transform: scaleX(-1); }} }}
@keyframes bulb {{ 50% {{ fill: #fff; }} }}
@keyframes rise {{ 0% {{ opacity:0; transform: translateY(0); }} 20% {{ opacity:1; }} 100% {{ opacity:0; transform: translateY(-46px); }} }}
@keyframes blink {{ 0%,92%,100% {{ transform: scaleY(1); }} 95% {{ transform: scaleY(.1); }} }}

@media (prefers-reduced-motion: reduce) {{
  .node, .link::after, .s-stop .dot, .bot *, .reader .say span {{ animation: none !important; }}
  .reader .say span:first-child {{ opacity:1; }}
}}
@media (max-width: 760px) {{
  .hero {{ flex-direction:column; align-items:flex-start; padding:1.2rem; }} .hero-bot {{ display:none; }}
  .chain {{ flex-direction:column; }} .link {{ flex-basis:14px; width:3px; height:14px; align-self:flex-start; margin-left:22px; }}
}}
</style>
"""


def robot(idle: bool = False) -> str:
    """An ink robot reading an open book: eyes scan the lines, pages turn, letters float up."""
    lines = "".join(
        f'<line x1="{x1}" y1="{y}" x2="{x2}" y2="{y}" stroke="#C9D1E6" stroke-width="2.6" stroke-linecap="round"/>'
        for y in (118, 125, 132, 139) for x1, x2 in ((60, 92), (108, 140))
    )
    return (
        f'<svg class="bot{" idle" if idle else ""}" viewBox="0 0 200 172" role="img" aria-label="A robot reading a book">'
        f'<line x1="100" y1="22" x2="100" y2="10" stroke="{INK}" stroke-width="3"/>'
        f'<circle class="bulb" cx="100" cy="8" r="5" fill="{SAFFRON}"/>'
        f'<rect x="64" y="22" width="72" height="48" rx="15" fill="{INK}"/>'
        f'<rect x="72" y="30" width="56" height="32" rx="10" fill="{MAJORELLE}"/>'
        f'<g class="eyes"><circle cx="89" cy="45" r="5" fill="#fff"/><circle cx="111" cy="45" r="5" fill="#fff"/></g>'
        f'<rect x="93" y="70" width="14" height="6" fill="{INK}"/>'
        f'<rect x="56" y="76" width="88" height="58" rx="18" fill="{INK}"/>'
        f'<circle cx="100" cy="92" r="4" fill="{SAFFRON}"/>'
        f'<path d="M100 112 Q74 103 42 110 L42 158 Q74 151 100 160 Q126 151 158 158 L158 110 Q126 103 100 112Z" fill="{MAJORELLE}"/>'
        f'<path d="M100 110 Q78 101 50 107 L50 152 Q78 146 100 154Z" fill="#fff"/>'
        f'<path d="M100 110 Q122 101 150 107 L150 152 Q122 146 100 154Z" fill="#fff"/>'
        f"{lines}"
        f'<path class="flip" d="M100 110 Q122 101 150 107 L150 152 Q122 146 100 154Z" fill="#E9EDFA" stroke="#C9D1E6"/>'
        f'<path d="M62 100 Q44 112 48 128" stroke="{INK}" stroke-width="10" stroke-linecap="round" fill="none"/>'
        f'<path d="M138 100 Q156 112 152 128" stroke="{INK}" stroke-width="10" stroke-linecap="round" fill="none"/>'
        f'<circle cx="48" cy="130" r="8" fill="{INK}"/><circle cx="152" cy="130" r="8" fill="{INK}"/>'
        f'<text class="glyph" x="76" y="104" font-size="15" fill="{MAJORELLE}" font-weight="700">A</text>'
        f'<text class="glyph g2" x="118" y="104" font-size="16" fill="{MINT}" font-weight="700">س</text>'
        f'<text class="glyph g3" x="97" y="100" font-size="14" fill="{SAFFRON}" font-weight="700">é</text>'
        "</svg>"
    )


def reading(has_llm: bool) -> str:
    says = (["Reading the passages…", "Checking each fact against its source…", "Writing the answer with citations…"]
            if has_llm else ["Searching the documents…", "Ranking the passages…", "Almost there…"])
    return f'<div class="reader">{robot()}<div class="say">{"".join(f"<span>{s}</span>" for s in says)}</div></div>'


def hero() -> str:
    return (
        f'<div class="hero"><div><div class="mark" lang="ar">سند</div>'
        "<h1>Answers from your documents, with the sources to prove it</h1>"
        "<p>Ask in English, French or Arabic. Sanad shows the passages behind every sentence, "
        "and when the documents don't say, it tells you instead of guessing.</p></div>"
        f'<div class="hero-bot">{robot(idle=True)}</div></div>'
    )


LANG_NAME = {"en": "English", "fr": "French", "ar": "Arabic"}


def chain(a, lang: str, quarantine_on: bool) -> str:
    """Five steps of the evidence chain. Each step lights up in turn; the chain stops where Sanad stops."""
    best = f"{a.best:.2f}" if a.best is not None else "n/a"
    steps = [("Question", f"Asked in {LANG_NAME.get(lang, 'an unknown language')}", "ok"),
             ("Search", f"{a.retrieved} passage{'s' * (a.retrieved != 1)} found", "ok" if a.retrieved else "stop")]
    if a.status == "abstained_gate":
        steps.append(("Relevance check", f"Nothing close enough (best match {best})", "stop"))
    else:
        steps.append(("Relevance check", f"Closest match scores {best}", "ok"))
    if a.status == "abstained_gate":
        steps.append(("Safety screen", "Not needed", "skip"))
    elif not quarantine_on:
        steps.append(("Safety screen", "Turned off", "warn"))
    elif a.quarantined:
        n = len(a.quarantined)
        steps.append(("Safety screen", f"Blocked {n} passage{'s' * (n != 1)} with hidden instructions", "warn"))
    else:
        steps.append(("Safety screen", "No hidden instructions", "ok"))
    answer = {
        "answered": ("Answer", f"Backed by {len(a.citations.get('cited', []))} cited source(s)", "ok"),
        "abstained_llm": ("Answer", "The documents don't say, so no answer", "hold"),
        "abstained_gate": ("Answer", "Not attempted", "skip"),
        "retrieval_only": ("Answer", "No model connected: sources only", "warn"),
    }[a.status]
    steps.append(answer)

    parts, stopped = [], False
    for i, (title, detail, state) in enumerate(steps):
        if stopped and state != "skip":
            state = "skip"
        delay = f"animation-delay:{i * 0.38:.2f}s"
        if i:
            parts.append(f'<span class="link{" off" if state == "skip" else ""}" style="{delay}"></span>')
        parts.append(f'<div class="node s-{state}" style="{delay}"><b><span class="dot"></span>{title}</b>'
                     f"<small>{html.escape(detail)}</small></div>")
        stopped = stopped or state == "stop"
    return f'<div class="chain" role="list" aria-label="How this answer was produced">{"".join(parts)}</div>'


def answer_card(a, lang: str) -> str:
    text = html.escape(a.text)
    text = re.sub(r"\[(S\d+)\]", r'<span class="cite">\1</span>', text)
    cls = {"answered": "", "abstained_llm": "abstain", "abstained_gate": "abstain"}.get(a.status, "plain")
    d = "rtl" if lang == "ar" else "ltr"
    flag = ""
    if a.citations.get("invalid"):
        flag = f'<div class="flag">Cites a source that wasn\'t provided ({", ".join(a.citations["invalid"])}). Check this answer by hand.</div>'
    elif a.status == "answered" and a.citations.get("uncited"):
        flag = '<div class="flag">This answer cites no source. Check it against the passages before relying on it.</div>'
    foot = f'<div class="foot">Answered in {a.latency_s} s using {a.tokens or "?"} tokens</div>' if a.latency_s else ""
    return f'<div class="answer {cls}"><div class="text" dir="{d}">{text}</div>{flag}{foot}</div>'


def source_cards(a) -> str:
    cited = set(a.citations.get("cited", []))
    label_of = {c.id: lab for lab, c in a.labels.items()}
    top = max((s for _, s in a.hits), default=1) or 1
    out = []
    for c, score in a.hits:
        lab = label_of.get(c.id, "")
        d = "rtl" if c.lang == "ar" else "ltr"
        chip = f'<span class="cite">{lab}</span>' if lab else ""
        width = max(4, min(100, round(100 * score / top)))
        out.append(
            f'<div class="src{" cited" if lab in cited else ""}"><div class="src-head">{chip}'
            f'<span class="doc">{html.escape(c.doc)}</span><span class="sec">{html.escape(c.section)}</span></div>'
            f'<div class="bar" title="Relevance {score:.3f}"><i style="width:{width}%"></i></div>'
            f'<div class="src-body" dir="{d}">{html.escape(c.text).replace(chr(10), "<br>")}</div></div>'
        )
    for c in a.quarantined:
        out.append(
            f'<div class="src blocked"><div class="why">Blocked: this passage tries to give orders to the assistant</div>'
            f'<div class="src-head"><span class="doc">{html.escape(c.doc)}</span></div>'
            f'<div class="src-body">{html.escape(c.text).replace(chr(10), "<br>")}</div></div>'
        )
    return "".join(out) or '<p>No passages matched.</p>'
