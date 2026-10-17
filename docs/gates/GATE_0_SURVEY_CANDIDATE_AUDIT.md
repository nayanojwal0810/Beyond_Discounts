# GATE 0 CANDIDATE DATASET AUDIT: MENDELEY QUICK-COMMERCE SURVEY (CHANDRA 2026)

**Document Type:** Formal Candidate Dataset Verification, Routing Audit & Project-Direction Lock  
**Target Dataset:** *A Large-Scale Survey Dataset on Quick-Commerce Adoption, Ordering Patterns, Product Categories and Spending Behaviour among Indian Consumers*  
**Primary Source:** Mendeley Data (`cw88nb7822/1`, DOI: `10.17632/cw88nb7822.1`, published 14 Oct 2026)  
**Approved Working Direction:** *Beyond Discounts: Data-Driven Customer Segmentation and Retention Strategy for Indian Quick Commerce — A Blinkit Case Application*  
**Central Research Question:** *Which customer segments differ in their stated willingness to continue using quick commerce when discounts are reduced, and what retention or reactivation interventions should a platform prioritise for each segment?*  
**Assigned Role:** Implementation Engineer (operating under the Principal Project Lead)  
**Audit Completion Date:** 2026-10-17  
**Status:** **CONDITIONALLY APPROVED BY PRINCIPAL PROJECT LEAD (FINAL AUDIT LOCK)**  

---

## 1. Executive Assessment & Approved Scope Boundaries

The Principal Project Lead has conditionally approved the Mendeley quick-commerce survey workbook as a candidate for exploratory CRM analysis, subject to documented provenance boundaries, questionnaire routing corrections, and strict scope limits.

### Core Approved Working Direction
- **Approved Project Title:** *Beyond Discounts: Data-Driven Customer Segmentation and Retention Strategy for Indian Quick Commerce — A Blinkit Case Application*
- **Central Question:** Which customer segments differ in their stated willingness to continue using quick commerce when discounts are reduced, and what retention or reactivation interventions should a platform prioritise for each segment?
- **Focal Platform:** Blinkit serves as the primary focal application context for translating findings into actionable CRM retention strategies.

### Binding Scope Boundaries
1. **Blinkit is the Focal Business Application:** Strategic implications and playbooks are tailored for Blinkit's operational model.
2. **Category-Level Behaviour (No Platform-Specific Satisfaction):** The survey captures platform awareness and historical usage (QA 11, 12), but all service satisfaction (QA 37–40), operational complaints (QA 36), discount habits (QA 28, 29), and choice factors (QA 31, 32) are measured strictly at the general quick-commerce category level. The project must **not** claim platform-specific satisfaction benchmarks for Blinkit.
3. **Exploratory Survey (Not Representative National Census):** The achieved sample of 1,263 respondents reflects an exploratory non-probability sample. Large sample size does not confer national demographic representativeness.
4. **Stated Intention vs. Observed Behaviour:** Stated likelihood of future use (QA 46) and willingness to continue if discounts are reduced (QA 47) represent stated customer perceptions, **not** observed repeat purchases, actual customer retention, or proven transactional churn.
5. **Absent Transactional CRM Outcomes:** No customer transaction logs, actual customer churn, cohort retention tables, customer lifetime value (CLV), or causal retention uplift data exist in this cross-sectional survey.
6. **App-Review Corpus Superseded as Primary:** The earlier scraped app-review corpus (Candidate A) is not the primary dataset; its upstream scraping provenance and rights to redistribute raw review text remain unresolved.
7. **Strict Gate 0 Boundary:** Execution is strictly limited to data verification, routing reconciliation, and baseline schema locking. Exploratory segmentation modeling, predictive analytics, and dashboard implementation will not begin until Gate 1 is formally opened.

---

## 2. File Verification & Physical Inventory

The candidate bundle (`A Large-Scale Survey Dataset on Quick-Commerce Ado.zip`) was located, preserved, and extracted into the local repository directory `data/raw/survey/`. All raw respondent-level data files, workbooks, and document files remain strictly excluded from version control via `.gitignore`.

