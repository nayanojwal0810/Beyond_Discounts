# Quick-Commerce Data Registry & Ingestion Guide

This document defines the data assets evaluated and governed during **Gate 0**, data access and local storage conventions, licensing and provenance boundaries, schema definitions, and instructions for reproducing all quantitative audit pipelines.

---

## 1. Approved Project Direction & Scope Status

Under the controlling decisions of the Principal Project Lead:
- **Approved Working Title:** *Beyond Discounts: Customer Segmentation and Retention Strategy for Indian Quick Commerce*
- **Current Research Question:** *Which lifecycle-based CRM actions are best supported by the observed sample's stated future-use intentions, discount-reduction continuation intentions, non-use barriers, and preferred service improvements? Do exploratory behavioral clusters add actionable differentiation beyond lifecycle cohorts?*
- **Problem Investigated:** Quick-commerce consumers may differ in the importance they place on discounts, shopping convenience, spending behaviour, service experience, and other factors. A single retention strategy may not suit every consumer. We investigate these differences using the survey data and determine whether defensible, interpretable customer segments can be developed.
- **Proposed Business Value:** The eventual project should translate observed customer differences into evidence-based recommendations for customer acquisition, reactivation, and retention (intended applications, not established results).
- **Scope:** General Indian Quick-Commerce Industry. (Earlier framing applied to Blinkit as a focal case has been formally superseded because the survey measures general quick-commerce behaviour, not firm-specific satisfaction or retention).
- **Primary Exploratory Dataset:** The Mendeley Quick-Commerce Survey Dataset (`cw88nb7822/1`, Chandra 2026). Conditionally approved under Gate 0 lock.
- **Superseded Dataset:** The customer app-review corpus (Candidate A, 4,290 common-window records) is formally **superseded for primary analysis** due to unresolved upstream data-rights and scraping provenance, but is retained as a secondary qualitative reference for complaint themes and service recovery taxonomies.

---

## 2. Primary Exploratory Dataset: Mendeley Survey Microdata

**Interpretation guardrail:** This is an exploratory, cross-sectional secondary-data analysis. The source's actual recruitment process, fieldwork dates, and sampling frame are not verified in the available source materials; the sample is not claimed to be nationally representative. QA46/QA47 are stated intentions, QA48 is a stated current non-use reason, and QA49 is a single stated preferred improvement. None is an observed transaction outcome or causal intervention effect.

### 2.1 Asset Identification & Provenance
- **Title:** *A Large-Scale Survey Dataset on Quick-Commerce Adoption, Ordering Patterns, Product Categories and Spending Behaviour among Indian Consumers*
- **Depositor:** Dr. Ashish Chandra (Amity Business School, Amity University, Lucknow)
- **Repository:** Mendeley Data (DOI: `10.17632/cw88nb7822.1`, published 14 October 2026)
- **Declared Licence:** Creative Commons Attribution 4.0 International (**CC BY 4.0**)
- **Local Storage:** `data/raw/survey/Data.xlsx` (Worksheet: `Data`) accompanied by `Code Book.docx` and `Questionairre.docx`
- **File Integrity:** 565,344 bytes; SHA-256: `c6e92099b960f11472558b629e90b2926012061eac45b9051973c8fe79e1a73d`
- **Dimensions:** Exactly **1,263 data rows $\times$ 130 columns**; 0 physical null/blank cells; 0 full duplicate rows.

### 2.2 Subgroup Derivation & Questionnaire Routing Architecture
The survey contains 1,263 respondents partitioned into three questionnaire-defined lifecycle cohorts via QA 10 (*Ever Ordered*) and QA 15 (*Current Order Frequency*):
1. **Never Users ($n=376$, 29.8%):** `Ever Ordered = 0`, `Order Frequency = 1 (Never)`.
2. **Previous Users Currently Reporting No Orders ($n=80$, 6.3%):** `Ever Ordered = 1`, `Order Frequency = 1 (Never)`.
3. **Current-User Cohort ($n=807$, 63.9%):** `Ever Ordered = 1`, `Order Frequency > 1 (not coded 'Never')`.

