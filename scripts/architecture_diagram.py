"""Write architecture/Architecture_Diagram.svg (rendered to PDF / PNG / JPEG by scripts/build_docs.py).

The layout follows the data path the submission guidelines ask for:
Dataset -> Preprocessing -> Chunking -> Embeddings -> Vector DB -> Retriever -> LLM / RAG -> Agents -> API -> UI,
with the online request path drawn left to right (UI -> API -> LangGraph workflow -> support plan) and the offline build
underneath. No metrics are drawn here (numbers live in the generated reports), only components and how they connect.
"""
from __future__ import annotations

from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "architecture" / "Architecture_Diagram.svg"

W, H = 2000, 1020
NAVY, TEAL, TEAL_BG = "#17324d", "#1f6f8b", "#eaf3f6"
PURPLE, PURPLE_BG = "#6b4aa0", "#f2edf9"
GREEN, GREEN_BG = "#2d7a5a", "#e9f4ee"
ORANGE, ORANGE_BG = "#b7791f", "#fdf5e6"
SLATE, SLATE_BG, MUTED = "#55606e", "#f3f5f7", "#5d6b7a"
FONT = "Segoe UI, Inter, Helvetica Neue, Arial, sans-serif"

parts: list[str] = []


def t(x, y, s, size=15, color=NAVY, weight=400, anchor="middle", italic=False, spacing=0):
    style = ' font-style="italic"' if italic else ""
    ls = f' letter-spacing="{spacing}"' if spacing else ""
    parts.append(f'<text x="{x}" y="{y}" font-family="{FONT}" font-size="{size}" fill="{color}" font-weight="{weight}" '
                 f'text-anchor="{anchor}"{style}{ls}>{escape(s)}</text>')


def box(x, y, w, h, stroke=TEAL, fill="#ffffff", sw=2.2, r=12, dash=None):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"{d}/>')


def node(x, y, w, h, title, lines, kicker=None, stroke=TEAL, fill="#ffffff", title_size=21, kicker_color=None, sw=2.2):
    box(x, y, w, h, stroke=stroke, fill=fill, sw=sw)
    cx = x + w / 2
    ty = y + (34 if kicker else 30)
    if kicker:
        t(cx, y + 26, kicker, 12.5, kicker_color or stroke, 700, spacing=0.6)
        ty = y + 60
    for i, tl in enumerate(title.split("\n")):
        t(cx, ty + i * 25, tl, title_size, NAVY, 700)
    ly = ty + 25 * (len(title.split("\n")) - 1) + 30
    for i, ln in enumerate(lines):
        t(cx, ly + i * 20, ln, 14, MUTED)


def arrow(x1, y1, x2, y2, color=SLATE, sw=2.4, dash=None, head=True):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    m = f' marker-end="url(#ah-{color[1:]})"' if head else ""
    parts.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="{sw}"{d}{m}/>')


