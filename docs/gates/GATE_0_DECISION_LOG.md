# GATE 0 — DECISION LOG (FINAL REMEDIATION)

**Project Title:** Evidence-Led CRM Service-Recovery Prioritisation for Indian Quick Commerce: A Public-Feedback-Based Customer Retention Decision Framework  
**Focal Business:** Blinkit  
**Primary Competitor Benchmark:** Zepto  
**Secondary Comparative Context:** JioMart (same-window verified; secondary benchmark only)  
**Assigned Role:** Implementation Engineer  
**Decision Authority:** Principal Project Lead  
**Remediation Date:** 2026-10-17  
**Gate Status:** **PENDING PRINCIPAL PROJECT LEAD APPROVAL (FINAL REMEDIATION SUBMITTED)**  
**Recommended Disposition:** **PASS (UNDER AUTHORIZED CONDITIONAL SCOPE)**

---

## 1. Controlling Decisions of the Principal Project Lead

The Principal Project Lead reviewed the project repository and established the following binding determinations:

1. **Focal Company:** Blinkit is retained as the focal platform.
2. **Primary Competitor:** Zepto is designated as the primary competitor benchmark for the review-data comparison.
3. **JioMart Role:** JioMart is retained strictly as secondary comparative context (verified at remediation: 1,174 usable records in the common window).
4. **No Scraping of Swiggy Instamart:** Do not scrape Swiggy Instamart reviews to compensate for missing data.
5. **Common Review Window (Static Scope Only):** The common period, **14 August 2024 to 31 December 2024 (inclusive)**, is authorized for a limited, **STATIC complaint-theme and expressed-switching-signal analysis only**. It must **not** be used to claim temporal trends or seasonality.
6. **Exploratory Status of Corpus:** The existing 4,620-record dataset is classified as a candidate exploratory corpus, **not** an approved representative sample of platform customers.
7. **Gate Boundary:** Execution is strictly restricted to Gate 0 remediation, evidence validation, and Git synchronization. No progression to Gate 1.

---

## 2. Core Evaluation Questions & Remediation Findings

| # | Question Evaluated | Remediation Evidence & Direct Finding | Status |
| :--- | :--- | :--- | :--- |
| **Q1** | Does the common review window (14 Aug–31 Dec 2024) provide sufficient usable records for Blinkit and Zepto? | **Yes.** Programmatic re-audit via `scripts/audit_data.py` confirmed:<br/>- **Blinkit:** 1,376 usable records (138 days span, 2024-08-15 to 2024-12-31; 4 out-of-window exclusions). Exceeds 500 threshold.<br/>- **Zepto:** 1,740 usable records (139 days span, 2024-08-14 to 2024-12-31; 0 exclusions). Exceeds 500 threshold.<br/>- **JioMart:** 1,174 usable records (139 days span, 2024-08-14 to 2024-12-31; 326 exclusions). Exceeds 500 threshold.<br/>- **Total Window Volume:** 4,290 usable records (330 total exclusions; 0 in-window quality exclusions). Zero missing fields, zero blank text, zero invalid ratings.<br/>*Methodological Caveat:* Record-count thresholds demonstrate qualitative sample feasibility; they do **not** establish statistical power or population representativeness. | **PASSED (FEASIBILITY CONFIRMED)** |
| **Q2** | Is Candidate B independent of Candidate A? | **No.** Direct row-for-row cross-examination and hash inspection confirmed Candidate B is a 100% derivative copy of Candidate A with reformatted dates and added columns (`month`, `sentiment`). Candidate B is permanently rejected as redundant. | **RESOLVED (REJECTED)** |
| **Q3** | Can Swiggy Instamart reviews be acquired legally and reproducibly? | **No.** In accordance with controlling decision 4, direct scraping is prohibited. Reviews on `in.swiggy.android` conflate food delivery with Instamart, and Google Play terms restrict unauthorized bulk scraping. Swiggy Instamart is formally removed from empirical microdata scope; secondary macro data (Financial Express 2026, Datum Intelligence 2024) provides Instamart industry context. | **RESOLVED (REMOVED FROM MICRODATA)** |
| **Q4** | Does the recently published Mendeley dataset (cw88nb7822/1) provide usable empirical consumer data? | **No.** Direct inspection of the Mendeley Data repository page (`10.17632/cw88nb7822.1`, Chandra 2026) revealed that only metadata and a 49-question reproduction methodology are displayed. The "Download All" button is disabled; zero raw data files (CSV, XLSX, SAV), questionnaire instruments, or codebooks are accessible. Formally classified as **UNAVAILABLE for empirical analysis**. | **RESOLVED (UNAVAILABLE)** |
| **Q5** | Is the legal and policy assessment of Google Play access factually grounded? | **Yes.** Factually grounded distinctions established: (a) Google Play Developer API (`androidpublisher.reviews.list`) requires the `androidpublisher` authorization scope and app developer ownership, meaning third-party developers cannot query competitor reviews via this official API; (b) Google Terms of Service prohibit accessing services using methods other than provided interfaces or instructions (addressing automated access that violates machine-readable instructions); (c) automated crawling is subject to `robots.txt` disallows and rate-limiting. No live scraping is authorized for this project; candidate corpus is retained subject to provenance and unlicenced text limitations. | **CORRECTED & RESOLVED** |
| **Q6** | Is statistical terminology properly constrained? | **Yes.** Enforced rigorous measurement distinctions throughout all documents:<br/>1. **Downloads-to-WAU ratio:** aggregate engagement ratio reported by external secondary sources (Financial Express May 19, 2026: Blinkit 24%, Zepto 23%; Oct 2, 2026 update reports revised figures); **not** cohort retention rates and **not** individual repeat purchase.<br/>2. **Ordering frequency:** aggregate orders-per-user metric from company disclosures.<br/>3. **Actual churn:** unobserved without customer-level transaction histories.<br/>4. **Cohort retention:** unavailable without customer transaction datasets.<br/>5. **Expressed switching intention:** text-based statement of intended defection, not an observed transaction outcome.<br/>Removed all claims of statistical representativeness or power. | **CORRECTED & RESOLVED** |
| **Q7** | Is the novelty assessment properly framed against existing work (including Candidate C)? | **Yes.** Acknowledged Candidate C's validation methodology (gold-set classifier accuracy, inter-run stability, scorecard) and catalog adoption focus. Framed our contribution as an **intended applied contribution** (evidence-to-action decision chain linking failure severity and addressability to issue-specific CRM interventions, bounded economic trade-offs, and an A/B pilot plan), not a proven unique research invention. | **CORRECTED & RESOLVED** |

