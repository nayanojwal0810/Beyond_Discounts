# Beyond Discounts: Customer Segmentation and Retention Strategy for Indian Quick Commerce

[![Gate Status](https://img.shields.io/badge/Gate%200-Closed%20%26%20Locked-success)](docs/gates/GATE_0_DECISION_LOG.md)
[![Current Gate](https://img.shields.io/badge/Current%20Gate-1C.1%20Technical%20QA-orange)](docs/gates/GATE_1C1_TECHNICAL_REVIEW.md)
[![License: CC BY 4.0](https://img.shields.io/badge/Data%20License-CC%20BY%204.0-lightgrey)](https://creativecommons.org/licenses/by/4.0/)

---

## 1. Project Overview & Canonical Framing

### Approved Working Title
**Beyond Discounts: Customer Segmentation and Retention Strategy for Indian Quick Commerce**

### Research Question
> *Which lifecycle-based CRM actions are best supported by the observed sample's stated future-use intentions, discount-reduction continuation intentions, non-use barriers, and preferred service improvements?*
>
> *Do exploratory behavioral clusters add actionable differentiation beyond lifecycle cohorts?*

### Project Approach
This is an evidence-led CRM decision project, not a contest to produce visually attractive clusters. The primary decision framework compares never-users, previous users and the survey-defined current-user cohort. Unsupervised clustering remains a bounded methodological experiment: it will be retained as an actionable segmentation method only if separation, reproducibility and independent outcome profiling justify it. If not, lifecycle cohort analysis is the more defensible result.

### Proposed Business Value
The final deliverable will translate measured differences into evidence-tagged candidate CRM actions for:
1. **Adoption:** understand barriers and future-use intention among never-users ($n=376$).
2. **Reactivation research:** describe previous users who currently report no orders ($n=80$) without claiming observed churn or knowing why they stopped.
3. **Retention hypothesis design:** understand current users' stated intention to continue at the same frequency if discounts/promotions are reduced ($n=807$), then use their stated improvement preferences to formulate pilot candidates.

These are hypotheses for a real-world experiment, not established intervention effects. The survey cannot prove campaign uplift, actual repeat purchase, transactional churn or customer lifetime value.

---

## 2. Scope Boundaries & Framing History

- **Industry-Wide Category Scope:** The underlying survey measures general quick-commerce shopping behavior, category preferences, discount habits, and service expectations across the Indian quick-commerce sector.
- **Removal of Single-Firm Focal Framing:** Earlier exploratory framing utilized Blinkit as a focal case application. This framing has been formally superseded because the empirical survey measures category-level behavior rather than firm-specific customer satisfaction or brand-level retention outcomes. No single company is treated as a focal case.
- **No Transactional Churn or CLV Claims:** Stated likelihood of future use (QA 46) and willingness to continue if discounts are reduced (QA 47) represent self-reported perceptions, not observed repeat purchases, bank transactions, or actual churn events.
- **Exploratory Sample Provenance:** The dataset contains 1,263 respondents. Fieldwork dates, geographic clustering, and sampling frame provenance remain unresolved; findings reflect the observed sample and are not claimed to be nationally representative.

---

## 3. Dataset Profile & Respondent Subgroups

The primary empirical source is the survey workbook `data/raw/survey/Data.xlsx` (worksheet `Data`, 1,263 rows $\times$ 130 columns), accompanied by `Code Book.docx` and `Questionairre.docx` (Chandra, Mendeley Data, DOI: `10.17632/cw88nb7822.1`).

### Subgroup Routing Ground Truth
The 1,263 respondents are partitioned into three mutually exclusive, verified subgroups:

| Subgroup | Definition / Filter | Count ($n$) | Share (%) | Questionnaire Routing Rules |
| :--- | :--- | :---: | :---: | :--- |
| **Never-Users** | `Ever Ordered == 0` AND `Order Frequency == 1 (Never)` | 376 | 29.8% | Routed to QA 48 (reasons for non-use); QA 47 coded 6 (Not Applicable). QA 46 & 49 substantive. |
| **Previous Users** | `Ever Ordered == 1` AND `Order Frequency == 1 (Never)` | 80 | 6.3% | Lapsed users reporting no current orders. Routed to QA 48; QA 47 coded 6 (Not Applicable). Historical satisfaction unobserved. QA 46 & 49 substantive. |
| **Current Users (survey-defined cohort)** | `Ever Ordered == 1` AND `Order Frequency > 1` | 807 | 63.9% | Questionnaire-defined current users; includes respondents selecting “less than once a month.” QA 47 substantive (1–5 scale: Definitely no to Definitely yes). QA 48 holds binary indicator `Reason Not Applicable Current User == 1`. QA 46 & 49 substantive. |
| **Total Sample** | Full workbook manifest | **1,263** | **100.0%** | **Physical nulls = 0; duplicate rows = 0.** |

### Mandatory Questionnaire Semantics
- **QA 46 (Next 3 Month Use):** Measures stated future-use intention across all 1,263 respondents (1 = Definitely will not, 5 = Definitely will).
- **QA 47 (Continue If Discounts Reduced):** Measures stated continuation intention under a hypothetical discount/promotion reduction among the 807 current users (1 = Definitely no, 5 = Definitely yes). Code 6 is an explicit questionnaire routing code ("Not Applicable") for the 456 non-current users; it must **never** be coded as churn or negative sentiment.
- **QA 48 (Reasons for Non-Use):** Multi-response binary flags for non-current users ($n=456$), analyzed with never-users ($n=376$) and previous users ($n=80$) distinguished.
- **QA 49 (Preferred Improvement):** Substantive single-choice preference across all 1,263 respondents (1–10 scale).
- **QA 24 (Physical Store Preferences):** Substantive across all 1,263 respondents (no N/A option in codebook).
- **QA 26 (Monthly Spend):** Code 1 represents substantive ₹0 spend, not missing data.
- **QA 43 (Shopping Routine Role):** Code 6 represents substantive "I do not use quick commerce", not missing data.

---

## 4. Repository Structure

```text
Beyond_Discounts/
├── README.md
├── requirements.txt
├── data/
│   └── README.md                                   # Provenance, routing semantics, input setup and privacy
├── docs/
│   ├── data/DATA_SOURCE_REGISTER.csv               # Source evaluation and provenance register
│   ├── research/LITERATURE_EVIDENCE_REGISTER.md     # Literature screening register; critical synthesis pending
│   └── gates/
│       ├── GATE_0_DECISION_LOG.md                  # Dataset and scope decision history
│       ├── GATE_0_SURVEY_CANDIDATE_AUDIT.md        # Source survey audit and limitations
│       └── GATE_1C1_TECHNICAL_REVIEW.md            # Current technical QA and closure criteria
├── scripts/
│   ├── audit_survey_data.py                        # Survey schema and routing audit
│   ├── run_eda.py                                  # Gate 1A EDA
│   ├── prepare_segmentation_features.py            # Typed features/specifications/holdouts
│   ├── run_segmentation_experiments.py              # Gower/PAM/HAC + QA49 holdout profiles
│   └── run_crm_analysis.py                         # Lifecycle CRM tables and QA47 ordinal model
├── reports/
│   ├── eda/                                        # Aggregate EDA tables, figures and report
│   ├── segmentation/                               # Aggregate clustering metrics/profiles
│   └── crm/                                        # Decision-analysis plan and generated aggregate tables
└── tests/                                          # Automated audit, segmentation and CRM tests
```

Historical app-review feasibility artifacts and scripts remain for auditability but are **superseded for primary quantitative analysis**. The survey workbook, codebook, questionnaire, processed matrices, and respondent-level assignments are local-only and must stay outside Git.

## 5. Reproduction & Execution Guide

### Local input setup
Place the Mendeley survey workbook and its codebook/questionnaire under `data/raw/survey/` as documented in `data/README.md`. Do not commit the workbook, questionnaire-level rows, or any row-level derived data. Install the declared direct-dependency baseline with `python -m pip install -r requirements.txt`; full pipeline verification on the local workbook is still pending. Dataset source: [Mendeley Data, DOI 10.17632/cw88nb7822.1](https://data.mendeley.com/datasets/cw88nb7822/1).

### Run sequence
```bash
python -m pip install -r requirements.txt
python scripts/audit_survey_data.py --file data/raw/survey/Data.xlsx --sheet Data --output docs/gates/GATE_0_SURVEY_AUDIT_SUMMARY.json
python scripts/run_eda.py --file data/raw/survey/Data.xlsx --sheet Data
python scripts/run_segmentation_experiments.py --survey-file data/raw/survey/Data.xlsx
python -m unittest discover -s tests -v
# Only after Gate 1C.1 is approved:
python scripts/run_crm_analysis.py --file data/raw/survey/Data.xlsx --sheet Data --out-dir reports/crm/tables
```

The segmentation experiment prepares its feature matrices and holdout locally if missing, then writes aggregate outputs under `reports/segmentation/`. Gate 1C.1 is not closed until the full local run succeeds and its regenerated reports reconcile. The Gate 1D runner is implemented but is not yet accepted as evidence until it has been executed on the real workbook and its diagnostics reviewed.

**Reproducibility status:** direct dependency versions are pinned in `requirements.txt`, but this is not a full transitive/hash lock and has not been verified against a complete real-workbook run. The clean-clone clustering test path now has synthetic fixtures; the full workbook pipeline remains an explicit Gate 1C.1 acceptance criterion. Existing committed aggregate reports are evidence of prior runs, not proof the current branch has been rerun end-to-end.

## 6. Project Governance & Working Rules

1. **Role of Implementation Worker:** Code implementation, automated verification, reproducible documentation, and evidence generation.
2. **Role of Principal Project Lead:** Analytical authority, methodological decisions, and gate approvals. Code execution alone does not constitute gate approval.
3. **Privacy & Data Security:** No raw survey rows, individual respondent answers, or personally identifiable information are committed to version control. All committed outputs are aggregate statistical summaries.
4. **Interpretation Discipline:** Survey outcomes are stated intentions and preferences, not observed purchase, churn, loyalty, price elasticity or causal treatment effects.
5. **Current Decision:** Complete Gate 1C.1 technical verification, then run the lifecycle-based Gate 1D CRM analyses before building the dashboard. See [Gate 1C.1 review](docs/gates/GATE_1C1_TECHNICAL_REVIEW.md) and [Gate 1D plan](reports/crm/CRM_DECISION_ANALYSIS_PLAN.md).
