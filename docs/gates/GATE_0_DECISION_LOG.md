# GATE 0 — DECISION LOG

**Project:** Evidence-Led CRM Service-Recovery Prioritisation for Indian Quick Commerce: A Public-Feedback-Based Customer Retention Decision Framework  
**Focal Business:** Blinkit (with Zepto and Swiggy Instamart as proposed comparators)  
**Role:** Implementation Engineer  
**Authority:** Principal Project Lead (ChatGPT) owns all final project scope, dataset acceptance, and gate progression decisions.  
**Audit Date:** 2026-10-17  
**Gate 0 Status:** CONDITIONAL PASS (Requires Scope & Comparator Alignment by Principal Project Lead)

---

## 1. Core Questions Evaluated at Gate 0

| # | Gate 0 Evaluation Question | Evidence & Direct Finding | Gate Status |
| :--- | :--- | :--- | :--- |
| **Q1** | Can Indian quick-commerce review data be accessed legally, freely, and without circumventing platform protections? | **Yes, with caveats.** Candidate A (`mdaniq45`) provides 4,620 pre-scraped public reviews freely. However, direct real-time scraping of Google Play Store (Candidate D) violates Google Play Terms of Service and triggers bot-mitigation controls. Direct PDP scraping on Blinkit requires authentication (Candidate C). | **CONDITIONALLY RESOLVED** |
| **Q2** | Are candidate datasets independent and verifiable? | **Candidate B is NOT independent.** Direct hash and row comparison confirmed Candidate B is a 100% derivative copy of Candidate A (same 4,620 rows, same ratings, same reviews) with reformatted dates and added columns. Candidate C is an independent repository but its Play Store reviews cover only Blinkit (32k rows), while its comparison file contains 3.2k YouTube comments lacking ratings. | **RESOLVED** (Candidate B rejected as redundant) |
| **Q3** | Does the available empirical data cover the intended comparison platforms (Blinkit, Zepto, Swiggy Instamart)? | **No.** Candidate A covers Blinkit (1,380), Zepto (1,740), and JioMart (1,500). Swiggy Instamart is **missing**. Direct extraction of Instamart reviews from the unified Swiggy app (`in.swiggy.android`) suffers from severe service-entanglement (food delivery vs. grocery) and scraping restrictions. | **BLOCKED / REQUIRES LEAD DECISION** |
| **Q4** | Does the empirical data meet quantitative sample and temporal coverage thresholds? | **Partially.** Total usable volume (4,620 rows) exceeds both minimum (1,500) and target (3,000) thresholds. Blinkit (1,380) and Zepto (1,740) exceed the 1,000-row target. However, temporal coverage for Blinkit (157 days, ~5.2 months) and Zepto (139 days, ~4.6 months) fails the 6-month minimum and 12-month preferred target. JioMart spans 53.4 months, creating severe temporal asymmetry. | **CONDITIONALLY ACCEPTABLE** (requires window truncation) |
| **Q5** | Can public customer reviews distinguish operational service failures and explicit switching intentions from generic negative sentiment? | **Yes.** A reproducible 60-review pilot (30 Blinkit, 30 Zepto) proved that reviews contain rich operational signals across delivery delays, missing/wrong items, customer support failures, dynamic pricing friction, and product quality. Furthermore, explicit switching intentions ("uninstalled", "switched to Blinkit", "deleted app") can be cleanly separated from ordinary negative sentiment. | **PASSED** |
| **Q6** | Is the proposed evidence-to-action CRM decision framework distinct from existing published work? | **Yes.** Existing public projects (Candidates A, B, C) and papers (Naik & Kapdi 2025, Goel & Sharma 2024) perform descriptive sentiment analysis, topic word clouds, and generic advice. None build an empirical bridge linking failure severity to addressability, operational recovery interventions, and bounded economic cost-benefit trade-offs. | **PASSED** |

---

## 2. Requirement Status Matrix

