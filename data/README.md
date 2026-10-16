# Quick-Commerce Review Data Registry & Ingestion Guide

This document describes the dataset candidates evaluated during **Gate 0**, data access and storage conventions, licensing boundaries, schema definitions, and instructions for reproducing the quantitative data audit.

---

## 1. Candidate Dataset Selection & Status

During Gate 0, three GitHub repositories and direct app store endpoints were audited:

| Candidate | Repository / Source | Records | Platforms Covered | Licensing | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Candidate A** | `mdaniq45/E-Commerce-BlinkIt-vs-Zepto-vs-JioMart-Reviews-Analysia` | 4,620 | Blinkit, Zepto, JioMart | Apache-2.0 repo licence (third-party review text unlicenced) | **Primary Feasibility Candidate (Conditional)** |
| **Candidate B** | `AkeelFarooq/Quick-Commerce-Review-Insights-Blinkit-vs-Zepto-vs-JioMart` | 4,620 | Blinkit, Zepto, JioMart | None stated | **Rejected as Duplicate** (100% derivative of Candidate A with reformatted dates) |
| **Candidate C** | `vaishSharma-15/BlinkitReviewAnalyzer` | 32,139 Play / 3,260 YouTube | Blinkit (Play Store), Unstructured Social | Unlicenced | **Reference Only** (Blinkit-only for reviews; YouTube comments lack star ratings and platform tags) |
| **Candidate D** | Google Play Store Listings (`com.grofers.customerapp`, `com.zeptoconsumerapp`, `in.swiggy.android`) | Real-time | Blinkit, Zepto, Swiggy Instamart | Google Play TOS prohibits automated scraping | **Legally / Operationally Restricted** |

### Selected Working Candidate: Candidate A (`reviews.csv`)
Candidate A provides a clean, pre-parsed review dataset comprising 4,620 observations. However, its adoption is **conditional** upon Principal Project Lead approval regarding platform scope: it covers **Blinkit (1,380)**, **Zepto (1,740)**, and **JioMart (1,500)**. It does **not** include Swiggy Instamart.

---

## 2. Local Storage Convention & Git Discipline

To strictly adhere to compliance requirements, data ethics, and repository size hygiene:

- **Raw Data Location:** All raw review files must be stored locally in `data/raw/` (e.g., `data/raw/reviews.csv`).
- **Version Control Policy:** `data/raw/*` is explicitly excluded from Git tracking via `.gitignore`.
- **Licensing Constraint:** A repository's open-source code licence (e.g., Apache 2.0) does **not** automatically grant copyright or redistribution rights over the scraped public user reviews contained inside it. Therefore, raw text bearing personal identifiers (usernames, reviewer IDs) must never be committed to Git.
- **Privacy (PII):** Raw files must omit or hash reviewer usernames and device identifiers.

---

## 3. Data Schema & Required Columns

When ingesting or auditing review data, the file must be a comma-separated values (CSV) file containing the following essential fields:

| Column Name | Data Type | Requirement | Description | Example Values |
| :--- | :--- | :--- | :--- | :--- |
| `platform` | String | **Mandatory** | Lowercase platform identifier | `blinkit`, `zepto`, `jiomart` |
| `review` | String | **Mandatory** | Verbatim text of customer review | `"Delivery was fast but tomato was spoiled"` |
| `rating` | Integer | **Mandatory** | Customer rating on a 1 to 5 integer scale | `1`, `2`, `3`, `4`, `5` |
| `date` | String / Date | **Mandatory** | Review submission date | `30 December 2024` or `2024-12-30` |

### Optional / Derived Fields (Gate 1+)
- `parsed_date`: ISO 8601 formatted date (`YYYY-MM-DD`).
- `char_len`: Character length of `review`.
- `word_len`: Word count of `review`.
- `service_failure_theme`: Categorized complaint topic (e.g., Delivery, Missing Item, Support).
- `switching_intention`: Boolean flag indicating explicit expression of defection or uninstallation.

---

## 4. Known Data Limitations & Bias

Any analysis utilizing this public review data must explicitly account for the following structural artefacts:

1. **Severe Voluntary Response Negativity Bias:** Over 71.5% of reviews are 1-star ratings (Zepto: 79.1%, JioMart: 81.1%, Blinkit: 51.7%). Satisfied users rarely leave app store reviews unless prompted. The data reflects **severe operational failure modes**, not the satisfaction of the average transacting user.
2. **Temporal Coverage Asymmetry:**
   - Blinkit reviews cover 157 days (27 Jul 2024 to 31 Dec 2024, ~5.2 months).
   - Zepto reviews cover 139 days (14 Aug 2024 to 31 Dec 2024, ~4.6 months).
   - JioMart reviews cover 1,624 days (21 Jul 2020 to 31 Dec 2024, ~53.4 months).
   *Mitigation:* Comparative analysis must truncate the window to the overlapping period (Aug–Dec 2024).
3. **Length Truncation Artefact:** All reviews in Candidate A have at least 6–10 words and 80+ characters. Extremely short reviews ("good", "bad app") were pre-filtered out by the upstream scraper.
4. **Platform Substitution:** Swiggy Instamart is not present in Candidate A. JioMart serves as the third comparator unless a separate compliant Swiggy pipeline is approved.
5. **Not Customer Transaction Data:** Public reviews cannot be interpreted as repurchase behaviour or verified customer order history. Switching intention in text indicates sentiment and friction, not confirmed behavioral defection.

---

## 5. Reproducing the Quantitative Data Audit

The data audit can be executed reproducibly on any local machine without fabricating synthetic records.

### Prerequisites
- Python 3.10+
- `pandas`, `numpy`

### Step-by-Step Execution
1. Place the candidate `reviews.csv` into `data/raw/reviews.csv`. Alternatively, download Candidate A directly:
   ```bash
   # Windows PowerShell
   Invoke-WebRequest -Uri "https://raw.githubusercontent.com/mdaniq45/E-Commerce-BlinkIt-vs-Zepto-vs-JioMart-Reviews-Analysia/main/reviews.csv" -OutFile "data/raw/reviews.csv"
   ```
2. Run the audit script:
   ```bash
   python scripts/audit_data.py --file data/raw/reviews.csv
   ```
3. The script will perform:
   - Verification of essential columns (`platform`, `review`, `rating`, `date`).
   - Missingness and blank string checks.
   - Exact and near-duplicate string matching.
   - Platform-wise usable row tally.
   - Date range calculation and format validation.
   - Rating frequency and mean rating calculation.
   - Feasibility check against preferred and minimum thresholds.
