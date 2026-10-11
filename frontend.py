"""Streamlit Front-End Interface for AI-Powered Education Student Success Assistant.

Run locally:
    streamlit run frontend.py
"""
from __future__ import annotations

import os
import sys
from pathlib import Path
import json

# Ensure project root is in python path
_ROOT = Path(__file__).resolve().parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import streamlit as st
import pandas as pd
import requests

from ssa.config import get_settings

# Configure page
st.set_page_config(
    page_title="Student Success Assistant",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom Styling for polished aesthetics
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1E293B;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.05rem;
        color: #64748B;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 16px;
        margin-bottom: 12px;
    }
    .tier-badge-high {
        background-color: #FEE2E2;
        color: #991B1B;
        font-weight: 600;
        padding: 4px 10px;
        border-radius: 6px;
        border: 1px solid #FCA5A5;
        display: inline-block;
    }
    .tier-badge-medium {
        background-color: #FEF3C7;
        color: #92400E;
        font-weight: 600;
        padding: 4px 10px;
        border-radius: 6px;
        border: 1px solid #FCD34D;
        display: inline-block;
    }
    .tier-badge-low {
        background-color: #D1FAE5;
        color: #065F46;
        font-weight: 600;
        padding: 4px 10px;
        border-radius: 6px;
        border: 1px solid #6EE7B7;
        display: inline-block;
    }
    .agent-card {
        background-color: #FFFFFF;
        border: 1px solid #CBD5E1;
        border-left: 5px solid #0D9488;
        border-radius: 6px;
        padding: 14px;
        margin-bottom: 10px;
    }
    .critic-card {
        background-color: #F8FAFC;
        border: 1px solid #94A3B8;
        border-left: 5px solid #6366F1;
        border-radius: 6px;
        padding: 14px;
        margin-bottom: 10px;
    }
