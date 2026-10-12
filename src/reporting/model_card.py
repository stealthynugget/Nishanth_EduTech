"""Generate the model card, results summary and the 10-minute panel deck *from the metric
artifacts*. Nothing numeric is hard-coded: re-run ``python -m src.cli report`` after every build
(v4's deck and README advertised a leaked 0.90 ROC-AUC)."""
from __future__ import annotations

import time

from src.utils.common import read_json
from src.utils.config import PROJECT_ROOT, Settings, course_week, get_settings

NAVY, TEAL, AMBER, RED, SLATE, PAPER = "1F2A44", "0F766E", "B45309", "B91C1C", "64748B", "FBFBF9"


def load_all(s: Settings) -> dict:
    s = s.at(None)
    names = ["data_build", "withdrawal_model", "outcome_model", "ablations", "fairness", "prioritization", "retrieval_benchmark",
             "text_search_benchmark", "embedding_eval", "retrieval_sensitivity"]
    m = {n: read_json(s.metrics_dir / f"{n}.json", {}) for n in names}
    for n in ("llm_evaluation", "quality_gate", "checkpoint_summary", "model_comparison", "ragas_eval"):
        m[n] = read_json(s.global_metrics_dir / f"{n}.json", {})
    m["fairness_by_checkpoint"] = {c: read_json(s.at(c).metrics_dir / "fairness.json", {}) for c in s.checkpoints}
    m["factors"] = read_json(s.analysis_dir / "factor_analysis.json", {})
    m["trends"] = read_json(s.analysis_dir / "trend_analysis.json", {})
    return m


def _f(x, d=3):
    return "n/a" if x is None else f"{x:.{d}f}"


def _pct(x, d=0):
    return "n/a" if x is None else f"{100 * x:.{d}f}%"


def _llm_lines(e: dict) -> str:
    if not e or not e.get("agents"):
        return "Not run yet: `python -m src.cli llm-eval`."
    ag, se, co, rb = e["agents"], e["search"], e["copilot"], e["robustness"]
    rows = [f"Generator: {e.get('generator_model') or 'not connected'}; judge: {e.get('judge_model') or 'not connected'}.", "",
            "| Check | Result |", "|---|---|",
            f"| Support plans passing every guardrail | {_pct(ag['deterministic']['final_plan_valid_rate'])} |",
            f"| AI plan drafts accepted / revised | {_pct(ag['deterministic']['llm_plan_accepted_rate'])} / {_pct(ag['deterministic']['revision_rate'])} |",
            f"| Judge pass rate | {_pct(ag['judge'].get('pass_rate')) if ag['judge'].get('pass_rate') is not None else 'not run'} |",
            f"| AI plan preferred in order-swapped A/B | {_pct(ag['pairwise_llm_vs_deterministic'].get('llm_win_rate')) if ag['pairwise_llm_vs_deterministic'].get('llm_win_rate') is not None else 'not run'} |",
            f"| Search understanding F1, templated (rules / AI) | {_f(se.get('templated_rules', {}).get('filter_f1'))} / {_f(se.get('templated_llm', {}).get('filter_f1'))} |",
            f"| Search understanding F1, paraphrased (rules / AI) | {_f(se.get('paraphrased_rules', {}).get('filter_f1'))} / {_f(se.get('paraphrased_llm', {}).get('filter_f1'))} |",
            f"| Copilot correct answers (rules / AI) | {_pct(co['rules'].get('answer_correct_rate'))} / {_pct(co.get('llm', {}).get('answer_correct_rate'))} |",
            f"| Adversarial copilot prompts handled safely ({rb['mode']}) | {_pct(rb['safe_rate'])} |"]
    sy, br, ou = e.get("synthesis") or {}, e.get("briefing") or {}, e.get("outreach") or {}
    if sy.get("n"):
        rows.append(f"| Precedent syntheses accepted by the code checks / judge pass | {_pct(sy.get('llm_accepted_rate'))} / "
                    f"{_pct(sy.get('judge_pass_rate')) if sy.get('judge_pass_rate') is not None else 'not run'} |")
    if br.get("n"):
        rows.append(f"| Cohort briefings accepted by the code checks / judge pass | {_pct(br.get('llm_accepted_rate'))} / "
                    f"{_pct(br.get('judge_pass_rate')) if br.get('judge_pass_rate') is not None else 'not run'} |")
    if ou.get("n"):
        rows.append(f"| Outreach rewrites accepted / within length / safe | {_pct(ou.get('llm_accepted_rate'))} / "
                    f"{_pct(ou.get('length_compliance'))} / {_pct(ou.get('safe_rate'))} |")
    de = (ag.get("deepeval") or {}).get("aggregate") or {}
    if de:
        rows += ["", f"DeepEval ({ag['deepeval'].get('judge_model')}; mean score, 95% bootstrap CI, pass rate):", "",
                 "| Metric | Mean | 95% CI | Pass rate |", "|---|---|---|---|"]
        rows += [f"| {k} | {_f(v['mean'], 2)} | {_f(v['ci95'][0], 2)}–{_f(v['ci95'][1], 2)} | {_pct(v.get('pass_rate'))} |"
                 for k, v in de.items()]
    m, u = e.get("models") or {}, (e.get("usage") or {}).get("total") or {}
    if m:
        rows += ["", f"Models: {m.get('fast')} (search, outreach, note themes), {m.get('main')} (agents, copilot, synthesis, "
                     f"briefing), {m.get('judge')} (judge, A/B, DeepEval). Last evaluation run: {u.get('n', 0)} calls, of which "
                     f"{u.get('cached', 0)} were answered from the response cache of earlier runs; {u.get('errors', 0)} errors; new "
                     f"spend ${u.get('estimated_cost_usd', 0):.2f} (spend across runs: `/api/llm/usage`)."]
    return "\n".join(rows)


