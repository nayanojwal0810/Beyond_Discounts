# Quick-Commerce Review Data Registry & Ingestion Guide

This document describes the candidate datasets evaluated during **Gate 0**, data access and storage conventions, licensing and provenance boundaries, schema definitions, and instructions for reproducing the quantitative data audit.

---

## 1. Candidate Dataset Selection & Scope Status

Under the controlling decisions of the Principal Project Lead:
- **Focal Company:** Blinkit
- **Primary Competitor Benchmark:** Zepto
- **Secondary Comparative Context:** JioMart (verified same-window records; retained strictly as secondary benchmark)
- **Swiggy Instamart:** Not available in candidate review datasets; direct scraping is prohibited. Swiggy Instamart is contextualized exclusively via published secondary industry research (Financial Express, Datum Intelligence).
- **Mendeley Survey Bundle (`cw88nb7822/1`):** Complete bundle (`Data.xlsx`, `Code Book.docx`, `Questionairre.docx`) located, verified, and audited under Gate 0. Conditionally approved as primary exploratory dataset under approved scope direction (see `docs/gates/GATE_0_SURVEY_CANDIDATE_AUDIT.md`).

### Candidate Evaluation Summary

| Candidate | Repository / Source | Total Records | Usable Records in Common Window (14 Aug–31 Dec 2024) | Licensing & Rights Status | Evaluation Disposition |
| :--- | :--- | :---: | :---: | :--- | :--- |
| **Candidate A** | `mdaniq45/E-Commerce-BlinkIt-vs-Zepto-vs-JioMart-Reviews-Analysia` | 4,620 | **4,290** (Blinkit: 1,376; Zepto: 1,740; JioMart: 1,174) | Apache-2.0 repository code licence; underlying third-party customer review text unlicenced; reuse rights **Unresolved** (no legal guarantee) | **Approved Candidate Exploratory Corpus (Static Scope Only)** |
| **Candidate B** | `AkeelFarooq/Quick-Commerce-Review-Insights-Blinkit-vs-Zepto-vs-JioMart` | 4,620 | 4,290 | Unlicenced | **Rejected as Redundant** (100% derivative copy of Candidate A row-for-row) |
| **Candidate C** | `vaishSharma-15/BlinkitReviewAnalyzer` | 35,399 | N/A (Blinkit-only for app reviews; YouTube lacks ratings) | Unlicenced (explicit badge) | **Methodological Reference Only** (retained for validation procedures and scorecard architecture) |
| **Candidate D** | Google Play Store Listings (`com.grofers.customerapp`, `com.zeptoconsumerapp`, `in.swiggy.android`) | Real-time | N/A | Proprietary / Google Terms of Service | **Live Scraping Prohibited** (Developer API uses `androidpublisher` scope requiring app ownership; Terms restrict automated access violating machine-readable rules; no scraping authorised) |
| **Mendeley Survey Bundle** | `data.mendeley.com/datasets/cw88nb7822/1` (Chandra 2026) | 1,263 | N/A (Survey dataset; not app reviews) | CC BY 4.0 (declared) | **Conditionally Approved Candidate Dataset** (Full bundle verified; 1,263 rows × 130 cols; 80-record previous-user routing reconciled; see `GATE_0_SURVEY_CANDIDATE_AUDIT.md`) |

---

## 2. Common Review Window & Scope Boundary

To eliminate the chronological asymmetry of the raw dataset (where JioMart dates back to July 2020 while Blinkit starts 27 July 2024 and Zepto starts 14 August 2024), the comparative analysis is strictly restricted to:

$$\text{Common Window: 14 August 2024 to 31 December 2024 (inclusive)}$$

### Boundary Convention
The window boundaries are strictly inclusive: any review with `2024-08-14 <= review_date <= 2024-12-31` is evaluated. Records dated 2024-08-13 or earlier, and 2025-01-01 or later, are excluded.

### Definition of Usable Record
A record is defined as **usable** if and only if all of the following conditions are met:
1. Review date falls within the inclusive date window (14 August 2024 to 31 December 2024).
2. Platform identifier is present, non-blank, and recognized (`blinkit`, `zepto`, `jiomart`).
3. Review text is present, non-null, and non-blank (contains at least one non-whitespace character).
4. Rating is an integer on the 1–5 scale.
5. Review date is valid and successfully parsed.

### Usable Volume & Exclusions Breakdown:
- **Total Dataset:** 4,620 raw rows.
- **Out-of-Window Exclusions:** 330 rows (326 JioMart records prior to 14 Aug 2024; 4 Blinkit records prior to 14 Aug 2024).
- **In-Window Quality Exclusions:** 0 rows (zero missing fields, zero blank text, zero invalid ratings in window).
- **Usable Records in Common Window:** **4,290 rows**:
  - **Blinkit (Focal):** 1,376 usable records (138 days span, 139 calendar days; 2024-08-15 to 2024-12-31). Exceeds 500 threshold.
  - **Zepto (Primary Competitor):** 1,740 usable records (139 days span, 140 calendar days; 2024-08-14 to 2024-12-31). Exceeds 500 threshold.
  - **JioMart (Secondary Context):** 1,174 usable records (139 days span, 140 calendar days; 2024-08-14 to 2024-12-31). Exceeds 500 threshold.

> [!CRITICAL]
> **Static Scope Boundary:** The common 4.5-month window is authorized exclusively for a **STATIC complaint-theme and expressed-switching-signal analysis**. It must **NOT** be used to claim temporal trends, annual progress, or seasonal patterns.

---

## 3. Data Provenance, Licensing, & Local Storage Convention

