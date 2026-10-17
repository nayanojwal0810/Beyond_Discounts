# Beyond Discounts: Customer Segmentation and Retention Strategy for Indian Quick Commerce

[![Gate Status](https://img.shields.io/badge/Gate%200-Closed%20%26%20Locked-success)](docs/gates/GATE_0_DECISION_LOG.md)
[![Current Gate](https://img.shields.io/badge/Current%20Gate-1A%20EDA%20In%20Progress-blue)](reports/eda/EDA_REPORT.md)
[![License: CC BY 4.0](https://img.shields.io/badge/Data%20License-CC%20BY%204.0-lightgrey)](https://creativecommons.org/licenses/by/4.0/)

---

## 1. Project Overview & Canonical Framing

### Approved Working Title
**Beyond Discounts: Customer Segmentation and Retention Strategy for Indian Quick Commerce**

### Research Question
> *How do quick-commerce consumers differ in their discount sensitivity, usage behaviour, and stated future-use intentions, and what adoption, reactivation, or retention actions are supported by these differences?*

### Problem We Are Investigating
Quick-commerce consumers in India may differ significantly in the importance they place on promotional discounts, delivery speed, shopping convenience, spending levels, service experience, and operational reliability. A one-size-fits-all retention or reactivation strategy cannot suit every consumer type. 

This project investigates these behavioral and attitudinal differences using empirical survey microdata ($N=1,263$) to evaluate whether defensible, interpretable customer segments can be developed across Indian quick-commerce consumers.

### Proposed Business Value
The ultimate objective is to translate observed, data-grounded consumer differences into actionable, evidence-based CRM strategies for:
1. **Adoption & Acquisition:** Overcoming specific barriers among non-users ($n=376$).
2. **Reactivation:** Re-engaging lapsed users who previously ordered but currently report no orders ($n=80$).
3. **Non-Discount Retention:** Designing targeted value propositions (delivery reliability, assortment depth, product quality) that preserve active customer retention ($n=807$) even when promotional discounts and coupons are scaled back.

*(Note: These represent intended applications and hypotheses to test, not results that have already been established).*

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
| **Current Active Users** | `Ever Ordered == 1` AND `Order Frequency > 1` | 807 | 63.9% | Active shoppers. QA 47 substantive (1–5 scale: Definitely no to Definitely yes). QA 48 holds binary indicator `Reason Not Applicable Current User == 1`. QA 46 & 49 substantive. |
| **Total Sample** | Full workbook manifest | **1,263** | **100.0%** | **Physical nulls = 0; duplicate rows = 0.** |

### Mandatory Questionnaire Semantics
- **QA 46 (Next 3 Month Use):** Measures stated future-use intention across all 1,263 respondents (1 = Definitely will not, 5 = Definitely will).
- **QA 47 (Continue If Discounts Reduced):** Evaluates post-promotional resilience strictly among the 807 current active users (1 = Definitely no, 5 = Definitely yes). Code 6 is an explicit questionnaire routing code ("Not Applicable") for the 456 non-current users; it must **never** be coded as churn or negative sentiment.
- **QA 48 (Reasons for Non-Use):** Multi-response binary flags for non-current users ($n=456$), analyzed with never-users ($n=376$) and previous users ($n=80$) distinguished.
- **QA 49 (Preferred Improvement):** Substantive single-choice preference across all 1,263 respondents (1–10 scale).
- **QA 24 (Physical Store Preferences):** Substantive across all 1,263 respondents (no N/A option in codebook).
- **QA 26 (Monthly Spend):** Code 1 represents substantive ₹0 spend, not missing data.
- **QA 43 (Shopping Routine Role):** Code 6 represents substantive "I do not use quick commerce", not missing data.

---

## 4. Repository Structure

```text
Beyond_Discounts/
├── README.md                                 # Canonical project overview, research question & reproduction guide
├── data/
│   ├── README.md                             # Dataset provenance, dictionary notes, and security controls
│   └── raw/survey/                           # Raw survey files (excluded from Git tracking)
│       ├── Data.xlsx                         # Survey microdata (1,263 rows x 130 columns)
│       ├── Code Book.docx                    # Questionnaire codebook and coding manual
│       └── Questionairre.docx                # Full survey questionnaire instrument
├── docs/
│   ├── data/
│   │   └── DATA_SOURCE_REGISTER.csv          # Register of evaluated data sources and provenance audits
│   └── gates/
│       ├── GATE_0_DECISION_LOG.md            # Formal decision record for Gate 0 closure & Gate 1 launch
│       ├── GATE_0_SURVEY_CANDIDATE_AUDIT.md  # Comprehensive technical audit of the survey dataset
│       └── GATE_0_SURVEY_AUDIT_SUMMARY.json  # Machine-readable audit summary artifact
├── reports/
│   └── eda/
│       ├── EDA_REPORT.md                     # Comprehensive Gate 1A exploratory data analysis report
│       ├── ANALYSIS_PLAN.md                  # Methodological analysis plan and hypothesis roadmap
│       ├── VARIABLE_REGISTER.md              # Question and variable register with coding rules
│       ├── figures/                          # Publication-quality PNG visualizations (8 figures)
│       └── tables/                           # Aggregate-only analytical CSV tables (11 tables)
├── scripts/
│   ├── audit_survey_data.py                  # Gate 0 schema and questionnaire routing validation script
│   └── run_eda.py                            # Gate 1A reproducible EDA pipeline and export script
└── tests/
    ├── test_audit_survey_data.py             # Unit tests for survey schema, routing, and error conditions
    └── test_eda.py                           # Automated tests for EDA derivations, tables, and denominators
```

---

## 5. Reproduction & Execution Guide

### Prerequisites
- Python 3.10+ (tested on Python 3.13)
- Required packages: `pandas`, `openpyxl`, `numpy`, `matplotlib`, `seaborn`, `scipy`

Install dependencies:
```bash
pip install pandas openpyxl numpy matplotlib seaborn scipy
```

### Run Survey Data Audit (Gate 0 Verification)
```bash
python scripts/audit_survey_data.py --file data/raw/survey/Data.xlsx --sheet Data --output docs/gates/GATE_0_SURVEY_AUDIT_SUMMARY.json
```

### Run Exploratory Data Analysis Pipeline (Gate 1A)
```bash
python scripts/run_eda.py --file data/raw/survey/Data.xlsx --sheet Data
```

### Run Automated Test Suite
```bash
python -m unittest discover tests
```

---

## 6. Project Governance & Working Rules

1. **Role of Implementation Worker:** Code implementation, automated verification, reproducible documentation, and evidence generation.
2. **Role of Principal Project Lead:** Analytical authority, methodological decisions, and gate approvals. Code execution alone does not constitute gate approval.
3. **Privacy & Data Security:** No raw survey rows, individual respondent answers, or personally identifiable information are committed to version control. All committed outputs are aggregate statistical summaries.