| File Artifact | File Type | Byte Size | SHA-256 Checksum | Git Tracking Status |
| :--- | :--- | :---: | :--- | :--- |
| `A Large-Scale Survey Dataset on Quick-Commerce Ado.zip` | ZIP Archive | 459,941 bytes | `c0ea677124407f634b0b61294cf5814f353649cb7777cbc56d37b4fdb67d8875` | Excluded (`*.zip`) |
| `data/raw/survey/Data.xlsx` | Excel Workbook | 565,344 bytes | `c6e92099b960f11472558b629e90b2926012061eac45b9051973c8fe79e1a73d` | Excluded (`*.xlsx`, `data/raw/*`) |
| `data/raw/survey/Code Book.docx` | Codebook | 27,666 bytes | `7c7692b730b5852ee18747b620734b5ada35b9e1a856854118c5a4e017895a23` | Excluded (`*.docx`, `data/raw/*`) |
| `data/raw/survey/Questionairre.docx` | Questionnaire | 26,137 bytes | `e5bfe1b1195e1e8c54ff62fe073165657cb1d5288f38a132329024e59b815665` | Excluded (`*.docx`, `data/raw/*`) |

---

## 3. Academic Provenance & Methodological Audit

An audit of the public repository record ([Mendeley Data `cw88nb7822/1`](https://data.mendeley.com/datasets/cw88nb7822/1)) and associated institutional materials was conducted:

| Provenance Dimension | Findings from Public Record & Bundle Documents | Classification Status |
| :--- | :--- | :--- |
| **Author & Affiliation** | Contributor is Dr. Ashish Chandra, Assistant Professor, Amity Business School, Amity University Uttar Pradesh, Lucknow Campus, India. Corroborated by official faculty profile. | **VERIFIED** |
| **DOI & Repository Record** | Published on Mendeley Data with DOI `10.17632/cw88nb7822.1` (Version 1, 14 October 2026). No associated peer-reviewed journal article, preprint, or working paper is cited or indexed. | **PARTIALLY VERIFIED** |
| **Declared Licence** | Creative Commons Attribution 4.0 International (**CC BY 4.0**). Academic analysis permitted with proper attribution. Raw respondent rows withheld from Git. | **VERIFIED** |
| **Target Population & Sampling Frame** | Target population described in preamble as Indian urban/semi-urban smartphone users. However, **no defined sampling frame, geographic sampling quotas, or city breakdown** is documented. | **UNVERIFIED** |
| **Sampling & Recruitment Channel** | Undocumented and unverified in the public repository record. Recruitment channels (e.g., whether student pools, social media, commercial panels, or other mechanisms) are unrecorded. | **UNVERIFIED** |
| **Fieldwork Dates & Mode** | Digital survey via Google Forms implied. However, the workbook contains **no respondent ID, no submission timestamp, and no fieldwork date field**. Fieldwork timing is unverified. | **UNRESOLVED / ABSENT** |
| **Consent & Ethical Review (IRB)** | Preamble contains standard voluntary consent language (*"participation is entirely voluntary..."*), but **no formal IRB protocol or ethical clearance number** is provided. | **UNVERIFIED** |
| **Data Cleaning & Exclusion Protocol** | Zero blank cells across 164,190 cells indicates forced-choice form validation. No screening log, completion dropoff rate, speeder filter, or straight-liner exclusions are recorded. | **UNRESOLVED** |

*Methodological Determination:* The absence of timestamps and sampling frame documentation does not imply data fabrication; it means sample authenticity and representativeness cannot be independently established from available artifacts. National representativeness is therefore formally disclaimed.

---

## 4. Structural Integrity & Multi-Tier Completeness Audit

### 4.1 Structural Dimensions
- **Worksheet Name:** Single worksheet named `Data`.
- **Dimensions:** Exactly **1,263 data rows $\times$ 130 columns** (matching codebook specifications).
- **Full Duplicate Rows:** **0 full duplicate rows**.
- **Demographic Duplication:** 5 pairs of rows share identical demographic profiles (QA 1–8), normal for discrete categorical demographic questions across 1,263 respondents.
- **Header Whitespace Flaws:** 5 column headers contain leading or trailing spaces (`' First Trial Reason'`, `' Order Frequency'`, `' Factor Low Delivery Fee'`, `'Fast Delivery Importance '`, `' Problem No Major Problem'`). Sanitized by `.strip()` in reproducible code.

### 4.2 Multi-Tier Completeness vs. Missingness Breakdown
The dataset exhibits zero physical null cells. However, physical completeness must be rigorously distinguished from substantive information availability:

```
Total Workbook Cells: 164,190 (1,263 rows x 130 columns)
├── Physical Blank/Null Cells: 0 (100.0% physical data presence)
└── Information Completeness:
    ├── Substantive Observed Responses (valid empirical measurement)
    └── Explicit Not-Applicable / Skip-Coded Responses (questionnaire routing)
```

| Information Tier | Definition & Analytical Significance | Observed Count in Survey Data |
| :--- | :--- | :--- |
| **Physical Blank / Null Cells** | Missing cell coordinates (`pd.isna()`). | **0 cells** across all 164,190 coordinates. |
| **Explicit Not-Applicable (N/A) Codes** | Dedicated numerical codes (e.g., Code 6, 7, 8, or 9) assigned when a question is logically inapplicable to the respondent. | - **QA 16–45 Source-Defined N/A Questions:** 456 non-current respondents across applicable questions (QA 24, QA 26, QA 43 remain substantive).<br/>- **QA 37–40 Satisfaction (Code 6):** 456 respondents.<br/>- **QA 47 Discount Reduction (Code 6):** 456 respondents.<br/>- **QA 48 Current-User Skip Flag (Code 1):** 807 respondents.<br/>- **Category / Problem N/A Dummies (Code 1):** 456 respondents. |
| **Substantive Observed Responses** | Meaningful self-reported measures within legitimate codebook ranges. | - **Demographics (QA 1–8):** 1,263 respondents.<br/>- **Platform Awareness & Usage (QA 11, 12):** 1,263 respondents.<br/>- **Physical-Store Category Preferences (QA 24):** 1,263 respondents (not skip-coded).<br/>- **QA 26 Monthly Spend ₹0 (Code 1):** 456 non-current respondents.<br/>- **QA 43 Shopping Routine Non-Use (Code 6):** 456 non-current respondents.<br/>- **QA 46 Stated Future Intention:** **1,263 respondents (100%)**.<br/>- **QA 47 Discount Reduction Continuation:** **807 current users**.<br/>- **QA 48 Non-Use Reasons:** **456 non-current users**.<br/>- **QA 49 Preferred Improvement:** **1,263 respondents (100%)**. |

*Critical Principle:* A workbook can have zero physical nulls while lacking substantive information on specific variables. The satisfaction and operational problem fields for the 456 non-current respondents are **not fully observed**; they are skip-coded.

---

## 5. Questionnaire Routing Reconciliation & The 80-Record Subgroup

### 5.1 Subgroup Triangulation
Cross-tabulating **QA 10** (*Ever Ordered through Quick Commerce*) against **QA 15** (*Current Order Frequency*) resolves the sample into three mutually exclusive subgroups:

$$\begin{aligned}
\text{Total Survey Respondents} &: \mathbf{1,263} \\
\text{Ever Ordered = Yes (QA 10 = 1)} &: 887\ (70.23\%) \\
\text{Ever Ordered = No (QA 10 = 0)} &: 376\ (29.77\%) \\
\text{Current Order Frequency = Never (QA 15 = 1)} &: 456\ (36.10\%) \\
\text{Current Order Frequency = Active (QA 15 } \ge \text{2)} &: 807\ (63.90\%)
\end{aligned}$$

| Triangulated Respondent Subgroup | QA 10 (Ever) | QA 15 (Frequency) | Count ($n$) | % of Total Sample |
| :--- | :---: | :---: | :---: | :---: |
| **1. Never Users** | `0` (No) | `1` (Never) | **376** | 29.77% |
| **2. Previous Users (Reporting No Current Orders)** | `1` (Yes) | `1` (Never) | **80** | **6.33%** |
| **3. Current Active Users** | `1` (Yes) | `2..7` (Active) | **807** | 63.90% |
| *Inconsistent Routing (Ever=0, Frequency>1)* | `0` (No) | `2..7` (Active) | **0** | 0.00% |

### 5.2 Corrected Questionnaire Routing Map

The questionnaire routing operates across four distinct modular blocks:

```
[All 1,263 Respondents]
       │
       ├── QA 1-8: Demographics (n=1,263 substantive)
       ├── QA 9-11: Awareness & Platforms (n=1,263 substantive)
       └── QA 10: Ever Ordered?
             ├── Ever = No (n=376) ──> QA 15 = 1 (Never)
             └── Ever = Yes (n=887) ──> QA 12-14: Usage History & Platforms
                                           │
       ┌───────────────────────────────────┴───────────────────────────────────┐
       ▼                                                                       ▼
[QA 15 == 1: Never (n=456)]                                         [QA 15 >= 2: Active (n=807)]
(376 Never Users + 80 Previous Users)                                          │
       │                                                                       ├── QA 16-45: Orders, Categories,
       ├── QA 16-23, 25, 27-36, 41-42, 44-45: Source-Defined N/A Codes        │   Problems & Satisfaction
       │   - Historical satisfaction (QA 37-40) & problems (QA 36) unobserved  │   (n=807 substantive)
       ├── QA 24: Physical-Store Preferences (Substantive for all 456)         │
       ├── QA 26: Monthly Spend = ₹0 (Code 1 substantive zero spend)           │
       ├── QA 43: Shopping Routine = "Do not use" (Code 6 substantive non-use) │
       │                                                                       │
       ├── QA 46: Stated Future Intention (n=456 substantive 1-5)              ├── QA 46: Stated Future Intention (n=807 substantive 1-5)
       │                                                                       │
       ├── QA 47: NOT APPLICABLE (Code 6 for all 456)                          ├── QA 47: Continue if Discounts Reduced? (n=807 substantive 1-5)
       │   * Prohibited: Do NOT treat as unwillingness to continue!            │
       │                                                                       ├── QA 48: Reason Not Applicable Current User = 1 (n=807)
       ├── QA 48: Reasons for Not Using (n=456 substantive)                    │
       │   (Available for lapsed-user & non-user analysis)                     │
       │                                                                       │
       └── QA 49: Improvement Most Likely to Increase Use                      └── QA 49: Improvement Most Likely to Increase Use
           (n=456 substantive)                                                     (n=807 substantive)
```

### 5.3 Detailed Module Analysis & Routing Rules

#### Module A: QA 16–QA 45 (Order Patterns, Spending, Problems, Satisfaction)
- **Non-Current Users ($n=456$):** Respondents whose current order frequency is "Never" (376 never-users + 80 previous users). The source Code Book establishes distinct response semantics across these questions:
  - **Explicit Source-Defined N/A / Skip Codes:** Single-select questions (QA 16, 17, 19, 20, 21, 23, 25, 27–30, 32–35, 37–40, 41, 42, 44, 45) and multi-select N/A indicator dummies (QA 18 `Reason Not Applicable` = 1, QA 22 `Category Not Applicable` = 1, QA 36 `Problem Not Applicable` = 1; substantive options = 0; QA 31 factor dummies = 0) hold explicit codebook N/A values.
  - **Substantive Zero-Spend & Non-Use Responses:**
    - QA 26 (`Monthly Spend`): Code 1 explicitly means **₹0 monthly quick-commerce spend** in the Code Book, not N/A. All 456 non-current users substantive report ₹0 monthly spend.
    - QA 43 (`Shopping Routine Role`): Code 6 explicitly means **"I do not use quick commerce"**, a substantive non-use response rather than N/A. All 456 non-current users report this non-use routine role.
  - **Physical-Store Category Preferences (QA 24):** QA 24 has **no "not applicable – never used" option** in the Code Book and must **not** be blanket-classified as skip-coded. All respondents (both current active users and non-current users) report physical-store shopping preferences. Physical-store preference indicators are substantive across the sample and must not be required to be zero for non-current respondents.
- **Impact on the 80 Previous Users:** Historical service satisfaction scores (QA 37–40) and operational problem histories (QA 36) are unobserved for previous users because the questionnaire routed them to Code 6 (*"Not applicable – never used"*). **Do not impute this history.**

#### Module B: QA 46 (Stated Future-Use Intention)
- **Question:** *"How likely are you to use quick-commerce services in the next three months?"*
- **Observed Distribution ($N=1,263$):** Contains substantive Likert values 1–5 for **all 1,263 respondents**:
  - *Never Users ($n=376$):* 1: 114 | 2: 107 | 3: 79 | 4: 50 | 5: 26 (Mean = 2.38)
  - *Previous Users ($n=80$):* 1: 15 | 2: 24 | 3: 20 | 4: 19 | 5: 2 (Mean = 2.61)
  - *Current Users ($n=807$):* 1: 41 | 2: 92 | 3: 159 | 4: 281 | 5: 234 (Mean = 3.71)
- **Methodological Rule:** Report QA 46 as **stated future-use intention**. It is not observed repeat purchase, actual retention, or a proven churn outcome.

#### Module C: QA 47 (Willingness to Continue if Discounts are Reduced)
- **Question:** *"If discounts, coupons and promotional offers are significantly reduced or removed, how likely are you to continue using quick-commerce services?"*
- **Observed Distribution ($N=1,263$):**
  - *Current Users ($n=807$):* Substantive values 1–5 (1: 52 | 2: 121 | 3: 217 | 4: 250 | 5: 167; Mean = 3.44).
  - *Non-Current Users ($n=456$):* Exactly **456 respondents have Code 6 (Not applicable)**.
- **Strict Analytical Rule:** Analyse QA 47 **ONLY among respondents with substantive responses ($n=807$)**. Do **NOT** interpret Code 6 as defection, churn, or unwillingness to continue; it indicates that non-current users do not have current ordering to continue.

#### Module D: QA 48–QA 49 (Reasons for Non-Use & Preferred Improvements)
- **Substantive Availability:** Substantively recorded for all 456 non-current users.
- **Top Non-Use Reasons for Previous Users ($n=80$):** Prefer physical shopping (41.2%), prices higher than local stores (38.8%), prefer inspecting items (35.0%), no need for rapid delivery (28.7%), high delivery fees (27.5%), service unavailable (27.5%), distrust product freshness (25.0%).
- **Top Preferred Improvements for Previous Users ($n=80$):** Lower prices / transparent charges (41.2%), expanded delivery coverage (32.5%), better fresh produce quality (31.2%).
- **Analytical Application:** Use these fields for exploratory lapsed-user reactivation and never-user acquisition strategy, preserving the distinction between previous users and people who have never used quick commerce.
- **Terminology Rule:** Do **not** label the 80 previous users as "confirmed churn events". Use wording such as **"previous users currently reporting no orders"**.

---

## 6. Available vs. Unavailable CRM Outcome Measures

| Analytical Dimension | Available Measures in Survey Dataset | Strictly Unavailable / Unobserved Outcomes |
| :--- | :--- | :--- |
| **Customer Retention & Churn** | Stated future usage intention in next 3 months (QA 46); stated willingness to continue under discount reduction (QA 47); reasons for not currently ordering (QA 48). | **Actual transactional customer defection / churn logs; observed longitudinal repeat purchases; cohort retention curves.** |
| **Discount Dependence** | Self-reported discount-induced overspending frequency (QA 28); threshold extra item additions (QA 29); price vs. speed choice factor (QA 31, 32); post-discount continuation (QA 47). | **Transaction-level price elasticity; customer gross margin; coupon redemption transaction history; wallet-share data.** |
| **Customer Segmentation** | Demographics (QA 1–8); ordering frequency (QA 15); basket item count (QA 19); monthly spend tier (QA 26); category mix (QA 22, 23); impulse propensity (QA 21, 44). | **Customer Lifetime Value (CLV); behavioral RFM (Recency, Frequency, Monetary) metrics from real store transaction logs.** |
| **Platform Performance** | Binary awareness (QA 11) and historical usage footprint (QA 12) across Blinkit, Zepto, Instamart, BigBasket, Flipkart, Amazon. | **Platform-specific satisfaction; platform-specific service failure rates; brand-specific NPS or customer perceived equity.** |
| **Retention Uplift** | Desired improvement priorities (QA 49); service choice factors (QA 31, 32). | **Empirical causal retention uplift from CRM interventions; measured pre/post A/B test results.** |

---

## 7. Strict Prohibitions on Analytical Claims

To protect academic credibility and scientific integrity, the following practices are **STRICTLY PROHIBITED**:

1. **PROHIBITED:** Treating generic satisfaction measures (QA 37–40) or problem rates (QA 36) as Blinkit-specific results.
2. **PROHIBITED:** Treating platform-awareness or ever-used indicators (QA 11, 12) as proof of current platform-specific ordering or market share.
3. **PROHIBITED:** Treating stated future-use intention (QA 46) or post-discount continuation (QA 47) as observed repeat purchase or transactional retention.
4. **PROHIBITED:** Treating QA 47 Not-Applicable codes (Code 6, $n=456$) as negative responses, churn, or unwillingness to continue.
5. **PROHIBITED:** Treating the 80 previous users who currently report no orders as confirmed transactional churn events.
6. **PROHIBITED:** Claiming national demographic representativeness based on sample size ($N=1,263$) alone.
7. **PROHIBITED:** Claiming causal retention uplift from cross-sectional survey responses.

---

## 8. Reproducible Verification Tooling & Deliverables

1. **Audit Script ([`scripts/audit_survey_data.py`](file:///e:/FDA/Beyond_Discounts/scripts/audit_survey_data.py)):**
   - Implements full 130-column normalized schema manifest verification (`EXPECTED_COLUMN_MANIFEST_130`), detecting missing, unexpected, or replaced columns even when total column count remains 130.
   - Enforces strict QA 47 routing: 807 current users strictly in $\{1..5\}$, 456 non-current users strictly Code 6; violations trigger status `FAILED` and exit code 1.
   - Enforces QA 16–QA 45 routing against source codebook rules: verifies explicit source-defined N/A codes, substantive zero-spend (QA 26 = ₹0), substantive non-use routine (QA 43 = "I do not use quick commerce"), and preserves QA 24 physical-store preferences as not skip-coded.
   - Enforces universal substantive coverage for QA 46 (1–5) and QA 49 (1–10) across all 1,263 respondents.
   - Fully supports `--sheet` argument pass-through to `pd.read_excel`.
   - Returns exit code 1 on blocking schema, routing, dimension, or code violations.
2. **Test Suite ([`tests/test_audit_survey_data.py`](file:///e:/FDA/Beyond_Discounts/tests/test_audit_survey_data.py)):**
   - 25 automated unit tests repository-wide (15 in `test_audit_survey_data.py`), executing cleanly (`Ran 25 tests, OK`).
   - Validates missing mandatory columns, duplicate normalized headers, full 130-column manifest column replacement regression, sheet arguments, null vs N/A handling, subgroup derivation, and exit codes.
   - Features comprehensive negative tests for QA 47 routing violations, QA 16–45 routing/skip violations (satisfaction, categories, problems, spend, shopping routine, skip flags), and QA 46/49 coverage violations using synthetic fixtures.
3. **Machine-Readable Summary ([`docs/gates/GATE_0_SURVEY_AUDIT_SUMMARY.json`](file:///e:/FDA/Beyond_Discounts/docs/gates/GATE_0_SURVEY_AUDIT_SUMMARY.json)):**
   - Aggregate audit findings including source hashes, dimensions, subgroup counts, questionnaire routing metrics, and platform usage footprints (zero row-level PII).

---

## 9. Final Gate 0 Recommendation Submitted to the Principal Project Lead

The Implementation Engineer submits this completed verification and routing audit to the Principal Project Lead with the following recommendation:

- **Recommended Gate 0 Disposition:** **CLOSE GATE 0 (ACCEPT WITH DOCUMENTED CONDITIONAL SCOPE)**
- **Approved Project Scope:** *Beyond Discounts: Data-Driven Customer Segmentation and Retention Strategy for Indian Quick Commerce — A Blinkit Case Application*.
- **Next Phase Authorization:** With Gate 0 data verification, routing reconciliation, and schema locking complete, the project is technically prepared to proceed to **Gate 1 (Exploratory Data Analysis, Feature Engineering, and Consumer Segmentation Modeling)** upon formal direction from the Principal Project Lead.