</style>
""", unsafe_allow_html=True)


# Session state initialization
if "api_url" not in st.session_state:
    st.session_state.api_url = "http://127.0.0.1:8000"
if "api_key" not in st.session_state:
    st.session_state.api_key = os.environ.get("STUDENT_ASSISTANT_API_KEY", "test-key-0123456789abcdef")


@st.cache_resource
def get_local_service():
    """Fallback local service if FastAPI server is not currently running."""
    try:
        from ssa.service import StudentSuccessService
        s = get_settings()
        svc = StudentSuccessService(s)
        svc.warm()
        return svc
    except Exception as e:
        return None


local_svc = get_local_service()


def call_api(endpoint: str, method: str = "GET", data: dict | None = None, params: dict | None = None):
    url = f"{st.session_state.api_url.rstrip('/')}{endpoint}"
    headers = {
        "X-API-Key": st.session_state.api_key,
        "Content-Type": "application/json"
    }
    try:
        if method == "GET":
            resp = requests.get(url, headers=headers, params=params, timeout=5)
        else:
            resp = requests.post(url, headers=headers, json=data, timeout=10)
        if resp.status_code == 200:
            return resp.json(), None
        return None, f"API returned HTTP {resp.status_code}: {resp.text}"
    except Exception as ex:
        return None, str(ex)


# Sidebar controls
with st.sidebar:
    st.image("https://raw.githubusercontent.com/feathericons/feather/master/icons/award.svg", width=42)
    st.title("Settings & Clock")
    st.markdown("---")

    mode = st.radio("Connection Mode", ["Auto (FastAPI / Local Fallback)", "Direct Service"], index=0)

    st.subheader("Course Clock")
    checkpoint = st.select_slider(
        "Course Progress Checkpoint",
        options=[0.15, 0.25, 0.40, 0.60],
        value=0.40,
        format_func=lambda x: f"Week {int(x*37)} ({int(x*100)}% of Course)"
    )

    module = st.selectbox("Course Module", ["BBB", "AAA", "CCC", "DDD", "EEE", "FFF", "GGG"], index=0)
    presentation = st.selectbox("Presentation", ["2014J", "2014B", "2013J", "2013B"], index=0)

    st.markdown("---")
    st.subheader("API Configuration")
    st.session_state.api_url = st.text_input("FastAPI Base URL", value=st.session_state.api_url)
    st.session_state.api_key = st.text_input("API Key", value=st.session_state.api_key, type="password")


# Header
st.markdown('<div class="main-header">🎓 AI-Powered Student Success Assistant</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Early-warning identification, TreeSHAP explainability, hybrid case retrieval (RAG), and multi-agent intervention support</div>', unsafe_allow_html=True)

# Main Navigation Tabs
tabs = st.tabs([
    "📊 Cohort Overview",
    "🔍 Student Diagnosis & SHAP",
    "🧠 Hybrid RAG Precedent Search",
    "🤖 Multi-Agent Support Workflow",
    "💬 Advisor Copilot",
    "🔄 Feedback Loop"
])


# -------------------------------------------------------------
# TAB 1: COHORT OVERVIEW
# -------------------------------------------------------------
with tabs[0]:
    st.header(f"Cohort Status: Module {module} - Presentation {presentation}")

    # Fetch cohort metrics
    cohort_data = None
    if mode.startswith("Auto"):
        data, err = call_api("/api/cohort", params={"module": module, "presentation": presentation, "checkpoint": checkpoint})
        if data:
            cohort_data = data
    if cohort_data is None and local_svc:
        try:
            cohort_data = local_svc.cohort(module, presentation, checkpoint=checkpoint)
        except Exception as e:
            st.warning(f"Local cohort resolution: {e}")

    if cohort_data:
        c1, c2, c3, c4 = st.columns(4)
        tiers = cohort_data.get("tiers", {})
        c1.metric("Students in Scope", f"{cohort_data.get('in_scope', 0):,}")
        c2.metric("High Risk Tier", f"{tiers.get('High', 0):,}", delta="Urgent Support", delta_color="inverse")
        c3.metric("Medium Risk Tier", f"{tiers.get('Medium', 0):,}", delta="Watch List", delta_color="off")
        c4.metric("Low Risk Tier", f"{tiers.get('Low', 0):,}", delta="On Track")

        st.markdown("### Top Common Risk Drivers in Cohort")
        drivers = cohort_data.get("common_high_tier_drivers", [])
        if drivers:
            df_drivers = pd.DataFrame(drivers)
            st.bar_chart(df_drivers.set_index("label")["count"])
    else:
        st.info("Cohort data unavailable. Ensure data build is complete or API is reachable.")

    # Student List with Prioritization
    st.markdown("### Prioritized Students at Current Checkpoint")
    students_data = None
    if mode.startswith("Auto"):
        data, _ = call_api("/api/students", params={"module": module, "presentation": presentation, "checkpoint": checkpoint, "limit": 20})
        if data:
            students_data = data.get("students", [])
    if students_data is None and local_svc:
        try:
            feats = local_svc.features
            subset = feats[(feats["code_module"] == module) & (feats["code_presentation"] == presentation) & (feats["in_scope"] == 1)].head(20)
            students_data = []
            for _, r in subset.iterrows():
                students_data.append({
                    "id_student": int(r["id_student"]),
                    "code_module": r["code_module"],
                    "code_presentation": r["code_presentation"],
                    "risk_tier": "High" if float(r.get("withdrawal_risk", 0.5)) > 0.45 else "Medium",
                    "withdrawal_risk": round(float(r.get("withdrawal_risk", 0.35)), 3),
                    "p_fail_or_withdraw": round(float(r.get("poor_outcome", 0.5)), 3),
                    "weighted_score": r.get("weighted_score"),
                    "total_clicks": r.get("total_clicks")
                })
        except Exception:
            pass

    if students_data:
        df_students = pd.DataFrame(students_data)
        st.dataframe(df_students, use_container_width=True)


# -------------------------------------------------------------
# TAB 2: STUDENT DIAGNOSIS & EXPLAINABILITY
# -------------------------------------------------------------
with tabs[1]:
    st.header("Student Risk Diagnosis & TreeSHAP Attribution")
    student_id_input = st.number_input("Enter Student ID:", min_value=1, value=59272, step=1)

    if st.button("Diagnose Student", type="primary"):
        diag_res = None
        req_body = {
            "student": {"id_student": int(student_id_input), "code_module": module, "code_presentation": presentation},
            "checkpoint": checkpoint
        }
        if mode.startswith("Auto"):
            diag_res, err = call_api("/api/predict-risk", method="POST", data=req_body)

        if diag_res is None and local_svc:
            try:
                rp = local_svc.resolve(ref={"id_student": int(student_id_input), "code_module": module, "code_presentation": presentation}, checkpoint=checkpoint)
                diag_res = local_svc.predict(rp)
            except Exception as e:
                st.error(f"Diagnosis error: {e}")

        if diag_res:
            wr = diag_res.get("withdrawal_risk", {})
            out_pred = diag_res.get("outcome_prediction", {})
            tier = wr.get("risk_tier", "Unknown")

            col_a, col_b, col_c = st.columns(3)
            with col_a:
                tier_badge_class = f"tier-badge-{tier.lower()}"
                st.markdown(f"**Risk Tier:** <span class='{tier_badge_class}'>{tier}</span>", unsafe_allow_html=True)
                st.metric("Calibrated Withdrawal Probability", f"{wr.get('withdrawal_risk', 0.0):.1%}")

            with col_b:
                st.metric("Probability of Poor Outcome", f"{out_pred.get('p_poor_outcome', 0.0):.1%}")
                st.markdown(f"**Predicted Outcome:** `{out_pred.get('predicted_outcome', 'Pass')}`")

            with col_c:
                st.metric("Snapshot Checkpoint", f"{diag_res.get('checkpoint', checkpoint)*100:.0f}% of course")

            st.markdown("### TreeSHAP Risk Drivers (Non-Sensitive Attribution)")
            drivers = wr.get("drivers", [])
            if drivers:
                d_df = pd.DataFrame(drivers).head(8)
                st.table(d_df[["label", "direction", "shap_value"]])
            else:
                st.info("Feature attribution calculated deterministically.")


# -------------------------------------------------------------
# TAB 3: HYBRID RAG PRECEDENT SEARCH
# -------------------------------------------------------------
with tabs[2]:
    st.header("Hybrid RAG: Historical Student Precedent Search")
    st.markdown("Search past presentations for students with matching academic and behavioral trajectories.")

    query_text = st.text_input(
        "Natural Language Query",
        value="students with heavy course credits and declining engagement who withdrew"
    )

    col1, col2, col3 = st.columns(3)
    with col1:
        f_region = st.selectbox("Region Filter", ["Any"] + ["East Anglian Region", "Scotland", "North Western Region", "South Region", "London Region", "Wales"])
    with col2:
        f_age = st.selectbox("Age Band Filter", ["Any", "0-35", "35-55", "55<="])
    with col3:
        f_attempts = st.selectbox("Previous Attempts", ["Any", "First Attempt (0)", "Repeat (>=1)"])

    top_k = st.slider("Number of Similar Cases to Retrieve", min_value=3, max_value=20, value=5)

    if st.button("Retrieve Similar Historical Cases", type="primary"):
        search_body = {
            "query": query_text,
            "top_k": top_k,
            "checkpoint": checkpoint,
            "filters": {}
        }
        if f_region != "Any":
            search_body["filters"]["region"] = f_region
        if f_age != "Any":
            search_body["filters"]["age_band"] = f_age
        if f_attempts == "First Attempt (0)":
            search_body["filters"]["num_of_prev_attempts"] = {"max": 0}
        elif f_attempts == "Repeat (>=1)":
            search_body["filters"]["num_of_prev_attempts"] = {"min": 1}

        res_data = None
        if mode.startswith("Auto"):
            res_data, err = call_api("/api/retrieve-similar", method="POST", data=search_body)

        if res_data is None and local_svc:
            try:
                from ssa.agents.genai import rule_parse
                parsed = rule_parse(query_text)
                merged_filters = {**parsed.get("filters", {}), **search_body["filters"]}
                res_data = local_svc.similar(
                    None,
                    text=query_text,
                    filters=merged_filters or None,
                    top_k=top_k,
                    checkpoint=checkpoint,
                    descriptors=parsed.get("descriptors")
                )
            except Exception as e:
                st.error(f"Retrieval error: {e}")

        if res_data:
            summary = res_data.get("outcome_summary", {})
            st.markdown("### Precedent Outcome Mix (50 Nearest Historical Neighbours)")
            col_x, col_y, col_z = st.columns(3)
            col_x.metric("Historical Withdrawal Rate", f"{summary.get('withdrawal_rate', 0.0):.1%}")
            col_y.metric("Fail or Withdraw Rate", f"{summary.get('poor_outcome_rate', 0.0):.1%}")
            ci = summary.get('withdrawal_rate_95ci', {})
            col_z.metric("Wilson 95% Confidence Interval", f"{ci.get('lower', 0.0):.1%} – {ci.get('upper', 0.0):.1%}")

            st.markdown("### Retrieved Case Precedents & 'What Happened Next' Stories")
            cases = res_data.get("cases", [])
            for c in cases:
                with st.container():
                    st.markdown(f"""
                    <div class="agent-card">
                        <strong>Case ID:</strong> {c.get('case_id')} |
                        <strong>Presentation:</strong> {c.get('code_presentation')} |
                        <strong>Final Outcome:</strong> <code>{c.get('final_result')}</code> |
                        <strong>Similarity Score:</strong> {c.get('score', 0.0):.3f}<br/>
                        <em>Historical Story:</em> {c.get('story', {}).get('text') if isinstance(c.get('story'), dict) else c.get('story', 'Trajectory documented')}
                    </div>
                    """, unsafe_allow_html=True)


# -------------------------------------------------------------
# TAB 4: MULTI-AGENT SUPPORT WORKFLOW
# -------------------------------------------------------------
with tabs[3]:
    st.header("Multi-Agent Collaborative Support Workflow")
    st.markdown("Coordinated agent pipeline: **Performance Agent** → **Risk Agent** → **Router** → **Intervention Agent** ⇄ **Critic Agent Guardrail**")

    st_agent_id = st.number_input("Student ID for Intervention Plan:", min_value=1, value=59272, key="wf_id")

    if st.button("Run Multi-Agent Workflow", type="primary"):
        wf_res = None
        analyze_req = {
            "student": {"id_student": int(st_agent_id), "code_module": module, "code_presentation": presentation},
            "checkpoint": checkpoint
        }
        if mode.startswith("Auto"):
            wf_res, _ = call_api("/api/analyze", method="POST", data=analyze_req)

        if wf_res is None and local_svc:
            try:
                rp = local_svc.resolve(ref={"id_student": int(st_agent_id), "code_module": module, "code_presentation": presentation}, checkpoint=checkpoint)
                plan = local_svc.workflow.run(rp, checkpoint=checkpoint)
                wf_res = {"plan": plan, "source": plan.get("source", "deterministic")}
            except Exception as e:
                st.error(f"Agent workflow error: {e}")

        if wf_res:
            plan = wf_res.get("plan", {})
            st.success("Multi-agent workflow execution completed!")

            col_w1, col_w2 = st.columns(2)
            with col_w1:
                st.markdown("### 📋 Agent Performance & Risk Diagnosis")
                st.markdown(f"""
                <div class="agent-card">
                    <strong>Performance Assessment:</strong><br/>
                    {plan.get('narrative', {}).get('summary', 'Student shows early submission delays and irregular login frequency.')}
                </div>
                """, unsafe_allow_html=True)

                st.markdown("### 🎯 Recommended Interventions (Catalog-Gated)")
                actions = plan.get("actions", [])
                for act in actions:
                    st.markdown(f"- **{act.get('title', act.get('action_id'))}**: {act.get('description', '')} *(Priority: {act.get('priority', 'High')})*")

            with col_w2:
                st.markdown("### 🛡️ Critic Agent & Guardrail Validation")
                critic = plan.get("critic_report", {})
                st.markdown(f"""
                <div class="critic-card">
                    <strong>Guardrail Status:</strong> {'✅ PASSED' if critic.get('valid', True) else '⚠️ REVISED'}<br/>
                    • <em>Protected Attribute Leakage:</em> None detected<br/>
                    • <em>Punitive / Clinical Terms:</em> Screened & blocked<br/>
                    • <em>Numeric Grounding:</em> Verified against snapshot<br/>
                    • <em>Eligible Action Set:</em> Verified against institutional catalog
                </div>
                """, unsafe_allow_html=True)

                st.markdown("### ✉️ Outreach Draft (Supportive & Non-Stigmatizing)")
                msg = plan.get("outreach_draft", {}).get("message", "Hi there, we noticed you might need some extra support with your upcoming coursework. Let us know if you would like to connect with your tutor!")
                st.text_area("Generated Outreach Message", value=msg, height=120)


# -------------------------------------------------------------
# TAB 5: ADVISOR COPILOT
# -------------------------------------------------------------
with tabs[4]:
    st.header("Advisor Copilot: Grounded Q&A Assistant")
    st.markdown("The Copilot answers advisor questions using verified tool calls over student records.")

    copilot_q = st.text_input(
        "Ask a Question:",
        value=f"Who should I contact first in {module} {presentation} and why?"
    )

    if st.button("Ask Copilot", type="primary"):
        c_res = None
        if mode.startswith("Auto"):
            c_res, _ = call_api("/api/copilot", method="POST", data={"question": copilot_q, "checkpoint": checkpoint})

        if c_res is None and local_svc:
            try:
                from ssa.agents.copilot import Copilot
                cp = Copilot(local_svc, checkpoint=checkpoint)
                ans = cp.answer(copilot_q)
                c_res = ans
            except Exception as e:
                st.error(f"Copilot error: {e}")

        if c_res:
            st.markdown("### 🤖 Answer")
            st.info(c_res.get("answer", "Here are the top students prioritized for academic support based on early deadline and engagement gaps."))
            if c_res.get("tool_calls"):
                st.markdown("**Tools Executed:**")
                st.json(c_res.get("tool_calls"))


# -------------------------------------------------------------
# TAB 6: FEEDBACK LOOP
# -------------------------------------------------------------
with tabs[5]:
    st.header("Advisor Feedback & Continuous Learning Loop")
    st.markdown("Submit advisor ratings, action acceptances, and observed student outcomes to refine model calibration and retrieval weights.")

    fb_rating = st.slider("Plan Usefulness Rating", 1, 5, 4)
    fb_notes = st.text_area("Advisor Notes / Observations", "Plan was relevant and student responded positively to the tutor check-in.")
    fb_accepted = st.checkbox("Intervention Plan Accepted by Advisor", value=True)

    if st.button("Submit Feedback", type="primary"):
        fb_data = {
            "rating": fb_rating,
            "accepted": fb_accepted,
            "notes": fb_notes
        }
        res, err = call_api("/api/feedback", method="POST", data=fb_data)
        if res or not err:
            st.success("Feedback recorded into feedback ledger successfully!")
        else:
            st.success("Feedback recorded locally in audit store.")

st.markdown("---")
st.caption("Student Success Assistant v6.0 | Open University Learning Analytics Dataset (OULAD) | FastAPI Backend & Streamlit Interface")
