"""presentation/Project_Presentation.pptx: the 10-minute panel deck, built from the finished artifacts.

Slides follow the submission guidelines (problem, business need, solution, architecture, data flow, technology stack,
agent workflow, demo, evaluation results, challenges and learnings) plus retrieval, models and responsible AI. Every
number is read from artifacts; speaker notes carry the talk track (docs/Presentation_Guide has the full version).
Images: architecture/Architecture_Diagram.png and docs/screenshots/*.jpg.
"""
from __future__ import annotations

from pathlib import Path

from src.utils.common import read_json
from src.utils.config import PROJECT_ROOT, Settings, course_week, get_settings

NAVY, TEAL, TEAL_BG, PURPLE, PURPLE_BG = "17324D", "1F6F8B", "EAF3F6", "6B4AA0", "F2EDF9"
GREEN, GREEN_BG, ORANGE, ORANGE_BG = "2D7A5A", "E9F4EE", "B7791F", "FDF5E6"
SLATE, MUTED, LIGHT, RULE, WHITE, YELLOW, RED = "55606E", "5D6B7A", "F3F5F7", "D5DEE5", "FFFFFF", "F2C94C", "B23A2B"
FONT = "Segoe UI"


def _pct(x, d=0):
    return "n/a" if x is None else f"{100 * float(x):.{d}f}%"


def _f(x, d=3):
    return "n/a" if x is None else f"{float(x):.{d}f}"


def _count_tests() -> int | None:
    """Number of collected pytest tests (parametrized cases included), or None if pytest is unavailable."""
    import re
    import subprocess
    import sys
    try:
        out = subprocess.run([sys.executable, "-m", "pytest", "--collect-only", "-qq", "-p", "no:cacheprovider"], cwd=PROJECT_ROOT,
                             capture_output=True, text=True, timeout=300).stdout
    except (OSError, subprocess.SubprocessError):
        return None
    counts = [int(n) for n in re.findall(r"^tests\S*\.py: (\d+)$", out, flags=re.M)]
    return sum(counts) or None