def _fairness_detail_lines(fa: dict, by_cp: dict) -> list[str]:
    out = ["", "### Across the course", "| Course week | " + " | ".join(fa.get("attributes", {})) + " |",
           "|---|" + "---|" * len(fa.get("attributes", {}))]
    for c, f in sorted(by_cp.items()):
        if not f:
            continue
        cells = []
        for k in fa.get("attributes", {}):
            v = f.get("attributes", {}).get(k, {})
            gap, pv = v.get("equal_opportunity_gap"), v.get("gap_null", {}).get("p_value")
            cells.append("–" if gap is None else f"{_f(gap, 2)} (p {_f(pv, 3)})")
        out.append(f"| {course_week(c)} | " + " | ".join(cells) + " |")
    out += ["", "Gap and permutation p-value per checkpoint. With 24 tests, a few p-values under 0.05 are expected by chance alone."]
    for k, v in fa.get("attributes", {}).items():
        if "verdict" not in v:
            continue
        lo, hi = v["lowest_tpr_group"], v["highest_tpr_group"]
        glo, ghi = v["groups"][lo], v["groups"][hi]
        out += ["", f"**{k}**: {v['verdict']}. Lowest TPR {lo} {_f(glo['tpr_high'], 2)} (95% CI {_f(glo['tpr_high_ci95'][0], 2)}–"
                    f"{_f(glo['tpr_high_ci95'][1], 2)}, {glo['positives']} withdrawn); highest {hi} {_f(ghi['tpr_high'], 2)} "
                    f"(95% CI {_f(ghi['tpr_high_ci95'][0], 2)}–{_f(ghi['tpr_high_ci95'][1], 2)}, {ghi['positives']} withdrawn). "
                    f"Observed withdrawal rate {_pct(glo['observed_rate'], 1)} vs mean predicted {_pct(glo['mean_predicted'], 1)} ({lo}); "
                    f"{_pct(ghi['observed_rate'], 1)} vs {_pct(ghi['mean_predicted'], 1)} ({hi})."]
        prox = []
        proxies = list(v.get("proxies", {}).items())
        for g, pr in proxies[1:] if len(v["groups"]) == 2 else proxies:  # two groups: the second mirrors the first
            feats = ", ".join(f"{d['label'].replace('code_module=', 'module ')} ({d['standardised_mean_difference']:+.2f} SD)"
                              for d in pr["most_different_inputs"][:3])
            prox.append(f"{g}: model inputs identify membership with ROC-AUC {_f(pr['membership_auc_from_model_inputs'], 2)}; "
                        f"most different inputs {feats}")
        if prox:
            out.append("Proxies. " + "; ".join(prox) + ".")
        tr = v.get("threshold_review")
        if tr and v["gap_null"]["p_value"] < 0.05:
            out += ["", f"Threshold review (target TPR {_f(tr['target_tpr'], 2)}, "
                        f"current High cut-off {_f(tr['current_threshold'], 3)}):", "",
                    "| Group | TPR now | Cut-off for target TPR | Selection rate now → then | PPV now → then | Students flagged |",
                    "|---|---|---|---|---|---|"]
            out += [f"| {g} | {_f(r['current_tpr'], 2)} | {_f(r['equalising_threshold'], 3)} | {_pct(r['current_selection_rate'])} → "
                    f"{_pct(r['selection_rate_at_equalising'])} | {_pct(r['current_ppv'])} → {_pct(r['ppv_at_equalising'])} | "
                    f"{r['change_in_flagged_students']:+d} |" for g, r in tr["groups"].items()]
    return out


