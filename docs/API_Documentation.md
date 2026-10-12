<div class="cover" markdown="1">

# API Documentation

<div class="sub">Uplift: Student Success Assistant · REST API v6.0.0</div>
<div class="meta">39 operations. Generated from the running service's OpenAPI specification; every sample
request and response below is a real call made on 2026-10-12 22:00 (responses trimmed for length only: long lists
show their first items and are marked "... N more").</div>

</div>

## 1. Overview
| Item | Value |
|---|---|
| Base URL (local) | `http://127.0.0.1:8000` |
| Start the service | `uvicorn src.main:app --reload` (from the repository root, virtual environment active) |
| Interactive documentation | `http://127.0.0.1:8000/api/docs` (Swagger UI); OpenAPI JSON at `/api/openapi.json` |
| Format | JSON in and out (`Content-Type: application/json`), UTF-8. `/api/copilot/stream` returns server-sent events. |
| Authentication | Header `X-API-Key: <STUDENT_ASSISTANT_API_KEY>` on every route except `/api/health`. `SSA_DEV_MODE=1` disables the key check for local demos. `/api/feedback-loop/run` also needs `X-Admin-Key`. |
| Course checkpoint | Most routes take `checkpoint` (share of the course: 0.15, 0.25, 0.40, 0.60 = weeks 5, 9, 15, 22). Omitted = week 15. |
| Rate limit | Token bucket per client (120 requests per minute by default, `RATE_LIMIT_PER_MINUTE`); 429 with `Retry-After` when exceeded. |
| Body size | Requests above 512 KB are rejected with 413. |
| Tracing | Every response carries `X-Request-ID`; error bodies repeat it as `request_id`. |

### Error format
Every error uses one envelope: `{"error": "...", "request_id": "...", "details": [...]}` (details only for validation
errors). Status codes: 400 invalid input, 401 missing or wrong API key, 403 admin key required, 404 unknown student,
job or recommendation, 409 the student had already unregistered at that checkpoint, 413 body too large, 429 rate limit,
503 artifacts not built yet (`python -m src.cli build`), 500 internal error (no internals are exposed).

Example (`POST /api/predict-risk` with an invalid student reference, HTTP 400):

```json
{
  "error": "validation error",
  "request_id": "446798e4b55f43e2afb332537c7c93fd",
  "details": [
    {
      "loc": "student.id_student",
      "msg": "Input should be greater than 0",
      "type": "greater_than"
    },
    {
      "loc": "student.code_module",
      "msg": "Input should be 'AAA', 'BBB', 'CCC', 'DDD', 'EEE', 'FFF' or 'GGG'",
      "type": "literal_error"
    }
  ]
}
```

### Endpoint index
| Method | Endpoint | Summary |
|---|---|---|
| GET | `/api/health` | Liveness |
| GET | `/api/ready` | Readiness |
| GET | `/api/config` | Console configuration |
| GET | `/api/overview` | All presentations at a checkpoint |
| GET | `/api/cohort` | One presentation at a checkpoint |
| GET | `/api/students` | List students |
| POST | `/api/prioritize` | Rank students for advisor capacity |
| GET | `/api/students/{id_student}` | Student snapshot |
| POST | `/api/predict-risk` | Predict withdrawal risk and outcome |
| POST | `/api/students/timeline` | Risk at every checkpoint |
| POST | `/api/trends/student` | Weekly activity trend |
| POST | `/api/analyze` | Run the support workflow (synchronous) |
| POST | `/api/jobs/analyze` | Run the support workflow (background job) |
| POST | `/api/jobs/briefing` | Cohort briefing (background job) |
| POST | `/api/jobs/copilot` | Copilot (background job) |
| GET | `/api/jobs/{job_id}` | Job status |
| POST | `/api/cohort/briefing` | Cohort briefing |
| POST | `/api/copilot` | Ask the copilot |
| POST | `/api/copilot/stream` | Ask the copilot (streamed) |
| POST | `/api/outreach/variants` | Rewrite an outreach message |
| POST | `/api/search/parse` | Understand a search request |
| POST | `/api/retrieve-similar` | Find similar historical students (hybrid RAG) |
| GET | `/api/trends/course` | Engagement trends by outcome |
| GET | `/api/insights/factors` | Factors behind poor outcomes |
| GET | `/api/insights/assessments` | Assessment analytics |
| GET | `/api/insights/checkpoints` | Model quality by checkpoint |
| GET | `/api/metrics` | All evaluation metrics |
| GET | `/api/evaluations/llm` | AI evaluation results |
| GET | `/api/evaluations/online` | Live reviews |
| POST | `/api/evaluations/judge` | Judge a support plan |
| GET | `/api/evaluations/human-review` | Cases for human review |
| POST | `/api/evaluations/human-labels` | Save a human rating |
| GET | `/api/llm/usage` | AI usage and cost |
| POST | `/api/feedback` | Submit advisor feedback |
| GET | `/api/feedback` | Recent feedback |
| GET | `/api/feedback/summary` | Feedback summary |
| GET | `/api/feedback/themes` | Themes in advisor notes |
| GET | `/api/improvement-plan` | Improvement proposals |
| POST | `/api/feedback-loop/run` | Run the feedback loop (admin) |


## System
Liveness, readiness and the configuration the console needs.

### <span class="method GET">GET</span> `/api/health`
**Liveness.** Always 200 while the process is up. The only route that needs no API key.

| Endpoint | HTTP method | Authentication | Responses |
|---|---|---|---|
| `/api/health` | GET | none | 200 |

**Request format:** no parameters or body.

**Response format** (JSON object, HTTP 200):
`status` (string).

**Sample request**
```bash
curl -X GET "http://127.0.0.1:8000/api/health"
```

**Sample response** (HTTP 200, 0.01 s)

```json
{
  "status": "ok"
}
```

---

### <span class="method GET">GET</span> `/api/ready`
**Readiness.** Which build artifacts exist (features, models, prioritiser, case index), the checkpoints built and the index size. Use it to check a fresh install.

| Endpoint | HTTP method | Authentication | Responses |
|---|---|---|---|
| `/api/ready` | GET | X-API-Key | 200 |

**Request format:** no parameters or body.

**Response format** (JSON object, HTTP 200):
`ready` (boolean), `checks` (object), `checkpoints` (array), `index` (object), `llm_configured` (boolean), `llm_provider` (string), `llm_model` (string), `fast_model` (string), `judge_model` (string).

**Sample request**
```bash
curl -X GET "http://127.0.0.1:8000/api/ready" \
  -H "X-API-Key: $STUDENT_ASSISTANT_API_KEY"
```

**Sample response** (HTTP 200, 0.02 s)

```json
{
  "ready": true,
  "checks": {
    "features": true,
    "course_level_records": true,
    "withdrawal_model": true,
    "outcome_model": true,
    "prioritization": true,
    "retrieval_index": true
  },
  "checkpoints": [
    {
      "checkpoint": 0.15,
      "tag": "c15",
      "approx_week": 5,
      "primary": false,
      "available": true
    },
    {
      "checkpoint": 0.25,
      "tag": "c25",
      "approx_week": 9,
      "primary": false,
      "available": true
    },
    "... 2 more"
  ],
  "index": {
    "index_version": "5.0",
    "built_at": "2026-10-12T10:41:37",
    "n_docs": 25204,
    "presentations": [
      "2013B",
      "2013J",
      "... 2 more"
    ],
    "dense_channel": "built",
    "embedding_model": "intfloat/e5-small-v2",
    "embedding_query_prefix": "query: ",
    "embedding_passage_prefix": "passage: ",
    "vector_checksum": "66d383963018909a",
    "vector_store": "lancedb",
    "supervised_feature_weights": true,
    "build_seconds": 478.4
  },
  "llm_configured": true,
  "llm_provider": "anthropic",
  "llm_model": "claude-sonnet-5-5",
  "fast_model": "claude-haiku-5-5",
  "judge_model": "claude-opus-5-5"
}
```

---

### <span class="method GET">GET</span> `/api/config`
**Console configuration.** Checkpoints with their course week, modules and presentations, the temporal split, vocabularies for filters, LLM models in use and the dense-retrieval status.

| Endpoint | HTTP method | Authentication | Responses |
|---|---|---|---|
| `/api/config` | GET | X-API-Key | 200 |

**Request format:** no parameters or body.

**Response format** (JSON object, HTTP 200):
`checkpoints` (array), `modules` (array), `presentations_by_module` (object), `latest_presentation` (string), `vocab` (object), `features` (object), `llm` (object), `dense_retrieval` (string), `split` (object).

**Sample request**
```bash
curl -X GET "http://127.0.0.1:8000/api/config" \
  -H "X-API-Key: $STUDENT_ASSISTANT_API_KEY"
```

**Sample response** (HTTP 200, 10.8 s)

```json
{
  "checkpoints": [
    {
      "checkpoint": 0.15,
      "tag": "c15",
      "approx_week": 5,
      "primary": false,
      "available": true
    },
    {
      "checkpoint": 0.25,
      "tag": "c25",
      "approx_week": 9,
      "primary": false,
      "available": true
    },
    "... 2 more"
  ],
  "modules": [
    "AAA",
    "BBB",
    "... 5 more"
  ],
  "presentations_by_module": {
    "AAA": [
      "2013J",
      "2014J"
    ],
    "BBB": [
      "2013B",
      "2013J",
      "... 2 more"
    ],
    "CCC": [
      "2014B",
      "2014J"
    ],
    "DDD": [
      "2013B",
      "2013J",
      "... 2 more"
    ],
    "EEE": [
      "2013J",
      "2014B",
      "... 1 more"
    ],
    "FFF": [
      "2013B",
      "2013J",
      "... 2 more"
    ],
    "GGG": [
      "2013J",
      "2014B",
      "... 1 more"
    ]
  },
  "latest_presentation": "2014J",
  "vocab": {
    "regions": [
      "East Anglian Region",
      "East Midlands Region",
      "... 11 more"
    ],
    "education": [
      "No Formal quals",
      "Lower Than A Level",
      "... 3 more"
    ],
    "age_bands": [
      "0-35",
      "35-55",
      "... 1 more"
    ],
    "outcomes": [
      "Distinction",
      "Pass",
      "... 2 more"
    ]
  },
  "features": {
    "num_of_prev_attempts": "Previous attempts at this module",
    "studied_credits": "Credits studied this term",
    "registration_days_before_start": "How early the student registered",
    "registration_date_missing": "Registration date missing",
    "late_registration": "Registered after start",
    "snapshot_day": "Course day of snapshot",
    "weeks_observed": "Weeks observed",
    "assessments_due": "Assessments due so far",
    "submitted_count": "Assessments submitted",
    "submitted_due_count": "Due assessments submitted",
    "missed_count": "Missed assessments",
    "missed_rate": "Share of due assessments missed",
    "...": "54 more fields"
  },
  "llm": {
    "configured": true,
    "enabled": true,
    "provider": "anthropic",
    "model": "claude-sonnet-5-5",
    "fast_model": "claude-haiku-5-5",
    "judge_model": "claude-opus-5-5",
    "online_eval_sample_rate": 0.1
  },
  "dense_retrieval": "built",
  ... (trimmed for the document; the API returns the full response)
```

---

## Cohort
Cohort views at a course checkpoint: overview, one presentation, student lists, ranking.

### <span class="method GET">GET</span> `/api/overview`
**All presentations at a checkpoint.** Per module presentation: students still enrolled, tier mix, expected withdrawals and students already gone.

| Endpoint | HTTP method | Authentication | Responses |
|---|---|---|---|
| `/api/overview` | GET | X-API-Key | 200, 400 |

**Request format: parameters**

| Name | In | Type | Required | Constraints | Description |
|---|---|---|---|---|---|
| `checkpoint` | query | number (optional) | no | >= 0.05, <= 0.95 | Course checkpoint (share of planned length) |

**Response format** (JSON object, HTTP 200):
`checkpoint` (number), `presentations` (array), `totals` (object), `thresholds` (object).

**Sample request**
```bash
curl -X GET "http://127.0.0.1:8000/api/overview?checkpoint=0.4" \
  -H "X-API-Key: $STUDENT_ASSISTANT_API_KEY"
```

**Sample response** (HTTP 200, 0.07 s)

```json
{
  "checkpoint": 0.4,
  "presentations": [
    {
      "code_module": "AAA",
      "code_presentation": "2013J",
      "enrolled": 383,
      "in_scope": 355,
      "already_withdrawn": 28,
      "high": 58,
      "medium": 158,
      "low": 139,
      "expected_withdrawals": 35.9,
      "expected_fail_or_withdraw": 104.0,
      "snapshot_day": 107
    },
    {
      "code_module": "AAA",
      "code_presentation": "2014J",
      "enrolled": 365,
      "in_scope": 333,
      "already_withdrawn": 32,
      "high": 59,
      "medium": 133,
      "low": 141,
      "expected_withdrawals": 33.8,
      "expected_fail_or_withdraw": 110.1,
      "snapshot_day": 108
    },
    "... 20 more"
  ],
  "totals": {
    "enrolled": 32593,
    "in_scope": 25204,
    "already_withdrawn": 7389,
    "high": 6646,
    "medium": 6187,
    "low": 12371
  },
  "thresholds": {
    "medium": 0.0771072325145041,
    "high": 0.14122656421985777,
    "method": "validation_f1_above_medium",
    "medium_recall_target": 0.8,
    "validation": {
      "medium": {
        "threshold": 0.0771072325145041,
        "precision": 0.16940143286341577,
        "recall": 0.8002183406113537,
        "flag_rate": 0.5142925060914008
      },
      "high": {
        "threshold": 0.14122656421985777,
        "precision": 0.23717059639389737,
        "recall": 0.5600436681222707,
        "flag_rate": 0.257086824745944
      }
    }
  }
}
```

---

