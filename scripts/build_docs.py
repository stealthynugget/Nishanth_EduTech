"""Build the submission documents from the finished artifacts.

    python scripts/build_docs.py            # everything
    python scripts/build_docs.py --only design api

Every number in these documents is read from artifacts/ (metrics written by the build and the evaluations), from
docs/api/api_samples.json (real API calls, see scripts/capture_api_samples.py) or from the data files; templates hold
words only. Outputs (Markdown for GitHub, PDF for submission):

  architecture/Architecture_Diagram.{svg,pdf,png,jpeg}
  design/Design_Document.{md,pdf}
  docs/API_Documentation.{md,pdf}
  docs/Evaluation_Report.{md,pdf}
  docs/Dataset_Details.{md,pdf}
  docs/Presentation_Guide.{md,pdf}
  README.md

Needs requirements-docs.txt (Jinja2, Markdown, Playwright + Chromium: `python -m playwright install chromium`).
"""
from __future__ import annotations

import argparse
import ast
import json
import re
import subprocess
import sys
from pathlib import Path

import jinja2
import markdown

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.utils.config import course_week, get_settings  # noqa: E402

TEMPLATES = ROOT / "docs" / "templates"
OUTPUTS = {  # template -> markdown output (PDF next to it); title for the PDF header
    "design": ("Design_Document.md.j2", ROOT / "design" / "Design_Document.md", "Design Document"),
    "api": ("API_Documentation.md.j2", ROOT / "docs" / "API_Documentation.md", "API Documentation"),
    "evaluation": ("Evaluation_Report.md.j2", ROOT / "docs" / "Evaluation_Report.md", "Evaluation Report"),
    "dataset": ("Dataset_Details.md.j2", ROOT / "docs" / "Dataset_Details.md", "Dataset Details"),
    "guide": ("Presentation_Guide.md.j2", ROOT / "docs" / "Presentation_Guide.md", "Presentation Guide and Panel Q&A"),
    "readme": ("README.md.j2", ROOT / "README.md", None),
}


# ---------------------------------------------------------------- context
def _read(path: Path, default=None):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default


def _csv_rows(path: Path) -> int | None:
    if not path.exists():
        return None
    with path.open("rb") as f:
        return sum(1 for _ in f) - 1


def _csv_header(path: Path) -> list[str]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as f:
        return [c.strip().strip('"') for c in f.readline().strip().split(",")]


def _project_version() -> str:
    import tomllib
    return tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]["version"]


def _tests() -> list[dict]:
    """Test inventory: every test function with its file and first docstring line (static, no imports)."""
    out = []
    for f in sorted((ROOT / "tests").glob("test_*.py")):
        tree = ast.parse(f.read_text(encoding="utf-8"))
        for node in tree.body:
            if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
                doc = (ast.get_docstring(node) or "").strip().split("\n")[0]
                out.append({"file": f.name, "name": node.name, "doc": doc})
    return out


def _openapi() -> dict:
    from src.api.app import create_app
    return create_app().openapi()


# ---------------------------------------------------------------- API reference
def _schema_type(sch: dict, comps: dict) -> str:
    if "$ref" in sch:
        return sch["$ref"].split("/")[-1]
    if "anyOf" in sch:
        parts = [_schema_type(x, comps) for x in sch["anyOf"]]
        opt = "null" in parts
        parts = [p for p in parts if p != "null"]
        return " or ".join(parts) + (" (optional)" if opt else "")
    if "enum" in sch:
        return "one of " + ", ".join(f"`{v}`" for v in sch["enum"])
    if "const" in sch:
        return f"`{sch['const']}`"
    t = sch.get("type", "any")
    if t == "array":
        return f"array of {_schema_type(sch.get('items', {}), comps)}"
    if t == "object" and "additionalProperties" in sch and isinstance(sch["additionalProperties"], dict):
        return f"object of {_schema_type(sch['additionalProperties'], comps)}"
    return {"integer": "integer", "number": "number", "string": "string", "boolean": "boolean", "object": "object"}.get(t, t)