def _strategy_lines(sv: dict) -> list[str]:
    if not sv.get("top_k"):
        return []
    prod = sv["production"]
    lines = ["", "### Retrieval strategy: documents, top-K and context",
             "One document per enrolment, no chunking: each case is one record (snapshot features, discretised descriptors and a "
             "~60-word narrative), and splitting it would separate the signals from the outcome they lead to. Each channel ranks "
             f"the eligible cases and fusion reads the top {prod['candidate_pool']} of each (weighted RRF, k = {prod['rrf_k']}). "
             f"The agents and the precedent synthesis get the {prod['precedents_shown']} closest cases as stories (what happened "
             f"after this point), and outcome statistics use the {prod['outcome_neighbourhood']} nearest. Sensitivity on "
             f"{sv['queries']} students of {sv['query_presentation']} (hybrid):", "",
             "| Setting | Neighbour-vote AUC (fail/withdraw) | Neighbour-vote AUC (withdrawal) | Outcome agreement |", "|---|---|---|---|"]
    for g in ("top_k", "candidate_pool", "rrf_k"):
        for name, v in sv.get(g, {}).items():
            if name != "seconds":
                lines.append(f"| {name} | {_f(v['vote_auc_poor_outcome'])} | {_f(v['vote_auc_withdrawal'])} | "
                             f"{_f(v['outcome_agreement'])} |")
    lines += ["", "More neighbours make better outcome estimates (hence 50 for the outcome mix); a handful of concrete stories "
              "keeps the context readable and the prompt short (hence 6). Pool depth and the RRF constant hardly matter here."]
    return lines