### <span class="method GET">GET</span> `/api/cohort`
**One presentation at a checkpoint.** Enrolled / in-scope counts, tier counts, expected withdrawals and fail-or-withdraw, risk histogram, tier thresholds, common High-tier drivers, median weekly activity and assessment deadlines.

| Endpoint | HTTP method | Authentication | Responses |
|---|---|---|---|
| `/api/cohort` | GET | X-API-Key | 200, 400 |

**Request format: parameters**

| Name | In | Type | Required | Constraints | Description |
|---|---|---|---|---|---|
| `code_module` | query | string | yes |  |  |
| `code_presentation` | query | string | yes |  |  |
| `checkpoint` | query | number (optional) | no | >= 0.05, <= 0.95 | Course checkpoint (share of planned length) |

**Response format** (JSON object, HTTP 200):
`code_module` (string), `code_presentation` (string), `checkpoint` (number), `snapshot_day` (integer), `snapshot_week` (integer), `course_length_days` (integer), `enrolled` (integer), `in_scope` (integer), `already_withdrawn` (integer), `tiers` (object), `expected_withdrawals` (number), `expected_fail_or_withdraw` (number), `risk_histogram` (object), `thresholds` (object), `common_high_tier_drivers` (array), `cohort_median_weekly_clicks` (array), `medians` (object), `assessments` (array).

**Sample request**
```bash
curl -X GET "http://127.0.0.1:8000/api/cohort?code_module=BBB&code_presentation=2014J&checkpoint=0.4" \
  -H "X-API-Key: $STUDENT_ASSISTANT_API_KEY"
```

**Sample response** (HTTP 200, 0.14 s)

```json
{
  "code_module": "BBB",
  "code_presentation": "2014J",
  "checkpoint": 0.4,
  "snapshot_day": 105,
  "snapshot_week": 15,
  "course_length_days": 262,
  "enrolled": 2292,
  "in_scope": 1702,
  "already_withdrawn": 590,
  "tiers": {
    "High": 341,
    "Medium": 507,
    "Low": 854
  },
  "expected_withdrawals": 157.5,
  "expected_fail_or_withdraw": 763.6,
  "...": "6 more fields"
}
```

---

### <span class="method GET">GET</span> `/api/students`
**List students.** Students still enrolled in a presentation with computed signals; sort, tier filter, ID search and paging. Students who already left are excluded by design.

| Endpoint | HTTP method | Authentication | Responses |
|---|---|---|---|
| `/api/students` | GET | X-API-Key | 200, 400 |

**Request format: parameters**

| Name | In | Type | Required | Constraints | Description |
|---|---|---|---|---|---|
| `code_module` | query | string | yes |  |  |
| `code_presentation` | query | string | yes |  |  |
| `checkpoint` | query | number (optional) | no | >= 0.05, <= 0.95 | Course checkpoint (share of planned length) |
| `tier` | query | string (optional) | no |  |  |
| `search` | query | string (optional) | no | max length 10 |  |
| `sort` | query | string | no | default `"withdrawal_risk"` |  |
| `descending` | query | boolean | no | default `true` |  |
| `limit` | query | integer | no | >= 1, <= 5000, default `200` |  |
| `offset` | query | integer | no | >= 0, default `0` |  |

**Response format** (JSON object, HTTP 200):
`total` (integer), `offset` (integer), `limit` (integer), `checkpoint` (number), `students` (array).

**Sample request**
```bash
curl -X GET "http://127.0.0.1:8000/api/students?code_module=BBB&code_presentation=2014J&checkpoint=0.4&tier=High&sort=withdrawal_risk&limit=3" \
  -H "X-API-Key: $STUDENT_ASSISTANT_API_KEY"
```

**Sample response** (HTTP 200, 0.02 s)

```json
{
  "total": 341,
  "offset": 0,
  "limit": 3,
  "checkpoint": 0.4,
  "students": [
    {
      "id_student": 652288,
      "weighted_score": 1.0,
      "score_pct": 0.0128597672994488,
      "missed_rate": 0.5,
      "clicks_pct": 0.9054054054054054,
      "days_since_last_activity": 3.0,
      "engagement_momentum": -0.992722,
      "num_of_prev_attempts": 0,
      "studied_credits": 60,
      "in_scope": 1,
      "withdrawal_risk": 0.5209726790195787,
      "p_poor_outcome": 0.9040288396993452,
      "...": "1 more fields"
    },
    {
      "id_student": 632605,
      "weighted_score": 1.0,
      "score_pct": 0.0128597672994488,
      "missed_rate": 0.5,
      "clicks_pct": 0.9212690951821386,
      "days_since_last_activity": 11.0,
      "engagement_momentum": -0.99647886,
      "num_of_prev_attempts": 1,
      "studied_credits": 60,
      "in_scope": 1,
      "withdrawal_risk": 0.4038699777253766,
      "p_poor_outcome": 0.9379578227833447,
      "...": "1 more fields"
    },
    "... 1 more"
  ]
}
```

---

### <span class="method POST">POST</span> `/api/prioritize`
**Rank students for advisor capacity.** Ranks a presentation's enrolled students with weights learned on an earlier presentation, marks who fits the capacity and gives the reasons for each.

| Endpoint | HTTP method | Authentication | Responses |
|---|---|---|---|
| `/api/prioritize` | POST | X-API-Key | 200, 400 |

**Request format: JSON body** (`PrioritizeRequestV2`)

| Field | Type | Required | Constraints | Description |
|---|---|---|---|---|
| `code_module` | one of `AAA`, `BBB`, `CCC`, `DDD`, `EEE`, `FFF`, `GGG` (optional) | no |  |  |
| `code_presentation` | string (optional) | no |  |  |
| `students` | array of StudentRef (optional) | no | max items 2000 |  |
| `profiles` | array of FeatureProfile (optional) | no | max items 500 |  |
| `capacity` | number (optional) | no | > 0.0, <= 1.0, default `0.2` |  |
| `limit` | integer | no | >= 1.0, <= 2000.0, default `100` |  |
| `checkpoint` | number (optional) | no | >= 0.05, <= 0.95 | Share of the planned course length; nearest built checkpoint is used |

Types written in CamelCase (for example `StudentRef`) are described once in *Appendix: shared request models*.

**Response format** (JSON object, HTTP 200):
`source` (string), `checkpoint` (number), `cohort_size` (integer), `capacity` (number), `weights` (object), `weights_provenance` (string), `ranking` (array), `input_quality` (null).

**Sample request**
```bash
curl -X POST "http://127.0.0.1:8000/api/prioritize" \
  -H "X-API-Key: $STUDENT_ASSISTANT_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"code_module": "BBB", "code_presentation": "2014J", "capacity": 0.1, "limit": 3, "checkpoint": 0.4}'
```

**Sample response** (HTTP 200, 0.06 s)

```json
{
  "source": "feature_store_presentation",
  "checkpoint": 0.4,
  "cohort_size": 1702,
  "capacity": 0.1,
  "weights": {
    "p_withdraw": 0.1,
    "p_poor": 0.75,
    "academic_gap": 0.05,
    "engagement_gap": 0.05,
    "missed_work": 0.05,
    "recent_decline": 0.0
  },
  "weights_provenance": "exhaustive simplex grid (step 0.05, 53130 weightings) on the validation presentation; rule one_se_blend",
  "ranking": [
    {
      "priority_rank": 1,
      "id_student": 692826,
      "code_module": "BBB",
      "code_presentation": "2014J",
      "priority_score": 0.9621,
      "within_capacity": true,
      "withdrawal_risk": 0.2494,
      "risk_tier": "High",
      "p_poor_outcome": 0.9619,
      "signals": {
        "p_withdraw": 0.2494,
        "p_poor": 0.9619,
        "academic_gap": 0.9871,
        "engagement_gap": 0.8666,
        "missed_work": 0.5,
        "recent_decline": 0.9048
      },
      "weighted_contributions": {
        "p_withdraw": 0.0989,
        "p_poor": 0.724,
        "academic_gap": 0.0494,
        "engagement_gap": 0.0434,
        "missed_work": 0.0464,
        "recent_decline": 0.0
      },
      "reasons": [
        "Low score relative to cohort",
        "Missed due assessments",
        "... 1 more"
      ],
      "...": "1 more fields"
    },
    {
      "priority_rank": 2,
      "id_student": 656755,
      "code_module": "BBB",
      "code_presentation": "2014J",
      "priority_score": 0.9593,
      "within_capacity": true,
      "withdrawal_risk": 0.2336,
      "risk_tier": "High",
      "p_poor_outcome": 0.9582,
      "signals": {
        "p_withdraw": 0.2336,
        "p_poor": 0.9582,
        "academic_gap": 0.955,
        "engagement_gap": 0.9659,
        "missed_work": 0.5,
        "recent_decline": -0.0
      },
      "weighted_contributions": {
        "p_withdraw": 0.0984,
        "p_poor": 0.7183,
        "academic_gap": 0.0479,
        "engagement_gap": 0.0483,
        "missed_work": 0.0464,
        "recent_decline": 0.0
      },
      "reasons": [
        "Low activity relative to cohort",
        "Low score relative to cohort",
        "... 1 more"
      ],
      "...": "1 more fields"
    },
    "... 1 more"
  ],
  ... (trimmed for the document; the API returns the full response)
```

---

## Student
One student: calibrated risk with drivers, what-if, snapshot, risk across checkpoints.

### <span class="method GET">GET</span> `/api/students/{id_student}`
**Student snapshot.** The student's features as of the checkpoint (only what was known then). 409 if they had already unregistered.

| Endpoint | HTTP method | Authentication | Responses |
|---|---|---|---|
| `/api/students/{id_student}` | GET | X-API-Key | 200, 400 |

**Request format: parameters**

| Name | In | Type | Required | Constraints | Description |
|---|---|---|---|---|---|
| `id_student` | path | integer | yes |  |  |
| `code_module` | query | string | yes |  |  |
| `code_presentation` | query | string | yes |  |  |
| `checkpoint` | query | number (optional) | no | >= 0.05, <= 0.95 | Course checkpoint (share of planned length) |

**Response format** (JSON object, HTTP 200):
`snapshot` (object), `labels` (object), `note` (string).

**Sample request**
```bash
curl -X GET "http://127.0.0.1:8000/api/students/692826?code_module=BBB&code_presentation=2014J&checkpoint=0.4" \
  -H "X-API-Key: $STUDENT_ASSISTANT_API_KEY"
```

**Sample response** (HTTP 200, 0.0 s)

```json
{
  "snapshot": {
    "code_module": "BBB",
    "code_presentation": "2014J",
    "id_student": 692826,
    "num_of_prev_attempts": 0,
    "studied_credits": 60,
    "date_registration": -39.0,
    "presentation_id": 5,
    "length": 262,
    "snapshot_day": 105,
    "snapshot_week": 15,
    "enrollment_key": 50692826,
    "registration_date_missing": 0,
    "...": "66 more fields"
  },
  "labels": {
    "code_module": "Module",
    "num_of_prev_attempts": "Previous attempts at this module",
    "studied_credits": "Credits studied this term",
    "snapshot_day": "Course day of snapshot",
    "registration_date_missing": "Registration date missing",
    "registration_days_before_start": "How early the student registered",
    "late_registration": "Registered after start",
    "submitted_count": "Assessments submitted",
    "submitted_due_count": "Due assessments submitted",
    "late_rate": "Late submission rate",
    "mean_days_early": "Average days submitted before deadline",
    "banked_count": "Banked results",
    "...": "55 more fields"
  },
  "note": "Outcome labels and sensitive attributes are not exposed."
}
```

---

### <span class="method POST">POST</span> `/api/predict-risk`
**Predict withdrawal risk and outcome.** Calibrated withdrawal risk, tier and TreeSHAP drivers, plus the four-class outcome model. Accepts a student reference or a raw feature profile; `what_if` overrides signals.

| Endpoint | HTTP method | Authentication | Responses |
|---|---|---|---|
| `/api/predict-risk` | POST | X-API-Key | 200, 400 |

**Request format: JSON body** (`PredictRequest`)

| Field | Type | Required | Constraints | Description |
|---|---|---|---|---|
| `student` | StudentRef (optional) | no |  |  |
| `profile` | FeatureProfile (optional) | no |  |  |
| `what_if` | object of number or integer (optional) (optional) | no |  |  |
| `checkpoint` | number (optional) | no | >= 0.05, <= 0.95 | Share of the planned course length; nearest built checkpoint is used |

Types written in CamelCase (for example `StudentRef`) are described once in *Appendix: shared request models*.

**Response format** (JSON object, HTTP 200):
`student` (object), `checkpoint` (number), `withdrawal_risk` (object), `outcome_prediction` (object), `input_quality` (object).

**Sample request**
```bash
curl -X POST "http://127.0.0.1:8000/api/predict-risk" \
  -H "X-API-Key: $STUDENT_ASSISTANT_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"student": {"id_student": 692826, "code_module": "BBB", "code_presentation": "2014J"}, "checkpoint": 0.4}'
```

**Sample response** (HTTP 200, 0.03 s)