def path(d, color=SLATE, sw=2.4, dash=None, head=True):
    da = f' stroke-dasharray="{dash}"' if dash else ""
    m = f' marker-end="url(#ah-{color[1:]})"' if head else ""
    parts.append(f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{sw}"{da}{m}/>')


def label(x, y, s, color=MUTED, size=13.5):
    t(x, y, s, size, color, 400, italic=True)


# ------------------------------------------------------------------ header
t(40, 58, "Uplift: Student Success Assistant", 40, NAVY, 700, anchor="start")
t(42, 96, "MULTI-AGENT WORKFLOW  ·  HYBRID RAG  ·  ML RISK PREDICTION  ·  LLM-AS-JUDGE  ·  FEEDBACK LOOP", 17, TEAL, 700,
  anchor="start", spacing=0.4)

# Evaluation (top left) and direct tools (top right)
node(1236, 108, 729, 84, "Direct tools", ["cohort · predict & explain · prioritise · case search · insights · copilot (Claude tool use)"],
     stroke=NAVY, title_size=20)
path("M 353 318 L 353 150 L 1230 150", color=NAVY, sw=2.2, dash="4 6")
label(790, 140, "direct requests (no agent run)")

# ------------------------------------------------------------------ online path
node(40, 342, 178, 140, "Web UI", ["React console", "(landing at /)"], kicker="INPUT", stroke=NAVY, sw=2.6)
node(258, 318, 190, 188, "FastAPI", ["Input guardrails:", "API key · rate limit", "schema validation",
                                     "injection screening"], kicker="API GATEWAY", stroke=NAVY, sw=2.6, title_size=21)
arrow(218, 412, 252, 412, NAVY)
arrow(448, 412, 508, 412, NAVY)

# LangGraph workflow container
box(490, 205, 1236, 342, stroke=TEAL, fill=TEAL_BG, sw=2.2, r=16)
t(512, 234, "LANGGRAPH MULTI-AGENT WORKFLOW  ·  shared typed state", 15, TEAL, 700, anchor="start", spacing=0.3)
box(514, 248, 1190, 44, stroke=PURPLE, fill=PURPLE_BG, sw=2, r=8)
t(534, 277, "LLM  ·  Claude via the Anthropic API", 17.5, PURPLE, 700, anchor="start")
t(1688, 277, "Sonnet 5.5 agents · Haiku 5.5 parsing & rewrites · structured outputs · computed fallback for every step",
  13.5, PURPLE, 400, anchor="end")

NX, NY, NW, NH, GAP = 514, 342, 168, 140, 36
nodes = [
    ("01", "Evidence", ["ML risk · drivers", "6 similar cases (RAG)"]),
    ("02", "Performance\nAnalysis", ["strengths · concerns"]),
    ("03", "Risk\nAssessment", ["risk · precedents", "uncertainty"]),
    ("04", "Intervention\nPlanning", ["router · 2-4 actions", "outreach draft"]),
    ("05", "Critic", ["IDs · numbers ·", "protected terms"]),
    ("06", "Precedent\nSynthesis", ["what happened next", "to similar students"]),
]
xs = []
for i, (num, title, lines) in enumerate(nodes):
    x = NX + i * (NW + GAP)
    xs.append(x)
    box(x, NY, NW, NH, stroke=TEAL, fill="#ffffff", sw=2.4)
    cx = x + NW / 2
    t(cx, NY + 25, num, 13, TEAL, 700)
    tl = title.split("\n")
    ty = NY + (56 if len(tl) == 1 else 50)
    for k, s in enumerate(tl):
        t(cx, ty + k * 23, s, 19.5, NAVY, 700)
    ly = ty + 23 * (len(tl) - 1) + 28
    for k, s in enumerate(lines):
        t(cx, ly + k * 18, s, 13.5, MUTED)
    if i:
        arrow(x - GAP, NY + NH / 2, x - 5, NY + NH / 2, TEAL)
# LLM calls into the LLM-backed agents (dashed purple)
for i, dx in ((1, 0), (2, 0), (3, -40), (5, 0)):
    cx = xs[i] + NW / 2 + dx
    arrow(cx, 292, cx, NY - 5, PURPLE, 1.8, dash="4 4")
# self-check loop: critic -> intervention (revise once)
c4, c5 = xs[3] + NW - 30, xs[4] + 40
path(f"M {c5} {NY} C {c5 - 10} 306, {c4 + 10} 306, {c4} {NY - 3}", color=ORANGE, sw=2.4, dash="9 6")
t((xs[3] + xs[4] + NW) / 2, NY + NH + 24, "SELF-CHECK LOOP · critic finds violations → revise once (05 → 04)", 13, ORANGE, 700)
label((xs[3] + xs[4] + NW) / 2, NY + NH + 44, "router 'monitor' or failed checks → deterministic, catalogue-gated planner", TEAL, 12.5)

# Output
node(1762, 330, 203, 164, "Support\nPlan", ["risk · drivers · actions", "outreach · precedents", "checks passed"],
     kicker="OUTPUT", stroke=NAVY, fill="#f1f6fa", sw=3.2)
arrow(1726, 412, 1756, 412, NAVY)
label(1863, 518, "streamed live to the console")

# ------------------------------------------------------------------ shared services row
RY, RH = 584, 124
node(40, RY, 420, RH, "Evaluation", ["DeepEval · RAGAS · LLM-as-Judge (Opus 5.5)", "retrieval & model benchmarks · quality gate"],
     kicker="QUALITY", stroke=SLATE, fill=SLATE_BG, title_size=20)
node(526, RY, 330, RH, "Hybrid Retriever", ["BM25 + behavioural kNN + dense", "RRF fusion · metadata pre-filter"],
     kicker="KNOWLEDGE BASE", stroke=GREEN, fill=GREEN_BG, title_size=20)
node(956, RY, 360, RH, "ML Models", ["XGBoost risk (calibrated) · outcome", "prioritiser · TreeSHAP drivers"],
     kicker="PREDICTION", stroke=GREEN, fill=GREEN_BG, title_size=20)
node(1492, RY, 360, RH, "Feedback Loop", ["advisor ratings → action ranking,", "fusion weights, recalibration (approved)"],
     kicker="LEARNING", stroke=ORANGE, fill=ORANGE_BG, title_size=20)
# retriever -> evidence ; models -> evidence (orthogonal routing inside the workflow's lower margin)
arrow(598, RY, 598, NY + NH + 6, GREEN, 2.6)
# evaluation scores what the workflow and copilot produce (offline suites, sampled online judging)
path(f"M 250 {RY} L 250 {NY + NH + 48} L 484 {NY + NH + 48}", color=SLATE, sw=2.2, dash="6 5")
label(366, NY + NH + 40, "judges plans & answers", SLATE, 12.5)
path(f"M 1040 {RY} L 1040 {NY + NH + 40} L 650 {NY + NH + 40} L 650 {NY + NH + 6}", color=GREEN, sw=2.6)
label(840, NY + NH + 34, "scores · drivers", GREEN, 12.5)
# output -> feedback -> models / retriever
path(f"M 1860 530 L 1790 {RY - 6}", color=ORANGE, sw=2.4, dash="9 6")
arrow(1492, RY + RH / 2, 1322, RY + RH / 2, ORANGE, 2.4, dash="9 6")

# ------------------------------------------------------------------ offline build
OY = 760
box(40, OY, 1925, 222, stroke=SLATE, fill=SLATE_BG, sw=2, r=16, dash="10 7")
t(62, OY + 30, "OFFLINE  ·  BUILT ONCE PER CHECKPOINT (python -m src.cli build): weeks 5, 9, 15 and 22 of the course", 15, SLATE,
  700, anchor="start", spacing=0.3)
BY, BH, BW = OY + 52, 108, 252
chain = [
    (72, "Dataset", ["OULAD · 7 CSV tables", "Open University"]),
    (370, "Preprocessing", ["snapshot features per week", "in-scope only · no leakage"]),
    (668, "Chunking", ["1 enrolment = 1 case", "narrative + descriptor tokens"]),
    (966, "Embeddings", ["intfloat/e5-small-v2", "+ behavioural vectors"]),
    (1264, "Vector DB + BM25", ["LanceDB (filtered kNN)", "+ keyword index"]),
]
for x, title, lines in chain:
    node(x, BY, BW, BH, title, lines, stroke=SLATE, title_size=20)
for (x1, *_), (x2, *_) in zip(chain, chain[1:]):
    arrow(x1 + BW, BY + BH / 2, x2 - 6, BY + BH / 2, SLATE)
node(1640, BY, 292, BH, "Model Training", ["XGBoost + calibration + SHAP", "temporal split (test 2014J)"], stroke=SLATE, title_size=20)
path(f"M {370 + BW / 2} {BY + BH} L {370 + BW / 2} {BY + BH + 30} L {1640 + 146} {BY + BH + 30} L {1640 + 146} {BY + BH + 6}",
     color=SLATE, sw=2.2)
parts.append(f'<rect x="1030" y="{BY + BH + 20}" width="100" height="20" fill="{SLATE_BG}"/>')
t(1080, BY + BH + 35, "feature table", 13, SLATE, 400, italic=True)
# offline -> online
arrow(1390, BY, 700, RY + RH + 6, GREEN, 2.6)
label(1035, 744, "indexes", GREEN)
arrow(1786, BY, 1180, RY + RH + 6, GREEN, 2.6)
label(1450, 744, "models", GREEN)

# arrow heads per colour
defs = "".join(
    f'<marker id="ah-{c[1:]}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
    f'<path d="M 0 0 L 10 5 L 0 10 z" fill="{c}"/></marker>' for c in {NAVY, TEAL, PURPLE, GREEN, ORANGE, SLATE})
svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">'
       f'<defs>{defs}</defs><rect width="{W}" height="{H}" fill="#ffffff"/>' + "".join(parts) + "</svg>")


def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(svg, encoding="utf-8")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