def _constraints(sch: dict) -> str:
    out = []
    for src in [sch, *sch.get("anyOf", [])]:
        for k, label in (("minimum", ">="), ("exclusiveMinimum", ">"), ("maximum", "<="), ("exclusiveMaximum", "<"),
                         ("minLength", "min length"), ("maxLength", "max length"), ("maxItems", "max items")):
            if k in src:
                out.append(f"{label} {src[k]}")
    if "default" in sch and sch["default"] is not None:
        out.append(f"default `{json.dumps(sch['default'])}`")
    return ", ".join(out)


def _fields(name: str, comps: dict, seen=None) -> list[dict]:
    """Rows for a request schema; nested models used by it are listed after it."""
    seen = seen if seen is not None else set()
    if name in seen or name not in comps:
        return []
    seen.add(name)
    sch = comps[name]
    req = set(sch.get("required", []))
    return [{"model": name, "field": f, "type": _schema_type(p, comps), "required": f in req, "constraints": _constraints(p),
             "description": p.get("description", "")} for f, p in sch.get("properties", {}).items()]


def _refs(name: str, comps: dict, seen: set) -> None:
    """Every model reachable from `name` (for the shared-models appendix)."""
    for p in comps.get(name, {}).get("properties", {}).values():
        for ref in re.findall(r'"\$ref": "#/components/schemas/([^"]+)"', json.dumps(p)):
            if ref not in seen:
                seen.add(ref)
                _refs(ref, comps, seen)


def _value_type(v) -> str:
    if v is None:
        return "null"
    if isinstance(v, bool):
        return "boolean"
    if isinstance(v, int):
        return "integer"
    if isinstance(v, float):
        return "number"
    if isinstance(v, str):
        return "string"
    if isinstance(v, list):
        return "array"
    return "object"


def api_operations(spec: dict, samples: dict, route_docs: dict, tags: list[dict]) -> list[dict]:
    comps = spec.get("components", {}).get("schemas", {})
    by_key = samples.get("samples", {})
    ops = []
    for path, methods in spec["paths"].items():
        for method, op in methods.items():
            m = method.upper()
            summary, desc = route_docs.get((m, path), (op.get("summary", ""), op.get("description", "")))
            params = [{"name": x["name"], "in": x["in"], "required": x.get("required", False),
                       "type": _schema_type(x.get("schema", {}), comps), "constraints": _constraints(x.get("schema", {})),
                       "description": x.get("description", "") or x.get("schema", {}).get("description", "")}
                      for x in op.get("parameters", [])]
            body_ref = op.get("requestBody", {}).get("content", {}).get("application/json", {}).get("schema", {}).get("$ref")
            body_model = body_ref.split("/")[-1] if body_ref else None
            related = [(k, v) for k, v in by_key.items() if v["path"] == path and v["method"] == m
                       or (k.startswith(f"{m} {path} (") and v["method"] == m)]
            if not related:  # templated paths (e.g. /api/students/{id_student}) are keyed by the template
                related = [(k, v) for k, v in by_key.items() if k == f"{m} {path}"]
            ok = [r for r in related if r[1]["status"] < 400] or related
            first = ok[0][1] if ok else None
            resp = first["response"] if first else None
            resp_fields = ([{"field": k, "type": _value_type(v)} for k, v in resp.items()] if isinstance(resp, dict) else [])
            codes = sorted({"400" if c == "422" else c for c in op.get("responses", {})})
            ops.append({"method": m, "path": path, "tag": (op.get("tags") or ["other"])[0], "summary": summary, "description": desc,
                        "params": params, "body_model": body_model, "body_fields": _fields(body_model, comps) if body_model else [],
                        "samples": [{"key": k, **v} for k, v in ok], "resp_fields": resp_fields, "codes": codes,
                        "auth": "none" if path == "/api/health" else ("X-API-Key + X-Admin-Key" if path == "/api/feedback-loop/run"
                                                                       else "X-API-Key")})
    order = [t["name"] for t in tags]
    ops.sort(key=lambda o: (order.index(o["tag"]) if o["tag"] in order else 99))
    return ops


