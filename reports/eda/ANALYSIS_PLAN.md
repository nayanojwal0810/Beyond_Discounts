# Gate 1A Analysis Plan: Exploratory Data Analysis & Feasibility Roadmap

**Canonical Project Title:** Beyond Discounts: Customer Segmentation and Retention Strategy for Indian Quick Commerce  
**Phase:** Gate 1A — Exploratory Data Analysis & Customer Segmentation Feasibility  
**Dataset:** `data/raw/survey/Data.xlsx` (Worksheet `Data`, 1,263 respondents × 130 features)  
**Governing Documents:** [`VARIABLE_REGISTER.md`](VARIABLE_REGISTER.md), [`GATE_0_DECISION_LOG.md`](../../docs/gates/GATE_0_DECISION_LOG.md)  
**Assigned Role:** Implementation Worker (under Principal Project Lead)  

---

## 1. Executive Structure of the Analysis Plan

This analysis plan establishes a clear, rigorous demarcation between:
1. **Descriptive Evidence:** Observable, empirical facts directly reproduced from the survey dataset without inferential overreach.
2. **Exploratory Associations:** Bivariate cross-tabulations, rank correlations, and statistical association tests examining relationships among variables.
3. **Hypotheses for Further Investigation:** Formal analytical propositions to be tested during subsequent feature engineering and modeling phases.
4. **Decisions Requiring Principal Approval:** Methodological choices that cannot be finalized by the implementation worker.

---

## 2. Descriptive Evidence to Establish in Gate 1A

The EDA pipeline must reproducibly compute and report the following empirical baselines:

### A. Dataset Quality & Routing Baselines
- Dimension verification: $1,263$ rows $\times 130$ columns.
- Missingness profile: Confirm $0$ physical nulls (`pd.isna`) across the entire matrix.
- Verification of subgroup distributions:
  * Never-Users: $n = 376$ ($29.77\%$)
  * Previous Users (no current orders): $n = 80$ ($6.33\%$)
  * Current Active Users: $n = 807$ ($63.89\%$)
- Questionnaire routing audits:
  * QA 47: Exactly 807 current users in $\{1..5\}$, exactly 456 non-current users coded 6.
  * QA 48: Exactly 456 non-current users reporting reasons, 807 current users holding skip flag 11.
  * QA 46 & QA 49: Universal coverage ($1,263$ substantive responses).
  * QA 26: $456$ respondents at Code 1 (₹0 monthly spend).

### B. Demographic Sample Profile
- Age group distribution (QA 1), gender composition (QA 2), education (QA 3), occupational split (QA 4).
- Monthly personal income (QA 5), area of residence tier (QA 6), regional footprint (QA 7), household size (QA 8).
- Explicit recognition that this sample represents an exploratory cross-sectional sample, not a nationally representative census.

### C. Usage & Shopping Behavior Landscape
- Platform awareness (QA 11) and historical trial/usage footprint (QA 12) across Blinkit, Zepto, Swiggy Instamart, BigBasket, Flipkart, Amazon.
- Primary order frequency (QA 15) and tenure duration (QA 13).
- Shopping basket metrics: Items per order (QA 19), spend per order (QA 25), total monthly spend (QA 26).
- Product category penetration (QA 22) and primary category attachment (QA 23).
- Offline channel resilience: Product categories preferred in physical stores (QA 24).

### D. Discount Sensitivity Baseline (QA 47)
- Response distribution among the 807 current active users:
  * Code 1 (Definitely no): Count, percentage.
  * Code 2 (Probably no): Count, percentage.
  * Code 3 (Not sure): Count, percentage.
  * Code 4 (Probably yes): Count, percentage.
  * Code 5 (Definitely yes): Count, percentage.
- Summary metrics: Mean, standard deviation, median, interquartile range (IQR).
- Distribution across derived resilience tiers: Discount-Sensitive (Codes 1–2), Uncertain (Code 3), Discount-Resilient (Codes 4–5).

### E. Future Intention (QA 46) & Non-Use Barriers (QA 48)
- QA 46 distribution across the 3 subgroups (Never, Previous, Current).
- QA 48 barrier prevalence comparison between Never-Users ($n=376$) and Previous Users ($n=80$).
- QA 49 preferred improvement distribution overall and by subgroup.

---

## 3. Exploratory Associations to Quantify

To investigate customer differentiation, the EDA pipeline evaluates the following empirical relationships:

