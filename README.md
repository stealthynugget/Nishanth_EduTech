# AI-Powered Education Student Success Assistant

An end-to-end, calibrated early-warning and student-support microservice built on the complete Open University Learning Analytics Dataset (OULAD). At temporal checkpoints across a course (Weeks 6, 9, 15, 22), the assistant identifies currently enrolled students who are at risk of failing or withdrawing, provides exact TreeSHAP factor attributions, retrieves similar historical student precedents via hybrid search (BM25 + behavioural kNN), prioritizes students under advisor capacity constraints, and drafts guardrail-verified supportive intervention plans via a multi-agent workflow.

![Architecture Overview](architecture/Architecture_Diagram.png)

---

## 1. Project Overview
Educational institutions require scalable methods to identify students who struggle academically, disengage from online learning platforms, or are at high risk of course withdrawal. The **Student Success Assistant** replaces manual, retrospective record scanning with proactive, semantic retrieval and multi-agent AI decision support.

---

## 2. Problem Statement
Distance and online learning courses exhibit dropout rates exceeding 30%. Academic advising teams face tens of thousands of student records across course modules, assessments, and clickstream interactions. 
- **Core Dilemma:** How can advisors detect disengagement *before* deadlines are missed and early enough to intervene?
- **Data Leakage Pitfall in Prior Work:** Prior benchmarks frequently trained on students who had *already unregistered* before course start or cutoff day. This creates artificial 0.90+ ROC-AUC metrics that fail in production. Our system enforces strict **temporal in-scope isolation**, evaluating only actively enrolled students at decision time.
- **Explainability Gap:** Advisors reject black-box probabilities. Every prediction must surface observable, actionable drivers.

---

## 3. Business Objective
1. **Early Retention Intervention:** Shift advising teams from reactive post-mortems to proactive early outreach at Weeks 6, 9, 15, and 22.
2. **Maximize Advisor Efficiency:** Optimize student prioritization so that contacting the top 10%–20% of the cohort captures over 80% of eventual dropouts (2.3× lift over random outreach).
3. **Equitable & Non-Stigmatizing Support:** Isolate sensitive attributes (gender, age, region, deprivation, disability) to prevent algorithmic bias. Ensure outreach drafts never mention risk scores, predictions, or withdrawal.
4. **Continual Improvement:** Record advisor feedback (plan usefulness ratings, accepted actions, and actual semester outcomes) into a versioned learning loop.

---

## 4. Solution Summary
The system provides a three-pillar architecture:
1. **Calibrated Machine Learning:** Temporal snapshotting at Weeks 6, 9, 15, and 22. Boosted decision trees (HistGradientBoosting / XGBoost) with LOPO Platt scaling (ECE: 0.006) and TreeSHAP feature attributions.
2. **Hybrid RAG Precedent Retrieval:** Lexical BM25 search over discretized behavioral tokens combined with supervised kNN weighted by TreeSHAP importance. Reciprocal Rank Fusion (RRF) delivers **0.835 neighbour-vote AUC** (vs 0.512 random baseline).
3. **Multi-Agent Support Workflow:** A 5-agent pipeline (**Performance Agent** → **Risk Agent** → **Router** → **Intervention Agent** ⇄ **Critic Agent**) with deterministic code guardrails and an interactive tool-using Copilot.

---

## 5. Technology Stack

| Component | Technology | Justification |
|---|---|---|
| **Programming Language** | Python 3.10+ | Primary standard for data science, machine learning, and GenAI backends |
| **LLM Used** | OpenAI-Compatible LLM (GPT-4o, GPT-4o-mini, or Ollama) | Fast, structured JSON generation; all numbers and facts computed in code |
| **Embedding Model** | Supervised TreeSHAP feature vectors + Sentence-Transformers (MiniLM) | Overcomes tabular embedding limitations by weighting predictive drivers |
| **Vector Database** | In-Memory Supervised kNN + Rank-BM25 Inverted Index | Sub-10ms retrieval across 25k+ cases without external microservice overhead |
| **Machine Learning** | Scikit-Learn (HistGradientBoosting), XGBoost, TreeSHAP | Native NaN handling, robust missing assessment tracking, exact attributions |
| **Microservice Backend** | FastAPI + Uvicorn | High-throughput asynchronous REST API with strict Pydantic v2 schemas |
| **Front-End Interface** | Streamlit (`frontend.py`) | Interactive Streamlit evaluation dashboard & student success advising console |
| **Evaluation Framework** | DeepEval, Custom LLM-as-Judge, Pytest | Comprehensive guardrail, faithfulness, and integration test suite |
| **Database & Auditing** | SQLite (`artifacts/app/app.sqlite3`) | Atomic transaction ledger for feedback, usage tokens, and model runs |