def _embedding_lines(ee: dict, in_use: str | None = None) -> list[str]:
    rows = [r for r in ee.get("models", []) if "error" not in r]
    if not rows:
        return []
    parsers = sorted({p for r in rows for p in r.get("typed_search", {})})
    head = " | ".join(f"Typed {p}: dense / hybrid P@10" for p in parsers)
    lines = ["", "## Embedding model evaluation (dense narrative channel)",
             f"Same {rows[0]['corpus_docs']:,} case narratives (checkpoint {ee['checkpoint']}), encoded on CPU by each model. "
             "Typed search: "
             "40 labelled queries, hybrid ratio tuned per model on separate tuning queries. Precedents: dense-only neighbours "
             f"of {ee['profile_queries'].split(' ')[0]} test students. Evaluated while {ee['current_model']} was in production; "
             f"in production now: {in_use or ee['current_model']} (index manifest).", "",
             f"| Model | Params (M) | Dims | Index MB | Encode docs/s | Query ms | {head} | Precedents vote-AUC (fail/withdraw) |",
             "|---|---|---|---|---|---|" + "---|" * len(parsers) + "---|"]
    for r in rows:
        ts = " | ".join(f"{_f(r['typed_search'].get(p, {}).get('dense_precision_at_10'))} / "
                        f"{_f(r['typed_search'].get(p, {}).get('hybrid_precision_at_10'))}" for p in parsers)
        lines.append(f"| {r['model']} | {r['parameters_millions']} | {r['dimensions']} | {r['index_mb']} | {r['encode_docs_per_second']} | "
                     f"{r['query_latency_ms']} | {ts} | {_f(r['profile_dense']['vote_auc_poor_outcome'])} |")
    failed = [r["model"] for r in ee.get("models", []) if "error" in r]
    if failed:
        lines += ["", f"Not evaluated (error): {', '.join(failed)}."]
    return lines


def _ragas_lines(rg: dict) -> list[str]:
    if not rg.get("features"):
        return []
    lines = ["", "### RAGAS (retrieval-augmented features)",
             f"Evaluator: {rg['judge_model']} (judge tier, never the generator), via the project's LLM client. Faithfulness = share "
             "of the response's claims supported by the retrieved context; hallucination rate = 1 - faithfulness. Precedent "
             "synthesis is scored on its factual sections; its advice is scored by the judge and DeepEval. Copilot answers "
             "are scored whole, so explanations of what a metric means count as unsupported.", "",
             "| Feature | Cases | Faithfulness | Hallucination rate | Fully supported | Response groundedness | Context relevance |",
             "|---|---|---|---|---|---|---|"]
    for f, v in rg["features"].items():
        mm = v["mean"]
        lines.append(f"| {f} | {v['n']} | {_f(mm.get('faithfulness'))} | {_pct(v.get('hallucination_rate'), 1)} | "
                     f"{_pct(v.get('fully_supported_rate'))} | {_f(mm.get('nv_response_groundedness'))} | "
                     f"{_f(mm.get('nv_context_relevance'))} |")
    return lines


def _model_choice_lines(mc: dict) -> list[str]:
    if not mc.get("search_understanding"):
        return []
    pc = mc["production_choice"]
    lines = ["", "### LLM selection: the same features on each tier",
             f"Production: search understanding on {pc['search_understanding']}, precedent synthesis on {pc['precedent_synthesis']}, "
             f"judge {pc['judge']}. Same prompts, schemas, effort and code checks; only the model changes. Cost and latency per "
             "live call (from the usage ledger where this run was answered from cache).", "",
             "| Feature | Model | Quality | Passes code checks | Cost per call | Median latency |", "|---|---|---|---|---|---|"]
    for m, v in mc["search_understanding"].items():
        lines.append(f"| Search understanding | {m} | filter F1 {_f(v['filter_f1'])}, exact {_pct(v['exact_match'])} | "
                     f"{_pct(v['accepted_by_code_checks'])} | ${v['cost_per_call_usd']:.4f} | {v['median_latency_s']} s |")
    for m, v in mc["precedent_synthesis"].items():
        js = v.get("judge_mean_scores") or {}
        q = f"judge pass {_pct(v['judge_pass_rate'])}, faithfulness {js.get('faithfulness', 'n/a')}"
        q += " (self-judged)" if v["self_judged"] else ""
        lines.append(f"| Precedent synthesis | {m} | {q} | {_pct(v['accepted_by_code_checks'])} | ${v['cost_per_call_usd']:.4f} | "
                     f"{v['median_latency_s']} s |")
    return lines


