# GATE 0 — DECISION LOG (SURVEY VERIFICATION & PROJECT-DIRECTION LOCK)

**Canonical Approved Project Title:** *Beyond Discounts: Customer Segmentation and Retention Strategy for Indian Quick Commerce*
*(Earlier provisional framing "A Blinkit Case Application" formally superseded at Gate 1 launch to reflect general quick-commerce survey scope)*
**Original Gate 0 Research Question (superseded 17 Oct 2026):** *How do quick-commerce consumers differ in their discount sensitivity, usage behaviour, and stated future-use intentions, and what adoption, reactivation, or retention actions are supported by these differences?*
**Current Research Question:** *Which lifecycle-based CRM actions are best supported by the observed sample's stated future-use intentions, discount-reduction continuation intentions, non-use barriers, and preferred service improvements? Do exploratory behavioral clusters add actionable differentiation beyond lifecycle cohorts?*
**Current Decision:** Lifecycle-based CRM analysis is primary. Existing Gower/PAM/HAC clustering remains an exploratory benchmark only; no hard customer-persona targeting is approved.
**Problem Investigated:** Quick-commerce consumers may differ in the importance they place on discounts, shopping convenience, spending behaviour, service experience, and other factors. A single retention strategy may not suit every consumer. We investigate these differences using the survey data and determine whether defensible, interpretable customer segments can be developed.
**Proposed Business Value:** The eventual project should translate observed customer differences into evidence-based recommendations for customer acquisition, reactivation, and retention (intended applications, not established results).
**Industry Scope:** General Indian Quick-Commerce Industry (category-level; not firm-specific)
**Assigned Role:** Implementation Engineer  
**Decision Authority:** Principal Project Lead  
**Audit Completion Date:** 2026-10-17  
**Gate 0 Status:** **CONDITIONALLY APPROVED BY PRINCIPAL PROJECT LEAD (FINAL AUDIT LOCK)**  
**Recommended Disposition:** **PASS (UNDER AUTHORIZED CONDITIONAL SCOPE)**  

---

## 1. Controlling Decisions of the Principal Project Lead

The Principal Project Lead reviewed the project repository and the candidate survey bundle (`A Large-Scale Survey Dataset on Quick-Commerce Ado.zip`), establishing the following binding determinations:

1. **Approved Working Direction:** The project direction is locked as *Beyond Discounts: Customer Segmentation and Retention Strategy for Indian Quick Commerce*.
2. **Central Research Question:** Investigates how quick-commerce consumers differ in discount sensitivity, usage behaviour, and stated future-use intentions, and what adoption, reactivation, or retention actions are supported by these differences.
3. **General Category Scope:** The survey dataset measures general quick-commerce consumer behavior, not Blinkit-specific satisfaction or retention outcomes. Earlier provisional framing using Blinkit as a focal case is formally superseded; firm-specific satisfaction claims are strictly prohibited.
4. **General Quick-Commerce Category Scope:** The survey dataset measures general quick-commerce consumer behavior, not platform-specific satisfaction. Platform-specific satisfaction benchmarks are strictly prohibited.
5. **Conditional Approval of Survey Dataset:** The Mendeley survey dataset (`cw88nb7822/1`, Chandra 2026) is conditionally approved as an exploratory dataset for customer segmentation, discount dependency modeling, and non-use barrier analysis.
6. **App-Review Corpus Superseded:** The earlier scraped app-review corpus (Candidate A, 4,290 common-window records) is superseded as the primary dataset due to unresolved upstream collection provenance and unlicenced raw review text.
7. **Strict Gate 0 Boundary:** Execution of Gate 0 was strictly restricted to verification, schema validation, and routing audit.
8. **Framing Correction at Gate 1 Launch:** Following completion of the Gate 0 audit, the Principal Project Lead directed that Blinkit must not be used as a focal case because the survey measures general quick commerce. The canonical project title is locked as *Beyond Discounts: Customer Segmentation and Retention Strategy for Indian Quick Commerce*.

---

## 2. Core Evaluation Questions & Resolution Status