```json
{
  "student": {
    "id_student": 692826,
    "code_module": "BBB",
    "code_presentation": "2014J"
  },
  "checkpoint": 0.4,
  "withdrawal_risk": {
    "withdrawal_risk": 0.2494,
    "risk_tier": "High",
    "thresholds": {
      "medium": 0.0771,
      "high": 0.1412
    },
    "drivers": [
      {
        "feature": "mean_score",
        "label": "Average assessment score",
        "value": 1.0,
        "contribution_logodds": 0.2757,
        "direction": "increases_risk",
        "method": "tree_shap"
      },
      {
        "feature": "min_score",
        "label": "Lowest score",
        "value": 1.0,
        "contribution_logodds": 0.1975,
        "direction": "increases_risk",
        "method": "tree_shap"
      },
      "... 4 more"
    ],
    "calibration": "platt_lopo",
    "interpretation": "Calibrated probability of withdrawing after the snapshot among students still enrolled. An early-warning estimate, not a diagnosis or a causal claim."
  },
  "outcome_prediction": {
    "predicted_outcome": "Fail",
    "probabilities": {
      "Distinction": 0.0066,
      "Pass": 0.0315,
      "Fail": 0.734,
      "Withdrawn": 0.2279
    },
    "decision_rule": "balanced_argmax (macro-F1 optimised); probabilities are calibrated",
    "p_poor_outcome": 0.9619
  },
  "input_quality": {
    "source": "feature_store",
    "imputed_fields": [],
    "out_of_distribution": [],
    "key_signal_completeness": 1.0,
    "confidence": "normal",
    "checkpoint": 0.4
  }
}
```
**Sample request** (what-if)
```bash
curl -X POST "http://127.0.0.1:8000/api/predict-risk" \
  -H "X-API-Key: $STUDENT_ASSISTANT_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"student": {"id_student": 692826, "code_module": "BBB", "code_presentation": "2014J"}, "checkpoint": 0.4, "what_if": {"days_since_last_activity": 3}}'
```

**Sample response** (HTTP 200, 0.03 s; The same student with one signal changed: only the fields in what_if are overridden.)

```json
{
  "student": {
    "id_student": 692826,
    "code_module": "BBB",
    "code_presentation": "2014J"
  },
  "checkpoint": 0.4,
  "withdrawal_risk": {
    "withdrawal_risk": 0.2925,
    "risk_tier": "High",
    "thresholds": {
      "medium": 0.0771,
      "high": 0.1412
    },
    "drivers": [
      {
        "feature": "mean_score",
        "label": "Average assessment score",
        "value": 1.0,
        "contribution_logodds": 0.2774,
        "direction": "increases_risk",
        "method": "tree_shap"
      },
      {
        "feature": "min_score",
        "label": "Lowest score",
        "value": 1.0,
        "contribution_logodds": 0.1975,
        "direction": "increases_risk",
        "method": "tree_shap"
      },
      "... 4 more"
    ],
    "calibration": "platt_lopo",
    "interpretation": "Calibrated probability of withdrawing after the snapshot among students still enrolled. An early-warning estimate, not a diagnosis or a causal claim."
  },
  "outcome_prediction": {
    "predicted_outcome": "Fail",
    "probabilities": {
      "Distinction": 0.0069,
      "Pass": 0.0568,
      "Fail": 0.6847,
      "Withdrawn": 0.2516
    },
    "decision_rule": "balanced_argmax (macro-F1 optimised); probabilities are calibrated",
    "p_poor_outcome": 0.9363
  },
  "input_quality": {
    "source": "feature_store+overrides",
    "imputed_fields": [],
    "out_of_distribution": [],
    "key_signal_completeness": 1.0,
    "confidence": "normal",
    "checkpoint": 0.4
  }
}
```

---

### <span class="method POST">POST</span> `/api/students/timeline`
**Risk at every checkpoint.** The student's risk recomputed at each built checkpoint, using only the data available at that point.

| Endpoint | HTTP method | Authentication | Responses |
|---|---|---|---|
| `/api/students/timeline` | POST | X-API-Key | 200, 400 |

**Request format: JSON body** (`TimelineRequest`)

| Field | Type | Required | Constraints | Description |
|---|---|---|---|---|
| `student` | StudentRef | yes |  |  |

Types written in CamelCase (for example `StudentRef`) are described once in *Appendix: shared request models*.

**Response format** (JSON object, HTTP 200):
`student` (object), `points` (array), `note` (string).

**Sample request**
```bash
curl -X POST "http://127.0.0.1:8000/api/students/timeline" \
  -H "X-API-Key: $STUDENT_ASSISTANT_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"student": {"id_student": 692826, "code_module": "BBB", "code_presentation": "2014J"}}'
```

**Sample response** (HTTP 200, 30.07 s)

```json
{
  "student": {
    "id_student": 692826,
    "code_module": "BBB",
    "code_presentation": "2014J"
  },
  "points": [
    {
      "checkpoint": 0.15,
      "snapshot_week": 5,
      "in_scope": true,
      "withdrawal_risk": 0.4351,
      "risk_tier": "High",
      "p_poor_outcome": 0.8067,
      "weighted_score": 1.0,
      "clicks_pct": 0.2554806070826307,
      "missed_rate": 0.0
    },
    {
      "checkpoint": 0.25,
      "snapshot_week": 9,
      "in_scope": true,
      "withdrawal_risk": 0.3779,
      "risk_tier": "High",
      "p_poor_outcome": 0.9401,
      "weighted_score": 1.0,
      "clicks_pct": 0.1689734717416378,
      "missed_rate": 0.5
    },
    "... 2 more"
  ],
  "note": "Each point uses only information available at that checkpoint."
}
```

---

### <span class="method POST">POST</span> `/api/trends/student`
**Weekly activity trend.** Weekly clicks up to the checkpoint against the cohort median, deadlines and trend signals (drop, decline, inactivity).

| Endpoint | HTTP method | Authentication | Responses |
|---|---|---|---|
| `/api/trends/student` | POST | X-API-Key | 200, 400 |

**Request format: JSON body** (`PredictRequest`)

| Field | Type | Required | Constraints | Description |
|---|---|---|---|---|
| `student` | StudentRef (optional) | no |  |  |
| `profile` | FeatureProfile (optional) | no |  |  |
| `what_if` | object of number or integer (optional) (optional) | no |  |  |
| `checkpoint` | number (optional) | no | >= 0.05, <= 0.95 | Share of the planned course length; nearest built checkpoint is used |

Types written in CamelCase (for example `StudentRef`) are described once in *Appendix: shared request models*.

**Response format** (JSON object, HTTP 200):
`student` (object), `checkpoint` (number), `weekly_clicks` (array), `cohort_median_weekly_clicks` (array), `snapshot_week` (integer), `assessment_deadlines` (array), `engagement` (object), `academic` (object), `signals` (array), `note` (string).

**Sample request**
```bash
curl -X POST "http://127.0.0.1:8000/api/trends/student" \
  -H "X-API-Key: $STUDENT_ASSISTANT_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"student": {"id_student": 692826, "code_module": "BBB", "code_presentation": "2014J"}, "checkpoint": 0.4}'
```

**Sample response** (HTTP 200, 0.02 s)

```json
{
  "student": {
    "id_student": 692826,
    "code_module": "BBB",
    "code_presentation": "2014J"
  },
  "checkpoint": 0.4,
  "weekly_clicks": [
    0.0,
    19.0,
    "... 38 more"
  ],
  "cohort_median_weekly_clicks": [
    55.0,
    16.0,
    "... 38 more"
  ],
  "snapshot_week": 15,
  "assessment_deadlines": [
    {
      "week": 2,
      "type": "TMA",
      "weight": 0.0,
      "id": 15020
    },
    {
      "week": 7,
      "type": "TMA",
      "weight": 10.0,
      "id": 15021
    },
    "... 3 more"
  ],
  "engagement": {
    "engagement_slope": -1.2573529411764706,
    "engagement_slope_rel": -0.2073984232868405,
    "engagement_momentum": -0.9047619,
    "engagement_drop_ratio": 1.0,
    "longest_inactive_streak": 10,
    "inactive_weeks_last3": 3,
    "clicks_pct": 0.1333725029377203,
    "planned_coverage": 0.2352941176470588
  },
  "academic": {
    "weighted_score": 1.0,
    "score_pct": 0.0128597672994488,
    "score_slope": 0.0,
    "min_score": 1.0,
    "max_score": 1.0,
    "last_score": 1.0,
    "tma_mean_score": 1.0,
    "cma_mean_score": null,
    "missed_rate": 0.5,
    "late_rate": 1.0
  },
  "signals": [
    "recent_engagement_drop",
    "declining_weekly_trend",
    "... 2 more"
  ],
  "note": "Observed behaviour up to the checkpoint; descriptive, not causal."
}
```

---

## Agents
The multi-agent support workflow, cohort briefing, copilot and outreach rewriting.

### <span class="method POST">POST</span> `/api/analyze`
**Run the support workflow (synchronous).** Scores the student, retrieves similar cases, runs the LangGraph agents (performance, risk, router, intervention, critic, revision) and the precedent synthesis. Prefer the job form from a browser.

| Endpoint | HTTP method | Authentication | Responses |
|---|---|---|---|
| `/api/analyze` | POST | X-API-Key | 200, 400 |

**Request format: JSON body** (`AnalyzeRequestV2`)

| Field | Type | Required | Constraints | Description |
|---|---|---|---|---|
| `student` | StudentRef (optional) | no |  |  |
| `profile` | FeatureProfile (optional) | no |  |  |
| `what_if` | object of number or integer (optional) (optional) | no |  |  |
| `use_llm` | boolean | no | default `true` |  |
| `judge` | boolean | no | default `false` |  |
| `checkpoint` | number (optional) | no | >= 0.05, <= 0.95 | Share of the planned course length; nearest built checkpoint is used |
| `synthesize` | boolean | no | default `true` |  |

Types written in CamelCase (for example `StudentRef`) are described once in *Appendix: shared request models*.

**Response format** (JSON object, HTTP 200):
`student` (object), `checkpoint` (number), `withdrawal_risk` (object), `outcome_prediction` (object), `input_quality` (object), `similar_cases` (object), `workflow` (object), `precedent_synthesis` (object).

**Sample request**
```bash
curl -X POST "http://127.0.0.1:8000/api/analyze" \
  -H "X-API-Key: $STUDENT_ASSISTANT_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"student": {"id_student": 692826, "code_module": "BBB", "code_presentation": "2014J"}, "checkpoint": 0.4, "use_llm": true}'
```

**Sample response** (HTTP 200, 24.71 s)

```json
{
  "student": {
    "id_student": 692826,
    "code_module": "BBB",
    "code_presentation": "2014J"
  },
  "checkpoint": 0.4,
  "withdrawal_risk": {
    "withdrawal_risk": 0.2494,
    "risk_tier": "High",
    "thresholds": {
      "medium": 0.0771,
      "high": 0.1412
    },
    "drivers": [
      {
        "feature": "mean_score",
        "label": "Average assessment score",
        "value": 1.0,
        "contribution_logodds": 0.2757,
        "direction": "increases_risk",
        "method": "tree_shap"
      },
      {
        "feature": "min_score",
        "label": "Lowest score",
        "value": 1.0,
        "contribution_logodds": 0.1975,
        "direction": "increases_risk",
        "method": "tree_shap"
      },
      "... 4 more"
    ],
    "calibration": "platt_lopo",
    "interpretation": "Calibrated probability of withdrawing after the snapshot among students still enrolled. An early-warning estimate, not a diagnosis or a causal claim."
  },
  "outcome_prediction": {
    "predicted_outcome": "Fail",
    "probabilities": {
      "Distinction": 0.0066,
      "Pass": 0.0315,
      "Fail": 0.734,
      "Withdrawn": 0.2279
    },
    "decision_rule": "balanced_argmax (macro-F1 optimised); probabilities are calibrated",
    "p_poor_outcome": 0.9619
  },
  "input_quality": {
    "source": "feature_store",
    "imputed_fields": [],
    "out_of_distribution": [],
    "key_signal_completeness": 1.0,
    "confidence": "normal",
    "checkpoint": 0.4
  },
  "similar_cases": {
    "cases": [
      {
        "case_id": 32459051,
        "id_student": 2459051,
        "code_module": "BBB",
        "code_presentation": "2013J",
        "final_result": "Fail",
        "fusion_score": 0.024458,
        "behavioural_distance": 1.5152,
        "channel_ranks": "{...}",
        "shared_descriptors": [
          "module_bbb",
          "credits_standard",
          "... 6 more"
        ],
  ... (trimmed for the document; the API returns the full response)
```

---

### <span class="method POST">POST</span> `/api/jobs/analyze`
**Run the support workflow (background job).** Same as /api/analyze; returns 202 with a job id. Poll /api/jobs/{job_id} to see each agent step as it finishes.

| Endpoint | HTTP method | Authentication | Responses |
|---|---|---|---|
| `/api/jobs/analyze` | POST | X-API-Key | 202, 400 |

**Request format: JSON body** (`AnalyzeRequestV2`)

| Field | Type | Required | Constraints | Description |
|---|---|---|---|---|
| `student` | StudentRef (optional) | no |  |  |
| `profile` | FeatureProfile (optional) | no |  |  |
| `what_if` | object of number or integer (optional) (optional) | no |  |  |
| `use_llm` | boolean | no | default `true` |  |
| `judge` | boolean | no | default `false` |  |
| `checkpoint` | number (optional) | no | >= 0.05, <= 0.95 | Share of the planned course length; nearest built checkpoint is used |
| `synthesize` | boolean | no | default `true` |  |

Types written in CamelCase (for example `StudentRef`) are described once in *Appendix: shared request models*.

**Response format** (JSON object, HTTP 202):
`id` (string), `kind` (string), `status` (string), `steps` (array), `error` (null), `elapsed_s` (number).

**Sample request**
```bash
curl -X POST "http://127.0.0.1:8000/api/jobs/analyze" \
  -H "X-API-Key: $STUDENT_ASSISTANT_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"student": {"id_student": 692826, "code_module": "BBB", "code_presentation": "2014J"}, "checkpoint": 0.4, "use_llm": false}'
```

**Sample response** (HTTP 202, 0.01 s)

```json
{
  "id": "a038c3cb04a94060b9a0bb5ce679ac18",
  "kind": "analysis",
  "status": "running",
  "steps": [],
  "error": null,
  "elapsed_s": 0.0
}
```

---

### <span class="method POST">POST</span> `/api/jobs/briefing`
**Cohort briefing (background job).** Weekly briefing for a module team as a background job.

