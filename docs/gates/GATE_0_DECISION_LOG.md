# GATE 0 — DECISION LOG (REVISED)

**Project Title:** Evidence-Led CRM Service-Recovery Prioritisation for Indian Quick Commerce: A Public-Feedback-Based Customer Retention Decision Framework  
**Focal Business:** Blinkit  
**Primary Competitor Benchmark:** Zepto  
**Secondary Comparative Context:** JioMart (same-window verified; secondary benchmark only)  
**Assigned Role:** Implementation Engineer  
**Decision Authority:** Principal Project Lead (ChatGPT)  
**Revision Date:** 2026-10-17  
**Gate Status:** **PASS (UNDER AUTHORIZED CONDITIONAL SCOPE)**

---

## 1. Controlling Decisions of the Principal Project Lead

The Principal Project Lead reviewed the initial Gate 0 report and established the following binding determinations:

1. **Focal Company:** Blinkit is retained as the focal platform.
2. **Primary Competitor:** Zepto is designated as the primary competitor benchmark for the initial review-data comparison.
3. **JioMart Role:** JioMart is **not** to be treated as a directly comparable primary benchmark until same-window record counts and coverage have been verified. (Verified at revision: 1,174 usable records in the common window; retained strictly as secondary comparative context).
4. **No Scraping of Swiggy Instamart:** Do not scrape Swiggy Instamart reviews to compensate for missing data.
5. **Common Review Window (Static Scope Only):** The common period, **14 August 2024 to 31 December 2024 (inclusive)**, is authorized for a limited, **STATIC complaint-theme and expressed-switching-signal analysis only**. It must **not** be used to claim temporal trends or seasonality.
6. **Exploratory Status of Corpus:** The existing 4,620-record dataset is classified as a candidate exploratory corpus, **not** an approved representative sample of platform customers.
7. **Gate Boundary:** Execution is strictly restricted to Gate 0 correction and Git synchronization. No progression to Gate 1.

---

## 2. Core Evaluation Questions & Re-Audit Findings

| # | Question Evaluated | Revision Evidence & Direct Finding | Status |
| :--- | :--- | :--- | :--- |
| **Q1** | Does the common review window (14 Aug–31 Dec 2024) provide sufficient usable records for Blinkit and Zepto? | **Yes.** Programmatic re-audit via `scripts/audit_data.py` confirmed:<br/>- **Blinkit:** 1,376 usable records (138 days span, 2024-08-15 to 2024-12-31; 4 out-of-window exclusions). Exceeds 500 threshold.<br/>- **Zepto:** 1,740 usable records (139 days span, 2024-08-14 to 2024-12-31; 0 exclusions). Exceeds 500 threshold.<br/>- **JioMart:** 1,174 usable records (139 days span, 2024-08-14 to 2024-12-31; 326 exclusions). Exceeds 500 threshold.<br/>- **Total Window Volume:** 4,290 usable records (330 total exclusions). Zero missing fields, zero blank text, zero exact duplicate rows. | **PASSED** |
| **Q2** | Is Candidate B independent of Candidate A? | **No.** Direct row-for-row cross-examination and hash inspection confirmed Candidate B is a 100% derivative copy of Candidate A with reformatted dates and added columns (`month`, `sentiment`). Candidate B is permanently rejected as redundant. | **RESOLVED (REJECTED)** |
| **Q3** | Can Swiggy Instamart reviews be acquired legally and reproducibly? | **No.** In accordance with controlling decision 4, direct scraping is prohibited. Reviews on `in.swiggy.android` conflate food delivery with Instamart, and Google Play terms restrict unauthorized bulk scraping. Swiggy Instamart is formally removed from empirical microdata scope; secondary macro data (Financial Express 2026, Datum Intelligence 2024) provides Instamart industry context. | **RESOLVED (REMOVED FROM MICRODATA)** |
| **Q4** | Does the recently published Mendeley dataset (cw88nb7822/1) provide usable empirical consumer data? | **No.** Direct inspection of the Mendeley Data repository page (`10.17632/cw88nb7822.1`, Chandra 2026) revealed that only metadata and a 49-question reproduction methodology are displayed. The "Download All" button is disabled; zero raw data files (CSV, XLSX, SAV), questionnaire instruments, or codebooks are accessible. Formally classified as **UNAVAILABLE for empirical analysis**. | **RESOLVED (UNAVAILABLE)** |
| **Q5** | Is the legal and policy assessment of Google Play access factually grounded? | **Yes.** Corrected erroneous citation of "section 3.3". Direct inspection of official documentation confirmed: (a) Google Play Developer API (`androidpublisher.reviews.list`) requires developer account ownership/authorization; (b) Google Terms of Service prohibit accessing services outside provided interfaces; (c) automated crawling is subject to `robots.txt` and rate-limiting. Candidate A's pre-scraped snapshot avoids active scraping, but raw text must remain excluded from Git due to unlicenced third-party user text. | **CORRECTED & RESOLVED** |
| **Q6** | Is statistical terminology properly constrained? | **Yes.** Removed all claims of "statistical representativeness" or "statistical power". Acknowledged extreme voluntary response negativity bias (71.5% 1-star). Explicitly distinguished: (1) public reviews, (2) expressed switching intention, (3) actual customer defection, (4) observed repeat purchase, and (5) measured retention. | **CORRECTED & RESOLVED** |
| **Q7** | Is the novelty assessment properly framed against existing work (including Candidate C)? | **Yes.** Acknowledged Candidate C's validation methodology (gold-set classifier accuracy, inter-run stability, scorecard) and catalog adoption focus. Framed our contribution as an **intended applied contribution** (evidence-to-action decision chain linking failure severity and addressability to issue-specific CRM interventions, bounded economic trade-offs, and an A/B pilot plan), not a proven unique research invention. | **CORRECTED & RESOLVED** |

---

## 3. Requirement Verification Summary

### Passed Requirements
- **Usable Volume in Common Window:** Blinkit (1,376) and Zepto (1,740) both exceed the mandatory 500-record threshold.
- **Completeness:** 0.00% missing fields across platform, review text, rating, and date in the common window.
- **Git Reconciliation & Synchronization:** Local repository reconciled non-destructively with remote `origin/main` (`git merge origin/main --allow-unrelated-histories`) and successfully pushed without `--force`.
- **Pilot Annotation Feasibility:** Demonstrated consistent operational failure categorization and isolation of explicit switching intention (8.3%) from general negative sentiment (91.7%).
- **Scope Restriction:** Analysis strictly bounded to a STATIC review-theme comparison for 14 August–31 December 2024. Monthly trends and seasonality claims are formally excluded.

### Excluded / Prohibited Actions
- Scraping live platforms (Swiggy Instamart, Blinkit, Zepto) is prohibited.
- Committing raw review text or reviewer identifiers to Git is prohibited.
- Claiming temporal trends or seasonal shifts across the 4.5-month window is prohibited.
- Treating public reviews as customer-level transaction or churn logs is prohibited.

---

## 4. Final Recommendation & Gate Boundary Confirmation

The Implementation Engineer confirms that all Gate 0 revision requirements have been executed, verified, and synchronized with GitHub.

- **Recommended Gate 0 Disposition:** **PASS (UNDER AUTHORIZED CONDITIONAL SCOPE)**
- **Gate Boundary:** Execution is strictly halted at Gate 0. No Gate 1 modeling, no sentiment classification pipeline, and no Power BI dashboard construction have commenced.