| # | Question Evaluated | Direct Evidence & Finding | Resolution Status |
| :--- | :--- | :--- | :--- |
| **Q1** | Does the common review window (14 Aug–31 Dec 2024) provide sufficient usable records? | Programmatic audit confirmed 4,290 usable records across Blinkit (1,376), Zepto (1,740), and JioMart (1,174). However, the corpus is superseded as the primary dataset by the structured survey dataset. | **SUPERSEDED BY SURVEY SCOPE** |
| **Q2** | Is Candidate B independent of Candidate A? | No. Candidate B is a 100% derivative copy of Candidate A row-for-row. Permanently rejected. | **RESOLVED (REJECTED)** |
| **Q3** | Can Swiggy Instamart reviews be acquired legally and reproducibly? | No. Google Play Terms restrict automated scraping, and reviews conflate food delivery with Instamart. Scraping is prohibited; Instamart is contextualized via published secondary research. | **RESOLVED (PROHIBITED)** |
| **Q4** | Does the Mendeley dataset (`cw88nb7822/1`) provide usable empirical consumer data? | **Yes.** The complete candidate bundle (`Data.xlsx`, `Code Book.docx`, `Questionairre.docx`) was obtained, verified, and audited (`scripts/audit_survey_data.py`). 1,263 data rows $\times$ 130 columns, 0 null cells, valid codebook ranges. Previous metadata-only classification is formally updated to **Conditionally Approved Candidate Survey Dataset**. | **RESOLVED (CONDITIONALLY APPROVED)** |
| **Q5** | What is the academic provenance and licence of the survey dataset? | Published on Mendeley Data (`10.17632/cw88nb7822.1`, 14 Oct 2026) under **CC BY 4.0** by Dr. Ashish Chandra (Amity University, Lucknow). Recruitment method, sampling frame, and fieldwork dates remain unrecorded. National representativeness is disclaimed. | **CORRECTED & RESOLVED** |
| **Q6** | How does questionnaire routing affect the 80 previous users? | For the 456 non-current respondents (including the 80 previous users), questions with source-defined N/A options (e.g. service satisfaction QA 37–40 and service problems QA 36) hold explicit Code 6 or dummy N/A values, meaning historical satisfaction and experienced problems are unobserved for previous users. However, QA 16–QA 45 is not entirely skipped: QA 24 (physical-store preferences), QA 26 (substantive ₹0 monthly spend), QA 43 (substantive non-use routine role), QA 46 (future intent), QA 48 (non-use reasons), and QA 49 (improvements) remain substantive. | **CORRECTED & RESOLVED** |
| **Q7** | How should QA 46 and QA 47 be interpreted? | QA 46 is stated future intention across all 1,263 respondents (not actual repurchase). QA 47 contains substantive values 1–5 for the 807 current users and Code 6 (Not applicable) for the 456 non-current users. Code 6 must **not** be interpreted as defection or unwillingness to continue. | **CORRECTED & RESOLVED** |

---

## 3. Strict Analytical Prohibitions

To ensure academic and methodological credibility, the following seven practices are strictly prohibited:

1. **PROHIBITED:** Treating generic satisfaction measures (QA 37–40) or problem rates (QA 36) as Blinkit-specific results.
2. **PROHIBITED:** Treating platform-awareness or ever-used indicators (QA 11, 12) as proof of current platform-specific ordering.
3. **PROHIBITED:** Treating stated future-use intention (QA 46) or post-discount continuation (QA 47) as observed repeat purchase or transactional retention.
4. **PROHIBITED:** Treating QA 47 Not-Applicable codes (Code 6, $n=456$) as negative responses, churn, or unwillingness to continue.
5. **PROHIBITED:** Treating the 80 previous users who currently report no orders as confirmed transactional churn events.
6. **PROHIBITED:** Claiming national demographic representativeness based on sample size ($N=1,263$) alone.
7. **PROHIBITED:** Claiming causal retention uplift from cross-sectional survey responses.

---

## 4. Multi-Tier Missingness & Data Completeness Architecture

```
Total Survey Cells: 164,190 (1,263 respondents x 130 columns)
├── Physical Null / Blank Cells: 0 (100.0% physical data presence)
└── Information Availability Tiers:
    ├── Substantive Observed Responses:
    │   ├── Demographics (QA 1-8): n=1,263
    │   ├── Platform Footprint (QA 11-12): n=1,263
    │   ├── Physical-Store Category Preferences (QA 24): n=1,263 (not skip-coded; substantive across all respondents)
    │   ├── Substantive Zero-Spend (QA 26 Code 1 = ₹0): n=456 non-current users
    │   ├── Substantive Non-Use Routine (QA 43 Code 6 = Do not use): n=456 non-current users
    │   ├── Order Habits & Active Spending (QA 16-27): n=807 current users
    │   ├── Service Satisfaction (QA 37-40): n=807 current users
    │   ├── QA 46 Stated Future Intention: n=1,263 (100% of respondents)
    │   ├── QA 47 Discount Reduction Continuation: n=807 current users
    │   ├── QA 48 Non-Use Reasons: n=456 non-current users (376 never + 80 previous)
    │   └── QA 49 Preferred Improvements: n=1,263 (100% of respondents)
    └── Explicit Source-Defined Not-Applicable / Skip-Coded Responses:
        ├── QA 16-45 Single-Select & Dummy N/A Codes: n=456 non-current respondents
        ├── QA 37-40 Satisfaction Code 6: n=456 non-current respondents
        ├── QA 47 Discount Continuation Code 6: n=456 non-current respondents
        └── QA 48 Current-User Skip Flag (Code 1): n=807 current users
```

---

## 5. Gate Boundary Confirmation & Recommended Disposition

- **Gate Status:** **CONDITIONALLY APPROVED BY PRINCIPAL PROJECT LEAD (FINAL AUDIT LOCK)**
- **Recommended Gate 0 Disposition:** **PASS (UNDER AUTHORIZED CONDITIONAL SCOPE)**
- **Gate Boundary Confirmation:** All Gate 0 audit deliverables, schema validators, test suites, and documentation locks are fully in place. Work is halted; no Gate 1 exploratory analysis, segmentation modeling, or dashboard implementation has commenced.