| Endpoint | HTTP method | Authentication | Responses |
|---|---|---|---|
| `/api/jobs/briefing` | POST | X-API-Key | 202, 400 |

**Request format: JSON body** (`BriefingRequest`)

| Field | Type | Required | Constraints | Description |
|---|---|---|---|---|
| `code_module` | one of `AAA`, `BBB`, `CCC`, `DDD`, `EEE`, `FFF`, `GGG` | yes |  |  |
| `code_presentation` | string | yes |  |  |
| `capacity` | number | no | > 0.0, <= 1.0, default `0.2` |  |
| `checkpoint` | number (optional) | no | >= 0.05, <= 0.95 | Share of the planned course length; nearest built checkpoint is used |

Types written in CamelCase (for example `StudentRef`) are described once in *Appendix: shared request models*.

**Response format** (JSON object, HTTP 202):
`id` (string), `kind` (string), `status` (string), `steps` (array), `error` (null), `elapsed_s` (number).

**Sample request**
```bash
curl -X POST "http://127.0.0.1:8000/api/jobs/briefing" \
  -H "X-API-Key: $STUDENT_ASSISTANT_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"code_module": "BBB", "code_presentation": "2014J", "checkpoint": 0.4, "capacity": 0.2}'
```

**Sample response** (HTTP 202, 0.12 s)

```json
{
  "id": "0affb8920c034259b030f1c1a55170fd",
  "kind": "briefing",
  "status": "queued",
  "steps": [],
  "error": null,
  "elapsed_s": 0.0
}
```

---

### <span class="method POST">POST</span> `/api/jobs/copilot`
**Copilot (background job).** A copilot question as a background job.

| Endpoint | HTTP method | Authentication | Responses |
|---|---|---|---|
| `/api/jobs/copilot` | POST | X-API-Key | 202, 400 |

**Request format: JSON body** (`CopilotRequest`)

| Field | Type | Required | Constraints | Description |
|---|---|---|---|---|
| `question` | string | yes | min length 2, max length 1500 |  |
| `history` | array of ChatTurn | no | max items 20 |  |
| `checkpoint` | number (optional) | no | >= 0.05, <= 0.95 | Share of the planned course length; nearest built checkpoint is used |
| `use_llm` | boolean | no | default `true` |  |

Types written in CamelCase (for example `StudentRef`) are described once in *Appendix: shared request models*.

**Response format** (JSON object, HTTP 202):
`id` (string), `kind` (string), `status` (string), `steps` (array), `error` (null), `elapsed_s` (number).

**Sample request**
```bash
curl -X POST "http://127.0.0.1:8000/api/jobs/copilot" \
  -H "X-API-Key: $STUDENT_ASSISTANT_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"question": "How accurate is the withdrawal model?", "checkpoint": 0.4}'
```

**Sample response** (HTTP 202, 0.01 s)

```json
{
  "id": "a21e8b50c7ce45e997ab39dba61c38ca",
  "kind": "copilot",
  "status": "running",
  "steps": [],
  "error": null,
  "elapsed_s": 0.0
}
```

---

### <span class="method GET">GET</span> `/api/jobs/{job_id}`
**Job status.** Status (queued, running, done, error), the steps completed so far and the result.

| Endpoint | HTTP method | Authentication | Responses |
|---|---|---|---|
| `/api/jobs/{job_id}` | GET | X-API-Key | 200, 400 |

**Request format: parameters**

| Name | In | Type | Required | Constraints | Description |
|---|---|---|---|---|---|
| `job_id` | path | string | yes |  |  |

**Response format** (JSON object, HTTP 200):
`id` (string), `kind` (string), `status` (string), `steps` (array), `error` (null), `elapsed_s` (number), `result` (object).

**Sample request**
```bash
curl -X GET "http://127.0.0.1:8000/api/jobs/a038c3cb04a94060b9a0bb5ce679ac18" \
  -H "X-API-Key: $STUDENT_ASSISTANT_API_KEY"
```

**Sample response** (HTTP 200, 0.01 s; Polled until done; `steps` lists each agent as it ran.)

```json
{
  "id": "a038c3cb04a94060b9a0bb5ce679ac18",
  "kind": "analysis",
  "status": "done",
  "steps": [
    {
      "step": "models",
      "source": "computed",
      "t": 0.03
    },
    {
      "step": "retrieval",
      "source": "computed",
      "t": 0.05
    },
    "... 3 more"
  ],
  "error": null,
  "elapsed_s": 0.07,
  "result": {
    "student": {
      "id_student": 692826,
      "code_module": "BBB",
      "code_presentation": "2014J"
    },
    "checkpoint": 0.4,
    "withdrawal_risk": {
      "withdrawal_risk": 0.2494,
      "risk_tier": "High",
      "thresholds": {
        "medium": 0.0771,
        "high": 0.1412
      },
      "drivers": [
        "{...}",
        "{...}",
        "... 4 more"
      ],
      "calibration": "platt_lopo",
      "interpretation": "Calibrated probability of withdrawing after the snapshot among students still enrolled. An early-warning estimate, not a diagnosis or a causal claim."
    },
    "outcome_prediction": {
      "predicted_outcome": "Fail",
      "probabilities": {
        "Distinction": 0.0066,
        "Pass": 0.0315,
        "Fail": 0.734,
        "Withdrawn": 0.2279
      },
      "decision_rule": "balanced_argmax (macro-F1 optimised); probabilities are calibrated",
      "p_poor_outcome": 0.9619
    },
    "input_quality": {
      "source": "feature_store",
      "imputed_fields": [],
      "out_of_distribution": [],
      "key_signal_completeness": 1.0,
      "confidence": "normal",
      "checkpoint": 0.4
    },
    "similar_cases": {
      "cases": [
        "{...}",
        "{...}",
        "... 4 more"
      ],
      "outcome_summary": {
        "n_neighbours": 50,
        "counts": "{...}",
        "withdrawn_rate": 0.08,
        "withdrawn_ci95": [
          0.0315,
          0.1884
        ],
        "fail_or_withdrawn_rate": 0.98,
        "fail_or_withdrawn_ci95": [
          0.895,
          0.9965
        ]
      },
      "channels_used": [
        "behavioural",
        "lexical",
        "... 1 more"
      ],
      "fusion_weights": {
        "behavioural": 1.0,
        "lexical": 0.5,
        "dense": 0.0
      },
      "candidates": 4326,
      "historical_only_before": "2014J",
  ... (trimmed for the document; the API returns the full response)
```

---

### <span class="method POST">POST</span> `/api/cohort/briefing`
**Cohort briefing.** Headline, key points, focus for the week and who to contact first, drafted by the LLM from computed figures; every number and ID is checked, with a computed fallback.

| Endpoint | HTTP method | Authentication | Responses |
|---|---|---|---|
| `/api/cohort/briefing` | POST | X-API-Key | 200, 400 |

**Request format: JSON body** (`BriefingRequest`)

| Field | Type | Required | Constraints | Description |
|---|---|---|---|---|
| `code_module` | one of `AAA`, `BBB`, `CCC`, `DDD`, `EEE`, `FFF`, `GGG` | yes |  |  |
| `code_presentation` | string | yes |  |  |
| `capacity` | number | no | > 0.0, <= 1.0, default `0.2` |  |
| `checkpoint` | number (optional) | no | >= 0.05, <= 0.95 | Share of the planned course length; nearest built checkpoint is used |

Types written in CamelCase (for example `StudentRef`) are described once in *Appendix: shared request models*.

**Response format** (JSON object, HTTP 200):
`briefing` (object), `cohort` (object).

**Sample request**
```bash
curl -X POST "http://127.0.0.1:8000/api/cohort/briefing" \
  -H "X-API-Key: $STUDENT_ASSISTANT_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"code_module": "BBB", "code_presentation": "2014J", "checkpoint": 0.4, "capacity": 0.2}'
```

**Sample response** (HTTP 200, 0.48 s)

```json
{
  "briefing": {
    "headline": "Module BBB (2014J) week 15: 341 of 1,702 still-enrolled students are in the High risk tier, and the week 15 TMA (20% weight) is due now.",
    "key_points": [
      "1,702 students are still enrolled: 341 High, 507 Medium and 854 Low risk.",
      "The 590 students who withdrew before this week are not in the enrolled count and are reported separately.",
      "... 3 more"
    ],
    "focus_this_week": [
      "Contact the top-priority students first, starting with those showing missed due assessments plus low activity or recent engagement decline.",
      "Send a reminder and offer support before the week 15 TMA deadline to High and Medium tier students who have not yet submitted.",
      "... 2 more"
    ],
    "students_to_contact": [
      692826,
      656755,
      "... 3 more"
    ],
    "source": "llm",
    "checks": []
  },
  "cohort": {
    "code_module": "BBB",
    "code_presentation": "2014J",
    "snapshot_week": 15,
    "tiers": {
      "High": 341,
      "Medium": 507,
      "Low": 854
    },
    "in_scope": 1702
  }
}
```

---

### <span class="method POST">POST</span> `/api/copilot`
**Ask the copilot.** Answers questions by calling the same tools as the console (cohort, ranking, student, cases, insights, model performance); every number in the answer is checked against the tool results. Rule-based when the LLM is off.

| Endpoint | HTTP method | Authentication | Responses |
|---|---|---|---|
| `/api/copilot` | POST | X-API-Key | 200, 400 |

**Request format: JSON body** (`CopilotRequest`)

| Field | Type | Required | Constraints | Description |
|---|---|---|---|---|
| `question` | string | yes | min length 2, max length 1500 |  |
| `history` | array of ChatTurn | no | max items 20 |  |
| `checkpoint` | number (optional) | no | >= 0.05, <= 0.95 | Share of the planned course length; nearest built checkpoint is used |
| `use_llm` | boolean | no | default `true` |  |

Types written in CamelCase (for example `StudentRef`) are described once in *Appendix: shared request models*.

**Response format** (JSON object, HTTP 200):
`answer` (string), `tool_calls` (array), `source` (string), `revised` (boolean), `grounding` (object), `flags` (array), `seconds` (number).

**Sample request**
```bash
curl -X POST "http://127.0.0.1:8000/api/copilot" \
  -H "X-API-Key: $STUDENT_ASSISTANT_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"question": "Who should I contact first in BBB 2014J?", "checkpoint": 0.4, "use_llm": true}'
```

**Sample response** (HTTP 200, 0.09 s)

```json
{
  "answer": "Here are the top 10 students to contact in BBB 2014J. The cohort has 1,702 students, and the ranking assumes advisor capacity of 20%. All figures are statistical estimates. [rank_cohort]\n\n| Rank | Student ID | Withdrawal risk | Fail-or-withdraw risk | Main drivers |\n|---|---|---|---|---|\n| 1 | 692826 | 25% | 96% | Low score, missed assessments, low activity  ...",
  "tool_calls": [
    {
      "tool": "rank_cohort",
      "arguments": {
        "code_module": "BBB",
        "code_presentation": "2014J"
      },
      "ok": true,
      "ms": 68,
      "result": {
        "cohort_size": 1702,
        "capacity": 0.2,
        "ranking": [
          "{...}",
          "{...}",
          "... 8 more"
        ]
      }
    }
  ],
  "source": "llm",
  "revised": false,
  "grounding": {
    "passed": true,
    "ungrounded_numbers": []
  },
  "flags": [],
  "seconds": 0.09
}
```

---

### <span class="method POST">POST</span> `/api/copilot/stream`
**Ask the copilot (streamed).** Server-sent events: tool_call, tool_result, text (unverified until done), text_reset, revision, done, error.

| Endpoint | HTTP method | Authentication | Responses |
|---|---|---|---|
| `/api/copilot/stream` | POST | X-API-Key | 200, 400 |

**Request format: JSON body** (`CopilotRequest`)

| Field | Type | Required | Constraints | Description |
|---|---|---|---|---|
| `question` | string | yes | min length 2, max length 1500 |  |
| `history` | array of ChatTurn | no | max items 20 |  |
| `checkpoint` | number (optional) | no | >= 0.05, <= 0.95 | Share of the planned course length; nearest built checkpoint is used |
| `use_llm` | boolean | no | default `true` |  |

Types written in CamelCase (for example `StudentRef`) are described once in *Appendix: shared request models*.

**Response format:** text/event-stream; 4 events in this answer (1 text deltas). Shown: the non-text events and the first two text deltas.

**Sample request**
```bash
curl -X POST "http://127.0.0.1:8000/api/copilot/stream" \
  -H "X-API-Key: $STUDENT_ASSISTANT_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"question": "Give me an overview of BBB 2014J", "checkpoint": 0.4}'
```

**Sample response** (HTTP 200, 0.15 s; text/event-stream; 4 events in this answer (1 text deltas). Shown: the non-text events and the first two text deltas.)

```json
[
  {
    "event": "tool_call",
    "data": {
      "id": "toolu_014rMVinREZofJHF8kLSb36v",
      "tool": "cohort_overview",
      "arguments": {
        "code_module": "BBB",
        "code_presentation": "2014J"
      }
    }
  },
  {
    "event": "tool_result",
    "data": {
      "id": "toolu_014rMVinREZofJHF8kLSb36v",
      "tool": "cohort_overview",
      "ok": true,
      "ms": 126
    }
  },
  "... 2 more"
]
```

---

### <span class="method POST">POST</span> `/api/outreach/variants`
**Rewrite an outreach message.** Rewrites an advisor's message for a channel (email, SMS, phone script), tone and language, with an English back-translation; length and wording checks with a computed fallback.

| Endpoint | HTTP method | Authentication | Responses |
|---|---|---|---|
| `/api/outreach/variants` | POST | X-API-Key | 200, 400 |

**Request format: JSON body** (`OutreachRequest`)