| Target Association | Variable Pair | Analytical Technique | Motivation / Research Purpose |
| :--- | :--- | :--- | :--- |
| **Discount Resilience vs Order Frequency** | QA 47 (1–5) $\times$ QA 15 (Frequency tier) | Spearman rank correlation ($\rho$), Kruskal-Wallis $H$-test, Chi-square test of independence ($\chi^2$) | Do frequent quick-commerce buyers exhibit higher or lower discount dependency than occasional buyers? |
| **Discount Resilience vs Monthly Spend** | QA 47 (1–5) $\times$ QA 26 (Monthly spend tier) | Spearman $\rho$, Jonckheere-Terpstra / ANOVA, cross-tabulation | Do high-spending households continue ordering regardless of discounts? |
| **Discount Resilience vs Deal Seeking Habits** | QA 47 $\times$ QA 28 (Discount overspend) & QA 29 (Threshold items) | Spearman $\rho$, Goodman-Kruskal $\gamma$ | Are consumers who build baskets to meet discount thresholds the most discount-sensitive? |
| **Discount Resilience vs Multi-Platform Usage** | QA 47 $\times$ Count of platforms used (QA 12) | Pearson/Spearman $r$, Welch's $t$-test | Are multi-homers more deal-sensitive than single-platform loyalists? |
| **Discount Resilience vs Service Satisfaction** | QA 47 $\times$ Composite satisfaction (QA 37–40) | Pearson $r$, OLS regression slope | Does high service/speed satisfaction buffer against discount reductions? |
| **Future Intent vs Subgroups** | QA 46 $\times$ User Subgroup (Never, Prev, Current) | Mann-Whitney $U$ test, ordinal logistic regression | Quantify the intention gap between non-users, lapsed users, and active shoppers. |
| **Non-Use Barriers: Never vs Previous** | QA 48 items $\times$ Subgroup (Never $n=376$ vs Prev $n=80$) | Two-sample proportion $z$-tests, Fisher's exact test | Do lapsed users cite quality/service friction while never-users cite awareness/need? |

---

## 4. Hypotheses for Further Investigation (Post-EDA)

The following hypotheses are formulated based on industry literature and survey structure, to be formally tested in Gate 1B (Feature Engineering) and Gate 2 (Segmentation):

1. **Hypothesis 1 (Habitual Inelasticity):**  
   *Current users with high order frequency (weekly+) and integration into household routines (QA 43 Codes 1–2) exhibit significantly higher discount resilience (QA 47 $\ge 4$) than low-frequency occasional top-up shoppers.*

2. **Hypothesis 2 (Convenience-Driven Insulation):**  
   *Consumers who cite delivery speed and urgent need as their primary choice factors (QA 31/32) are less discount-sensitive than consumers who cite promotional coupons and low delivery fees.*

3. **Hypothesis 3 (Category Basket Differentiation):**  
   *Consumers whose primary category is fresh produce/dairy (daily essentials) have higher repeat-order stability but stricter quality requirements than consumers ordering packaged snacks/beverages.*

4. **Hypothesis 4 (Lapsed User Reactivation vs Non-User Adoption):**  
   *Previous users ($n=80$) are primarily driven away by perceived pricing/fee friction or unmet expectations, whereas never-users ($n=376$) are held back by habit inertia and preference for physical inspection.*

---

## 5. Decisions Requiring Principal Project Lead Approval

The Implementation Worker explicitly flags the following methodological questions for review and direction by the Principal Project Lead:

1. **Clustering Strategy & Algorithm Family:**
   - Option A: Latent Class Analysis (LCA) / Mixture Models (ideal for mixed categorical/ordinal survey data).
   - Option B: Factor Analysis of Mixed Data (FAMD) followed by $k$-Means or Hierarchical Agglomerative Clustering (HAC).
   - Option C: Two-step partitioning (e.g., segmenting by behavioral engagement first, then clustering on attitudes within active users).
   - *Status:* **Awaiting Principal Project Lead Directive.**

2. **Treatment of Lapsed Users ($n=80$) in Segmentation:**
   - Option A: Segment all 1,263 respondents in an all-inclusive segmentation model.
   - Option B: Conduct segmentation primarily on the 807 current active users (who have complete behavioral, satisfaction, and discount resilience data), while profiling previous users ($n=80$) and never-users ($n=376$) as distinct strategic macro-segments.
   - *Worker Recommendation:* Option B is strongly recommended to avoid sparsity artifacts and artificial clustering driven by skip codes.

3. **Handling of QA 47 Scale in Downstream Modeling:**
   - Option A: Continuous / numeric treatement (1 to 5).
   - Option B: Binary classification target (0 = Sensitive/Uncertain $\le 3$, 1 = Resilient $\ge 4$).
   - Option C: 3-tier ordinal grouping (Sensitive 1–2, Neutral 3, Resilient 4–5).

4. **Feature Selection Thresholds:**
   - Minimum variance filter and multicollinearity exclusion rules for multi-response items (e.g., categories with $<5\%$ endorsement).