def api_models(spec: dict, ops: list[dict]) -> list[dict]:
    """Models nested inside request bodies, documented once."""
    comps = spec.get("components", {}).get("schemas", {})
    seen: set = set()
    for op in ops:
        if op["body_model"]:
            _refs(op["body_model"], comps, seen)
    return [{"name": n, "description": comps[n].get("description", ""), "fields": _fields(n, comps)} for n in sorted(seen) if n in comps]


def curl(sample: dict) -> str:
    url = "http://127.0.0.1:8000" + sample["path"]
    if sample.get("params"):
        url += "?" + "&".join(f"{k}={v}" for k, v in sample["params"].items())
    lines = [f'curl -X {sample["method"]} "{url}"']
    if sample["path"] != "/api/health":
        lines.append('  -H "X-API-Key: $STUDENT_ASSISTANT_API_KEY"')
    if sample["path"] == "/api/feedback-loop/run":
        lines.append('  -H "X-Admin-Key: $STUDENT_ASSISTANT_ADMIN_KEY"')
    if sample.get("body") is not None:
        lines.append('  -H "Content-Type: application/json"')
        lines.append("  -d '" + json.dumps(sample["body"], ensure_ascii=False) + "'")
    return " \\\n".join(lines)


def context() -> dict:
    s = get_settings()
    gm = s.global_metrics_dir
    cpm = {c: s.at(c).metrics_dir for c in s.checkpoints}
    primary = s.at(s.primary_checkpoint).metrics_dir
    m = {n: _read(primary / f"{n}.json", {}) for n in ("withdrawal_model", "outcome_model", "data_build", "prioritization",
                                                         "retrieval_benchmark", "retrieval_sensitivity", "text_search_benchmark",
                                                         "embedding_eval", "fairness", "ablations")}
    m.update({n: _read(gm / f"{n}.json", {}) for n in ("checkpoint_summary", "llm_evaluation", "ragas_eval", "model_comparison",
                                                       "quality_gate")})
    m["fairness_by_checkpoint"] = {c: _read(cpm[c] / "fairness.json", {}) for c in s.checkpoints}
    raw = ROOT / "data" / "raw"
    sample = ROOT / "data" / "sample_data"
    tables = ["courses.csv", "assessments.csv", "vle.csv", "studentInfo.csv", "studentRegistration.csv", "studentAssessment.csv",
              "studentVle.csv"]
    data = {"tables": {t: {"rows": _csv_rows(raw / t), "sample_rows": _csv_rows(sample / t),
                           "columns": _csv_header(raw / t) or _csv_header(sample / t)} for t in tables}}
    from src.models.features import FRIENDLY, NUMERIC
    from src.reporting.model_card import model_card
    card = model_card(s)
    samples = _read(ROOT / "docs" / "api" / "api_samples.json", {"samples": {}})
    from src.api.route_docs import ROUTE_DOCS, TAGS
    spec = _openapi()
    ops = api_operations(spec, samples, ROUTE_DOCS, TAGS)
    cases_path = gm / "llm_evaluation_cases.jsonl"
    eval_cases = [json.loads(x) for x in cases_path.read_text(encoding="utf-8").splitlines() if x.strip()] if cases_path.exists() else []
    from src.agents.evidence import ACTION_CATALOG
    from src.evaluation.search_queries import text_search_queries
    n_actions = len(ACTION_CATALOG)
    # exact counts (parametrized cases included) from pytest's own collection
    out = subprocess.run([sys.executable, "-m", "pytest", "--collect-only", "-qq", "-p", "no:cacheprovider"], cwd=ROOT,
                         capture_output=True, text=True).stdout
    test_files = {Path(f).name: int(n) for f, n in re.findall(r"^(tests[\/]\S+\.py): (\d+)$", out, flags=re.M)}
    return {
        "api_ops": ops, "api_models": api_models(spec, ops), "curl": curl, "eval_cases": eval_cases, "n_actions": n_actions,
        "text_queries": text_search_queries(), "test_files": test_files, "n_tests": sum(test_files.values()),
        "s": s, "m": m, "data": data, "tests": _tests(), "openapi": spec, "samples": samples, "route_docs": ROUTE_DOCS,
        "tags": TAGS, "features": [(k, FRIENDLY.get(k, k)) for k in NUMERIC], "course_week": course_week,
        "model_card_body": card.split("\n", 3)[3] if card.count("\n") > 3 else card,
        "primary_week": course_week(s.primary_checkpoint), "weeks": [course_week(c) for c in s.checkpoints],
        "version": _project_version(),
    }