| Field | Type | Required | Constraints | Description |
|---|---|---|---|---|
| `message` | string | yes | min length 20, max length 1500 |  |
| `channel` | one of `email`, `sms`, `phone_script` | no | default `"email"` |  |
| `tone` | one of `warm`, `concise`, `formal` | no | default `"warm"` |  |
| `language` | one of `English`, `French`, `Spanish`, `German`, `Welsh` | no | default `"English"` |  |

Types written in CamelCase (for example `StudentRef`) are described once in *Appendix: shared request models*.

**Response format** (JSON object, HTTP 200):
`message` (string), `subject` (null), `english_back_translation` (null), `language` (string), `channel` (string), `tone` (string), `source` (string), `checks` (array).

**Sample request**
```bash
curl -X POST "http://127.0.0.1:8000/api/outreach/variants" \
  -H "X-API-Key: $STUDENT_ASSISTANT_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"message": "Hi, I noticed the last assignment hasn't come in yet. Would a short call this week help you plan the next steps? Reply with a time that suits you.", "channel": "sms", "tone": "warm", "language": "English"}'
```

**Sample response** (HTTP 200, 2.34 s)

```json
{
  "message": "Hi, we hope you're doing well. We noticed the last assignment hasn't come in yet, and we'd be glad to help you plan the next steps. Would a short call this week suit you? Reply with a time that works for you.",
  "subject": null,
  "english_back_translation": null,
  "language": "English",
  "channel": "sms",
  "tone": "warm",
  "source": "llm",
  "checks": []
}
```

---

## Retrieval
Hybrid RAG over historical enrolments: query understanding and similar-case search.

### <span class="method POST">POST</span> `/api/search/parse`
**Understand a search request.** Turns plain English into metadata filters and behaviour descriptors (LLM with a rule-based fallback).

| Endpoint | HTTP method | Authentication | Responses |
|---|---|---|---|
| `/api/search/parse` | POST | X-API-Key | 200, 400 |

**Request format: JSON body** (`ParseQueryRequest`)

| Field | Type | Required | Constraints | Description |
|---|---|---|---|---|
| `query` | string | yes | min length 3, max length 500 |  |

Types written in CamelCase (for example `StudentRef`) are described once in *Appendix: shared request models*.

**Response format** (JSON object, HTTP 200):
`filters` (object), `descriptors` (array), `explanation` (string), `source` (string), `rules_interpretation` (object).

**Sample request**
```bash
curl -X POST "http://127.0.0.1:8000/api/search/parse" \
  -H "X-API-Key: $STUDENT_ASSISTANT_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "repeat students in FFF with heavy workloads who dropped out"}'
```

**Sample response** (HTTP 200, 0.02 s)

```json
{
  "filters": {
    "code_module": "FFF",
    "num_of_prev_attempts": {
      "min": 1.0
    },
    "final_result": "Withdrawn"
  },
  "descriptors": [
    "repeat_attempt",
    "credits_heavy"
  ],
  "explanation": "The request asks for repeat students in module FFF with heavy workloads who dropped out. 'Repeat' maps to num_of_prev_attempts min 1, 'dropped out' maps to final_result Withdrawn, and 'heavy workloads' maps to the credits_heavy descriptor.",
  "source": "llm",
  "rules_interpretation": {
    "filters": {
      "code_module": "FFF",
      "num_of_prev_attempts": {
        "min": 1
      },
      "final_result": "Withdrawn"
    },
    "descriptors": [
      "repeat_attempt"
    ],
    "explanation": "Rule-based interpretation.",
    "source": "rules"
  }
}
```

---

### <span class="method POST">POST</span> `/api/retrieve-similar`
**Find similar historical students (hybrid RAG).** Similar enrolments from earlier presentations by profile, text or both: BM25 + behavioural kNN + dense vectors fused with RRF, metadata pre-filtered in LanceDB, with outcome mix and what happened next.

| Endpoint | HTTP method | Authentication | Responses |
|---|---|---|---|
| `/api/retrieve-similar` | POST | X-API-Key | 200, 400 |

**Request format: JSON body** (`RetrievalRequestV2`)

| Field | Type | Required | Constraints | Description |
|---|---|---|---|---|
| `student` | StudentRef (optional) | no |  |  |
| `profile` | FeatureProfile (optional) | no |  |  |
| `query` | string (optional) | no | min length 3, max length 500 |  |
| `filters` | RetrievalFilters (optional) | no |  |  |
| `top_k` | integer | no | >= 1.0, <= 50.0, default `10` |  |
| `mode` | one of `hybrid`, `behavioural`, `lexical`, `dense` | no | default `"hybrid"` |  |
| `historical_only` | boolean | no | default `true` |  |
| `checkpoint` | number (optional) | no | >= 0.05, <= 0.95 | Share of the planned course length; nearest built checkpoint is used |
| `understand` | boolean | no | default `true` |  |
| `descriptors` | array of string (optional) | no | max items 30 |  |

Types written in CamelCase (for example `StudentRef`) are described once in *Appendix: shared request models*.

**Response format** (JSON object, HTTP 200):
`cases` (array), `outcome_summary` (object), `channels_used` (array), `fusion_weights` (object), `candidates` (integer), `historical_only_before` (null), `query_descriptors` (array), `aftermath` (object), `checkpoint` (number), `interpretation` (object), `applied_filters` (null).

**Sample request**
```bash
curl -X POST "http://127.0.0.1:8000/api/retrieve-similar" \
  -H "X-API-Key: $STUDENT_ASSISTANT_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "students who stopped turning in their coursework", "top_k": 3, "checkpoint": 0.4, "understand": true}'
```

**Sample response** (HTTP 200, 0.1 s; Text search across all modules; the request is first understood as filters and behaviour descriptors.)

```json
{
  "cases": [
    {
      "case_id": 12429854,
      "id_student": 2429854,
      "code_module": "AAA",
      "code_presentation": "2014J",
      "final_result": "Fail",
      "fusion_score": 0.016393,
      "behavioural_distance": null,
      "channel_ranks": {
        "lexical": 1
      },
      "shared_descriptors": [
        "missed_most",
        "engagement_declining",
        "... 1 more"
      ],
      "summary": "Student on module AAA: repeating the module after a previous attempt; standard study load; no assessment results yet; has missed most due assessments; below-average online activity; online activity has been declining; had a long period without activity. Final outcome: fail.",
      "snapshot": {
        "weighted_score": null,
        "missed_rate": 1.0,
        "clicks_pct": 0.2552552552552553,
        "score_pct": null,
        "engagement_momentum": -0.9867257,
        "days_since_last_activity": 2.0,
        "studied_credits": 60.0,
        "num_of_prev_attempts": 1.0
      },
      "metadata": {
        "region": "London Region",
        "highest_education": "A Level or Equivalent",
        "age_band": "35-55"
      },
      "...": "1 more fields"
    },
    {
      "case_id": 50645753,
      "id_student": 645753,
      "code_module": "BBB",
      "code_presentation": "2014J",
      "final_result": "Fail",
      "fusion_score": 0.016129,
      "behavioural_distance": null,
      "channel_ranks": {
        "lexical": 2
      },
      "shared_descriptors": [
        "missed_most",
        "engagement_declining",
        "... 1 more"
      ],
      "summary": "Student on module BBB: first attempt at the module; standard study load; no assessment results yet; has missed most due assessments; below-average online activity; online activity has been declining; had a long period without activity. Final outcome: fail.",
      "snapshot": {
        "weighted_score": null,
        "missed_rate": 1.0,
        "clicks_pct": 0.3557579318448883,
        "score_pct": null,
        "engagement_momentum": -0.96,
        "days_since_last_activity": 5.0,
        "studied_credits": 60.0,
        "num_of_prev_attempts": 0.0
      },
      "metadata": {
  ... (trimmed for the document; the API returns the full response)
```
**Sample request** (by student)
```bash
curl -X POST "http://127.0.0.1:8000/api/retrieve-similar" \
  -H "X-API-Key: $STUDENT_ASSISTANT_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"student": {"id_student": 692826, "code_module": "BBB", "code_presentation": "2014J"}, "top_k": 3, "checkpoint": 0.4, "filters": {"num_of_prev_attempts": {"max": 0}}}'
```

**Sample response** (HTTP 200, 0.05 s; Profile search for one student: same module, earlier presentations only, metadata filter applied in the vector store.)

```json
{
  "cases": [
    {
      "case_id": 100613105,
      "id_student": 613105,
      "code_module": "DDD",
      "code_presentation": "2014B",
      "final_result": "Fail",
      "fusion_score": 0.02364,
      "behavioural_distance": 0.8245,
      "channel_ranks": {
        "behavioural": 1,
        "lexical": 9
      },
      "shared_descriptors": [
        "first_attempt",
        "credits_standard",
        "... 6 more"
      ],
      "summary": "Student on module DDD: first attempt at the module; standard study load; failing assessment results; among the lowest scores in the cohort; with steady grades; has missed most due assessments; often submits late; very little online activity compared with peers; online activity has been declining; inactive in recent weeks; had a long period without activity.  ...",
      "snapshot": {
        "weighted_score": 9.0,
        "missed_rate": 0.6666666666666666,
        "clicks_pct": 0.1214596949891067,
        "score_pct": 0.0011709601873536,
        "engagement_momentum": -0.97183096,
        "days_since_last_activity": 66.0,
        "studied_credits": 60.0,
        "num_of_prev_attempts": 0.0
      },
      "metadata": {
        "region": "Yorkshire Region",
        "highest_education": "Lower Than A Level",
        "age_band": "0-35"
      },
      "...": "1 more fields"
    },
    {
      "case_id": 160198691,
      "id_student": 198691,
      "code_module": "FFF",
      "code_presentation": "2013J",
      "final_result": "Fail",
      "fusion_score": 0.023565,
      "behavioural_distance": 0.9712,
      "channel_ranks": {
        "behavioural": 3,
        "lexical": 5
      },
      "shared_descriptors": [
        "first_attempt",
        "credits_standard",
        "... 6 more"
      ],
      "summary": "Student on module FFF: first attempt at the module; standard study load; failing assessment results; among the lowest scores in the cohort; with steady grades; has missed most due assessments; often submits late; very little online activity compared with peers; online activity has been declining; inactive in recent weeks; had a long period without activity;  ...",
      "snapshot": {
        "weighted_score": 14.0,
  ... (trimmed for the document; the API returns the full response)
```

---

## Insights
Computed analyses from complete historical records (factors, trends, assessments).

### <span class="method GET">GET</span> `/api/trends/course`
**Engagement trends by outcome.** Weekly activity by final outcome for a module and the week each outcome group falls below 60% of passing students.

| Endpoint | HTTP method | Authentication | Responses |
|---|---|---|---|
| `/api/trends/course` | GET | X-API-Key | 200, 400 |

**Request format: parameters**

| Name | In | Type | Required | Constraints | Description |
|---|---|---|---|---|---|
| `code_module` | query | string (optional) | no |  |  |

**Response format** (JSON object, HTTP 200):
`module` (string), `weekly_mean_clicks_by_outcome` (object), `weeks` (array), `first_week_below_60pct_of_pass` (object).

**Sample request**
```bash
curl -X GET "http://127.0.0.1:8000/api/trends/course?code_module=BBB" \
  -H "X-API-Key: $STUDENT_ASSISTANT_API_KEY"
```

**Sample response** (HTTP 200, 0.01 s)

```json
{
  "module": "BBB",
  "weekly_mean_clicks_by_outcome": {
    "Distinction": [
      70.61,
      59.86,
      "... 37 more"
    ],
    "Fail": [
      29.29,
      23.41,
      "... 37 more"
    ],
    "Pass": [
      52.13,
      46.18,
      "... 37 more"
    ],
    "Withdrawn": [
      39.3,
      32.03,
      "... 37 more"
    ]
  },
  "weeks": [
    0,
    1,
    "... 37 more"
  ],
  "first_week_below_60pct_of_pass": {
    "Fail": 0,
    "Withdrawn": 9
  }
}
```

---

### <span class="method GET">GET</span> `/api/insights/factors`
**Factors behind poor outcomes.** Signals ranked by the gap in fail-or-withdraw rate between best and worst fifth, with quintile rates and confidence intervals.

| Endpoint | HTTP method | Authentication | Responses |
|---|---|---|---|
| `/api/insights/factors` | GET | X-API-Key | 200 |

**Request format:** no parameters or body.

**Response format** (JSON object, HTTP 200):
`population` (string), `n` (integer), `base_rates` (object), `model_importance_mean_abs_logodds` (object), `numeric_factors_ranked` (array), `categorical_factors` (object), `caveat` (string).

**Sample request**
```bash
curl -X GET "http://127.0.0.1:8000/api/insights/factors" \
  -H "X-API-Key: $STUDENT_ASSISTANT_API_KEY"
```

**Sample response** (HTTP 200, 0.02 s)

