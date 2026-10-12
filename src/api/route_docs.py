"""Summaries and descriptions for every API route: shown in Swagger (/api/docs) and used by docs/API_Documentation.

Kept apart from the route functions so the API reference reads as one document. `apply()` attaches them after the routes
are registered; `tests/test_api.py` fails if a route is added without an entry here.
"""
from __future__ import annotations

TAGS = [
    {"name": "system", "description": "Liveness, readiness and the configuration the console needs."},
    {"name": "cohort", "description": "Cohort views at a course checkpoint: overview, one presentation, student lists, ranking."},
    {"name": "student", "description": "One student: calibrated risk with drivers, what-if, snapshot, risk across checkpoints."},
    {"name": "agents", "description": "The multi-agent support workflow, cohort briefing, copilot and outreach rewriting."},
    {"name": "retrieval", "description": "Hybrid RAG over historical enrolments: query understanding and similar-case search."},
    {"name": "insights", "description": "Computed analyses from complete historical records (factors, trends, assessments)."},
    {"name": "evaluation", "description": "Model and AI evaluation results, LLM-as-judge, human review and AI usage/cost."},
    {"name": "feedback", "description": "Advisor feedback and the approval-gated improvement loop."},
]

# (METHOD, path) -> (summary, description)
ROUTE_DOCS: dict[tuple[str, str], tuple[str, str]] = {
    ("GET", "/api/health"): ("Liveness", "Always 200 while the process is up. The only route that needs no API key."),
    ("GET", "/api/ready"): ("Readiness", "Which build artifacts exist (features, models, prioritiser, case index), the checkpoints "
                                         "built and the index size. Use it to check a fresh install."),
    ("GET", "/api/config"): ("Console configuration", "Checkpoints with their course week, modules and presentations, the temporal "
                                                      "split, vocabularies for filters, LLM models in use and the dense-retrieval status."),
    ("GET", "/api/overview"): ("All presentations at a checkpoint", "Per module presentation: students still enrolled, tier mix, "
                                                                     "expected withdrawals and students already gone."),
    ("GET", "/api/cohort"): ("One presentation at a checkpoint", "Enrolled / in-scope counts, tier counts, expected withdrawals and "
                                                                 "fail-or-withdraw, risk histogram, tier thresholds, common High-tier "
                                                                 "drivers, median weekly activity and assessment deadlines."),
    ("GET", "/api/students"): ("List students", "Students still enrolled in a presentation with computed signals; sort, tier filter, "
                                                "ID search and paging. Students who already left are excluded by design."),
    ("GET", "/api/students/{id_student}"): ("Student snapshot", "The student's features as of the checkpoint (only what was known "
                                                                "then). 409 if they had already unregistered."),
    ("POST", "/api/predict-risk"): ("Predict withdrawal risk and outcome", "Calibrated withdrawal risk, tier and TreeSHAP drivers, plus "
                                                                           "the four-class outcome model. Accepts a student reference or "
                                                                           "a raw feature profile; `what_if` overrides signals."),
    ("POST", "/api/students/timeline"): ("Risk at every checkpoint", "The student's risk recomputed at each built checkpoint, using "
                                                                     "only the data available at that point."),
    ("POST", "/api/trends/student"): ("Weekly activity trend", "Weekly clicks up to the checkpoint against the cohort median, deadlines "
                                                               "and trend signals (drop, decline, inactivity)."),
    ("POST", "/api/analyze"): ("Run the support workflow (synchronous)", "Scores the student, retrieves similar cases, runs the "
                                                                         "LangGraph agents (performance, risk, router, intervention, "
                                                                         "critic, revision) and the precedent synthesis. Prefer the job "
                                                                         "form from a browser."),
    ("POST", "/api/jobs/analyze"): ("Run the support workflow (background job)", "Same as /api/analyze; returns 202 with a job id. Poll "
                                                                                 "/api/jobs/{job_id} to see each agent step as it finishes."),
    ("POST", "/api/jobs/briefing"): ("Cohort briefing (background job)", "Weekly briefing for a module team as a background job."),
    ("POST", "/api/jobs/copilot"): ("Copilot (background job)", "A copilot question as a background job."),
    ("GET", "/api/jobs/{job_id}"): ("Job status", "Status (queued, running, done, error), the steps completed so far and the result."),
    ("POST", "/api/cohort/briefing"): ("Cohort briefing", "Headline, key points, focus for the week and who to contact first, drafted "
                                                          "by the LLM from computed figures; every number and ID is checked, with a "
                                                          "computed fallback."),
    ("POST", "/api/copilot"): ("Ask the copilot", "Answers questions by calling the same tools as the console (cohort, ranking, "
                                                  "student, cases, insights, model performance); every number in the answer is "
                                                  "checked against the tool results. Rule-based when the LLM is off."),
    ("POST", "/api/copilot/stream"): ("Ask the copilot (streamed)", "Server-sent events: tool_call, tool_result, text (unverified until "
                                                                    "done), text_reset, revision, done, error."),
    ("POST", "/api/outreach/variants"): ("Rewrite an outreach message", "Rewrites an advisor's message for a channel (email, SMS, phone "
                                                                        "script), tone and language, with an English back-translation; "
                                                                        "length and wording checks with a computed fallback."),
    ("POST", "/api/search/parse"): ("Understand a search request", "Turns plain English into metadata filters and behaviour descriptors "
                                                                   "(LLM with a rule-based fallback)."),
    ("POST", "/api/retrieve-similar"): ("Find similar historical students (hybrid RAG)", "Similar enrolments from earlier "
                                                                                         "presentations by profile, text or both: "
                                                                                         "BM25 + behavioural kNN + dense vectors fused "
                                                                                         "with RRF, metadata pre-filtered in LanceDB, "
                                                                                         "with outcome mix and what happened next."),
    ("POST", "/api/prioritize"): ("Rank students for advisor capacity", "Ranks a presentation's enrolled students with weights learned on "
                                                                        "an earlier presentation, marks who fits the capacity and gives "
                                                                        "the reasons for each."),
    ("GET", "/api/trends/course"): ("Engagement trends by outcome", "Weekly activity by final outcome for a module and the week each "
                                                                    "outcome group falls below 60% of passing students."),
    ("GET", "/api/insights/factors"): ("Factors behind poor outcomes", "Signals ranked by the gap in fail-or-withdraw rate between best "
                                                                       "and worst fifth, with quintile rates and confidence intervals."),
    ("GET", "/api/insights/assessments"): ("Assessment analytics", "Per assessment: submission and late rates, mean score and how "
                                                                   "strongly missing it marks later failure or withdrawal (AUC)."),
    ("GET", "/api/insights/checkpoints"): ("Model quality by checkpoint", "Withdrawal-model metrics at every checkpoint on the untouched "
                                                                          "test presentation."),
    ("GET", "/api/metrics"): ("All evaluation metrics", "Data build, withdrawal and outcome models, ablations, fairness audit, "
                                                        "prioritisation, retrieval benchmark, LLM evaluation and the quality gate."),
    ("GET", "/api/evaluations/llm"): ("AI evaluation results", "Offline evaluation of every LLM feature: code checks, LLM-as-judge, "
                                                               "order-swapped A/B, DeepEval metrics, copilot golden set and robustness."),
    ("GET", "/api/evaluations/online"): ("Live reviews", "Judgements of sampled live requests (ONLINE_EVAL_SAMPLE_RATE) and on-demand "
                                                         "reviews."),
    ("POST", "/api/evaluations/judge"): ("Judge a support plan", "An independent judge model (Claude Opus 5.5) scores a plan on six "
                                                                 "criteria; the verdict is computed from the scores in code."),
    ("GET", "/api/evaluations/human-review"): ("Cases for human review", "The evaluation cases advisors can rate blind, with current "
                                                                         "agreement between their ratings and the judge (Cohen's kappa)."),
    ("POST", "/api/evaluations/human-labels"): ("Save a human rating", "Stores an advisor's blind rating of one evaluation case."),
    ("GET", "/api/llm/usage"): ("AI usage and cost", "Calls, cache hits, tokens, latency and estimated cost per feature and model."),
    ("POST", "/api/feedback"): ("Submit advisor feedback", "Rating of a recommendation, accepted actions, useful precedents and the real "
                                                           "outcome when known."),
    ("GET", "/api/feedback"): ("Recent feedback", "The latest feedback rows."),
    ("GET", "/api/feedback/summary"): ("Feedback summary", "Counts, average usefulness, plan acceptance and agreement rates."),
    ("GET", "/api/feedback/themes"): ("Themes in advisor notes", "Groups free-text notes into themes (LLM with a keyword fallback)."),
    ("GET", "/api/improvement-plan"): ("Improvement proposals", "Changes the feedback currently justifies, each with its evidence and "
                                                                "minimum-sample guard."),
    ("POST", "/api/feedback-loop/run"): ("Run the feedback loop (admin)", "Recalculates proposals; with apply=true, applies the ready "
                                                                          "ones as versioned artifacts. Needs X-Admin-Key."),
}


def api_routes(routes):
    """Every APIRoute, including those inside included routers (FastAPI keeps those nested rather than flattening them)."""
    from fastapi.routing import APIRoute
    for route in routes:
        if isinstance(route, APIRoute):
            yield route
        elif getattr(route, "original_router", None) is not None:
            yield from api_routes(route.original_router.routes)


def apply(app) -> None:
    """Attach summaries and descriptions to the registered routes."""
    for route in api_routes(app.routes):
        for method in route.methods:
            doc = ROUTE_DOCS.get((method, route.path))
            if doc:
                route.summary, route.description = doc
    app.openapi_tags = TAGS
