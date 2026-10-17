# GATE 0 CANDIDATE DATASET AUDIT: MENDELEY QUICK-COMMERCE SURVEY (CHANDRA 2026)

**Document Type:** Formal Candidate Dataset Verification & Structural Feasibility Audit  
**Target Dataset:** *A Large-Scale Survey Dataset on Quick-Commerce Adoption, Ordering Patterns, Product Categories and Spending Behaviour among Indian Consumers*  
**Primary Source:** Mendeley Data (`cw88nb7822/1`, DOI: `10.17632/cw88nb7822.1`)  
**Investigated Project Direction:** *Beyond Discounts: Customer Segmentation and Non-Discount Retention Strategy for Indian Quick Commerce, applied to Blinkit*  
**Assigned Role:** Implementation Engineer (operating under the Principal Project Lead)  
**Audit Completion Date:** 2026-10-17  
**Status:** **SUBMITTED FOR PRINCIPAL PROJECT LEAD REVIEW (NON-BINDING EVALUATION)**

---

## 1. Executive Assessment

Following the receipt and extraction of the candidate dataset bundle (`A Large-Scale Survey Dataset on Quick-Commerce Ado.zip`), an independent structural, logical, and provenance audit was performed across `Data.xlsx`, `Code Book.docx`, and `Questionairre.docx`.

### Core Verdict & Recommendation
The candidate survey workbook is **structurally complete, internally consistent, and possesses zero null or out-of-range cells across all 1,263 rows and 130 columns**. It provides rich consumer-level survey data on demographics, ordering frequency, platform awareness/usage, discount dependence, and reasons for platform abandonment.

However, the dataset exhibits **two critical structural and methodological boundaries**:
1. **Generic Category-Level Perceptions (No Platform-Specific Satisfaction):** While the survey identifies which platforms respondents have used (e.g., 577 used Blinkit, 439 Zepto, 430 Instamart), all satisfaction (QA 37–40), operational problems (QA 36), discount sensitivity (QA 28, 29, 47), and choice factors (QA 31, 32) are asked at the general quick-commerce category level. There is **zero platform-specific satisfaction or failure data**. Any application to Blinkit must be framed as a *managerial application of category-level consumer segmentation*, not an empirical audit of Blinkit's proprietary operations.
2. **The 80-Record Skip-Logic Routing:** All 456 respondents who reported their current ordering frequency as "Never" (QA 15 = 1)—which includes **80 previous users** who have ordered in the past—were routed past the satisfaction, problem, and spending modules (QA 16–47). In the workbook, these fields are coded as "Not applicable – never used", causing an information loss regarding their historical service satisfaction while preserving their reasons for current non-use (QA 48) and desired improvements (QA 49).

### Recommendation Submitted to Principal Project Lead
The dataset is **conditionally admissible** for an applied research study on *Customer Segmentation, Discount Dependence, and Non-Discount Retention Priorities in Indian Quick Commerce*, provided the project explicitly respects the boundary between general quick-commerce consumer behavior and firm-specific operational performance.

---

## 2. File Verification & Physical Provenance

The survey bundle was extracted and verified on the local filesystem. All raw data files remain strictly excluded from Git tracking via `.gitignore`.

| File Artifact | File Type | Byte Size | SHA-256 Hash | Repository Status |
| :--- | :--- | :---: | :--- | :--- |
| `A Large-Scale Survey Dataset on Quick-Commerce Ado.zip` | Archive Bundle | 459,941 bytes | `c0ea677124407f634b0b61294cf5814f353649cb7777cbc56d37b4fdb67d8875` | Local only (excluded by `.gitignore`) |
| `data/raw/survey/Data.xlsx` | Excel Workbook | 565,344 bytes | `c6e92099b960f11472558b629e90b2926012061eac45b9051973c8fe79e1a73d` | Local only (excluded by `.gitignore`) |
| `data/raw/survey/Code Book.docx` | Data Codebook | 27,666 bytes | `7c7692b730b5852ee18747b620734b5ada35b9e1a856854118c5a4e017895a23` | Local only (excluded by `.gitignore`) |
| `data/raw/survey/Questionairre.docx` | Survey Instrument | 26,137 bytes | `e5bfe1b1195e1e8c54ff62fe073165657cb1d5288f38a132329024e59b815665` | Local only (excluded by `.gitignore`) |

---

## 3. Academic Provenance & Verification Matrix