```json
{
  "population": "historical in-scope enrolments",
  "n": 16827,
  "base_rates": {
    "withdrawal": 0.10887264515362216,
    "poor_outcome": 0.40999584001901707
  },
  "model_importance_mean_abs_logodds": {
    "Missed assessments": 0.15098623931407928,
    "Average assessment score": 0.14465002715587616,
    "Score percentile in cohort": 0.1285749226808548,
    "Average days submitted before deadline": 0.10553442686796188,
    "Tutor-marked assignments missed": 0.09945375472307205,
    "Lowest score": 0.0896458849310875,
    "Highest score": 0.07958342880010605,
    "Module": 0.07197745144367218,
    "Relative weekly engagement trend": 0.065945565700531,
    "Assessments due so far": 0.06325087696313858,
    "Late submission rate": 0.051485683768987656,
    "Credits studied this term": 0.05078485608100891,
    "...": "55 more fields"
  },
  "numeric_factors_ranked": [
    {
      "feature": "missed_rate",
      "label": "Share of due assessments missed",
      "spearman_with_poor_outcome": 0.5482364112756932,
      "poor_outcome_rate_spread": 0.7061794414735592,
      "quintiles": [
        "{...}",
        "{...}",
        "... 3 more"
      ],
      "missing_share": 0.0
    },
    {
      "feature": "missed_count",
      "label": "Missed assessments",
      "spearman_with_poor_outcome": 0.5448275642712603,
      "poor_outcome_rate_spread": 0.7002376708259062,
      "quintiles": [
        "{...}",
        "{...}",
        "... 3 more"
      ],
      "missing_share": 0.0
    },
    "... 23 more"
  ],
  "categorical_factors": {
    "code_module": {
      "descriptive_only": false,
      "levels": [
        "{...}",
        "{...}",
        "... 5 more"
      ]
    },
    "num_of_prev_attempts": {
      "descriptive_only": false,
      "levels": [
        "{...}",
        "{...}",
        "... 2 more"
      ]
    },
    "gender": {
      "descriptive_only": true,
      "levels": [
        "{...}",
        "{...}"
      ]
    },
    "region": {
      "descriptive_only": true,
      "levels": [
        "{...}",
        "{...}",
        "... 11 more"
      ]
    },
    "highest_education": {
      "descriptive_only": true,
      "levels": [
        "{...}",
  ... (trimmed for the document; the API returns the full response)
```

---

### <span class="method GET">GET</span> `/api/insights/assessments`
**Assessment analytics.** Per assessment: submission and late rates, mean score and how strongly missing it marks later failure or withdrawal (AUC).

| Endpoint | HTTP method | Authentication | Responses |
|---|---|---|---|
| `/api/insights/assessments` | GET | X-API-Key | 200, 400 |

**Request format: parameters**

| Name | In | Type | Required | Constraints | Description |
|---|---|---|---|---|---|
| `code_module` | query | string (optional) | no |  |  |
| `code_presentation` | query | string (optional) | no |  |  |

**Response format** (JSON object, HTTP 200):
`note` (string), `assessments` (array).

**Sample request**
```bash
curl -X GET "http://127.0.0.1:8000/api/insights/assessments?code_module=BBB&code_presentation=2014J" \
  -H "X-API-Key: $STUDENT_ASSISTANT_API_KEY"
```

**Sample response** (HTTP 200, 0.01 s)

```json
{
  "note": "Computed from complete historical records. AUC = how well missing / low-scoring this assessment separates students who later failed or withdrew (0.5 = no signal).",
  "assessments": [
    {
      "id_assessment": 15020,
      "code_module": "BBB",
      "code_presentation": "2014J",
      "assessment_type": "TMA",
      "deadline_day": 19,
      "deadline_week": 2,
      "weight": 0.0,
      "enrolled_at_deadline": 1804,
      "submission_rate": 0.9395787139689579,
      "mean_score": 59.145981087470446,
      "fail_rate_below_40": 0.4101654846335697,
      "late_rate": 0.05014749262536873,
      "...": "2 more fields"
    },
    {
      "id_assessment": 15021,
      "code_module": "BBB",
      "code_presentation": "2014J",
      "assessment_type": "TMA",
      "deadline_day": 54,
      "deadline_week": 7,
      "weight": 10.0,
      "enrolled_at_deadline": 1752,
      "submission_rate": 0.8984018264840182,
      "mean_score": 68.29669631512071,
      "fail_rate_below_40": 0.011435832274459974,
      "late_rate": 0.09148665819567979,
      "...": "2 more fields"
    },
    "... 4 more"
  ]
}
```

---

### <span class="method GET">GET</span> `/api/insights/checkpoints`
**Model quality by checkpoint.** Withdrawal-model metrics at every checkpoint on the untouched test presentation.

| Endpoint | HTTP method | Authentication | Responses |
|---|---|---|---|
| `/api/insights/checkpoints` | GET | X-API-Key | 200 |

**Request format:** no parameters or body.

**Response format** (JSON object, HTTP 200):
`checkpoints` (array).

**Sample request**
```bash
curl -X GET "http://127.0.0.1:8000/api/insights/checkpoints" \
  -H "X-API-Key: $STUDENT_ASSISTANT_API_KEY"
```

**Sample response** (HTTP 200, 0.0 s)

```json
{
  "checkpoints": [
    {
      "checkpoint": 0.15,
      "tag": "c15",
      "approx_week": 5.6,
      "in_scope": 27157,
      "withdrawal": {
        "n": 9056,
        "positive_rate": 0.1791077738515901,
        "roc_auc": 0.6861329556239586,
        "pr_auc": 0.31596324382933005,
        "brier": 0.1375645397337802,
        "log_loss": 0.4386839182790676,
        "ece_10": 0.01671667210011917,
        "roc_auc_95ci": "{...}"
      },
      "thresholds": {
        "medium": 0.1289293491758349,
        "high": 0.17476850860365434,
        "method": "validation_f1_above_medium",
        "medium_recall_target": 0.8,
        "validation": "{...}"
      },
      "outcome_macro_f1": 0.39688722999549914,
      "p_poor_auc": 0.7660114493351569,
      "prioritization_precision_at_10": 0.8653421633554084
    },
    {
      "checkpoint": 0.25,
      "tag": "c25",
      "approx_week": 9.4,
      "in_scope": 26241,
      "withdrawal": {
        "n": 8746,
        "positive_rate": 0.1500114337983078,
        "roc_auc": 0.7003070619008248,
        "pr_auc": 0.2893076585124664,
        "brier": 0.11885072598961065,
        "log_loss": 0.3902793676902645,
        "ece_10": 0.010904285528292363,
        "roc_auc_95ci": "{...}"
      },
      "thresholds": {
        "medium": 0.10061204937892895,
        "high": 0.17260539970977043,
        "method": "validation_f1_above_medium",
        "medium_recall_target": 0.8,
        "validation": "{...}"
      },
      "outcome_macro_f1": 0.45418854380349244,
      "p_poor_auc": 0.8170959077333816,
      "prioritization_precision_at_10": 0.952
    },
    "... 2 more"
  ]
}
```

---

## Evaluation
Model and AI evaluation results, LLM-as-judge, human review and AI usage/cost.

### <span class="method GET">GET</span> `/api/metrics`
**All evaluation metrics.** Data build, withdrawal and outcome models, ablations, fairness audit, prioritisation, retrieval benchmark, LLM evaluation and the quality gate.

| Endpoint | HTTP method | Authentication | Responses |
|---|---|---|---|
| `/api/metrics` | GET | X-API-Key | 200, 400 |

**Request format: parameters**

| Name | In | Type | Required | Constraints | Description |
|---|---|---|---|---|---|
| `checkpoint` | query | number (optional) | no | >= 0.05, <= 0.95 | Course checkpoint (share of planned length) |

**Response format** (JSON object, HTTP 200):
`data_build` (object), `withdrawal_model` (object), `outcome_model` (object), `ablations` (object), `fairness` (object), `prioritization` (object), `retrieval_benchmark` (object), `llm_evaluation` (object), `quality_gate` (object), `checkpoint_summary` (object), `checkpoint` (number).

**Sample request**
```bash
curl -X GET "http://127.0.0.1:8000/api/metrics?checkpoint=0.4" \
  -H "X-API-Key: $STUDENT_ASSISTANT_API_KEY"
```

**Sample response** (HTTP 200, 0.03 s)

```json
{
  "data_build": {
    "feature_version": "5.0",
    "cutoff_fraction": 0.4,
    "records": 32593,
    "in_scope_records": 25204,
    "withdrawn_total": 10156,
    "withdrawn_before_snapshot": 7389,
    "withdrawn_before_start": 3097,
    "withdrawn_after_snapshot_in_scope": 2775,
    "presentations": [
      "2013B",
      "2013J",
      "... 2 more"
    ],
    "synthetic_fixture": false,
    "build_seconds": 12.0,
    "leakage_controls": [
      "assessment and VLE rows filtered to date <= snapshot_day",
      "students unregistered on/before snapshot_day excluded from modelling scope (in_scope=0)",
      "... 3 more"
    ]
  },
  "withdrawal_model": {
    "test": {
      "n": 8377,
      "positive_rate": 0.11257013250567029,
      "roc_auc": 0.7255685308195328,
      "pr_auc": 0.26301911267610545,
      "brier": 0.09263649781211399,
      "log_loss": 0.3186435406111674,
      "ece_10": 0.008742683871515326,
      "roc_auc_95ci": {
        "lower": 0.7076739828305996,
        "upper": 0.7400489384532395,
        "n_boot": 300
      }
    },
    "historical_out_of_fold": {
      "n": 16827,
      "positive_rate": 0.10887264515362216,
      "roc_auc": 0.7343106726987598,
      "pr_auc": 0.25702291887550904,
      "brier": 0.08952318055082886,
      "log_loss": 0.30930093091718264,
      "ece_10": 0.006109591886914804
    },
    "thresholds": {
      "medium": 0.0771072325145041,
      "high": 0.14122656421985777,
      "method": "validation_f1_above_medium",
      "medium_recall_target": 0.8,
      "validation": {
        "medium": "{...}",
        "high": "{...}"
      }
    },
    "test_at_high_threshold": {
      "precision": 0.23588205897051473,
      "recall": 0.5005302226935313,
      "f1": 0.32065217391304346,
      "flag_rate": 0.23886832995105647
    },
    "test_at_medium_threshold": {
      "precision": 0.1720876585928489,
      "recall": 0.7910922587486744,
      "flag_rate": 0.5174883609884207
    },
    "test_tiers": {
      "High": {
        "n": 2001,
        "share": 0.23886832995105647,
        "observed_withdrawal_rate": 0.23588205897051473,
        "share_of_all_withdrawals": 0.5005302226935313
      },
      "Medium": {
        "n": 2334,
  ... (trimmed for the document; the API returns the full response)
```

---

### <span class="method GET">GET</span> `/api/evaluations/llm`
**AI evaluation results.** Offline evaluation of every LLM feature: code checks, LLM-as-judge, order-swapped A/B, DeepEval metrics, copilot golden set and robustness.

| Endpoint | HTTP method | Authentication | Responses |
|---|---|---|---|
| `/api/evaluations/llm` | GET | X-API-Key | 200 |

**Request format:** no parameters or body.

**Response format** (JSON object, HTTP 200):
`generated_at` (string), `llm_configured` (boolean), `use_llm` (boolean), `generator_model` (string), `judge_model` (string), `models` (object), `agents` (object), `search` (object), `copilot` (object), `synthesis` (object), `briefing` (object), `outreach` (object), `robustness` (object), `human_agreement` (object), `seconds` (number), `usage` (object).

**Sample request**
```bash
curl -X GET "http://127.0.0.1:8000/api/evaluations/llm" \
  -H "X-API-Key: $STUDENT_ASSISTANT_API_KEY"
```

**Sample response** (HTTP 200, 0.01 s)

```json
{
  "generated_at": "2026-10-12T08:10:47",
  "llm_configured": true,
  "use_llm": true,
  "generator_model": "claude-sonnet-5-5",
  "judge_model": "claude-opus-5-5",
  "models": {
    "provider": "anthropic",
    "fast": "claude-haiku-5-5",
    "main": "claude-sonnet-5-5",
    "judge": "claude-opus-5-5"
  },
  "agents": {
    "deterministic": {
      "n_cases": 24,
      "tiers": {
        "High": 8,
        "Medium": 8,
        "Low": 8
      },
      "final_plan_valid_rate": 1.0,
      "llm_plan_accepted_rate": 0.7916666666666666,
      "revision_rate": 0.0,
      "deterministic_fallback_rate": 0.20833333333333334,
      "routing": {
        "intervene": 19,
        "monitor": 5
      },
      "tier_routing_consistency": 1.0,
      "mean_seconds": 0.08004166666666666
    },
    "judge": {
      "status": "ok",
      "pass_rate": 0.9583333333333334,
      "mean_scores": {
        "evidence_alignment": 7.958333333333333,
        "actionability": 8.083333333333334,
        "specificity": 8.125,
        "non_punitiveness": 10.0,
        "fairness": 10.0,
        "safety": 9.708333333333334
      },
      "judge_model": "claude-opus-5-5",
      "same_model_as_generator": false
    },
    "pairwise_llm_vs_deterministic": {
      "status": "ok",
      "n": 19,
      "llm_win_rate": 0.8947368421052632,
      "deterministic_win_rate": 0.0,
      "tie_rate": 0.10526315789473684,
      "position_consistency": 0.8947368421052632
    },
    "deepeval": {
      "status": "ok",
      "judge_model": "claude-opus-5-5",
      "aggregate": {
        "Actionable for an advisor": "{...}",
        "AnswerRelevancyMetric": "{...}",
        "FaithfulnessMetric": "{...}",
        "No protected-attribute reasoning": "{...}",
        "Supportive and non-punitive": "{...}"
      },
      "per_case": [
        "{...}",
        "{...}",
        "... 22 more"
      ]
    }
  },
  "search": {
    "note": "Templated queries share phrasing with the rule parser (optimistic for rules); the paraphrase set tests generalisation to natural wording.",
    "templated_rules": {
      "n": 60,
      "filter_precision": 0.9752066115702479,
      "filter_recall": 0.9752066115702479,
  ... (trimmed for the document; the API returns the full response)
```

---

### <span class="method GET">GET</span> `/api/evaluations/online`
**Live reviews.** Judgements of sampled live requests (ONLINE_EVAL_SAMPLE_RATE) and on-demand reviews.

| Endpoint | HTTP method | Authentication | Responses |
|---|---|---|---|
| `/api/evaluations/online` | GET | X-API-Key | 200, 400 |

**Request format: parameters**

| Name | In | Type | Required | Constraints | Description |
|---|---|---|---|---|---|
| `kind` | query | string (optional) | no |  |  |
| `limit` | query | integer | no | >= 1, <= 500, default `100` |  |