---

## 3. Requirement Verification Summary

### Passed Requirements
- **Usable Volume in Common Window:** Blinkit (1,376) and Zepto (1,740) both exceed the mandatory 500-record threshold within the synchronized 14 August–31 December 2024 window.
- **Completeness & Integrity:** 0.00% missing fields across platform, review text, rating, and date in the common window.
- **Code Audit & Test Suite:** Personal machine-specific scratch paths completely removed. Audit script (`scripts/audit_data.py`) enforces strict validation, disaggregates missing vs. blank vs. unparseable values, validates ratings (1-5), normalizes platforms safely, and exports aggregate summary JSON (`docs/gates/GATE_0_AUDIT_SUMMARY.json`). Fully validated by automated test suite (`tests/test_audit_data.py`).
- **Pilot Annotation Remediation:** Re-evaluated 60-record pilot under a 6-category compact rubric distinguishing:
  1. Explicit intention to leave reviewed platform (Blinkit: 1 [3.3%]; Zepto: 2 [6.7%]).
  2. Explicit completed departure (Blinkit: 2 [6.7%]; Zepto: 1 [3.3%]).
  3. Switching intention towards named competitor (Blinkit: 0; Zepto: 1 [3.3%]).
  4. Positive competitive acquisition / conquesting (Blinkit: 1 [3.3%], switched *from* BigBasket *to* Blinkit; Zepto: 0).
  5. General dissatisfaction without switching statement (Blinkit: 10 [33.3%]; Zepto: 23 [76.7%]).
  6. Positive / neutral feedback (Blinkit: 16 [53.3%]; Zepto: 3 [10.0%]).
  *Crucial Clarification:* Corrected the previous misclassification of Record 12 (acquisition mention for Blinkit conflated with defection) and established explicit departure/switching signals at 10.0% for Blinkit (3/30) and 13.3% for Zepto (4/30). Acknowledged single-coder limitation (cannot establish inter-rater reliability) and explained multi-label theme counts (summing to 75 across 60 reviews).
- **Scope Restriction:** Analysis strictly bounded to a STATIC review-theme comparison for 14 August–31 December 2024. Monthly trends and seasonality claims are formally excluded.

### Excluded / Prohibited Actions
- Scraping live platforms (Swiggy Instamart, Blinkit, Zepto) is prohibited.
- Committing raw review text or reviewer identifiers to Git is prohibited.
- Claiming temporal trends or seasonal shifts across the 4.5-month window is prohibited.
- Treating public reviews as customer-level transaction or churn logs is prohibited.

---

## 4. Recommended Disposition & Gate Boundary Confirmation

The Implementation Engineer has executed all Gate 0 remediation tasks, validated the quantitative evidence, and prepared verified Git synchronization.

- **Gate Status:** **PENDING PRINCIPAL PROJECT LEAD APPROVAL**
- **Recommended Gate 0 Disposition:** **PASS (UNDER AUTHORIZED CONDITIONAL SCOPE)**
- **Gate Boundary Confirmation:** Execution is strictly halted at Gate 0. No Gate 1 modeling, no sentiment classification pipeline, no CRM decision engine implementation, and no Power BI dashboard construction have commenced.
