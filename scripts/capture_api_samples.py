"""Call every API route once against a running server and save real request / response pairs for the API documentation.

    python scripts/capture_api_samples.py --base http://127.0.0.1:8001 --admin-key <admin key of that server>

Run it against a scratch copy of the artifacts (it writes one feedback row and one human rating). Responses are kept as
returned, then trimmed for readability only (long lists cut to a few items, long strings shortened); nothing is edited.
Output: docs/api/api_samples.json (read by scripts/build_docs.py).
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "api" / "api_samples.json"
STUDENT = {"id_student": 692826, "code_module": "BBB", "code_presentation": "2014J"}
CK = 0.4


def trim(x, depth=0, max_items=3, max_str=360):
    """Shorten for display: lists keep their first items, long strings are cut. Marks every cut."""
    if isinstance(x, dict):
        return {k: trim(v, depth + 1, max_items, max_str) for k, v in x.items()}
    if isinstance(x, list):
        keep = [trim(v, depth + 1, max_items, max_str) for v in x[:max_items]]
        if len(x) > max_items:
            keep.append(f"... {len(x) - max_items} more")
        return keep
    if isinstance(x, str) and len(x) > max_str:
        return x[:max_str] + " ..."
    return x


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="http://127.0.0.1:8001")
    ap.add_argument("--api-key", default="")
    ap.add_argument("--admin-key", default="")
    a = ap.parse_args()
    hdr = {"X-API-Key": a.api_key} if a.api_key else {}
    c = httpx.Client(base_url=a.base, headers=hdr, timeout=600)
    samples: dict[str, dict] = {}

    def call(method, path, *, params=None, body=None, key=None, headers=None, note=None):
        t0 = time.time()
        r = c.request(method, path, params=params, json=body, headers=headers)
        try:
            data = r.json()
        except ValueError:
            data = r.text
        samples[key or f"{method} {path}"] = {"method": method, "path": path, "params": params, "body": body, "status": r.status_code,
                                             "seconds": round(time.time() - t0, 2), "response": trim(data), "note": note}
        print(f"{r.status_code} {method} {path} ({time.time() - t0:.1f}s)")
        return data

    call("GET", "/api/health")
    call("GET", "/api/ready")
    call("GET", "/api/config")
    call("GET", "/api/overview", params={"checkpoint": CK})
    call("GET", "/api/cohort", params={"code_module": "BBB", "code_presentation": "2014J", "checkpoint": CK})
    call("GET", "/api/students", params={"code_module": "BBB", "code_presentation": "2014J", "checkpoint": CK, "tier": "High",
                                         "sort": "withdrawal_risk", "limit": 3})
    call("GET", f"/api/students/{STUDENT['id_student']}", key="GET /api/students/{id_student}",
         params={"code_module": "BBB", "code_presentation": "2014J", "checkpoint": CK})
    call("POST", "/api/predict-risk", body={"student": STUDENT, "checkpoint": CK})
    call("POST", "/api/predict-risk", key="POST /api/predict-risk (what-if)",
         body={"student": STUDENT, "checkpoint": CK, "what_if": {"days_since_last_activity": 3}},
         note="The same student with one signal changed: only the fields in what_if are overridden.")
    call("POST", "/api/students/timeline", body={"student": STUDENT})
    call("POST", "/api/trends/student", body={"student": STUDENT, "checkpoint": CK})
    res = call("POST", "/api/analyze", body={"student": STUDENT, "checkpoint": CK, "use_llm": True})
    rid = res.get("workflow", {}).get("recommendation_id") if isinstance(res, dict) else None
    job = call("POST", "/api/jobs/analyze", body={"student": STUDENT, "checkpoint": CK, "use_llm": False})
    for _ in range(200):
        j = c.get(f"/api/jobs/{job['id']}").json()
        if j["status"] in ("done", "error"):
            break
        time.sleep(0.3)
    call("GET", f"/api/jobs/{job['id']}", key="GET /api/jobs/{job_id}", note="Polled until done; `steps` lists each agent as it ran.")
    call("POST", "/api/cohort/briefing", body={"code_module": "BBB", "code_presentation": "2014J", "checkpoint": CK, "capacity": 0.2})
    bj = call("POST", "/api/jobs/briefing", body={"code_module": "BBB", "code_presentation": "2014J", "checkpoint": CK, "capacity": 0.2})
    cj = call("POST", "/api/jobs/copilot", body={"question": "How accurate is the withdrawal model?", "checkpoint": CK})
    for jid in (bj.get("id"), cj.get("id")):
        for _ in range(400):
            if c.get(f"/api/jobs/{jid}").json()["status"] in ("done", "error"):
                break
            time.sleep(0.3)
    call("POST", "/api/copilot", body={"question": "Who should I contact first in BBB 2014J?", "checkpoint": CK, "use_llm": True})
    # stream: keep the event sequence (names and first payloads)
    t0 = time.time()
    events = []
    with c.stream("POST", "/api/copilot/stream", json={"question": "Give me an overview of BBB 2014J", "checkpoint": CK}) as r:
        kind = None
        for line in r.iter_lines():
            if line.startswith("event: "):
                kind = line[7:]
            elif line.startswith("data: "):
                events.append({"event": kind, "data": trim(json.loads(line[6:]), max_items=2, max_str=200)})
    shown = [e for e in events if e["event"] != "text"][:6] + [e for e in events if e["event"] == "text"][:2]
    samples["POST /api/copilot/stream"] = {"method": "POST", "path": "/api/copilot/stream", "params": None, "status": 200,
                                           "body": {"question": "Give me an overview of BBB 2014J", "checkpoint": CK},
                                           "seconds": round(time.time() - t0, 2), "response": shown,
                                           "note": f"text/event-stream; {len(events)} events in this answer ({sum(e['event'] == 'text' for e in events)} "
                                                   "text deltas). Shown: the non-text events and the first two text deltas."}
    call("POST", "/api/outreach/variants", body={"message": "Hi, I noticed the last assignment hasn't come in yet. Would a short call "
                                                            "this week help you plan the next steps? Reply with a time that suits you.",
                                                 "channel": "sms", "tone": "warm", "language": "English"})
    call("POST", "/api/search/parse", body={"query": "repeat students in FFF with heavy workloads who dropped out"})
    call("POST", "/api/retrieve-similar", body={"query": "students who stopped turning in their coursework", "top_k": 3,
                                                "checkpoint": CK, "understand": True},
         note="Text search across all modules; the request is first understood as filters and behaviour descriptors.")
    call("POST", "/api/retrieve-similar", key="POST /api/retrieve-similar (by student)",
         body={"student": STUDENT, "top_k": 3, "checkpoint": CK, "filters": {"num_of_prev_attempts": {"max": 0}}},
         note="Profile search for one student: same module, earlier presentations only, metadata filter applied in the vector store.")
    call("POST", "/api/prioritize", body={"code_module": "BBB", "code_presentation": "2014J", "capacity": 0.1, "limit": 3, "checkpoint": CK})
    call("GET", "/api/trends/course", params={"code_module": "BBB"})
    call("GET", "/api/insights/factors")
    call("GET", "/api/insights/assessments", params={"code_module": "BBB", "code_presentation": "2014J"})
    call("GET", "/api/insights/checkpoints")
    call("GET", "/api/metrics", params={"checkpoint": CK})
    call("GET", "/api/evaluations/llm")
    if rid:
        call("POST", "/api/evaluations/judge", body={"recommendation_id": rid})
    call("GET", "/api/evaluations/online", params={"limit": 3})
    hr = call("GET", "/api/evaluations/human-review")
    case = (hr.get("cases") or [{}])[0] if isinstance(hr, dict) else {}
    if case:
        call("POST", "/api/evaluations/human-labels", body={"id_student": case["id_student"], "code_module": case["code_module"],
                                                            "code_presentation": case["code_presentation"], "verdict": "PASS",
                                                            "overall": 8, "notes": "Clear and supportive.", "reviewer": "demo"})
    call("GET", "/api/llm/usage", params={"since_hours": 720})
    if rid:
        call("POST", "/api/feedback", body={"recommendation_id": rid, "id_student": STUDENT["id_student"], "rating": 4,
                                            "plan_accepted": True, "risk_assessment_agrees": True,
                                            "notes": "Good plan; the student prefers phone calls.", "observed_outcome": None})
    call("GET", "/api/feedback", params={"limit": 3})
    call("GET", "/api/feedback/summary")
    call("GET", "/api/feedback/themes")
    call("GET", "/api/improvement-plan")
    call("POST", "/api/feedback-loop/run", body={"apply": False}, headers={"X-Admin-Key": a.admin_key})
    # error envelope examples
    call("POST", "/api/predict-risk", key="error: invalid input", body={"student": {"id_student": -5, "code_module": "XXX",
                                                                                   "code_presentation": "2014J"}})
    call("GET", "/api/students/1", key="error: unknown student", params={"code_module": "BBB", "code_presentation": "2014J"})

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"captured_at": time.strftime("%Y-%m-%d %H:%M"), "base_url": "http://127.0.0.1:8000",
                               "samples": samples}, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"wrote {OUT} ({len(samples)} samples)")


if __name__ == "__main__":
    main()