**Response format** (JSON object, HTTP 200):
`summary` (object), `items` (array).

**Sample request**
```bash
curl -X GET "http://127.0.0.1:8000/api/evaluations/online?limit=3" \
  -H "X-API-Key: $STUDENT_ASSISTANT_API_KEY"
```

**Sample response** (HTTP 200, 0.01 s)

```json
{
  "summary": {
    "by_kind": [
      {
        "kind": "analysis",
        "n": 7,
        "mean_overall": 9.261904761904761,
        "pass_rate": 1.0
      },
      {
        "kind": "cohort_briefing",
        "n": 1,
        "mean_overall": 8.5,
        "pass_rate": 1.0
      },
      "... 1 more"
    ]
  },
  "items": [
    {
      "id": 13,
      "ts": 1791822614.679635,
      "kind": "analysis",
      "ref_id": "cbee97dffd3415f758fe",
      "verdict": "PASS",
      "overall": 9.333333333333334,
      "scores": {
        "evidence_alignment": 9.0,
        "actionability": 9.0,
        "specificity": 8.0,
        "non_punitiveness": 10.0,
        "fairness": 10.0,
        "safety": 10.0
      },
      "judge_model": "claude-opus-5-5",
      "details": {
        "checks": "{...}",
        "rationale": "Nearly every figure traces to the evidence: the 1.0 score at the 1st percentile, 1 of 2 assessments missed, the single submission being late, the 13th-percentile engagement, 69 inactive days against a module median of 4, and the 10-week streak. The risk figures also match (24.94% against the 14.12% threshold, Fail 73.4%, poor outcome 96.2%), as do the neighb ...",
        "sampled": false
      }
    },
    {
      "id": 12,
      "ts": 1791822601.9906535,
      "kind": "cohort_briefing",
      "ref_id": "BBB-2014J",
      "verdict": "PASS",
      "overall": 8.5,
      "scores": {
        "faithfulness": 8.0,
        "usefulness": 8.0,
        "clarity": 8.0,
        "safety": 10.0
      },
      "judge_model": "claude-opus-5-5",
      "details": {
        "checks": null,
        "rationale": "Faithfulness: the core figures all match the evidence. These include the tier counts (which sum to 1,702), the 590 prior withdrawals, the 157.5 and 763.6 expected outcomes, the driver counts, the TMA weeks, weights and submission rates, and the 0.954–0.975 poor-outcome range. All 12 top-priority students do show missed due assessments. The problems are small ...",
        "sampled": true
      }
    },
    "... 1 more"
  ]
}
```

---

### <span class="method POST">POST</span> `/api/evaluations/judge`
**Judge a support plan.** An independent judge model (Claude Opus 5.5) scores a plan on six criteria; the verdict is computed from the scores in code.

| Endpoint | HTTP method | Authentication | Responses |
|---|---|---|---|
| `/api/evaluations/judge` | POST | X-API-Key | 200, 400 |

**Request format: JSON body** (`JudgeRequest`)

| Field | Type | Required | Constraints | Description |
|---|---|---|---|---|
| `recommendation_id` | string | yes | min length 8, max length 64 |  |

Types written in CamelCase (for example `StudentRef`) are described once in *Appendix: shared request models*.

**Response format** (JSON object, HTTP 200):
`verdict` (string), `scores` (object), `overall` (number), `score_spread_across_samples` (object), `unsupported_claims` (array), `rationale` (string), `deterministic_checks` (object), `n_samples` (integer), `status` (string), `judge_model` (string), `generator_model` (string), `same_model_as_generator` (boolean).

**Sample request**
```bash
curl -X POST "http://127.0.0.1:8000/api/evaluations/judge" \
  -H "X-API-Key: $STUDENT_ASSISTANT_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"recommendation_id": "cbee97dffd3415f758fe"}'
```

**Sample response** (HTTP 200, 9.38 s)

```json
{
  "verdict": "PASS",
  "scores": {
    "evidence_alignment": 9.0,
    "actionability": 9.0,
    "specificity": 8.0,
    "non_punitiveness": 10.0,
    "fairness": 10.0,
    "safety": 10.0
  },
  "overall": 9.333333333333334,
  "score_spread_across_samples": {
    "evidence_alignment": 0.0,
    "actionability": 0.0,
    "specificity": 0.0,
    "non_punitiveness": 0.0,
    "fairness": 0.0,
    "safety": 0.0
  },
  "unsupported_claims": [],
  "rationale": "Nearly every figure traces to the evidence: the 1.0 score at the 1st percentile, 1 of 2 assessments missed, the single submission being late, the 13th-percentile engagement, 69 inactive days against a module median of 4, and the 10-week streak. The risk figures also match (24.94% against the 14.12% threshold, Fail 73.4%, poor outcome 96.2%), as do the neighb ...",
  "deterministic_checks": {
    "passed": true,
    "issues": []
  },
  "n_samples": 1,
  "status": "ok",
  "judge_model": "claude-opus-5-5",
  "generator_model": "claude-sonnet-5-5",
  "same_model_as_generator": false
}
```

---