### A. Passed Requirements
1. **Tooling & Compute Constraints:** Normal CPU-only Python 3.13 and Pandas 3.0.3 execution verified; no paid APIs, GPU, or subscriptions required.
2. **Review Text Depth:** Reviews possess sufficient semantic density (mean ~52-58 words, ~360-410 characters) to distinguish granular operational failure modes.
3. **Switching Intention Detectability:** Explicit expressions of customer churn/switching can be reliably isolated from general negative sentiment.
4. **Distinction of Core Concepts:** Clear boundaries maintained between:
   - Observed customer transactions / repurchase behavior (unobserved in public data).
   - Public customer reviews (observable voluntary negative feedback).
   - Expressed switching intention (observable vocal defection signal).
   - Published aggregate industry research (secondary macro benchmarks).
5. **Novelty Boundary:** Differentiation is properly anchored on the evidence-to-action decision framework rather than basic NLP sentiment classification.

### B. Blocked & Unresolved Requirements (Reserved for Lead Decision)
1. **Comparator Alignment (Swiggy Instamart vs. JioMart):**
   - Candidate A provides 1,500 verified records for JioMart, but zero records for Swiggy Instamart.
   - The controlling brief requests Blinkit vs. Zepto vs. Swiggy Instamart.
   - *Status:* Blocked pending Principal Project Lead choice between accepting JioMart as the third platform or mandating a compliant Swiggy Instamart ingestion path.
2. **Temporal Window Harmonization:**
   - Blinkit data spans 27 Jul 2024 to 31 Dec 2024 (157 days).
   - Zepto data spans 14 Aug 2024 to 31 Dec 2024 (139 days).
   - JioMart spans 21 Jul 2020 to 31 Dec 2024 (1,624 days).
   - Neither Blinkit nor Zepto meets the 180-day (6-month) minimum threshold.
   - *Status:* Unresolved pending Principal Project Lead approval to restrict comparative analysis to the overlapping August–December 2024 window (~4.5 months) and supplement annual trend context using secondary industry reporting (Datum Intelligence, Financial Express).

---

## 3. Recommended Decisions for Principal Project Lead

### Recommendation 1 (Platform Scope): Approve JioMart as Third Comparator Platform
- **Proposal:** Formally accept Candidate A's three-platform corpus: **Blinkit (1,380 rows), Zepto (1,740 rows), and JioMart (1,500 rows)** (Total: 4,620 rows).
- **Rationale:**
  1. Candidate A is already downloaded, verified, and free of missing values.
  2. Attempting to scrape Swiggy Instamart reviews directly violates Google Play Terms of Service, risks IP blacklisting, and introduces severe review contamination because reviews on `in.swiggy.android` mix food delivery, restaurant dining, and grocery orders without clean native labels.
  3. JioMart represents a formidable competing quick/slotted commerce model backed by Reliance Retail, offering meaningful structural comparison against pure-play quick-commerce dark stores (Blinkit and Zepto).

### Recommendation 2 (Temporal Baseline): Truncate Comparative Corpus to Aug–Dec 2024
- **Proposal:** Filter the comparative analysis to the overlapping window: **14 August 2024 to 31 December 2024** (~4.5 months), while contextualizing long-term ordering frequency trends using verified aggregate secondary disclosures (Financial Express 2026, Datum Intelligence 2024).
- **Rationale:**
  1. Including JioMart reviews from 2020–2023 would introduce severe chronological distortion against 2024 quick-commerce dark-store realities.
  2. The 4.5-month overlapping window contains over 3,500 reviews, providing abundant statistical support for complaint categorization, severity ranking, and CRM recovery modeling without temporal skew.

---

## 4. Gate Boundary Confirmation

Gate 0 audit is complete. No exploratory data analysis beyond audit metrics, no sentiment classification pipeline, no Power BI dashboard modeling, and no Gate 1 activities have been initiated. Execution is halted awaiting Principal Project Lead determination on the recommendations above.
