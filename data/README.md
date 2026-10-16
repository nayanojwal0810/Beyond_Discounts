# Quick-Commerce Review Data Registry & Ingestion Guide

This document describes the candidate datasets evaluated during **Gate 0**, data access and storage conventions, licensing boundaries, schema definitions, and instructions for reproducing the quantitative data audit.

---

## 1. Candidate Dataset Selection & Scope Status

Under the controlling decisions of the Principal Project Lead:
- **Focal Company:** Blinkit
- **Primary Competitor Benchmark:** Zepto
- **Secondary Comparative Context:** JioMart (verified same-window records; retained as secondary benchmark only)
- **Swiggy Instamart:** Not available in candidate review datasets; direct scraping is prohibited. Swiggy Instamart is contextualized via published secondary industry research (Financial Express, Datum Intelligence).
- **Mendeley Dataset (`cw88nb7822/1`):** Verified as metadata-only; "Download All" disabled; no raw data files released. Marked UNAVAILABLE for empirical analysis.

### Candidate Evaluation Summary

| Candidate | Repository / Source | Total Records | Usable Records in Common Window (14 Aug–31 Dec 2024) | Licensing Status | Evaluation Disposition |
| :--- | :--- | :---: | :---: | :--- | :--- |
| **Candidate A** | `mdaniq45/E-Commerce-BlinkIt-vs-Zepto-vs-JioMart-Reviews-Analysia` | 4,620 | **4,290** (Blinkit: 1,376; Zepto: 1,740; JioMart: 1,174) | Apache-2.0 repo licence (third-party review text unlicenced) | **Approved Candidate Exploratory Corpus (Static Scope)** |
| **Candidate B** | `AkeelFarooq/Quick-Commerce-Review-Insights-Blinkit-vs-Zepto-vs-JioMart` | 4,620 | 4,290 | Unlicenced | **Rejected as Redundant** (100% derivative copy of Candidate A row-for-row) |
| **Candidate C** | `vaishSharma-15/BlinkitReviewAnalyzer` | 35,399 | N/A (Blinkit-only for app reviews; YouTube lacks ratings) | Unlicenced (explicit badge) | **Methodological Reference Only** (retained for validation procedures and scorecard architecture) |
| **Candidate D** | Google Play Store Listings (`com.grofers.customerapp`, `com.zeptoconsumerapp`, `in.swiggy.android`) | Real-time | N/A | Proprietary / Google Terms of Service | **Bulk Scraping Prohibited** (Developer API requires app ownership; scraping restricted) |
| **Mendeley Dataset** | `data.mendeley.com/datasets/cw88nb7822/1` (Chandra 2026) | N/A | 0 (no files released) | CC BY 4.0 (entry) | **Marked Unavailable** (metadata and questionnaire description only; no data files) |

---

## 2. Common Review Window & Scope Boundary

To eliminate the severe chronological asymmetry of the raw dataset (where JioMart dates back to 2020 while Blinkit and Zepto start in mid-2024), the comparative analysis is strictly restricted to:

$$\text{Common Window: 14 August 2024 to 31 December 2024 (inclusive)}$$

### Usable Volume & Exclusions Breakdown:
- **Total Dataset:** 4,620 rows.
- **Out-of-Window Exclusions:** 330 rows (326 JioMart records prior to 14 Aug 2024; 4 Blinkit records prior to 14 Aug 2024).
- **Usable Records in Common Window:** **4,290 rows**:
  - **Blinkit (Focal):** 1,376 usable records (138 days span; 2024-08-15 to 2024-12-31). Exceeds 500 threshold.
  - **Zepto (Primary Competitor):** 1,740 usable records (139 days span; 2024-08-14 to 2024-12-31). Exceeds 500 threshold.
  - **JioMart (Secondary Context):** 1,174 usable records (139 days span; 2024-08-14 to 2024-12-31). Exceeds 500 threshold.

> [!CRITICAL]
> **Static Scope Boundary:** The common 4.5-month window is authorized exclusively for a **STATIC complaint-theme and expressed-switching-signal analysis**. It must **NOT** be used to claim temporal trends, multi-year progress, or seasonal patterns.

---

## 3. Local Storage Convention & Git Hygiene

To ensure legal compliance and repository hygiene:
- **Raw Data Location:** All raw review files must be stored locally in `data/raw/` (e.g., `data/raw/reviews.csv`).
- **Version Control Policy:** `data/raw/*` is strictly excluded from Git tracking via `.gitignore`.
- **Licensing Constraint:** Open-source code licences (e.g., Apache 2.0) apply to repository code, not to scraped third-party user reviews. Raw review text bearing user identifiers must never be committed to Git.
- **Privacy (PII):** Raw files must omit or hash reviewer usernames and device identifiers.

---

## 4. Data Schema & Required Columns

The review dataset must be a comma-separated values (CSV) file containing the following essential fields:

| Column Name | Data Type | Requirement | Description | Example Values |
| :--- | :--- | :--- | :--- | :--- |
| `platform` | String | **Mandatory** | Platform identifier | `blinkit`, `zepto`, `jiomart` |
| `review` | String | **Mandatory** | Verbatim text of customer review | `"Delivery was fast but tomato was spoiled"` |
| `rating` | Integer | **Mandatory** | Rating on 1 to 5 integer scale | `1`, `2`, `3`, `4`, `5` |
| `date` | String / Date | **Mandatory** | Review submission date | `30 December 2024` or `2024-12-30` |

---

## 5. Statistical Interpretation & Known Biases

1. **Exploratory Corpus, Not Random Sample:** The dataset represents a selected sample of public online reviews. It is **not** a statistically representative random sample of all quick-commerce consumers.
2. **Extreme Voluntary Negativity Bias:** Over 71.5% of reviews are 1-star ratings (Zepto: 79.1%, JioMart: 79.9%, Blinkit: 51.7%). The corpus reflects **operational failure modes under stress**, not platform-wide baseline customer satisfaction.
3. **Strict Distinction of Metrics:**
   - **Negative Sentiment:** Frustration or dissatisfaction expressed in text.
   - **Expressed Switching Intention:** Stated intent to defect or uninstall (pilot observed ~8.3%).
   - **Actual Customer Defection:** True churn behaviour (unobserved in public reviews).
   - **Observed Repeat Purchase:** Behavioral repurchasing (unobserved in public reviews).
   - **Measured Retention:** Platform retention rates (available only via aggregate disclosures).

---

## 6. Reproducing the Quantitative Data Audit

The audit can be executed reproducibly on any machine:

### Prerequisites
- Python 3.10+
- `pandas`, `numpy`

### Step-by-Step Execution
1. Ensure candidate `reviews.csv` is in `data/raw/reviews.csv`.
2. Run the audit script:
   ```bash
   python scripts/audit_data.py --file data/raw/reviews.csv
   ```
3. To customize the common review window:
   ```bash
   python scripts/audit_data.py --file data/raw/reviews.csv --window-start 2024-08-14 --window-end 2024-12-31
   ```
4. The script performs:
   - Full-dataset baseline audit (completeness, missingness, duplicates).
   - Common-window filtering and exclusion tracking.
   - Platform-wise usable record counts against the 500-record threshold.
   - Date span and rating breakdown calculations.
   - Static scope boundary enforcement.
