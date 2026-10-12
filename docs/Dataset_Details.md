<div class="cover" markdown="1">

# Dataset Details

<div class="sub">Uplift: Student Success Assistant</div>
<div class="meta">Open University Learning Analytics Dataset (OULAD). Counts in this document are read from the data files and the
build metrics by <code>scripts/build_docs.py</code>.</div>

</div>

## 1. Dataset name
**Open University Learning Analytics Dataset (OULAD)**, the dataset named in the problem statement.

## 2. Dataset source
The Open University (United Kingdom), Knowledge Media Institute. Published by Kuzilek, Hlosta and Zdrahal (2017),
*Open University Learning Analytics dataset*, Scientific Data 4:170171, doi:10.1038/sdata.2017.171.
Licence: Creative Commons Attribution 4.0 (CC BY 4.0). The data is anonymised by the publisher; student IDs are not
linked to real people.

## 3. Dataset link
- Primary: <https://analyse.kmi.open.ac.uk/open_dataset> (also mirrored on Figshare, as given in the brief)
- Alternative: the OULAD GitHub mirror referenced in the brief
- Paper: <https://doi.org/10.1038/sdata.2017.171>

## 4. Data format
Seven CSV files (comma separated, header row, UTF-8), relational and joined on `code_module`, `code_presentation`,
`id_student`, `id_assessment` and `id_site`. Place them in `data/raw/` (not committed; see the README).

| File | What one row is | Rows (full dataset) | Rows (`data/sample_data`) |
|---|---|---|---|
| `courses.csv` | a module presentation and its length in days | 22 | 22 |
| `assessments.csv` | an assessment of a presentation (type, deadline day, weight) | 206 | 206 |
| `vle.csv` | a learning material in the virtual learning environment | 6,364 | 6,364 |
| `studentInfo.csv` | a student's enrolment on a presentation: demographics and final result | 32,593 | 880 |
| `studentRegistration.csv` | registration and (if any) unregistration day for an enrolment | 32,593 | 880 |
| `studentAssessment.csv` | a submission: day submitted and score | 173,912 | 4,644 |
| `studentVle.csv` | a student's clicks on one material on one day | 10,655,280 | 294,849 |

Scope: 4 presentations (2013B, 2013J, 2014B, 2014J) across
7 modules (AAA to GGG), 32,593 enrolments in total.

## 5. Key fields
| Table | Fields | Use in this project |
|---|---|---|
| studentInfo | `id_student, code_module, code_presentation, gender, region, highest_education, imd_band, age_band, num_of_prev_attempts, studied_credits, disability, final_result` | `final_result` is the **label** (Distinction / Pass / Fail / Withdrawn). Previous attempts and credits are features. The six demographic fields are **sensitive**: never model inputs, never sent to the LLM; used only for the fairness audit and as retrieval filters. |
| studentRegistration | `code_module, code_presentation, id_student, date_registration, date_unregistration` | Registration timing is a feature. `date_unregistration` only decides who is **still enrolled** at a checkpoint (scope); it is never a feature. |
| assessments | `code_module, code_presentation, id_assessment, assessment_type, date, weight` | Deadlines (TMA, CMA, Exam) and weights: which work was due by the checkpoint. |
| studentAssessment | `id_assessment, id_student, date_submitted, is_banked, score` | Scores, missed work, lateness, score trend, only for submissions on or before the checkpoint day. |
| vle | `id_site, code_module, code_presentation, activity_type, week_from, week_to` | Material types (content, resource, forum, quiz...) and planned weeks. |
| studentVle | `code_module, code_presentation, id_student, id_site, date, sum_click` | Daily clicks: weekly engagement, inactivity streaks, trends, material coverage, up to the checkpoint. |
| courses | `code_module, code_presentation, module_presentation_length` | Course length: checkpoints are fractions of it. |

## 6. Dataset purpose
OULAD links, for each enrolment, the student profile, the assessment record, day-by-day online learning activity and the
final result. That is what the brief needs:

- **Early warning**: predict withdrawal and the final outcome from what is known part-way through a course.
- **Similar-case retrieval (RAG)**: every finished enrolment is a historical case with a known outcome, so "what happened
  to students like this one" can be answered from real records.
- **Prioritisation, explanation and trends**: assessment and engagement signals rank and explain risk; weekly activity
  shows when struggling students diverge.
- **Fairness**: the demographic fields let us audit the model's errors by group, without using them as inputs.

## 7. Data preprocessing performed
Implemented in `src/pipeline/pipeline.py` (`python -m src.cli prepare`), once per checkpoint.

**7.1 Checkpoints ("as of" snapshots).** A snapshot is taken at 4 points of each presentation:
15% (week 5), 25% (week 9), 40% (week 15), 60% (week 22)of its length. Every feature uses only rows dated on or before the snapshot day.

**7.2 Population scoping (the most important step).** Students who had already unregistered by the snapshot day cannot
be helped by an early warning. They are kept in the data, marked `in_scope = 0`, and excluded from modelling, evaluation,
retrieval and ranking. At week 15: 32,593 enrolments, of which
25,204 are in scope; 7,389 had
already left (3,097 before the course started).

| Checkpoint | Course week | Students still enrolled (in scope) |
|---|---|---|
| c15 | 5 | 27,157 |
| c25 | 9 | 26,241 |
| c40 | 15 | 25,204 |
| c60 | 22 | 23,926 |

**7.3 Leakage controls** (recorded in the build metrics):
- assessment and VLE rows filtered to date <= snapshot_day
- students unregistered on/before snapshot_day excluded from modelling scope (in_scope=0)
- date_unregistration used for scoping only; never a feature
- final_result used as label only
- peer percentiles computed from in-scope peers at snapshot time