#### Module Classifications & Variable Availability:
- **QA 16–QA 45 Response Classifications for Non-Current Respondents ($n=456$):**
  - *Explicit Source-Defined N/A Codes:* Single-select variables (QA 16, 17, 19, 20, 21, 23, 25, 27–30, 32–35, 37–40, 41, 42, 44, 45) and multi-select N/A indicators (QA 18, 22, 36) hold codebook-defined N/A values.
  - *Substantive Zero-Spend & Non-Use Responses:* QA 26 (`Monthly Spend`) Code 1 represents substantive **₹0 monthly spend**, not N/A. QA 43 (`Shopping Routine Role`) Code 6 represents **"I do not use quick commerce"**, a substantive non-use response rather than N/A.
  - *Physical-Store Preferences (QA 24):* QA 24 has **no N/A option** in the Code Book and is **not skip-coded**. Physical-store category preferences are substantively indicated across both current and non-current respondents.
  - *Previous-User Satisfaction Blindspot:* For the 80 previous users, historical service satisfaction (QA 37–40) and experienced problems (QA 36) are unobserved (coded 6).
- **QA 46 (Stated Future-Use Intention):** Substantive Likert values 1–5 recorded across **all 1,263 respondents**.
- **QA 47 (Willingness to Continue if Discounts Reduced):** Substantive values 1–5 for the **807 current users**; Code 6 (*Not applicable*) for all **456 non-current users**. Code 6 is explicit routing N/A, not churn or defection.
- **QA 48 (Non-Use Reasons):** Recorded for all 456 non-current users (376 never + 80 previous); current users hold skip flag `Reason Not Applicable Current User = 1`.
- **QA 49 (Preferred Improvements):** Substantive choices 1–10 across **all 1,263 respondents**.
- **Platform Footprint (QA 12):** Blinkit 577 users (45.7% total / 65.1% of ever-users), Zepto 439 users (34.8% total / 49.5% of ever-users).

### 2.3 Strict Sampling & Provenance Limitations
To maintain academic credibility, the following empirical limitations are permanently documented:
1. **Undocumented Sampling Design:** The sampling frame, recruitment channels, fieldwork methodology, and administration dates are undocumented and unverified in the source dataset.
2. **Representativeness Disclaimed:** National demographic or geographic representativeness is **not established**. The dataset represents an exploratory cross-sectional sample.
3. **Category-Level Scope:** The questionnaire measures general quick-commerce industry behavior; it does not measure Blinkit-specific satisfaction, Net Promoter Scores, or firm-level service failure rates.
4. **Absence of Transactional CRM Outcomes:** There is **no transactional churn, longitudinal repeat-purchase history, customer lifetime value (CLV), or causal intervention-uplift data**. Stated intentions (QA 46/47) are proxy perceptions, not observed behaviors.

---

## 3. Superseded Secondary Dataset: App-Review Corpus (Candidate A)

### 3.1 Status & Purpose
The public customer review corpus (`mdaniq45/E-Commerce-BlinkIt-vs-Zepto-vs-JioMart-Reviews-Analysia`) is **superseded as the primary dataset** for quantitative segmentation. It is retained strictly as a secondary qualitative and contextual reference for:
- Developing complaint taxonomies and service failure classifications.
- Analyzing expressed switching intentions and customer pain points.

### 3.2 Provenance & Rights Warnings
- **Software Licence vs Data Rights:** Upstream repository provides Apache-2.0 for code; underlying third-party review text is unlicenced. Legal reuse rights remain **unresolved** (no legal guarantee).
- **Collection Provenance:** Scraping scripts, parameters, and filters are unverified.
- **Extreme Negativity Bias:** Over 70% of reviews are 1-star ratings, reflecting voluntary response bias rather than representative customer sentiment.
- **Common Date Window:** 14 August 2024 to 31 December 2024 (inclusive), yielding **4,290 usable records** (Blinkit: 1,376; Zepto: 1,740; JioMart: 1,174).