# ---------------------------------------------------------------- filters
def pct(x, d=0):
    return "n/a" if x is None else f"{100 * float(x):.{d}f}%"


def num(x, d=3):
    return "n/a" if x is None else f"{float(x):.{d}f}"


def thousands(x):
    return "n/a" if x is None else f"{int(x):,}"


def compact(x, depth=0):
    """Shorter view of an (already trimmed) API response for the printed reference: two list items, shallow nesting."""
    if isinstance(x, dict):
        if depth >= 4:
            return "{...}" if x else {}
        out = {k: compact(v, depth + 1) for k, v in list(x.items())[:12]}
        if len(x) > 12:
            out["..."] = f"{len(x) - 12} more fields"
        return out
    if isinstance(x, list):
        items = [v for v in x if not (isinstance(v, str) and v.startswith("... ") and v.endswith(" more"))]
        more = len(items) - 2 + sum(int(v.split()[1]) for v in x if isinstance(v, str) and v.startswith("... ") and v.endswith(" more"))
        out = [compact(v, depth + 1) for v in items[:2]]
        return out + ([f"... {more} more"] if more > 0 else [])
    return x


def jsonblock(x, limit=2200):
    text = json.dumps(compact(x), indent=2, ensure_ascii=False)
    if len(text) <= limit:
        return text
    return text[:text.rfind("\n", 0, limit)] + "\n  ... (trimmed for the document; the API returns the full response)"


def env() -> jinja2.Environment:
    e = jinja2.Environment(loader=jinja2.FileSystemLoader(str(TEMPLATES)), undefined=jinja2.StrictUndefined,
                           trim_blocks=True, lstrip_blocks=True, keep_trailing_newline=True)
    e.filters.update(pct=pct, num=num, thousands=thousands, jsonblock=jsonblock, tojson_inline=lambda x: json.dumps(x, ensure_ascii=False))
    return e