def build_presentation(s: Settings | None = None, out: Path | None = None) -> Path:
    from lxml import etree
    from pptx import Presentation
    from pptx.chart.data import CategoryChartData
    from pptx.dml.color import RGBColor
    from pptx.enum.chart import XL_CHART_TYPE, XL_LABEL_POSITION, XL_LEGEND_POSITION
    from pptx.enum.shapes import MSO_CONNECTOR, MSO_SHAPE
    from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
    from pptx.oxml.ns import qn
    from pptx.util import Inches, Pt

    s = s or get_settings()
    gm, pm = s.global_metrics_dir, s.at(s.primary_checkpoint).metrics_dir
    w = read_json(pm / "withdrawal_model.json", {})
    o = read_json(pm / "outcome_model.json", {})
    d = read_json(pm / "data_build.json", {})
    p = read_json(pm / "prioritization.json", {})
    r = read_json(pm / "retrieval_benchmark.json", {})
    ts = read_json(pm / "text_search_benchmark.json", {})
    ab = read_json(pm / "ablations.json", {})
    fa = read_json(pm / "fairness.json", {})
    cs = read_json(gm / "checkpoint_summary.json", {}).get("checkpoints", [])
    e = read_json(gm / "llm_evaluation.json", {})
    rg = read_json(gm / "ragas_eval.json", {}).get("features", {})
    q = read_json(gm / "quality_gate.json", {})
    t, pa, ag = w.get("test", {}), w.get("population_audit", {}), e.get("agents", {})
    pw = course_week(s.primary_checkpoint)
    n_tests = _count_tests()
    weeks = [course_week(c) for c in s.checkpoints]
    out = Path(out or PROJECT_ROOT / "presentation" / "Project_Presentation.pptx")
    out.parent.mkdir(parents=True, exist_ok=True)

    prs = Presentation()
    prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)
    blank = prs.slide_layouts[6]
    rgb = RGBColor.from_string
    state = {"n": 0}

    # ------------------------------------------------------------ primitives
    def para_fmt(par, size, color, bold=False, italic=False, align=None):
        for run in par.runs:
            run.font.size, run.font.bold, run.font.italic, run.font.name = Pt(size), bold, italic, FONT
            run.font.color.rgb = rgb(color)
        if align:
            par.alignment = align

    def text(sl, x, y, w_, h, items, size=16, color=NAVY, bold=False, align=None, anchor=MSO_ANCHOR.TOP, spacing=6, bullet=False):
        tb = sl.shapes.add_textbox(Inches(x), Inches(y), Inches(w_), Inches(h))
        tf = tb.text_frame
        tf.word_wrap, tf.vertical_anchor = True, anchor
        tf.margin_left = tf.margin_right = Inches(0.04)
        tf.margin_top = tf.margin_bottom = Inches(0.02)
        items = items if isinstance(items, list) else [items]
        for i, it in enumerate(items):
            par = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
            opts = {}
            if isinstance(it, tuple):
                it, opts = it
            if bullet and not opts.get("nobullet"):
                run = par.add_run()
                run.text = "•  "
                run.font.size, run.font.name = Pt(opts.get("size", size)), FONT
                run.font.color.rgb = rgb(TEAL)
            parts = it.split("**")  # **bold** segments
            for k, seg in enumerate(parts):
                if not seg:
                    continue
                run = par.add_run()
                run.text = seg
                run.font.size = Pt(opts.get("size", size))
                run.font.bold = opts.get("bold", bold) or (k % 2 == 1)
                run.font.name = FONT
                run.font.color.rgb = rgb(opts.get("color", color))
            if align or opts.get("align"):
                par.alignment = opts.get("align", align)
            par.space_after = Pt(opts.get("space", spacing))
        return tb

    def box(sl, x, y, w_, h, fill=WHITE, line=RULE, lw=1.25, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.06):
        sh = sl.shapes.add_shape(shape, Inches(x), Inches(y), Inches(w_), Inches(h))
        if shape == MSO_SHAPE.ROUNDED_RECTANGLE:
            sh.adjustments[0] = radius
        if fill:
            sh.fill.solid()
            sh.fill.fore_color.rgb = rgb(fill)
        else:
            sh.fill.background()
        if line:
            sh.line.color.rgb = rgb(line)
            sh.line.width = Pt(lw)
        else:
            sh.line.fill.background()
        sh.shadow.inherit = False
        sh.text_frame.text = ""
        return sh

    def arrow(sl, x1, y1, x2, y2, color=SLATE, lw=1.75, dash=False):
        c = sl.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(x1), Inches(y1), Inches(x2), Inches(y2))
        c.line.color.rgb = rgb(color)
        c.line.width = Pt(lw)
        ln = c.line._get_or_add_ln()
        if dash:
            ln.append(etree.SubElement(ln, qn("a:prstDash"), val="dash"))
        ln.append(etree.SubElement(ln, qn("a:tailEnd"), type="triangle", w="med", len="med"))
        return c

    def card(sl, x, y, w_, h, title, body, accent=TEAL, fill=WHITE, kicker=None, tsize=16, bsize=12.5):
        box(sl, x, y, w_, h, fill=fill, line=accent, lw=1.5)
        yy = y + 0.12
        if kicker:
            text(sl, x + 0.15, yy, w_ - 0.3, 0.3, kicker, size=10, color=accent, bold=True)
            yy += 0.28
        text(sl, x + 0.15, yy, w_ - 0.3, 0.4, title, size=tsize, color=NAVY, bold=True)
        text(sl, x + 0.15, yy + 0.42, w_ - 0.3, h - (yy - y) - 0.5, body, size=bsize, color=MUTED, spacing=3)

    def stat(sl, x, y, w_, value, label, color=TEAL, vsize=30):
        text(sl, x, y, w_, 0.6, value, size=vsize, color=color, bold=True)
        text(sl, x, y + 0.62, w_, 0.8, label, size=11.5, color=MUTED, spacing=2)

    def table(sl, x, y, w_, rows, widths, size=11.5, header_fill=NAVY, row_h=0.36):
        shape = sl.shapes.add_table(len(rows), len(rows[0]), Inches(x), Inches(y), Inches(w_), Inches(row_h * len(rows)))
        tbl = shape.table
        tbl.first_row = True
        for j, wd in enumerate(widths):
            tbl.columns[j].width = Inches(wd)
        for i, row in enumerate(rows):
            for j, val in enumerate(row):
                cell = tbl.cell(i, j)
                cell.text = str(val)
                cell.margin_left = cell.margin_right = Inches(0.08)
                cell.margin_top = cell.margin_bottom = Inches(0.03)
                cell.fill.solid()
                cell.fill.fore_color.rgb = rgb(header_fill if i == 0 else (LIGHT if i % 2 == 0 else WHITE))
                for par in cell.text_frame.paragraphs:
                    para_fmt(par, size, WHITE if i == 0 else NAVY, bold=(i == 0 or j == 0))
        return shape

    def bars(sl, x, y, w_, h, cats, series, colors, fmt="0.00", maxv=1.0, legend=True, horizontal=False, label_size=11):
        cd = CategoryChartData()
        cd.categories = cats
        for name, vals in series:
            cd.add_series(name, vals)
        kind = XL_CHART_TYPE.BAR_CLUSTERED if horizontal else XL_CHART_TYPE.COLUMN_CLUSTERED
        ch = sl.shapes.add_chart(kind, Inches(x), Inches(y), Inches(w_), Inches(h), cd).chart
        ch.font.size, ch.font.name = Pt(11), FONT
        ch.font.color.rgb = rgb(SLATE)
        ch.has_legend = legend and len(series) > 1
        if ch.has_legend:
            ch.legend.position, ch.legend.include_in_layout = XL_LEGEND_POSITION.BOTTOM, False
        va = ch.value_axis
        va.maximum_scale, va.minimum_scale = maxv, 0
        va.has_major_gridlines = True
        va.major_gridlines.format.line.color.rgb = rgb("E3E9EE")
        va.format.line.fill.background()
        va.tick_labels.font.size = Pt(10)
        ch.category_axis.tick_labels.font.size = Pt(11)
        ch.category_axis.format.line.color.rgb = rgb(RULE)
        plot = ch.plots[0]
        plot.gap_width, plot.overlap = 60, -10
        plot.has_data_labels = True
        dl = plot.data_labels
        dl.number_format, dl.number_format_is_linked = fmt, False
        dl.font.size, dl.font.color.rgb = Pt(label_size), rgb(NAVY)
        dl.position = XL_LABEL_POSITION.OUTSIDE_END
        for i, sr in enumerate(plot.series):
            sr.format.fill.solid()
            sr.format.fill.fore_color.rgb = rgb(colors[i % len(colors)])
        return ch

    def mark(sl, x, y, size, ink=NAVY):
        """Uplift's mark: a weekly-activity line that dips and climbs from a yellow diamond, over a baseline."""
        u = size / 24.0
        pts = [(1.5, 8.5), (4.5, 7.5), (8.5, 15), (12, 11.5), (14.5, 12.5), (22.5, 3)]
        fb = sl.shapes.build_freeform(Inches(x + pts[0][0] * u), Inches(y + pts[0][1] * u), scale=1.0)
        fb.add_line_segments([(Inches(x + px * u), Inches(y + py * u)) for px, py in pts[1:]], close=False)
        line = fb.convert_to_shape()
        line.fill.background()
        line.line.color.rgb, line.line.width = rgb(ink), Pt(max(1.5, size * 2.6))
        base = sl.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(x + 1.5 * u), Inches(y + 21.5 * u), Inches(x + 22.5 * u),
                                       Inches(y + 21.5 * u))
        base.line.color.rgb, base.line.width = rgb(ink), Pt(max(0.75, size * 1.1))
        dmd = sl.shapes.add_shape(MSO_SHAPE.DIAMOND, Inches(x + 5.3 * u), Inches(y + 11.8 * u), Inches(6.4 * u), Inches(6.4 * u))
        dmd.fill.solid()
        dmd.fill.fore_color.rgb = rgb(YELLOW)
        dmd.line.fill.background()

    def slide(kicker, title, message=None, notes="", dark=False):
        state["n"] += 1
        sl = prs.slides.add_slide(blank)
        sl.background.fill.solid()
        sl.background.fill.fore_color.rgb = rgb(NAVY if dark else WHITE)
        if not dark:
            box(sl, 0, 0, 0.16, 7.5, fill=NAVY, line=None, shape=MSO_SHAPE.RECTANGLE)
            text(sl, 0.6, 0.32, 9, 0.3, kicker.upper(), size=11, color=TEAL, bold=True)
            text(sl, 0.6, 0.58, 12.1, 0.7, title, size=28, color=NAVY, bold=True)
            if message:
                text(sl, 0.6, 1.25, 12.1, 0.5, message, size=15, color=MUTED)
            line = sl.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(0.6), Inches(7.05), Inches(12.75), Inches(7.05))
            line.line.color.rgb, line.line.width = rgb(RULE), Pt(0.75)
            mark(sl, 0.6, 7.13, 0.22)
            text(sl, 0.9, 7.12, 6, 0.3, "Uplift · Student Success Assistant", size=9.5, color=MUTED)
            text(sl, 11.6, 7.12, 1.15, 0.3, str(state["n"]), size=9.5, color=MUTED, align=PP_ALIGN.RIGHT)
        if notes:
            sl.notes_slide.notes_text_frame.text = notes
        return sl

    hi = w.get("test_tiers", {}).get("High", {})
    tc = p.get("test_comparison", {})
    dl = ag.get("deepeval", {}).get("aggregate", {})
    rb = r.get("modes", {})
    typed = ts.get("parsers", {}).get("llm", {}).get("modes", {}).get("hybrid", {}).get("precision_at_10")
    shots = PROJECT_ROOT / "docs" / "screenshots"
    arch = PROJECT_ROOT / "architecture" / "Architecture_Diagram.png"

    # 1 ---------------------------------------------------------------- title
    sl = slide("", "", dark=True, notes="Uplift is an AI student-success assistant for Open University module teams. It finds students "
               "who may withdraw or fail while there is still time, shows what happened to similar students before, and drafts a "
               "supportive plan that an advisor reviews.")
    mark(sl, 0.9, 1.35, 0.9, ink=WHITE)
    text(sl, 2.0, 1.25, 10, 1.0, "Uplift", size=60, color=WHITE, bold=True)
    text(sl, 0.9, 2.65, 11.5, 0.8, "AI-Powered Student Success Assistant", size=32, color=WHITE)
    text(sl, 0.9, 3.5, 11.5, 0.9, "Early warning, similar past students and supportive action plans for Open University module "
         "teams: hybrid RAG, a multi-agent workflow, calibrated prediction models and LLM-as-judge evaluation.", size=17, color="C9D7E2")
    box(sl, 0.9, 4.75, 3.6, 0.06, fill=YELLOW, line=None, shape=MSO_SHAPE.RECTANGLE)
    text(sl, 0.9, 5.0, 11.5, 0.4, "Capstone project · Education domain · Open University Learning Analytics Dataset (OULAD)",
         size=14, color="C9D7E2")
    text(sl, 0.9, 5.4, 11.5, 0.4, "Nishanth", size=16, color=WHITE, bold=True)

    # 2 ---------------------------------------------------------------- problem
    sl = slide("Problem statement", "Advisors cannot read thousands of records in time",
               "Students who disengage or fall behind are found too late, and dashboards say who, not why or what to do.",
               notes="Advisors have thousands of records and little time. The brief asks three questions: have similar students "
                     "struggled before, which factors are behind poor outcomes, and who should be supported first.")
    text(sl, 0.6, 1.95, 5.6, 4.6, [
        "Module teams hold rich data: profiles, assessment results, daily online activity, registration history, outcomes.",
        "Reviewing it by hand is slow and inconsistent; warning signs are spread across tables and weeks.",
        "By the time a student formally withdraws, it is too late to help: "
        f"**{_pct(pa.get('already_withdrawn_share_of_test_withdrawals'))}** of withdrawals in the test presentation happened "
        f"before week {pw}.",
        "Teams need early, explainable, prioritised and supportive guidance, with evidence."], size=16, bullet=True, spacing=12)
    for i, (k, qq, a) in enumerate([
            ("Q1", "Has a student with similar patterns struggled or withdrawn before?", "Hybrid RAG over historical cases"),
            ("Q2", "What factors are associated with poor performance or withdrawal?", "Explainable models and insights"),
            ("Q3", "Which students should be prioritised for support?", "Capacity-aware ranking and agent plans")]):
        y = 1.95 + i * 1.6
        box(sl, 6.7, y, 6.05, 1.38, fill=TEAL_BG, line=TEAL, lw=1.25)
        text(sl, 6.9, y + 0.14, 0.8, 0.5, k, size=22, color=TEAL, bold=True)
        text(sl, 7.7, y + 0.12, 4.9, 0.7, qq, size=14.5, color=NAVY, bold=True)
        text(sl, 7.7, y + 0.86, 4.9, 0.4, a, size=12.5, color=MUTED)

    # 3 ---------------------------------------------------------------- business need
    sl = slide("Business need", "Reach the right students early, with reasons",
               "Capacity is limited, so the top of the list must be right, and every recommendation must be defensible.",
               notes="Early contact is what changes outcomes, but capacity is limited: if an advisor can call 10% of a cohort, the "
                     "list must be right at the top. Advisors also need reasons they can defend and supportive messages.")
    stats = [(f"{d.get('in_scope_records', 0):,}", f"students still enrolled at week {pw} (all modules)", NAVY),
             (_pct(t.get("positive_rate"), 1), "of them will still withdraw: the students an early warning can help", RED),
             (_pct(tc.get("learned_weights", {}).get("at_capacity", [{}])[0].get("precision")),
              "of students contacted from the top 10% later fail or withdraw (random: "
              f"{_pct(tc.get('random', {}).get('at_capacity', [{}])[0].get('precision'))})", TEAL),
             (_pct(hi.get("share_of_all_withdrawals")), f"of withdrawals are in the High tier, which flags {_pct(hi.get('share'))} of students",
              ORANGE)]
    for i, (v, lab, col) in enumerate(stats):
        stat(sl, 0.6 + i * 3.1, 2.0, 2.8, v, lab, color=col, vsize=34)
    needs = [("Early", f"warnings from week {weeks[0]}, not after the student has gone"),
             ("Explainable", "drivers per student and what happened to similar students"),
             ("Capacity-aware", "a ranked list for the time advisors actually have"),
             ("Supportive and safe", "never punitive, no sensitive attributes, human review"),
             ("Measurable", "every model and AI output evaluated, cost tracked")]
    for i, (k, v) in enumerate(needs):
        y = 4.0 + i * 0.56
        box(sl, 0.6, y, 0.12, 0.38, fill=TEAL, line=None, shape=MSO_SHAPE.RECTANGLE)
        text(sl, 0.85, y - 0.02, 12, 0.45, f"**{k}**: {v}", size=15)

    # 4 ---------------------------------------------------------------- solution overview
    sl = slide("Solution overview", "One console, six capabilities, as of a course week",
               f"Built at weeks {', '.join(map(str, weeks))}; only students still enrolled are scored. The LLM narrates, code decides facts.",
               notes="Early warning with reasons, a ranked contact list, similar historical students, a multi-agent support plan "
                     "with an outreach draft, a copilot, and evaluation with a feedback loop.")
    caps = [("01", "Early warning", "Calibrated withdrawal risk, tier, TreeSHAP drivers and outcome probabilities", TEAL),
            ("02", "Who to contact first", "Ranking learned for advisor capacity, with the reasons for each student", TEAL),
            ("03", "Similar students (RAG)", "Hybrid search over past cohorts by student or plain English, with metadata filters", GREEN),
            ("04", "Support plan (agents)", "LangGraph agents: performance, risk, intervention, critic; outreach draft", PURPLE),
            ("05", "Copilot", "Questions answered by tool calls over the same computed functions, streamed and checked", PURPLE),
            ("06", "Insights and evaluation", "Factors, trends, fairness; DeepEval, RAGAS, judge; approved updates", ORANGE)]
    for i, (n, ttl, body, col) in enumerate(caps):
        x, y = 0.6 + (i % 3) * 4.1, 2.0 + (i // 3) * 2.45
        box(sl, x, y, 3.85, 2.2, fill=WHITE, line=col, lw=1.5)
        text(sl, x + 0.2, y + 0.15, 1, 0.4, n, size=13, color=col, bold=True)
        text(sl, x + 0.2, y + 0.5, 3.5, 0.5, ttl, size=18, color=NAVY, bold=True)
        text(sl, x + 0.2, y + 1.05, 3.5, 1.1, body, size=13, color=MUTED)

    # 5 ---------------------------------------------------------------- architecture
    sl = slide("Architecture", "Offline build per checkpoint, online agents behind FastAPI",
               notes="Bottom: dataset, preprocessing, one document per enrolment, embeddings, LanceDB plus BM25, model training. "
                     "Middle: React console, FastAPI with input guardrails, the LangGraph workflow. Claude drafts text; code "
                     "decides facts; every step has a computed fallback. Evaluation and the feedback loop alongside.")
    if arch.exists():
        sl.shapes.add_picture(str(arch), Inches(0.75), Inches(1.32), width=Inches(11.85))

    # 6 ---------------------------------------------------------------- data flow
    sl = slide("Data flow", "From seven OULAD tables to a checked support plan",
               "Only data dated before the checkpoint is used, and only students still enrolled are scored.",
               notes="OULAD becomes snapshot features at each checkpoint. Scoring students who already left would inflate ROC-AUC "
                     f"to {_f(pa.get('all_enrolments_including_already_withdrawn', {}).get('roc_auc'))} instead of {_f(t.get('roc_auc'))}.")
    text(sl, 0.6, 1.9, 6, 0.3, "OFFLINE  ·  python -m src.cli build", size=11, color=SLATE, bold=True)
    off = [("Dataset", "7 CSV tables"), ("Preprocess", "snapshot features, in scope"), ("Chunk", "1 enrolment = 1 case"),
           ("Embed", "e5-small-v2 + behavioural"), ("Index", "LanceDB + BM25"), ("Train", "XGBoost, calibrate, SHAP")]
    for i, (a, b) in enumerate(off):
        x = 0.6 + i * 2.07
        box(sl, x, 2.25, 1.8, 1.05, fill=LIGHT, line=SLATE, lw=1.25)
        text(sl, x + 0.08, 2.32, 1.65, 0.4, a, size=14, color=NAVY, bold=True, align=PP_ALIGN.CENTER)
        text(sl, x + 0.08, 2.72, 1.65, 0.55, b, size=11, color=MUTED, align=PP_ALIGN.CENTER)
        if i:
            arrow(sl, x - 0.27, 2.78, x - 0.03, 2.78)
    text(sl, 0.6, 3.6, 6, 0.3, "ONLINE  ·  draft a support plan for one student", size=11, color=TEAL, bold=True)
    on = [("Console", "POST /api/jobs/analyze"), ("Validate", "schema, scope, auth"), ("Score", "risk, outcome, drivers"),
          ("Retrieve", "6 cases + outcome mix of 50"), ("Agents", "LangGraph, critic, fallback"), ("Plan", "streamed, labelled, feedback")]
    for i, (a, b) in enumerate(on):
        x = 0.6 + i * 2.07
        box(sl, x, 3.95, 1.8, 1.05, fill=TEAL_BG, line=TEAL, lw=1.25)
        text(sl, x + 0.08, 4.02, 1.65, 0.4, a, size=14, color=NAVY, bold=True, align=PP_ALIGN.CENTER)
        text(sl, x + 0.08, 4.42, 1.65, 0.55, b, size=11, color=MUTED, align=PP_ALIGN.CENTER)
        if i:
            arrow(sl, x - 0.27, 4.48, x - 0.03, 4.48, color=TEAL)
    box(sl, 0.6, 5.35, 12.15, 1.45, fill=ORANGE_BG, line=ORANGE, lw=1.25)
    text(sl, 0.85, 5.45, 11.7, 0.4, "The leakage rule", size=15, color=ORANGE, bold=True)
    text(sl, 0.85, 5.85, 11.7, 0.95,
         f"Scoring every enrolment, including students who had already left, gives ROC-AUC "
         f"**{_f(pa.get('all_enrolments_including_already_withdrawn', {}).get('roc_auc'))}**. Scoring only students still enrolled "
         f"gives **{_f(t.get('roc_auc'))}**: lower, but it is the number an advisor actually gets. `date_unregistration` defines "
         "scope only; it is never a feature.", size=13.5, color=NAVY)

    # 7 ---------------------------------------------------------------- technology stack
    sl = slide("Technology stack", "Each choice was measured or justified against an alternative",
               notes="Claude in three tiers by measured need; e5-small-v2 won a five-model comparison; LanceDB embedded with "
                     "filters pushed into the search; LangGraph for the agent graph; XGBoost with TreeSHAP; FastAPI and React.")
    em = e.get("models", {})
    rows = [["Layer", "Choice", "Why"],
            ["LLM", f"Claude: {em.get('fast', '')} · {em.get('main', '')} · {em.get('judge', '')} (judge)",
             "Measured per task: small model parses as well; main model writes most faithfully; different judge"],
            ["Embeddings", "intfloat/e5-small-v2", "Best of five models on precedent quality at MiniLM latency"],
            ["Vector DB", "LanceDB (embedded)", "No server; metadata pre-filter; exact kNN; parity with brute force"],
            ["Agents", "LangGraph state graph", "Explicit router, critic and revision; parity with plain Python"],
            ["Prediction", "XGBoost + calibration + TreeSHAP", f"ROC-AUC {_f(t.get('roc_auc'))} vs {_f(w.get('baseline_logistic_regression_test', {}).get('roc_auc'))} logistic; exact explanations"],
            ["Retrieval", "BM25 + behavioural kNN + dense, RRF", "Numbers need numeric similarity; text needs keywords and meaning"],
            ["API", "FastAPI + Uvicorn, pydantic", "Typed validation, OpenAPI docs, streaming, background jobs"],
            ["UI", "React 19 + TypeScript (Vite)", "Beyond Streamlit: URLs, virtual tables, streaming; served by FastAPI"],
            ["Evaluation", "DeepEval · RAGAS · LLM judge · pytest", "Each layer catches a different failure"]]
    table(sl, 0.6, 1.4, 12.15, rows, [1.6, 4.1, 6.45], size=12, row_h=0.5)

    # 8 ---------------------------------------------------------------- agent workflow
    sl = slide("Agent workflow", "Agents on a shared state; code checks every draft",
               "Agents cite numbered evidence; the critic rejects unknown IDs, ineligible actions, ungrounded numbers and unsafe words.",
               notes="Performance and risk agents, a router, the intervention agent choosing 2 to 4 eligible actions and drafting "
                     "the message, a critic in code, one revision, then a deterministic fallback. Precedent synthesis afterwards.")
    nodes = [("Evidence", "scores · drivers\n6 similar cases", GREEN, GREEN_BG), ("Performance", "strengths, concerns", PURPLE, PURPLE_BG),
             ("Risk", "risk, precedents,\nuncertainty", PURPLE, PURPLE_BG), ("Router", "intervene or\nmonitor (rule)", SLATE, LIGHT),
             ("Intervention", "2-4 eligible actions\noutreach draft", PURPLE, PURPLE_BG), ("Critic", "IDs, numbers,\nterms (code)", SLATE, LIGHT),
             ("Synthesis", "what happened\nnext (RAG)", PURPLE, PURPLE_BG)]
    nx = [0.6 + i * 1.77 for i in range(len(nodes))]
    for i, (a, b, col, fill) in enumerate(nodes):
        box(sl, nx[i], 2.2, 1.55, 1.4, fill=fill, line=col, lw=1.5)
        text(sl, nx[i] + 0.05, 2.3, 1.45, 0.4, a, size=14, color=NAVY, bold=True, align=PP_ALIGN.CENTER)
        text(sl, nx[i] + 0.05, 2.75, 1.45, 0.8, b, size=10.5, color=MUTED, align=PP_ALIGN.CENTER)
        if i:
            arrow(sl, nx[i] - 0.2, 2.9, nx[i] - 0.02, 2.9, color=TEAL)
    box(sl, nx[4] + 0.1, 3.85, 3.05, 0.55, fill=ORANGE_BG, line=ORANGE, lw=1.25)
    text(sl, nx[4] + 0.15, 3.9, 2.95, 0.5, "violations → revise once, else fallback", size=11, color=ORANGE, bold=True,
         align=PP_ALIGN.CENTER)
    box(sl, nx[3] - 0.05, 4.6, 4.4, 0.55, fill=LIGHT, line=SLATE, lw=1.0)
    text(sl, nx[3], 4.65, 4.3, 0.5, "monitor / failed checks → deterministic planner", size=11, color=SLATE,
         align=PP_ALIGN.CENTER)
    text(sl, 0.6, 4.55, 4.7, 2.2, [
        "**Purple** = Claude drafts (structured JSON output)",
        "**Grey** = code only, deterministic",
        "**Green** = ML models and hybrid retriever",
        "Every LLM step has a computed fallback: the workflow runs with the LLM switched off."], size=12.5, spacing=6)
    det = ag.get("deterministic", {})
    stat(sl, 10.6, 4.55, 2.15, _pct(det.get("final_plan_valid_rate")), "plans pass every guardrail", color=GREEN)
    stat(sl, 10.6, 5.75, 2.15, _pct(ag.get("judge", {}).get("pass_rate")), f"judge pass rate ({em.get('judge', '')})", color=PURPLE)

    # 9 ---------------------------------------------------------------- hybrid RAG
    sl = slide("Hybrid RAG", "Three channels, fused with RRF, filtered in LanceDB",
               "Earlier presentations only, never the student's own rows; one document per enrolment; numbers banded, not embedded.",
               notes="Behavioural vectors weighted by what predicts outcomes, BM25 over descriptor tokens, e5 dense embeddings of "
                     "narratives; weighted reciprocal rank fusion; filters pushed into LanceDB.")
    chans = [("Behavioural kNN", "snapshot features weighted by the model's attributions", GREEN),
             ("BM25 keywords", "descriptor tokens: missed_most, engagement_declining ...", TEAL),
             ("Dense (e5-small-v2)", "narratives for plain-English search", PURPLE)]
    for i, (a, b, col) in enumerate(chans):
        y = 1.95 + i * 1.08
        box(sl, 0.6, y, 4.3, 0.92, fill=WHITE, line=col, lw=1.5)
        text(sl, 0.75, y + 0.06, 4.0, 0.4, a, size=14, color=NAVY, bold=True)
        text(sl, 0.75, y + 0.45, 4.0, 0.45, b, size=11, color=MUTED)
        arrow(sl, 4.9, y + 0.46, 5.35, 3.07, color=col)
    box(sl, 5.38, 2.62, 1.3, 0.9, fill=TEAL_BG, line=TEAL, lw=1.5)
    text(sl, 5.4, 2.7, 1.26, 0.8, ["RRF", ("fusion", {"size": 11, "bold": False, "color": MUTED})], size=16, color=NAVY, bold=True,
         align=PP_ALIGN.CENTER, spacing=0)
    text(sl, 0.6, 5.3, 6.2, 1.6, [
        "Metadata filters: course, region, education, age band, credits, previous attempts, outcome",
        "Plain English understood as filters + behaviours (Claude Haiku, rule fallback)",
        "Context: 6 closest stories; outcome mix of the 50 nearest"], size=12.5, bullet=True, spacing=4)
    modes = [m_ for m_ in ("hybrid", "behavioural", "lexical", "dense", "random") if m_ in rb]
    bars(sl, 7.0, 1.85, 5.75, 3.6, modes, [("Neighbour-vote AUC (fail or withdraw)", [rb[m_]["neighbour_vote_auc_poor_outcome"] for m_ in modes])],
         [GREEN], legend=False)
    text(sl, 7.0, 5.45, 5.75, 0.6, f"Do the retrieved students' real outcomes predict this student's? {r.get('queries', '')} test "
         "students vs earlier cohorts (not circular).", size=11.5, color=MUTED)
    stat(sl, 7.0, 6.0, 5.7, _f(typed), "precision@10, plain-English case search (AI parser)", color=TEAL, vsize=22)

    # 10 --------------------------------------------------------------- prediction models
    sl = slide("Prediction models", "Calibrated risk that holds on a later, untouched cohort",
               f"Trained on {' + '.join(w.get('split', {}).get('train', []))}, tuned on {', '.join(w.get('split', {}).get('validation', []))}, "
               f"tested once on {', '.join(w.get('split', {}).get('test', []))}.",
               notes="ROC-AUC on a later presentation, calibrated, the High tier catches half the withdrawals; accuracy rises "
                     "through the course while fewer students remain to help.")
    stat(sl, 0.6, 1.95, 2.9, _f(t.get("roc_auc")), f"ROC-AUC at week {pw} (95% CI {_f(t.get('roc_auc_95ci', {}).get('lower'))} to "
         f"{_f(t.get('roc_auc_95ci', {}).get('upper'))})", color=NAVY)
    stat(sl, 0.6, 3.25, 2.9, _f(w.get("baseline_logistic_regression_test", {}).get("roc_auc")), "logistic regression baseline", color=SLATE)
    stat(sl, 3.5, 1.95, 2.9, _f(t.get("ece_10")), "calibration error: a 20% risk means about 20%", color=TEAL)
    stat(sl, 3.5, 3.25, 2.9, f"{_f(t.get('pr_auc'))}", f"PR-AUC vs base rate {_f(t.get('positive_rate'))}", color=TEAL)
    tiers = w.get("test_tiers", {})
    rows = [["Tier", "Share of students", "Observed withdrawal rate", "Share of withdrawals"]] + [
        [k, _pct(v.get("share")), _pct(v.get("observed_withdrawal_rate"), 1), _pct(v.get("share_of_all_withdrawals"))] for k, v in tiers.items()]
    table(sl, 0.6, 4.65, 5.9, rows, [1.1, 1.5, 1.8, 1.5], size=11.5)
    if cs:
        bars(sl, 6.8, 1.85, 5.95, 3.9, [f"week {course_week(c['checkpoint'])}" for c in cs],
             [("ROC-AUC", [c["withdrawal"]["roc_auc"] for c in cs]), ("PR-AUC", [c["withdrawal"]["pr_auc"] for c in cs]),
              ("Share who later withdraw", [c["withdrawal"]["positive_rate"] for c in cs])], [NAVY, TEAL, "9FB3C3"])
    text(sl, 6.8, 5.8, 5.95, 1.0, f"Outcome model macro-F1 {_f(o.get('test', {}).get('macro_f1'))} (logistic "
         f"{_f(o.get('baselines_test', {}).get('multinomial_logistic', {}).get('macro_f1'))}); P(fail or withdraw) ROC-AUC "
         f"{_f(o.get('poor_outcome_from_p_fail_plus_p_withdrawn_test', {}).get('roc_auc'))}. Ranking precision at 10%: "
         f"{_pct(tc.get('learned_weights', {}).get('at_capacity', [{}])[0].get('precision'))}.", size=11.5, color=MUTED)

    # 11 --------------------------------------------------------------- demo
    sl = slide("Demo", "Live: week, student, support plan, case search, copilot",
               notes="Follow the demo script in docs/Presentation_Guide: This week, student case file and support plan, case "
                     "finder, copilot, model quality.")
    for i, (name, cap) in enumerate([("student", "Student case file: why flagged, risk across the course, support plan"),
                                     ("copilot", "Copilot: tool calls, streamed answer, every number checked")]):
        f = shots / f"{name}.jpg"
        if f.exists():
            x = 0.6 + i * 6.15
            sl.shapes.add_picture(str(f), Inches(x), Inches(1.45), width=Inches(5.95))
            text(sl, x, 5.25, 5.95, 0.4, cap, size=12, color=MUTED)
    steps = ["uvicorn src.main:app --reload  →  http://127.0.0.1:8000", "This week: course clock, week 5 → 15, who to reach first",
             "Student: drivers, risk trail, Draft a support plan (agent steps), rewrite as SMS", "Case finder: plain-English search",
             "Copilot: 'Who should I contact first in BBB 2014J?'"]
    text(sl, 0.6, 5.7, 12.15, 1.3, [f"{i + 1}. {st}" for i, st in enumerate(steps)], size=12.5, spacing=2)

    # 12 --------------------------------------------------------------- evaluation results
    sl = slide("Evaluation results", "Five layers of evaluation, each catching what the others miss",
               f"AI evaluation: generators {em.get('main', '')} / {em.get('fast', '')}; judge {em.get('judge', '')}; release gate "
               f"{'passed' if q.get('passed') else 'failed'}.",
               notes="Code checks on every output; LLM-as-judge with an order-swapped A/B; DeepEval; RAGAS; human review and tests.")
    pair = ag.get("pairwise_llm_vs_deterministic", {})
    rows = [["Layer", "Measure", "Result"],
            ["1 Code checks", "plans passing every guardrail", _pct(det.get("final_plan_valid_rate"))],
            ["2 LLM-as-judge", "judge pass rate · AI plan preferred (order-swapped A/B)",
             f"{_pct(ag.get('judge', {}).get('pass_rate'))} · {_pct(pair.get('llm_win_rate'))}"],
            ["3 DeepEval", "faithfulness · answer relevancy · actionable (pass rate)",
             f"{_pct(dl.get('FaithfulnessMetric', {}).get('pass_rate'))} · {_pct(dl.get('AnswerRelevancyMetric', {}).get('pass_rate'))} · "
             f"{_pct(dl.get('Actionable for an advisor', {}).get('pass_rate'))}"],
            ["4 RAGAS", "faithfulness of precedent synthesis (hallucination rate)",
             f"{_f(rg.get('precedent_synthesis', {}).get('mean', {}).get('faithfulness'))} "
             f"({_pct(rg.get('precedent_synthesis', {}).get('hallucination_rate'), 1)})"],
            ["5 Copilot", "golden questions correct · adversarial prompts handled safely",
             f"{_pct(e.get('copilot', {}).get('llm', {}).get('answer_correct_rate'))} · {_pct(e.get('robustness', {}).get('safe_rate'))}"],
            ["Retrieval", "neighbour-vote AUC hybrid vs random",
             f"{_f(rb.get('hybrid', {}).get('neighbour_vote_auc_poor_outcome'))} vs {_f(rb.get('random', {}).get('neighbour_vote_auc_poor_outcome'))}"],
            ["Tests", "pytest suite: no network, no LLM", f"{n_tests} tests" if n_tests else "python -m pytest"]]
    table(sl, 0.6, 1.95, 7.2, rows, [1.65, 3.85, 1.7], size=11.5, row_h=0.52)
    names = [k for k in dl][:5]
    bars(sl, 8.1, 1.85, 4.65, 4.6, [n.replace("Metric", "").replace("Actionable for an advisor", "Actionable")
                                    .replace("No protected-attribute reasoning", "No protected attr.")
                                    .replace("Supportive and non-punitive", "Supportive") for n in names],
         [("DeepEval mean score", [dl[n]["mean"] for n in names])], [PURPLE], legend=False, horizontal=True, label_size=10)
    text(sl, 8.1, 6.45, 4.65, 0.5, "DeepEval mean scores (0 to 1)", size=11, color=MUTED, align=PP_ALIGN.CENTER)

    # 13 --------------------------------------------------------------- responsible AI
    sl = slide("Responsible AI", "Supportive by design, checked in code, fair by audit",
               notes="Sensitive attributes never model inputs and never sent to the LLM; every output checked for protected, "
                     "punitive and clinical wording; fairness gaps tested against chance and reported.")
    card(sl, 0.6, 1.5, 3.9, 2.55, "Input guardrails", ["API key and admin key", "Rate limit, request-size limit",
                                                         "Strict schemas and vocabularies", "Prompt-injection screening"], accent=NAVY)
    card(sl, 4.72, 1.5, 3.9, 2.55, "Output guardrails", ["IDs must exist, numbers must be in the evidence",
                                                          "Only eligible, supportive actions", "No protected, punitive, clinical or stigma terms",
                                                          "Revise once, else computed fallback"], accent=PURPLE)
    card(sl, 8.85, 1.5, 3.9, 2.55, "Human in the loop", ["AI text labelled; advisor edits every message", "Never for grading, admissions or sanctions",
                                                          "Feedback changes nothing until approved"], accent=GREEN)
    cost = ab.get("cost_of_excluding_sensitive_attributes", {}).get("roc_auc")
    dis = fa.get("attributes", {}).get("disability", {})
    text(sl, 0.6, 4.35, 12.15, 2.5, [
        f"**Sensitive attributes** (gender, region, deprivation, age, education, disability) are never model inputs and never sent "
        f"to the LLM; adding them would change ROC-AUC by only {_f(cost)}.",
        "**Fairness audit**: each group gap is tested against the gap random labels would give at the same group sizes "
        "(permutation test, overall and within module).",
        f"Region and deprivation gaps are within chance. The disability gap ({_f(dis.get('equal_opportunity_gap'), 2)}) is real and "
        "reported, with a per-group threshold review for the equity office, not applied automatically."], size=14, bullet=True, spacing=8)

    # 14 --------------------------------------------------------------- challenges and learnings
    sl = slide("Challenges and learnings", "What was hard, and what changed because of it",
               notes="Honest evaluation first; numbers do not belong in text embeddings; LLM narrates, code decides; reject "
                     "improvements that do not hold on the test set.")
    rows = [["Challenge", "What we did", "Learning"],
            ["Inflated accuracy (0.90 AUC) from scoring students who had left", "Score in-scope students only; temporal split",
             "Evaluate the decision the user actually faces"],
            ["Numbers in text made keyword and dense search random", "Band numbers into descriptors; numeric similarity in its own channel",
             "Hybrid retrieval must match the data type"],
            ["LLM drafts invented numbers and IDs", "Evidence IDs, code checks, one revision, fallback",
             "Let the LLM narrate and select; code decides facts"],
            ["Self-grading and position bias", "Different judge model, computed verdict, order-swapped A/B, human review",
             "Evaluate the evaluator"],
            ["Validation gains that did not hold on test", "Rejected the feature set instead of tuning on test",
             "Keep the test set untouched"],
            ["RAGAS dependencies broke the pinned service", "RAGAS in its own environment", "Isolate evaluation tooling"]]
    table(sl, 0.6, 1.45, 12.15, rows, [4.0, 4.3, 3.85], size=12, row_h=0.72)

    # 15 --------------------------------------------------------------- thank you
    sl = slide("", "", dark=True, notes="Invite questions; offer to show any part live.")
    mark(sl, 0.9, 1.6, 0.8, ink=WHITE)
    text(sl, 1.9, 1.5, 10, 1.0, "Thank you", size=54, color=WHITE, bold=True)
    text(sl, 0.9, 2.85, 11.5, 0.6, "Questions, or a live look at any part of Uplift.", size=24, color="C9D7E2")
    box(sl, 0.9, 3.7, 3.6, 0.06, fill=YELLOW, line=None, shape=MSO_SHAPE.RECTANGLE)
    text(sl, 0.9, 4.0, 11.5, 2.4, [
        "Run it:  uvicorn src.main:app --reload   →   http://127.0.0.1:8000",
        "Architecture_Diagram.pdf · Design_Document.pdf · API_Documentation.pdf · Evaluation_Report.pdf · Dataset_Details.pdf",
        "API reference live at /api/docs  ·  model card: docs/MODEL_CARD.md"], size=15, color="C9D7E2", spacing=10)

    prs.save(str(out))
    return out