---

## 4. Local Storage Convention & Version Control Policy

- **Local Storage Path:**
  - Survey Microdata: `data/raw/survey/Data.xlsx`, `Code Book.docx`, `Questionairre.docx`
  - Review Corpus: `data/raw/reviews.csv`
- **Git Tracking Rules:**
  - `data/raw/*` is strictly excluded from version control via `.gitignore`.
  - Raw respondent-level survey rows, Excel workbooks, Word codebooks, and customer review texts must **never** be committed to Git.
  - Only machine-readable aggregate audit summaries (`docs/gates/GATE_0_SURVEY_AUDIT_SUMMARY.json`, `docs/gates/GATE_0_AUDIT_SUMMARY.json`) and analytical reports are version-controlled.

---

## 5. Historical Audit Artifacts Preserved

To ensure full auditability across Gate 0 iterations, historical audit artifacts are permanently preserved:
- [`docs/gates/GATE_0_AUDIT_SUMMARY.json`](file:///e:/FDA/Beyond_Discounts/docs/gates/GATE_0_AUDIT_SUMMARY.json): Machine-readable audit summary of the 4,290 usable review records.
- [`docs/gates/GATE_0_FEASIBILITY_REPORT.md`](file:///e:/FDA/Beyond_Discounts/docs/gates/GATE_0_FEASIBILITY_REPORT.md): Initial Gate 0 feasibility evaluation of review candidates.
- [`docs/gates/GATE_0_DECISION_LOG.md`](file:///e:/FDA/Beyond_Discounts/docs/gates/GATE_0_DECISION_LOG.md): Binding decisions of the Principal Project Lead locking project direction.
- [`docs/gates/GATE_0_SURVEY_CANDIDATE_AUDIT.md`](file:///e:/FDA/Beyond_Discounts/docs/gates/GATE_0_SURVEY_CANDIDATE_AUDIT.md): Comprehensive quantitative audit of the candidate survey dataset.
- [`docs/gates/GATE_0_SURVEY_AUDIT_SUMMARY.json`](file:///e:/FDA/Beyond_Discounts/docs/gates/GATE_0_SURVEY_AUDIT_SUMMARY.json): Machine-readable aggregate summary of the 1,263 survey responses.

---

## 6. Reproducing the Quantitative Audits

### 6.1 Prerequisites
- Python 3.10+
- `pandas`, `openpyxl`, `numpy`

### 6.2 Executing the Survey Audit (Primary Dataset)
```bash
python scripts/audit_survey_data.py --file data/raw/survey/Data.xlsx --sheet Data --output docs/gates/GATE_0_SURVEY_AUDIT_SUMMARY.json
```
- Validates 130-column schema manifest (`EXPECTED_COLUMN_MANIFEST_130`).
- Enforces strict QA 47 routing (807 current users in 1–5, 456 non-current in Code 6).
- Validates QA 16–QA 45 routing and response classifications against source codebook.
- Verifies universal coverage for QA 46 (1–5) and QA 49 (1–10).
- Exits with code 0 on clean pass (`SUCCESS_WITH_WARNINGS`), code 1 on blocking errors.

### 6.3 Executing the Review Corpus Audit (Secondary Reference)
```bash
python scripts/audit_data.py --file data/raw/reviews.csv
```
- Audits the common date window (14 Aug–31 Dec 2024), disaggregated missingness, rating distributions, and volume thresholds (>= 500 records per platform).

### 6.4 Running the Automated Test Suite
```bash
python -m unittest discover tests
```
- Executes all 25 unit tests across survey schema/routing verification and review feasibility logic.