**7.4 Cleaning.**
- Missing is not zero: students with no scored assessment keep empty scores plus a `no_scores_yet` flag.
- Banked results (carried over from earlier attempts) are counted separately.
- `studentVle.csv` (the large table) is read with compact data types and joined on integer keys, so the full build fits in
  under 2 GB of memory.
- Categorical values are validated against fixed vocabularies (modules, regions, education levels, age bands).

**7.5 Feature engineering.** 66 numeric features in three groups, plus the module:

- *Enrolment*: previous attempts, credits, how early the student registered, late registration.
- *Academic*: assessments due, submitted, missed (TMA and CMA separately), average / weighted / last / lowest score,
  score trend, lateness, cohort percentiles.
- *Engagement*: weekly clicks on a dense week grid (zero-activity weeks included), active days, recent vs early activity,
  momentum, inactivity streaks, days since last activity, activity by material type, share of scheduled materials opened,
  cohort percentiles.

<details markdown="1"><summary>All features</summary>

| Feature | Meaning |
|---|---|
| `num_of_prev_attempts` | Previous attempts at this module |
| `studied_credits` | Credits studied this term |
| `registration_days_before_start` | How early the student registered |
| `registration_date_missing` | Registration date missing |
| `late_registration` | Registered after start |
| `snapshot_day` | Course day of snapshot |
| `weeks_observed` | Weeks observed |
| `assessments_due` | Assessments due so far |
| `submitted_count` | Assessments submitted |
| `submitted_due_count` | Due assessments submitted |
| `missed_count` | Missed assessments |
| `missed_rate` | Share of due assessments missed |
| `no_scores_yet` | No scored assessment yet |
| `mean_score` | Average assessment score |
| `weighted_score` | Weighted assessment score |
| `score_std` | Score variability |
| `min_score` | Lowest score |
| `max_score` | Highest score |
| `last_score` | Most recent score |
| `score_slope` | Score trajectory |
| `late_rate` | Late submission rate |
| `mean_days_early` | Average days submitted before deadline |
| `banked_count` | Banked results |
| `score_pct` | Score percentile in cohort |
| `missed_rate_pct` | Missed-assessment percentile in cohort |
| `tma_mean_score` | Tutor-marked assignment average |
| `cma_mean_score` | Computer-marked assessment average |
| `tma_due` | Tutor-marked assignments due |
| `cma_due` | Computer-marked assessments due |
| `tma_missed` | Tutor-marked assignments missed |
| `cma_missed` | Computer-marked assessments missed |
| `total_clicks` | VLE activity (clicks) |
| `log_total_clicks` | VLE activity (log clicks) |
| `active_days` | Active learning days |
| `resources_used` | Distinct resources used |
| `activity_types_used` | Distinct activity types used |
| `pre_start_clicks` | Pre-course activity |
| `clicks_content` | Course-content activity |
| `clicks_resource` | Resource activity |
| `clicks_forum` | Forum/collaboration activity |
| `clicks_quiz` | Quiz activity |
| `clicks_homepage` | Homepage visits |
| `clicks_other` | Other activity |
| `share_content` | Share of activity on content |
| `share_resource` | Share of activity on resources |
| `share_forum` | Share of activity on forums |
| `share_quiz` | Share of activity on quizzes |
| `share_homepage` | Share of activity on homepage |
| `no_vle_activity` | No VLE activity |
| `days_since_last_activity` | Days since last VLE activity |
| `clicks_per_active_day` | Activity per active day |
| `weeks_active` | Weeks with any activity |
| `engagement_weekly_mean` | Average weekly activity |
| `engagement_slope` | Weekly engagement trend |
| `engagement_slope_rel` | Relative weekly engagement trend |
| `engagement_early_mean` | Early-weeks activity |
| `engagement_recent_mean` | Recent-weeks activity |
| `engagement_momentum` | Recent engagement momentum |
| `engagement_cv` | Engagement irregularity |
| `longest_inactive_streak` | Longest inactive streak (weeks) |
| `inactive_weeks_last3` | Inactive weeks (last 3) |
| `engagement_drop_ratio` | Engagement decline ratio |
| `clicks_pct` | Activity percentile in cohort |
| `active_days_pct` | Active-days percentile in cohort |
| `planned_materials_due` | Scheduled materials so far |
| `planned_coverage` | Share of scheduled materials opened |

</details>

**7.6 Labels.** Withdrawal after the snapshot (binary, among students still enrolled) and the four-class final outcome.
"Poor outcome" (fail or withdraw) is used for prioritisation.

**7.7 Retrieval documents.** Each finished, in-scope enrolment becomes one case: its snapshot features, discretised
descriptor tokens (for example `missed_most`, `engagement_declining`) and a short narrative for the dense channel. Numbers
never reach the text channels; they are banded relative to the cohort. See the Design Document, section 4.

**7.8 Temporal split.** Train on 2013B + 2013J, tune on
2014B, test once on 2014J (the
latest presentation, never used for any choice). Historical retrieval only searches presentations earlier than the query.

## 8. Sample data (`data/sample_data/`)
A real slice of OULAD in the original seven-table format, committed so the pipeline can be run without downloading the
full dataset: a fixed number of students drawn (seed 42) from every module presentation, with all their rows; the
reference tables are complete. Made by `scripts/make_sample_data.py`. Run the whole pipeline on it with:

```bash
SSA_HOME=.sample SSA_RAW_DIR=data/sample_data python -m src.cli build --no-dense
```

It is far too small for meaningful metrics; every result reported in this submission comes from the full dataset.