def _selection_lines(p: dict) -> list[str]:
    d = p.get("selection_detail")
    if not d:
        return []
    return ["", f"Selection rule `{d['rule']}`: the best grid point on validation (`validation_argmax` below) was "
                f"`{d['argmax_weights']}`; {d['n_within_one_se']} weightings were within one bootstrap standard error "
                f"({_f(d['bootstrap_se'])}) of it, and the most blended of those is used. Both are scored once on the test presentation."]


def _typed_search_lines(t: dict) -> list[str]:
    if not t.get("parsers"):
        return []
    by = t.get("hybrid_text_weights_by_parser") or {"rules": t.get("hybrid_text_weights", {})}
    tw = "; ".join(f"{p} parser lexical {w.get('lexical')}, dense {w.get('dense')}" for p, w in by.items())
    lines = ["", "### Typed search", f"{t['queries']} labelled plain-English queries (templated, paraphrased and behaviour-led); a returned "
             "case is relevant when it meets every expected filter and shows every expected behaviour. Hybrid typed search uses "
             f"weights tuned per query parser on a separate query set ({tw}).", "",
             "| Query parser | Mode | Precision@10 | Filter match@10 | Behaviour match@10 |", "|---|---|---|---|---|"]
    for parser, res in t["parsers"].items():
        for mode, v in res["modes"].items():
            lines.append(f"| {parser} | {mode} | {_f(v.get('precision_at_10'))} | {_f(v.get('filter_match_at_10'))} | "
                         f"{_f(v.get('behaviour_match_at_10'))} |")
    return lines