---

## 6. Project Folder Structure

The repository conforms strictly to the Capstone Project Submission Guidelines:

```text
Nishanth_EduTech/
├── architecture/
│   ├── Architecture_Diagram.pdf     # High-resolution vector architecture diagram
│   └── Architecture_Diagram.png     # 300 DPI architecture diagram image
├── design/
│   └── Design_Document.pdf          # Comprehensive engineering design PDF
├── docs/
│   ├── API_Documentation.pdf        # Complete REST API documentation PDF
│   ├── Dataset_Details.pdf          # OULAD dataset specifications & key fields PDF
│   └── Evaluation_Report.pdf        # Empirical benchmarks, DeepEval & RAGAS PDF
├── presentation/
│   └── Project_Presentation.pptx     # 10-minute presentation deck (Section 12 compliant)
├── src/
│   ├── api/                         # FastAPI application, routers, schemas, jobs
│   ├── agents/                      # Multi-agent workflow, copilot, guardrails, critic
│   ├── rag/                         # Hybrid retriever (BM25 + kNN), descriptors, index
│   ├── services/                    # Application service orchestration layer
│   ├── utils/                       # Shared helper utilities and logger
│   ├── frontend.py                  # Streamlit interface entry point inside src
│   └── main.py                      # Main FastAPI microservice entrypoint
├── ssa/                             # Machine learning, data pipeline, and evaluation engine
├── data/
│   ├── sample_data/                 # Standalone sample OULAD CSVs for quick evaluation
│   ├── raw/                         # Raw 7 OULAD CSV tables (.gitkeep)
│   └── processed/                   # Generated temporal feature snapshots (.gitkeep)
├── artifacts/
│   ├── analysis/                    # Factor analysis, trends, and assessment analytics
│   └── metrics/                     # Checkpoint summaries, LLM evaluations, quality gate
├── tests/                           # 56 automated unit and integration tests
├── frontend.py                      # Root Streamlit web application
├── requirements.txt                 # Full Python dependencies
├── pyproject.toml                   # Project metadata and test configuration
├── README.md                        # Primary documentation
├── .gitignore                       # Git ignore configuration
└── .dockerignore                    # Docker ignore configuration
```

---

## 7. Installation & Environment Setup

### Prerequisites
- Python 3.10, 3.11, or 3.12
- Git

### Environment Setup
Clone the repository and create an isolated virtual environment:
```bash
git clone <repository-url>
cd Nishanth_EduTech
python -m venv .venv

# On Linux / macOS:
source .venv/bin/activate

# On Windows:
.venv\Scripts\activate
```

### Dependency Installation
Install required packages:
```bash
pip install -r requirements.txt
```

### API Key Configuration
Copy `.env.example` to `.env` and set your configuration:
```bash
cp .env.example .env
```
Key configuration parameters:
```ini
STUDENT_ASSISTANT_API_KEY=<generate_secure_key>
STUDENT_ASSISTANT_ADMIN_KEY=<generate_admin_key>
OPENAI_API_KEY=<optional_openai_key>   # Optional: deterministic fallbacks work without LLM
```

---

## 8. Local Deployment Instructions

### Option A: Run the Backend Microservice (FastAPI / Uvicorn)
Start the REST API server:
```bash
uvicorn src.main:app --reload --port 8000
```
- Interactive Swagger UI: `http://127.0.0.1:8000/api/docs`
- OpenAPI JSON Spec: `http://127.0.0.1:8000/api/openapi.json`
- Health check: `http://127.0.0.1:8000/api/health`

### Option B: Run the Front-End Interface (Streamlit)
Launch the interactive Streamlit dashboard:
```bash
streamlit run frontend.py
```
*Note: The Streamlit application features an integrated auto-fallback mode that runs locally even if the separate FastAPI process has not been launched.*


---

## 9. Sample User Queries & Expected Outputs