# ---------------------------------------------------------------- HTML / PDF
CSS = """
@page { size: A4; margin: 18mm 16mm 18mm 16mm; }
* { box-sizing: border-box; }
body { font-family: 'Segoe UI', Inter, Arial, sans-serif; color: #1b2733; font-size: 10.5pt; line-height: 1.5; }
h1 { font-size: 24pt; color: #17324d; margin: 0 0 4pt; letter-spacing: -0.01em; }
h2 { font-size: 15pt; color: #17324d; border-bottom: 1.5px solid #cfdde6; padding-bottom: 3pt; margin: 22pt 0 8pt; page-break-after: avoid; }
h3 { font-size: 12pt; color: #1f6f8b; margin: 14pt 0 5pt; page-break-after: avoid; }
h4 { font-size: 10.5pt; color: #17324d; margin: 10pt 0 4pt; page-break-after: avoid; }
p, li { orphans: 3; widows: 3; }
a { color: #1f6f8b; text-decoration: none; }
code { font-family: Consolas, 'Cascadia Mono', monospace; font-size: 9pt; background: #eef3f6; padding: 0 3px; border-radius: 3px; }
pre { background: #f4f7f9; border: 1px solid #dbe5ec; border-radius: 6px; padding: 8pt 10pt; font-size: 8.4pt; line-height: 1.35;
      white-space: pre-wrap; word-break: break-word; page-break-inside: auto; }
pre code { background: none; padding: 0; font-size: inherit; }
table { border-collapse: collapse; width: 100%; margin: 6pt 0 10pt; font-size: 9pt; page-break-inside: auto; }
tr { page-break-inside: avoid; }
th { background: #17324d; color: #fff; text-align: left; padding: 4pt 6pt; font-weight: 600; }
th code { background: transparent; color: #fff; }
td { border-bottom: 1px solid #dfe7ed; padding: 3.5pt 6pt; vertical-align: top; }
tr:nth-child(even) td { background: #f7fafb; }
blockquote { border-left: 3px solid #1f6f8b; margin: 8pt 0; padding: 2pt 10pt; color: #33475b; background: #f3f8fa; }
img { max-width: 100%; }
.cover { border-bottom: 3px solid #17324d; margin-bottom: 14pt; padding-bottom: 8pt; }
.cover .sub { color: #1f6f8b; font-weight: 600; font-size: 11pt; letter-spacing: 0.02em; }
.cover .meta { color: #5d6b7a; font-size: 9pt; margin-top: 4pt; }
.toc { background: #f4f7f9; border: 1px solid #dbe5ec; border-radius: 6px; padding: 6pt 12pt; margin-bottom: 10pt; font-size: 9.5pt; }
.toc ul { margin: 2pt 0; padding-left: 16pt; }
.method { display: inline-block; font-weight: 700; color: #fff; border-radius: 3px; padding: 0 6px; font-size: 9pt; margin-right: 6px; }
.GET { background: #2d7a5a; } .POST { background: #1f6f8b; }
hr { border: 0; border-top: 1px solid #dfe7ed; margin: 14pt 0; }
.pb { page-break-before: always; }
"""


def md_to_html(md_text: str, title: str, base: Path) -> str:
    md = markdown.Markdown(extensions=["tables", "fenced_code", "toc", "attr_list", "sane_lists", "md_in_html"],
                           extension_configs={"toc": {"toc_depth": "2-2"}})
    body = md.convert(md_text)
    # images and links relative to the markdown file -> file URLs, so Chromium can load them
    body = re.sub(r'src="(?!https?:|file:|data:)([^"]+)"', lambda mm: f'src="{(base / mm.group(1)).resolve().as_uri()}"', body)
    return f"<!doctype html><html><head><meta charset='utf-8'><title>{title}</title><style>{CSS}</style></head><body>{body}</body></html>"


def html_to_pdf(html: str, out: Path, title: str, browser):
    page = browser.new_page()
    tmp = out.with_suffix(".tmp.html")
    tmp.write_text(html, encoding="utf-8")
    try:
        page.goto(tmp.resolve().as_uri())
        page.wait_for_load_state("networkidle")
        footer = ("<div style='font-family:Segoe UI,Arial;font-size:7.5pt;color:#7a8794;width:100%;padding:0 16mm;display:flex;"
                  f"justify-content:space-between'><span>Uplift · Student Success Assistant · {title}</span>"
                  "<span><span class='pageNumber'></span> / <span class='totalPages'></span></span></div>")
        page.pdf(path=str(out), format="A4", print_background=True, display_header_footer=True,
                 header_template="<div></div>", footer_template=footer,
                 margin={"top": "16mm", "bottom": "18mm", "left": "15mm", "right": "15mm"})
    finally:
        page.close()
        tmp.unlink(missing_ok=True)