def model_card(s: Settings | None = None) -> str:
    s = s or get_settings()
    m = load_all(s)
    d, w, o, a, fa, p, r, q = (m[k] for k in ("data_build", "withdrawal_model", "outcome_model", "ablations", "fairness",
                                               "prioritization", "retrieval_benchmark", "quality_gate"))
    if not w:
        return "# Model card\n\nNo metrics yet. Run `python -m src.cli build`.\n"
    t = w["test"]
    pa = w.get("population_audit", {})
    tiers = w["test_tiers"]
    cap = {c["fraction"]: c for c in w["test_capacity"]}
    lines = [
        "# Model card — Uplift, the Student Success Assistant (v6)", "",
        f"_Generated {time.strftime('%Y-%m-%d %H:%M')} from `artifacts/metrics/*.json` by `python -m src.cli report`. "
        f"Engine: **{w.get('engine')}**. Evidence profile: **{q.get('profile', 'unknown')}** "
        f"(quality gate {'passed' if q.get('passed') else 'NOT passed'})._", "",
        "## Intended use",
        "Early-warning support for academic advisors at ~40% of a course presentation: surface students still enrolled who may "
        "withdraw or fail, explain why, show comparable historical cases and draft supportive outreach. A human advisor reviews "
        "every recommendation. Not for admissions, grading, sanctions or any automated adverse decision.", "",
        "## Data and population",
        f"- OULAD, {d.get('records', 'n/a'):,} enrolments; snapshot at {int(100 * d.get('cutoff_fraction', 0.4))}% of each presentation.",
        f"- **In scope:** {d.get('in_scope_records', 0):,} enrolments still registered at the snapshot. "
        f"{d.get('withdrawn_before_snapshot', 0):,} students who had already unregistered "
        f"({d.get('withdrawn_before_start', 0):,} before day 0) are excluded — they cannot be helped by an early warning and "
        "including them inflates every metric.",
        f"- Temporal protocol: {w['split'].get('train')} train, {w['split'].get('validation')} validation, "
        f"{w['split'].get('test')} untouched test.", "",
        "## Withdrawal model (target: withdrawal after the snapshot)",
        "| Metric (test presentation, in scope) | Value |", "|---|---|",
        f"| ROC-AUC | {_f(t['roc_auc'])} (95% CI {_f(t['roc_auc_95ci']['lower'])}–{_f(t['roc_auc_95ci']['upper'])}) |",
        f"| PR-AUC | {_f(t['pr_auc'])} (base rate {_f(t['positive_rate'])}) |",
        f"| Brier / ECE | {_f(t['brier'])} / {_f(t['ece_10'])} |",
        f"| Logistic-regression baseline ROC-AUC | {_f(w['baseline_logistic_regression_test']['roc_auc'])} |",
        f"| Precision / recall when contacting top 10% | {_pct(cap[0.1]['precision'])} / {_pct(cap[0.1]['recall'])} (lift {_f(cap[0.1]['lift'], 2)}) |",
        f"| Precision / recall when contacting top 20% | {_pct(cap[0.2]['precision'])} / {_pct(cap[0.2]['recall'])} |", "",
        f"Risk tiers (thresholds learned out-of-fold: Medium ≥ {_f(w['thresholds']['medium'])}, High ≥ {_f(w['thresholds']['high'])}):", "",
        "| Tier | Share of students | Observed withdrawal rate | Share of all withdrawals |", "|---|---|---|---|",
    ] + [f"| {k} | {_pct(v['share'])} | {_pct(v['observed_withdrawal_rate'], 1)} | {_pct(v['share_of_all_withdrawals'])} |"
         for k, v in tiers.items()] + [
        "",
        f"**Leakage audit.** Scoring the same model on *all* test enrolments, including students who had already left, gives "
        f"ROC-AUC {_f(pa.get('all_enrolments_including_already_withdrawn', {}).get('roc_auc'))} vs {_f(pa.get('in_scope_only', {}).get('roc_auc'))} "
        f"in scope; {_pct(pa.get('already_withdrawn_share_of_test_withdrawals'))} of the test presentation's withdrawals had already "
        "happened by the snapshot. v4 reported 0.90 by training and testing on that population.", "",
        "## Outcome model (Distinction / Pass / Fail / Withdrawn)",
        f"- Test macro-F1 {_f(o['test']['macro_f1'])} vs multinomial logistic {_f(o['baselines_test']['multinomial_logistic']['macro_f1'])} "
        f"and majority class {_f(o['baselines_test']['majority_class']['macro_f1'])}; class weighting `{o['chosen_weighting']}` chosen on validation.",
        f"- P(fail or withdraw): ROC-AUC {_f(o['poor_outcome_from_p_fail_plus_p_withdrawn_test']['roc_auc'])}, "
        f"ECE {_f(o['poor_outcome_from_p_fail_plus_p_withdrawn_test']['ece_10'])}.", "",
        "## Feature-group ablation (test ROC-AUC / PR-AUC)",
        "| Variant | ROC-AUC | PR-AUC |", "|---|---|---|",
    ] + [f"| {k} | {_f(v['roc_auc'])} | {_f(v['pr_auc'])} |" for k, v in a.get("variants", {}).items()] + [
        "", "Sensitive attributes add essentially nothing, so they are excluded from the model by default.", "",
        "## Prioritisation (target: fail or withdraw)",
        f"Weights learned on the validation presentation: `{p.get('weights')}` ({p.get('selection', 'grid search')}).",
    ] + _selection_lines(p) + [
        "", "| Ranking | Mean precision @10/20/30% | Precision @10% |", "|---|---|---|",
    ] + [f"| {k} | {_f(v['objective_mean_precision'])} | {_pct(v['at_capacity'][0]['precision'])} |"
         for k, v in p.get("test_comparison", {}).items()
         if k in ("learned_weights", "validation_argmax", "v4_hand_formula", "only_p_poor", "only_p_withdraw", "random")] + [
        "", "## Historical-case retrieval",
        f"Queries: {r.get('queries')} in-scope students of {r.get('query_presentation')}; corpus: earlier presentations, same module.", "",
        "| Mode | Neighbour-vote AUC (fail/withdraw) | Outcome agreement@10 | nDCG@10 (global ideal) |", "|---|---|---|---|",
    ] + [f"| {k} | {_f(v['neighbour_vote_auc_poor_outcome'])} | {_f(v['outcome_agreement_at_10'])} | {_f(v['reference_ndcg_at_10_global_ideal'])} |"
         for k, v in r.get("modes", {}).items()] + _typed_search_lines(m.get("text_search_benchmark", {})) + \
        _strategy_lines(m.get("retrieval_sensitivity", {})) + \
        _embedding_lines(m.get("embedding_eval", {}), r.get("index", {}).get("embedding_model")) + [
        "", "## Fairness audit (High tier, test presentation)",
        f"Groups count towards a gap only with {fa.get('sufficient_sample_rule', 'a sufficient sample')}. "
        "Chance gap: the median max−min gap when group labels are shuffled among withdrawn students (1,000 permutations), "
        "overall and within each module.", "",
        "| Attribute | Equal-opportunity gap (TPR max−min) | Chance gap | p | p within module | Selection-rate ratio "
        "| Max calibration gap |",
        "|---|---|---|---|---|---|---|",
    ] + [f"| {k} | {_f(v['equal_opportunity_gap'])} | {_f(v.get('gap_null', {}).get('median'))} | "
         f"{_f(v.get('gap_null', {}).get('p_value'))} | {_f(v.get('gap_null', {}).get('within_module_p_value'))} | "
         f"{_f(v['selection_rate_ratio'])} | {_f(v['max_calibration_gap'])} |"
         for k, v in fa.get("attributes", {}).items()] + _fairness_detail_lines(fa, m.get("fairness_by_checkpoint", {})) + [
        "", "Sensitive attributes are excluded from the model, so remaining gaps come from proxies and different base rates. "
        "They are surfaced as quality-gate warnings and must be reviewed with the institution's equity office before deployment. "
        "Per-group cut-offs are shown for that review only; applying them would use a sensitive attribute at decision time.", "",
        "## Early warning across the course (test presentation, students still enrolled at each point)",
        "| Course week | Still enrolled | ROC-AUC | PR-AUC | Base rate | ECE | Outcome macro-F1 |", "|---|---|---|---|---|---|---|",
    ] + [f"| {course_week(c['checkpoint'])} | {c['in_scope']:,} | {_f(c['withdrawal']['roc_auc'])} | {_f(c['withdrawal']['pr_auc'])} | "
         f"{_f(c['withdrawal']['positive_rate'])} | {_f(c['withdrawal']['ece_10'])} | {_f(c['outcome_macro_f1'])} |"
         for c in m["checkpoint_summary"].get("checkpoints", [])] + [
        "", "## AI features (offline evaluation)", _llm_lines(m["llm_evaluation"]), *_ragas_lines(m.get("ragas_eval", {})),
        *_model_choice_lines(m.get("model_comparison", {})), "",
        "## Limitations",
        "- Associations, not causes. Drivers explain the model, not the student.",
        "- One test presentation (2014J); performance can drift across cohorts — monitored by the feedback loop's tier-drift check.",
        "- OULAD is from one institution and 2013–2014; revalidate before use elsewhere.",
        "- LLM narration is optional; all facts, scores, priorities and eligible actions are computed deterministically.",
    ]
    return "\n".join(lines) + "\n"


def write_reports(s: Settings | None = None) -> dict:
    s = s or get_settings()
    docs = PROJECT_ROOT / "docs"
    docs.mkdir(exist_ok=True)
    (docs / "MODEL_CARD.md").write_text(model_card(s), encoding="utf-8")
    out = {"model_card": str(docs / "MODEL_CARD.md")}
    try:
        from src.reporting.presentation import build_presentation
        out["presentation"] = str(build_presentation(s))
    except ImportError:
        out["presentation"] = "python-pptx not installed"
    return out