The official candidate repository record ([Mendeley Data `cw88nb7822/1`](https://data.mendeley.com/datasets/cw88nb7822/1)) and associated documents were systematically audited.

| Provenance Dimension | Official Evidence & Document Findings | Classification Status |
| :--- | :--- | :--- |
| **Author Identity & Affiliation** | Contributor on Mendeley is Ashish Chandra. The questionnaire preamble explicitly identifies the researcher as **Dr. Ashish Chandra, Assistant Professor at Amity Business School, Amity University, Lucknow Campus, Uttar Pradesh, India**. | **VERIFIED** |
| **Associated Research Article / DOI** | Mendeley Data DOI is `10.17632/cw88nb7822.1` (Version 1, deposited 14 October 2026). No associated peer-reviewed paper (e.g. *Data in Brief*), preprint, or journal publication is cited or indexed. | **UNVERIFIED / ABSENT** |
| **Achieved Sample Size** | The workbook contains 1,263 data rows. However, no raw server timestamps, survey platform session IDs, IP hashes, or survey-tool audit trails are included. | **PARTIALLY VERIFIED** |
| **Recruitment & Sampling Frame** | Neither the Mendeley entry nor the Word documents specify the sampling methodology (e.g., convenience, snowball, commercial consumer panel, or academic intercept). | **UNVERIFIED** |
| **Fieldwork Dates & Duration** | The dataset contains no survey submission timestamp column. Fieldwork start and end dates are unrecorded. The only verified date is the Mendeley publication date (14 October 2026). | **UNVERIFIED / ABSENT** |
| **Target Population & Geography** | Captures 6 geographic regions across India (North, South, East, West, Central, North-East) and 6 residential tiers (Metro to Rural). Target population is Indian adult consumers. | **PARTIALLY VERIFIED** |
| **Data Collection Channel** | Questionnaire structure reflects a digital, self-administered survey ("Please select the option..."). Specific digital distribution channels are not documented. | **UNVERIFIED** |
| **Consent & Ethical Review** | Questionnaire preamble states voluntary participation, academic purpose, and anonymity. No formal Institutional Review Board (IRB) or Ethics Committee protocol number is cited. | **PARTIALLY VERIFIED** |
| **Data Cleaning & Exclusion Protocol** | Zero blank cells exist in 164,190 cells. No screening log, dropout counts, completion time filters, or straight-liner exclusion criteria are documented. | **UNVERIFIED** |
| **Declared Licence** | Mendeley Data listing declares Creative Commons Attribution 4.0 International (**CC BY 4.0**). No conflicting proprietary restrictions appear in the documents. | **VERIFIED** |

---

## 4. Independent Structural & Data Quality Audit

Programmatic audit was executed via [`scripts/audit_survey_data.py`](file:///e:/FDA/Beyond_Discounts/scripts/audit_survey_data.py) and validated by [`tests/test_audit_survey_data.py`](file:///e:/FDA/Beyond_Discounts/tests/test_audit_survey_data.py).

### 4.1 Dimensions and Completeness
- **Worksheet Name:** Single sheet named `Data`.
- **Dimensions:** 1,263 data rows $\times$ 130 columns (excluding header row).
- **Missing / Blank Cells:** **0 missing cells** (100.0% completeness across all 164,190 cell coordinates).
- **Full Duplicate Rows:** **0 full duplicate rows** across the complete 130-column vector.
- **Demographic Duplication:** Only 5 rows share identical demographic profiles (QA 1–8) out of 1,263 ($< 0.4\%$).

### 4.2 Header Whitespace Anomalies
The workbook contains leading or trailing whitespaces in **5 column headers**:
1. `' First Trial Reason'` (leading space; QA 14)
2. `' Order Frequency'` (leading space; QA 15)
3. `' Factor Low Delivery Fee'` (leading space; QA 31)
4. `'Fast Delivery Importance '` (trailing space; QA 35)
5. `' Problem No Major Problem'` (leading space; QA 36)

*Remediation Rule:* The audit script sanitizes headers using `.str.strip()` while preserving the raw headers in documentation.

### 4.3 Coding Conformance & Constraint Checks
1. **Multi-Select Binary Dummy Columns:** All indicator variables across QA 11 (Awareness), QA 12 (Usage), QA 18 (Usual Reasons), QA 22 (Categories Purchased), QA 24 (Physical Preference), QA 31 (Choice Factors), QA 36 (Problems Experienced), and QA 48 (Non-Use Reasons) strictly contain only binary integer codes: $\{0, 1\}$.
2. **Single-Select Range Conformance:** Every single-select categorical and ordinal variable conforms strictly to the numerical codes specified in `Code Book.docx`. Zero out-of-range values exist.
3. **Mutually Exclusive Logical Checks:**
   - `Aware None == 1` vs. named platform awareness: **0 conflicts**.
   - `Used Never Used == 1` vs. named platform usage: **0 conflicts**.
   - `Ever Ordered == 0` vs. named platform usage: **0 conflicts**.
   - `Problem No Major Problem == 1` vs. specific problems reported: **0 conflicts**.

---

## 5. Investigation of the 80-Record Usage-Status Issue

### 5.1 Subgroup Triangulation
Cross-tabulating **QA 10** (*Ever Ordered through Quick Commerce*) against **QA 15** (*Current Order Frequency*) resolves the exact consumer structure:

| Respondent Subgroup | QA 10: Ever Ordered | QA 15: Current Frequency | Respondent Count ($n$) | % of Survey ($N=1,263$) |
| :--- | :---: | :---: | :---: | :---: |
| **Never Users** | `0` (No) | `1` (Never) | **376** | 29.8% |
| **Previous Users (Lapsed / Churned)** | `1` (Yes) | `1` (Never) | **80** | **6.3%** |
| **Current Active Users** | `1` (Yes) | `2..7` (Active) | **807** | 63.9% |
| *Inconsistent / Error Responses* | `0` (No) | `2..7` (Active) | **0** | 0.0% |
| **Total Survey Respondents** | — | — | **1,263** | **100.0%** |

### 5.2 Downstream Skip-Logic Routing & Information Loss
In the online survey instrument, respondents answering QA 15 = 1 (*Never*) were branched directly to QA 48 (*Reasons for not currently using*) and QA 49 (*Desired improvement*). 

Consequently, for all 456 respondents who currently never order (including the **80 previous users**), questions QA 16 through QA 47 were skipped and populated with code `6`, `7`, `8`, or `9` labelled in the codebook as *"Not applicable – never used"*:
- **Service Satisfaction (QA 37–40):** All 80 previous users are coded `6` (*Not applicable – never used*). Their historical satisfaction levels with quick commerce are unobserved.
- **Operational Problems Experienced (QA 36):** All 80 previous users have `Problem Not Applicable = 1` and 0 on all specific failure modes.
- **Discount Sensitivity (QA 28, 29, 47):** All 80 previous users are coded `6` (*Not applicable – never used*).
- **Basket Characteristics & Ordering Habits (QA 16–25):** All 80 previous users are coded as not applicable.

### 5.3 Substantive Evidence Preserved for Previous Users
While intermediate service-satisfaction modules were skipped, the 80 previous users provided substantive data across several critical questions:
1. **Platforms Personally Used (QA 12):**
   - Blinkit: **52 users (65.0%)**
   - Zepto: **37 users (46.2%)**
   - Swiggy Instamart: **33 users (41.2%)**
   - BigBasket BBNow: **29 users (36.2%)**
   - Amazon Rapid: **16 users (20.0%)**
   - Flipkart Minutes: **14 users (17.5%)**
2. **Usage Duration (QA 13):**
   - $> 2$ years: 28 (35.0%) | 1–2 years: 27 (33.8%) | 7–12 months: 11 (13.8%) | 3–6 months: 7 (8.8%) | $< 3$ months: 7 (8.8%). None answered "never used".
3. **First Trial Motivation (QA 14):**
   - Faster delivery (25.0%), Convenience (21.2%), Urgent need (15.0%), Discounts/offers (15.0%), Limited time (11.2%), Ads (11.2%).
4. **Reasons for Not Currently Using Quick Commerce (QA 48):**
   - Prefer shopping in physical stores: **41.2% (33)**
   - Prices are too high: **38.8% (31)**
   - Prefer to inspect products before purchase: **35.0% (28)**
   - Do not need rapid delivery: **28.7% (23)**
   - Delivery charges / fees: **27.5% (22)**
   - Service not available in my area: **27.5% (22)**
   - Do not trust product quality: **25.0% (20)**
   - Privacy / digital payment concerns: **22.5% (18)**
   - Concern about excessive / impulsive spending: **20.0% (16)**
   - Unfamiliar with the apps: **18.8% (15)**
   *(All 80 correctly have `Reason Not Applicable Current User = 0`)*.
5. **Future Usage Probability (QA 46):**
   - Very unlikely: 18.8% (15) | Unlikely: 30.0% (24) | Not sure: 25.0% (20) | Likely: 23.8% (19) | Very likely: 2.5% (2).
6. **Desired Improvement to Increase Use (QA 49):**
   - Lower / no delivery fees: 18.8% (15) | Lower prices: 18.8% (15) | Reliable availability: 10.0% (8) | Wider range: 8.8% (7) | Faster delivery: 8.8% (7) | Better quality: 8.8% (7) | More discounts: 8.8% (7) | Customer service / refunds: 7.5% (6).

---

## 6. Available vs. Unavailable CRM Outcome Measures

| Analytical Dimension | Available Measures in Survey Dataset | Strictly Unavailable / Unobserved Measures |
| :--- | :--- | :--- |
| **Customer Retention & Churn** | Stated future usage likelihood in next 3 months (QA 46); stated willingness to continue if discounts reduced (QA 47); reasons for currently not ordering (QA 48). | **Actual customer defection / churn logs; actual longitudinal repeat purchase transactions; cohort retention curves.** |
| **Discount Dependence** | Frequency of discount-induced overspending (QA 28); threshold extra item addition (QA 29); price vs. speed choice factor (QA 31, 32); post-discount continuation (QA 47). | **Transaction-level discount elasticity; customer margin / wallet-share data; coupon redemption transaction history.** |
| **Customer Segmentation** | Demographic variables (QA 1–8); ordering frequency (QA 15); basket size (QA 19); monthly spend tier (QA 26); impulsive buying propensity (QA 21, 44); product category mix (QA 22, 23). | **Customer lifetime value (CLV); behavioral RFM (Recency, Frequency, Monetary) metrics from real store logs.** |
| **Platform-Specific Performance** | Binary awareness (QA 11) and historical usage (QA 12) across Blinkit, Zepto, Instamart, BigBasket, Flipkart, Amazon. | **Platform-specific satisfaction; platform-specific service failure rates; platform-specific NPS or brand equity.** |
| **Service Recovery Impact** | Desired improvement priorities (QA 49); past operational problem frequencies across the category (QA 36). | **Empirical causal retention uplift from service recovery interventions; measured pre/post A/B test results.** |

---

## 7. Project Fit Assessment

### 7.1 Proposed Research Reframing
*Preliminary Proposed Direction:* **"Beyond Discounts: Customer Segmentation and Non-Discount Retention Strategy for Indian Quick Commerce, applied to Blinkit."**

### 7.2 Legitimate Research Scope
The survey dataset **strongly supports**:
1. **Consumer Segmentation in Indian Quick Commerce:** Unsupervised clustering (e.g., $k$-means, latent class analysis) combining discount sensitivity (QA 28, 29, 47), basket economics (QA 19, 25, 26), product categories (QA 22, 23), and ordering frequency (QA 15) to identify distinct shopper personas (e.g., *Discount-Dependent Transactors*, *Convenience-First Regulars*, *Emergency Top-Up Shoppers*, *Price-Sensitive Physical Loyalists*).
2. **Analysis of Lapsed Consumer Drivers:** Comparing previous users ($n=80$) and never-users ($n=376$) against current active users ($n=807$) using logistic regression to identify primary drivers of platform cessation (e.g., fees, prices, product inspection preferences).
3. **Designing Non-Discount Retention Levers:** Utilizing QA 49 improvement preferences and QA 31/32 choice factors to formulate service-level CRM retention playbooks (e.g. delivery fee restructuring, product freshness guarantees, availability assurance).

### 7.3 Methodological Boundaries & Prohibitions
To preserve scientific integrity:
- **No Firm-Specific Imputation:** The project must **not** claim that Blinkit users are more or less satisfied than Zepto users based on generic QA 37–40 ratings. Blinkit recommendations must be framed explicitly as an *applied business case demonstration* for the market leader.
- **No Causal Uplift Claims:** Cross-sectional survey data cannot prove that introducing a non-discount retention policy will increase customer retention by $X\%$.
- **No Claim of Statistical Population Representativeness:** While geographically diverse, the absence of documented random sampling requires treating the sample as a non-probability convenience/purposive sample.

---

## 8. Risks Affecting Academic Credibility

1. **Misattributing Category Satisfaction to Blinkit:** Presenting generic quick-commerce satisfaction scores as Blinkit's operational scorecard would be academically invalid.
2. **Conflating Stated Intention with Behavioral Churn:** Stated intent (QA 46/47) reflects perception; treating it as verified customer attrition violates empirical standards.
3. **Mislabeled "Never-Used" Codes:** Treating the 80 previous users as non-users in satisfaction analyses would distort churned customer experiences.
4. **Undocumented Collection Dates:** Inability to pinpoint the exact fieldwork window precludes seasonal or temporal contextualization.

---

## 9. Recommendation Submitted to the Principal Project Lead

The Implementation Engineer submits the following recommendation for the Principal Project Lead's binding determination:

- **Recommended Scope Decision:** **ACCEPT CANDIDATE SURVEY FOR RE-FRAMED SCOPE (CONDITIONAL SCOPE BOUNDARY)**
- **Required Framing:**
  - The project title and research questions must explicitly state that customer segmentation and retention strategies are analyzed at the **Indian quick-commerce category level**, with Blinkit utilized as the **primary applied business context**.
  - Public review data (Candidate A, 4,290 common-window records) may be retained as complementary qualitative failure-evidence or superseded by the structured survey dataset, subject to the Principal Lead's strategic architecture.
- **Gate Boundary Confirmation:** Execution is strictly halted at Gate 0. No exploratory segmentation modeling, predictive analytics, or dashboard development will commence without the Principal Project Lead's formal approval.