### <span class="method GET">GET</span> `/api/evaluations/human-review`
**Cases for human review.** The evaluation cases advisors can rate blind, with current agreement between their ratings and the judge (Cohen's kappa).

| Endpoint | HTTP method | Authentication | Responses |
|---|---|---|---|
| `/api/evaluations/human-review` | GET | X-API-Key | 200 |

**Request format:** no parameters or body.

**Response format** (JSON object, HTTP 200):
`cases` (array), `labelled` (integer), `agreement` (object).

**Sample request**
```bash
curl -X GET "http://127.0.0.1:8000/api/evaluations/human-review" \
  -H "X-API-Key: $STUDENT_ASSISTANT_API_KEY"
```

**Sample response** (HTTP 200, 0.01 s)

```json
{
  "cases": [
    {
      "id_student": 2207874,
      "code_module": "AAA",
      "code_presentation": "2014J",
      "tier": "High",
      "plan_source": "llm",
      "label": null
    },
    {
      "id_student": 650105,
      "code_module": "CCC",
      "code_presentation": "2014J",
      "tier": "High",
      "plan_source": "llm",
      "label": null
    },
    "... 22 more"
  ],
  "labelled": 0,
  "agreement": {
    "status": "no human labels provided",
    "expected_file": "C:\\Users\\Nishanth\\AppData\\Local\\Temp\\edu_capture\\artifacts\\metrics\\human_labels.jsonl"
  }
}
```

---

### <span class="method POST">POST</span> `/api/evaluations/human-labels`
**Save a human rating.** Stores an advisor's blind rating of one evaluation case.

| Endpoint | HTTP method | Authentication | Responses |
|---|---|---|---|
| `/api/evaluations/human-labels` | POST | X-API-Key | 200, 400 |

**Request format: JSON body** (`HumanLabelRequest`)

| Field | Type | Required | Constraints | Description |
|---|---|---|---|---|
| `id_student` | integer | yes | > 0.0, < 10000000.0 |  |
| `code_module` | one of `AAA`, `BBB`, `CCC`, `DDD`, `EEE`, `FFF`, `GGG` | yes |  |  |
| `code_presentation` | string | yes |  |  |
| `verdict` | one of `PASS`, `REVIEW` | yes |  |  |
| `overall` | number | yes | >= 0.0, <= 10.0 |  |
| `notes` | string | no | max length 1000, default `""` |  |
| `reviewer` | string | yes | min length 1, max length 64 |  |

Types written in CamelCase (for example `StudentRef`) are described once in *Appendix: shared request models*.

**Response format** (JSON object, HTTP 200):
`cases` (array), `labelled` (integer), `agreement` (object).

**Sample request**
```bash
curl -X POST "http://127.0.0.1:8000/api/evaluations/human-labels" \
  -H "X-API-Key: $STUDENT_ASSISTANT_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"id_student": 2207874, "code_module": "AAA", "code_presentation": "2014J", "verdict": "PASS", "overall": 8, "notes": "Clear and supportive.", "reviewer": "demo"}'
```

**Sample response** (HTTP 200, 0.01 s)

```json
{
  "cases": [
    {
      "id_student": 2207874,
      "code_module": "AAA",
      "code_presentation": "2014J",
      "tier": "High",
      "plan_source": "llm",
      "label": {
        "id_student": 2207874,
        "code_module": "AAA",
        "code_presentation": "2014J",
        "verdict": "PASS",
        "overall": 8.0,
        "notes": "Clear and supportive.",
        "reviewer": "demo",
        "created_at": 1791822614.7113361
      }
    },
    {
      "id_student": 650105,
      "code_module": "CCC",
      "code_presentation": "2014J",
      "tier": "High",
      "plan_source": "llm",
      "label": null
    },
    "... 22 more"
  ],
  "labelled": 1,
  "agreement": {
    "status": "insufficient overlap",
    "n": 1
  }
}
```

---

### <span class="method GET">GET</span> `/api/llm/usage`
**AI usage and cost.** Calls, cache hits, tokens, latency and estimated cost per feature and model.

| Endpoint | HTTP method | Authentication | Responses |
|---|---|---|---|
| `/api/llm/usage` | GET | X-API-Key | 200, 400 |

**Request format: parameters**

| Name | In | Type | Required | Constraints | Description |
|---|---|---|---|---|---|
| `since_hours` | query | number (optional) | no | > 0, <= 8760 |  |

**Response format** (JSON object, HTTP 200):
`by_feature` (array), `total` (object), `prices_usd_per_million_tokens` (object), `note` (string).

**Sample request**
```bash
curl -X GET "http://127.0.0.1:8000/api/llm/usage?since_hours=720" \
  -H "X-API-Key: $STUDENT_ASSISTANT_API_KEY"
```

**Sample response** (HTTP 200, 0.01 s)

```json
{
  "by_feature": [
    {
      "feature": "deepeval",
      "model": "claude-opus-5-5",
      "n": 2184,
      "pt": 582982,
      "ct": 230942,
      "crt": 0,
      "cwt": 0,
      "unpriced": 0,
      "cached": 1819,
      "errors": 0,
      "estimated_cost_usd": 6.950768,
      "avg_latency_s": 1.097
    },
    {
      "feature": "search_understanding",
      "model": "claude-haiku-5-5",
      "n": 1450,
      "pt": 329815,
      "ct": 25135,
      "crt": 0,
      "cwt": 0,
      "unpriced": 0,
      "cached": 1277,
      "errors": 0,
      "estimated_cost_usd": 0.045549,
      "avg_latency_s": 0.254
    },
    "... 20 more"
  ],
  "total": {
    "n": 6460,
    "pt": 2538720,
    "ct": 913995,
    "crt": 249667,
    "cwt": 597563,
    "cached": 4620,
    "errors": 72,
    "unpriced": 0,
    "estimated_cost_usd": 25.575163
  },
  "prices_usd_per_million_tokens": {
    "claude-opus-5-5": {
      "input": 4.0,
      "cache_write": 5.0,
      "cache_read": 0.2,
      "output": 20.0
    },
    "claude-sonnet-5-5": {
      "input": 2.0,
      "cache_write": 2.5,
      "cache_read": 0.1,
      "output": 10.0
    },
    "claude-haiku-5-5": {
      "input": 0.1,
      "cache_write": 0.125,
      "cache_read": 0.01,
      "output": 0.5,
      "long_context_threshold": 100000,
      "long": {
        "input": 0.5,
        "cache_write": 0.625,
        "cache_read": 0.05,
        "output": 2.5
      }
    }
  },
  "note": "pt = uncached input tokens, crt/cwt = cache read/write tokens, ct = output tokens (thinking included); unpriced = calls to a model without a price entry (add it via LLM_PRICE_TABLE)."
}
```

---

## Feedback
Advisor feedback and the approval-gated improvement loop.

### <span class="method POST">POST</span> `/api/feedback`
**Submit advisor feedback.** Rating of a recommendation, accepted actions, useful precedents and the real outcome when known.

| Endpoint | HTTP method | Authentication | Responses |
|---|---|---|---|
| `/api/feedback` | POST | X-API-Key | 201, 400 |

**Request format: JSON body** (`FeedbackRequest`)

| Field | Type | Required | Constraints | Description |
|---|---|---|---|---|
| `recommendation_id` | string | yes | min length 8, max length 64 |  |
| `id_student` | integer | yes | > 0.0 |  |
| `advisor_id` | string (optional) | no | max length 64 |  |
| `rating` | integer | yes | >= 1.0, <= 5.0 |  |
| `plan_accepted` | boolean | yes |  |  |
| `risk_assessment_agrees` | boolean (optional) | no |  |  |
| `action_feedback` | object of ActionFeedback (optional) | no |  |  |
| `case_feedback` | object of boolean (optional) | no |  |  |
| `observed_outcome` | one of `Distinction`, `Pass`, `Fail`, `Withdrawn` (optional) | no |  |  |
| `intervention_effective` | boolean (optional) | no |  |  |
| `notes` | string | no | max length 2000, default `""` |  |

Types written in CamelCase (for example `StudentRef`) are described once in *Appendix: shared request models*.

**Response format** (JSON object, HTTP 201):
`status` (string), `feedback_id` (integer).

**Sample request**
```bash
curl -X POST "http://127.0.0.1:8000/api/feedback" \
  -H "X-API-Key: $STUDENT_ASSISTANT_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"recommendation_id": "cbee97dffd3415f758fe", "id_student": 692826, "rating": 4, "plan_accepted": true, "risk_assessment_agrees": true, "notes": "Good plan; the student prefers phone calls.", "observed_outcome": null}'
```

**Sample response** (HTTP 201, 0.01 s)

```json
{
  "status": "recorded",
  "feedback_id": 1
}
```

---

### <span class="method GET">GET</span> `/api/feedback`
**Recent feedback.** The latest feedback rows.

| Endpoint | HTTP method | Authentication | Responses |
|---|---|---|---|
| `/api/feedback` | GET | X-API-Key | 200, 400 |

**Request format: parameters**

| Name | In | Type | Required | Constraints | Description |
|---|---|---|---|---|---|
| `limit` | query | integer | no | >= 1, <= 500, default `50` |  |

**Response format** (JSON object, HTTP 200):
`items` (array).

**Sample request**
```bash
curl -X GET "http://127.0.0.1:8000/api/feedback?limit=3" \
  -H "X-API-Key: $STUDENT_ASSISTANT_API_KEY"
```

**Sample response** (HTTP 200, 0.01 s)

```json
{
  "items": [
    {
      "id": 1,
      "recommendation_id": "cbee97dffd3415f758fe",
      "created_at": 1791822614.739139,
      "advisor_id": null,
      "rating": 4,
      "plan_accepted": 1,
      "risk_assessment_agrees": 1,
      "action_feedback": {},
      "case_feedback": {},
      "observed_outcome": null,
      "intervention_effective": null,
      "notes": "Good plan; the student prefers phone calls.",
      "...": "6 more fields"
    }
  ]
}
```

---

### <span class="method GET">GET</span> `/api/feedback/summary`
**Feedback summary.** Counts, average usefulness, plan acceptance and agreement rates.

| Endpoint | HTTP method | Authentication | Responses |
|---|---|---|---|
| `/api/feedback/summary` | GET | X-API-Key | 200 |

**Request format:** no parameters or body.

**Response format** (JSON object, HTTP 200):
`count` (integer), `average_rating` (number), `plan_acceptance_rate` (number), `risk_agreement_rate` (number), `effectiveness_rate` (null), `with_observed_outcome` (integer).

**Sample request**
```bash
curl -X GET "http://127.0.0.1:8000/api/feedback/summary" \
  -H "X-API-Key: $STUDENT_ASSISTANT_API_KEY"
```

**Sample response** (HTTP 200, 0.0 s)

```json
{
  "count": 1,
  "average_rating": 4.0,
  "plan_acceptance_rate": 1.0,
  "risk_agreement_rate": 1.0,
  "effectiveness_rate": null,
  "with_observed_outcome": 0
}
```

---

### <span class="method GET">GET</span> `/api/feedback/themes`
**Themes in advisor notes.** Groups free-text notes into themes (LLM with a keyword fallback).

| Endpoint | HTTP method | Authentication | Responses |
|---|---|---|---|
| `/api/feedback/themes` | GET | X-API-Key | 200 |

**Request format:** no parameters or body.

**Response format** (JSON object, HTTP 200):
`themes` (array), `source` (string).

**Sample request**
```bash
curl -X GET "http://127.0.0.1:8000/api/feedback/themes" \
  -H "X-API-Key: $STUDENT_ASSISTANT_API_KEY"
```

**Sample response** (HTTP 200, 3.0 s)

```json
{
  "themes": [
    {
      "theme": "Clear, well-received advising plan",
      "count": 1,
      "note_ids": [
        1
      ],
      "suggestion": "Keep structuring plans clearly and check the student's preferred contact method, such as phone calls, when scheduling follow-up."
    }
  ],
  "source": "llm"
}
```

---

### <span class="method GET">GET</span> `/api/improvement-plan`
**Improvement proposals.** Changes the feedback currently justifies, each with its evidence and minimum-sample guard.

| Endpoint | HTTP method | Authentication | Responses |
|---|---|---|---|
| `/api/improvement-plan` | GET | X-API-Key | 200 |

**Request format:** no parameters or body.

**Response format** (JSON object, HTTP 200):
`generated_at` (string), `feedback_rows` (integer), `proposals` (array), `monitors` (array), `applied` (array), `process` (array).

**Sample request**
```bash
curl -X GET "http://127.0.0.1:8000/api/improvement-plan" \
  -H "X-API-Key: $STUDENT_ASSISTANT_API_KEY"
```

**Sample response** (HTTP 200, 0.0 s)

```json
{
  "generated_at": "2026-10-11T07:53:57",
  "feedback_rows": 0,
  "proposals": [
    {
      "type": "action_catalog_ranking",
      "status": "insufficient_data",
      "evidence": {
        "actions_with_feedback": 0
      },
      "payload": {
        "actions": {}
      }
    },
    {
      "type": "retrieval_fusion_weights",
      "status": "insufficient_data",
      "evidence": {
        "labelled_rows": 0,
        "required": 30
      }
    },
    "... 1 more"
  ],
  "monitors": [],
  "applied": [],
  "process": [
    "advisors rate plans, actions and similar cases; record real outcomes",
    "learners produce proposals with evidence and minimum-sample guards",
    "... 2 more"
  ]
}
```

---

### <span class="method POST">POST</span> `/api/feedback-loop/run`
**Run the feedback loop (admin).** Recalculates proposals; with apply=true, applies the ready ones as versioned artifacts. Needs X-Admin-Key.

| Endpoint | HTTP method | Authentication | Responses |
|---|---|---|---|
| `/api/feedback-loop/run` | POST | X-API-Key + X-Admin-Key | 200, 400 |

**Request format: JSON body** (`FeedbackLoopRequest`)

| Field | Type | Required | Constraints | Description |
|---|---|---|---|---|
| `apply` | boolean | no | default `false` |  |
| `approved_by` | string (optional) | no | max length 64 |  |

Types written in CamelCase (for example `StudentRef`) are described once in *Appendix: shared request models*.

**Response format** (JSON object, HTTP 200):
`generated_at` (string), `feedback_rows` (integer), `proposals` (array), `monitors` (array), `applied` (array), `process` (array).

**Sample request**
```bash
curl -X POST "http://127.0.0.1:8000/api/feedback-loop/run" \
  -H "X-API-Key: $STUDENT_ASSISTANT_API_KEY" \
  -H "X-Admin-Key: $STUDENT_ASSISTANT_ADMIN_KEY" \
  -H "Content-Type: application/json" \
  -d '{"apply": false}'
```

**Sample response** (HTTP 200, 0.01 s)

```json
{
  "generated_at": "2026-10-12T22:00:17",
  "feedback_rows": 1,
  "proposals": [
    {
      "type": "action_catalog_ranking",
      "status": "insufficient_data",
      "evidence": {
        "actions_with_feedback": 0
      },
      "payload": {
        "actions": {}
      }
    },
    {
      "type": "retrieval_fusion_weights",
      "status": "insufficient_data",
      "evidence": {
        "labelled_rows": 0,
        "required": 30
      }
    },
    "... 1 more"
  ],
  "monitors": [],
  "applied": [],
  "process": [
    "advisors rate plans, actions and similar cases; record real outcomes",
    "learners produce proposals with evidence and minimum-sample guards",
    "... 2 more"
  ]
}
```

---

<div class="pb"></div>

## Appendix: shared request models
Models used inside the request bodies above.

### ActionFeedback


| Field | Type | Required | Constraints | Description |
|---|---|---|---|---|
| `accepted` | boolean | yes |  |  |
| `useful` | boolean (optional) | no |  |  |

### ChatTurn


| Field | Type | Required | Constraints | Description |
|---|---|---|---|---|
| `role` | one of `user`, `assistant` | yes |  |  |
| `content` | string | yes | max length 4000 |  |

### FeatureProfile
Snapshot features (all optional). Units follow the feature pipeline.

| Field | Type | Required | Constraints | Description |
|---|---|---|---|---|
| `id_student` | integer (optional) | no | > 0.0, < 10000000.0 |  |
| `code_module` | one of `AAA`, `BBB`, `CCC`, `DDD`, `EEE`, `FFF`, `GGG` | yes |  |  |
| `code_presentation` | string (optional) | no |  |  |
| `gender` | one of `F`, `M`, `Unknown` (optional) | no |  |  |
| `region` | one of `East Anglian Region`, `East Midlands Region`, `Ireland`, `London Region`, `North Region`, `North Western Region`, `Scotland`, `South East Region`, `South Region`, `South West Region`, `Wales`, `West Midlands Region`, `Yorkshire Region`, `Unknown` (optional) | no |  |  |
| `highest_education` | one of `No Formal quals`, `Lower Than A Level`, `A Level or Equivalent`, `HE Qualification`, `Post Graduate Qualification`, `Unknown` (optional) | no |  |  |
| `imd_band` | one of `0-10%`, `10-20%`, `20-30%`, `30-40%`, `40-50%`, `50-60%`, `60-70%`, `70-80%`, `80-90%`, `90-100%`, `10-20`, `Unknown` (optional) | no |  |  |
| `age_band` | one of `0-35`, `35-55`, `55<=`, `Unknown` (optional) | no |  |  |
| `num_of_prev_attempts` | integer (optional) | no | >= 0.0, <= 10.0 |  |
| `studied_credits` | integer (optional) | no | >= 0.0, <= 700.0 |  |
| `registration_days_before_start` | number (optional) | no | >= -300.0, <= 400.0 |  |
| `late_registration` | integer (optional) | no | >= 0.0, <= 1.0 |  |
| `snapshot_day` | integer (optional) | no | >= 7.0, <= 300.0 |  |
| `assessments_due` | integer (optional) | no | >= 0.0, <= 30.0 |  |
| `submitted_count` | integer (optional) | no | >= 0.0, <= 40.0 |  |
| `submitted_due_count` | integer (optional) | no | >= 0.0, <= 30.0 |  |
| `missed_count` | integer (optional) | no | >= 0.0, <= 30.0 |  |
| `missed_rate` | number (optional) | no | >= 0.0, <= 1.0 |  |
| `no_scores_yet` | integer (optional) | no | >= 0.0, <= 1.0 |  |
| `mean_score` | number (optional) | no | >= 0.0, <= 100.0 |  |
| `weighted_score` | number (optional) | no | >= 0.0, <= 100.0 |  |
| `score_std` | number (optional) | no | >= 0.0, <= 60.0 |  |
| `min_score` | number (optional) | no | >= 0.0, <= 100.0 |  |
| `max_score` | number (optional) | no | >= 0.0, <= 100.0 |  |
| `last_score` | number (optional) | no | >= 0.0, <= 100.0 |  |
| `score_slope` | number (optional) | no | >= -100.0, <= 100.0 |  |
| `late_rate` | number (optional) | no | >= 0.0, <= 1.0 |  |
| `mean_days_early` | number (optional) | no | >= -30.0, <= 60.0 |  |
| `total_clicks` | number (optional) | no | >= 0.0, <= 200000.0 |  |
| `active_days` | integer (optional) | no | >= 0.0, <= 400.0 |  |
| `resources_used` | integer (optional) | no | >= 0.0, <= 2000.0 |  |
| `activity_types_used` | integer (optional) | no | >= 0.0, <= 25.0 |  |
| `pre_start_clicks` | number (optional) | no | >= 0.0, <= 100000.0 |  |
| `days_since_last_activity` | number (optional) | no | >= 0.0, <= 300.0 |  |
| `weeks_active` | integer (optional) | no | >= 0.0, <= 45.0 |  |
| `engagement_slope` | number (optional) | no | >= -5000.0, <= 5000.0 |  |
| `engagement_momentum` | number (optional) | no | >= -1.0, <= 1000.0 |  |
| `engagement_drop_ratio` | number (optional) | no | >= 0.0, <= 1.0 |  |
| `longest_inactive_streak` | integer (optional) | no | >= 0.0, <= 45.0 |  |
| `inactive_weeks_last3` | integer (optional) | no | >= 0.0, <= 3.0 |  |
| `clicks_pct` | number (optional) | no | >= 0.0, <= 1.0 |  |
| `score_pct` | number (optional) | no | >= 0.0, <= 1.0 |  |

### RetrievalFilters


| Field | Type | Required | Constraints | Description |
|---|---|---|---|---|
| `code_module` | one of `AAA`, `BBB`, `CCC`, `DDD`, `EEE`, `FFF`, `GGG` or array of one of `AAA`, `BBB`, `CCC`, `DDD`, `EEE`, `FFF`, `GGG` (optional) | no |  |  |
| `code_presentation` | string or array of string (optional) | no |  |  |
| `region` | one of `East Anglian Region`, `East Midlands Region`, `Ireland`, `London Region`, `North Region`, `North Western Region`, `Scotland`, `South East Region`, `South Region`, `South West Region`, `Wales`, `West Midlands Region`, `Yorkshire Region`, `Unknown` or array of one of `East Anglian Region`, `East Midlands Region`, `Ireland`, `London Region`, `North Region`, `North Western Region`, `Scotland`, `South East Region`, `South Region`, `South West Region`, `Wales`, `West Midlands Region`, `Yorkshire Region`, `Unknown` (optional) | no |  |  |
| `highest_education` | one of `No Formal quals`, `Lower Than A Level`, `A Level or Equivalent`, `HE Qualification`, `Post Graduate Qualification`, `Unknown` or array of one of `No Formal quals`, `Lower Than A Level`, `A Level or Equivalent`, `HE Qualification`, `Post Graduate Qualification`, `Unknown` (optional) | no |  |  |
| `age_band` | one of `0-35`, `35-55`, `55<=`, `Unknown` or array of one of `0-35`, `35-55`, `55<=`, `Unknown` (optional) | no |  |  |
| `studied_credits` | integer or object of number (optional) | no |  |  |
| `num_of_prev_attempts` | integer or object of number (optional) | no |  |  |
| `final_result` | one of `Distinction`, `Pass`, `Fail`, `Withdrawn` or array of one of `Distinction`, `Pass`, `Fail`, `Withdrawn` (optional) | no |  |  |

### StudentRef


| Field | Type | Required | Constraints | Description |
|---|---|---|---|---|
| `id_student` | integer | yes | > 0.0, < 10000000.0 |  |
| `code_module` | one of `AAA`, `BBB`, `CCC`, `DDD`, `EEE`, `FFF`, `GGG` | yes |  |  |
| `code_presentation` | string | yes |  |  |