### Query 1: Full Multi-Agent Student Diagnosis & Intervention Plan
**Request:**
```bash
curl -X POST http://127.0.0.1:8000/api/analyze \
  -H "X-API-Key: test-key-0123456789abcdef" \
  -H "Content-Type: application/json" \
  -d '{
    "student": {
      "id_student": 59272,
      "code_module": "BBB",
      "code_presentation": "2014J"
    },
    "checkpoint": 0.40
  }'
```
**Expected Output:**
```json
{
  "student": {"id_student": 59272, "code_module": "BBB", "code_presentation": "2014J"},
  "checkpoint": 0.4,
  "withdrawal_risk": {
    "withdrawal_risk": 0.682,
    "risk_tier": "High",
    "drivers": [
      {"label": "Days since last activity", "direction": "increases_risk", "shap_value": 0.412},
      {"label": "Missed assessments", "direction": "increases_risk", "shap_value": 0.285}
    ]
  },
  "outcome_prediction": {
    "predicted_outcome": "Fail",
    "p_poor_outcome": 0.814
  },
  "plan": {
    "narrative": {
      "summary": "Student 59272 is in the High risk tier with 18 days of zero VLE engagement and an unsubmitted TMA 02."
    },
    "actions": [
      {
        "action_id": "tutor_check_in",
        "title": "1-on-1 Academic Tutoring Check-In",
        "description": "Schedule a supportive check-in regarding assessment TMA 02.",
        "priority": "High"
      }
    ],
    "critic_report": {
      "valid": true,
      "violations": []
    }
  }
}
```

---

### Query 2: Hybrid RAG Search for Similar Historical Precedents
**Request:**
```bash
curl -X POST http://127.0.0.1:8000/api/retrieve-similar \
  -H "X-API-Key: test-key-0123456789abcdef" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "repeat students with heavy credit workloads who missed assessments and withdrew",
    "top_k": 3,
    "checkpoint": 0.40,
    "filters": {
      "code_module": "BBB",
      "num_of_prev_attempts": {"min": 1}
    }
  }'
```
**Expected Output:**
```json
{
  "outcome_summary": {
    "withdrawal_rate": 0.74,
    "poor_outcome_rate": 0.89,
    "withdrawal_rate_95ci": {"lower": 0.59, "upper": 0.85}
  },
  "cases": [
    {
      "case_id": "BBB_2013J_48123",
      "code_presentation": "2013J",
      "final_result": "Withdrawn",
      "score": 0.912,
      "story": {
        "text": "Repeat student was inactive for 19 days after TMA 01 and formally withdrew in course week 18."
      }
    }
  ]
}
```

---

### Query 3: Advisor Copilot Verifiable Tool Q&A
**Request:**
```bash
curl -X POST http://127.0.0.1:8000/api/copilot \
  -H "X-API-Key: test-key-0123456789abcdef" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Who should I contact first in BBB 2014J and why?",
    "checkpoint": 0.40
  }'
```
**Expected Output:**
```json
{
  "answer": "In BBB 2014J at Week 15, prioritize student 59272. They are in the High risk tier (withdrawal risk 68.2%) having missed TMA 02 and remained inactive on the VLE for 18 consecutive days.",
  "tool_calls": [
    {
      "tool": "rank_cohort",
      "arguments": {"code_module": "BBB", "code_presentation": "2014J", "capacity": 0.1}
    }
  ],
  "grounding_verified": true
}
```

---

## 10. Running Automated Tests & Verification
Run the complete unit and integration test suite:
```bash
pytest --basetemp=pytest_temp tests
```
*Result: 56 passed tests in ~45 seconds, verifying API contracts, model calibration, pipeline temporal isolation, hybrid retrieval, and multi-agent guardrails.*

---

## 11. Deliverables Checklist

- [x] **Architecture Diagram:** Available in [`architecture/Architecture_Diagram.pdf`](architecture/Architecture_Diagram.pdf) and [`architecture/Architecture_Diagram.png`](architecture/Architecture_Diagram.png)
- [x] **Design Document:** Available in [`design/Design_Document.pdf`](design/Design_Document.pdf)
- [x] **Complete Source Code:** Organized in [`src/`](src/) (`api`, `agents`, `rag`, `services`, `utils`, `main.py`)
- [x] **README File:** Comprehensive setup, deployment, stack, and query guide
- [x] **API Documentation:** Available in [`docs/API_Documentation.pdf`](docs/API_Documentation.pdf)
- [x] **Dataset Details:** Available in [`docs/Dataset_Details.pdf`](docs/Dataset_Details.pdf)
- [x] **Presentation Deck:** Available in [`presentation/Project_Presentation.pptx`](presentation/Project_Presentation.pptx)
- [x] **Evaluation Report:** Available in [`docs/Evaluation_Report.pdf`](docs/Evaluation_Report.pdf)
- [x] **Sample Test Cases:** 56 passing test cases in [`tests/`](tests/)
- [x] **Sample Data:** Packaged sample CSVs in [`data/sample_data/`](data/sample_data/)
- [x] **Local Execution:** Verified with FastAPI (`src.main:app`) and Streamlit (`frontend.py`)