### Provenance Status of Candidate A
- **Verified Repository Facts:** Public GitHub repository (`mdaniq45/E-Commerce-BlinkIt-vs-Zepto-vs-JioMart-Reviews-Analysia`) containing `reviews.csv` (1,898,980 bytes; SHA-256: `5d3bb24ee7185612e66f57cf2e21d99e9d628a15d3d68989b8cf560996e9f138`). 4,620 rows across `rating`, `date`, `review`, and `platform`.
- **Collection Provenance (Reported, Unverified):** The repository README claims the dataset was collected from Google Play reviews. The exact scraping scripts, request parameters, date of capture, and filter queries are not published in the upstream repository and cannot be independently established.
- **Software Licence vs. Third-Party Data Rights:** The upstream repository provides an Apache-2.0 software licence. This licence applies to the author's analysis scripts; it does not grant copyright ownership or clear third-party commercial redistribution rights for scraped customer reviews.
- **Data Reuse Assessment:** Intended use is restricted to local academic and analytical evaluation. Legal reuse and redistribution rights for third-party review text remain **unresolved**; no legal guarantees are provided.
- **Material Reproducibility Limitation:** If the upstream GitHub repository is removed, modified, or made private, independent retrieval of the exact source file depends on cached or archived copies.

### Local Storage & Git Hygiene
- **Raw Data Location:** All raw review files must be stored locally in `data/raw/` (e.g., `data/raw/reviews.csv`).
- **Version Control Policy:** `data/raw/*` is strictly excluded from Git tracking via `.gitignore`. Raw third-party review text bearing user statements is never committed to Git.
- **Aggregate Artifact Retention:** Machine-readable aggregate audit outputs containing no verbatim text or personal data (such as `docs/gates/GATE_0_AUDIT_SUMMARY.json`) are retained in version control.

---

## 4. Data Schema & Required Columns

The review dataset must be a comma-separated values (CSV) file containing the following essential fields:

| Column Name | Data Type | Requirement | Description | Validation Rule |
| :--- | :--- | :--- | :--- | :--- |
| `platform` | String | **Mandatory** | Platform identifier | Case-insensitive normalized to `blinkit`, `zepto`, `jiomart`. Unknown values flagged. |
| `review` | String | **Mandatory** | Verbatim text of customer review | Must be non-null and non-whitespace. Blank/null tracked separately. |
| `rating` | Integer | **Mandatory** | Customer rating on integer scale | Validated strictly against integer range 1 to 5. Non-integers flagged. |
| `date` | String / Date | **Mandatory** | Review submission date | Parseable as date (`%d %B %Y` or ISO). Unparseable dates flagged. |

---

## 5. Metric Boundaries & Statistical Interpretation

To maintain scientific integrity, the project enforces strict definitions across engagement, behavioral, and text-based metrics:

1. **Downloads-to-WAU Ratio (Aggregate Engagement Ratio):**
   - An aggregate engagement ratio reported by external secondary sources (e.g., *The Financial Express*, May 19, 2026: Blinkit 24%, Zepto 23%; an updated Financial Express report dated October 2, 2026 provides updated download and WAU figures).
   - **Boundary:** This ratio represents all-time app downloads converted into weekly active users at an aggregate market level. It is **NOT** a cohort retention rate and does **NOT** establish repeat purchase or retention by individual customers. It must never be used to calibrate cohort-retention models.
2. **Ordering Frequency (Aggregate Utilization):**
   - An aggregate orders-per-user metric as defined by quarterly company disclosures (e.g., Blinkit monthly frequency fell from 3.57 to 3.36 orders/user in FY24–FY25; Instamart fell from 4.22 to 4.01).
   - **Boundary:** Macro platform-level ordering frequency does not establish individual customer retention lifecycles.
3. **Actual Customer Defection / Churn:**
   - The permanent cessation of purchasing by an individual customer.
   - **Boundary:** **Unobserved** in public review datasets. Unavailable without customer-level transaction histories or another valid longitudinal behavioral measure.
4. **Cohort Retention:**
   - Longitudinal repurchasing probability across specific user acquisition cohorts.
   - **Boundary:** **Unavailable** unless an appropriate cohort-level transaction dataset and documented definition are obtained.
5. **Expressed Switching Intention:**
   - A text-based statement in a customer review declaring intent to defect, uninstall, or move to a competitor.
   - **Boundary:** A vocal proxy indicator of customer distress, **not** an observed transaction outcome.
6. **Exploratory Corpus (Non-Representative):**
   - The dataset represents a self-selected sample of public app-store reviews suffering extreme voluntary response negativity bias (over 70% 1-star ratings).
   - **Boundary:** Record-count thresholds (>= 500) demonstrate qualitative failure-theme feasibility. They do **NOT** prove statistical power or population representativeness.

---

## 6. Reproducing the Quantitative Data Audit

The audit can be executed reproducibly on any machine:

### Prerequisites
- Python 3.10+
- `pandas`, `numpy`

### Step-by-Step Execution
1. Obtain candidate `reviews.csv` from Candidate A repository (`mdaniq45/E-Commerce-BlinkIt-vs-Zepto-vs-JioMart-Reviews-Analysia`) and place it at:
   `data/raw/reviews.csv`
2. Verify SHA-256 hash:
   `5d3bb24ee7185612e66f57cf2e21d99e9d628a15d3d68989b8cf560996e9f138`
3. Run the audit script:
   ```bash
   python scripts/audit_data.py --file data/raw/reviews.csv
   ```
4. To run automated tests:
   ```bash
   python -m unittest discover tests
   ```
5. Audit outputs:
   - Console: Comprehensive formatted report detailing disaggregated missingness, boundary counts, rating distributions, and threshold checks.
   - JSON: Machine-readable summary saved to `docs/gates/GATE_0_AUDIT_SUMMARY.json` (containing aggregate statistics, SHA-256, and zero raw text).