def render_architecture(browser):
    subprocess.run([sys.executable, str(ROOT / "scripts" / "architecture_diagram.py")], check=True)
    svg = ROOT / "architecture" / "Architecture_Diagram.svg"
    w, h = map(int, re.search(r'viewBox="0 0 (\d+) (\d+)"', svg.read_text(encoding="utf-8")).groups())
    page = browser.new_page(viewport={"width": w, "height": h}, device_scale_factor=2)
    page.goto(svg.resolve().as_uri())
    page.screenshot(path=str(svg.with_suffix(".png")))
    page.screenshot(path=str(svg.with_suffix(".jpeg")), type="jpeg", quality=92)
    page.close()
    page = browser.new_page(viewport={"width": w, "height": h})
    page.set_content(f"<html><body style='margin:0'>{svg.read_text(encoding='utf-8')}</body></html>")
    page.pdf(path=str(svg.with_suffix(".pdf")), width=f"{w}px", height=f"{h + 2}px", print_background=True,
             margin={"top": "0", "bottom": "0", "left": "0", "right": "0"})
    page.close()
    print("architecture/Architecture_Diagram.{svg,png,jpeg,pdf}")


EVAL_EXPORT = {  # artifact (relative to artifacts/) -> docs/evaluation/<name>
    "metrics/llm_evaluation.json": "llm_evaluation_deepeval_judge.json",
    "metrics/llm_evaluation_cases.jsonl": "llm_evaluation_cases.jsonl",
    "metrics/ragas_eval.json": "ragas_scores.json",
    "metrics/rag_cases.jsonl": "ragas_cases.jsonl",
    "metrics/model_comparison.json": "llm_model_comparison.json",
    "metrics/quality_gate.json": "quality_gate.json",
    "metrics/checkpoint_summary.json": "models_by_checkpoint.json",
    "checkpoints/c40/metrics/retrieval_benchmark.json": "retrieval_results_profile_search.json",
    "checkpoints/c40/metrics/text_search_benchmark.json": "retrieval_results_typed_search.json",
    "checkpoints/c40/metrics/retrieval_sensitivity.json": "retrieval_sensitivity.json",
    "checkpoints/c40/metrics/embedding_eval.json": "embedding_model_comparison.json",
    "checkpoints/c40/metrics/withdrawal_model.json": "withdrawal_model.json",
    "checkpoints/c40/metrics/outcome_model.json": "outcome_model.json",
    "checkpoints/c40/metrics/prioritization.json": "prioritization.json",
    "checkpoints/c40/metrics/fairness.json": "fairness_audit.json",
}


def export_evaluation() -> None:
    """Copy the raw evaluation results next to the report, byte for byte (recommended evaluation artifacts)."""
    import shutil
    s = get_settings()
    out = ROOT / "docs" / "evaluation"
    out.mkdir(parents=True, exist_ok=True)
    rows = []
    for src_rel, name in EVAL_EXPORT.items():
        src = s.artifact_dir / src_rel
        if src.exists():
            shutil.copyfile(src, out / name)
            rows.append(f"| `{name}` | `artifacts/{src_rel}` |")
    readme = ["# Evaluation artifacts", "",
              "Raw results behind `docs/Evaluation_Report.pdf`, copied unchanged from `artifacts/` by `scripts/build_docs.py` "
              "(week-15 checkpoint where per-checkpoint). Sample API outputs: `docs/api/api_samples.json`.", "",
              "| File | Source |", "|---|---|", *rows, ""]
    (out / "README.md").write_text(chr(10).join(readme), encoding="utf-8", newline=chr(10))
    print(f"docs/evaluation/ ({len(rows)} files)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", nargs="*", choices=[*OUTPUTS, "architecture"])
    a = ap.parse_args()
    want = set(a.only or [*OUTPUTS, "architecture", "evaluation"])
    if "evaluation" in want:
        export_evaluation()
    from playwright.sync_api import sync_playwright
    ctx = context()
    e = env()
    with sync_playwright() as p:
        browser = p.chromium.launch()
        if "architecture" in want:
            render_architecture(browser)
        for key, (tpl, out, title) in OUTPUTS.items():
            if key not in want:
                continue
            text = e.get_template(tpl).render(**ctx)
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(text, encoding="utf-8", newline="\n")
            msg = str(out.relative_to(ROOT))
            if title:
                html_to_pdf(md_to_html(text, title, out.parent), out.with_suffix(".pdf"), title, browser)
                msg += " + .pdf"
            print(msg)
        browser.close()


if __name__ == "__main__":
    main()
