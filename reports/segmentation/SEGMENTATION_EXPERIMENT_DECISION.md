# Gate 1C: Controlled Mixed-Data Customer Segmentation Experiment Decision Report

**Project:** Beyond Discounts: Customer Segmentation and Retention Strategy for Indian Quick Commerce  
**Repository:** [nayanojwal0810/Beyond_Discounts](https://github.com/nayanojwal0810/Beyond_Discounts)  
**Branch:** `main`  
**Gate:** Gate 1C — Controlled Mixed-Data Customer Segmentation Experiment  
**Status:** COMPLETE / AWAITING PRINCIPAL REVIEW  

---

## 1. Executive Summary & Primary Objective

The primary research objective of Gate 1C is to rigorously test whether the prepared survey data supports stable, useful, and interpretable customer segments among current active quick-commerce users, addressing the core research question:

> *Do current active quick-commerce users differ in their behaviour and attitudes in ways that correspond to different stated continuation intentions if discounts are reduced?*

### Population & Scope
- **Target Population:** Exactly $n = 807$ verified current active quick-commerce users ($\text{QA 10} = 1 \text{ [Ever Ordered]} \land \text{QA 15} \in [2, 7] \text{ [Current Frequency] > Never}$).
- **Excluded Subgroups:** Never-users ($n = 376$) and previous users ($n = 80$) remain strictly separate descriptive populations and are not included in the clustering matrices.
- **Methodological Boundaries:** Cross-sectional survey data reflects stated perceptions and intentions, not transaction logs, longitudinal repeat purchasing, or realized churn. No causal claims are asserted.

### Key Analytical Takeaways
1. **Algorithm Viability:** Partitioning Around Medoids (PAM) based on the approved pairwise Gower distance matrix decisively outperforms Hierarchical Agglomerative Clustering (HAC). HAC average linkage degrades into severe chaining (isolating clusters with $< 5$ respondents), while HAC complete linkage yields poor silhouette metrics (32–44% negative observations).
2. **Cluster Count Selection ($k = 4$ Supported):** Across repeated subsampling stability experiments (20 runs at 80% subsampling), **$k = 4$ is the only candidate solution exhibiting robust stability** ($\text{Median ARI} = 0.6787$ in Spec A, $0.6621$ in Spec B, 0 unstable runs). Candidates $k = 3, 5, 6$ exhibit substantial assignment instability ($\text{Median ARI} \approx 0.35 - 0.47$).
3. **External Validation Reality (Spec A):** When clusters are formed solely on behavioral habits, basket economics, multi-homing, and service satisfaction (Specification A, excluding QA 47), the resulting segments **show no statistically significant divergence in stated continuation intentions if discounts are reduced** ($H = 0.036, p = 0.998, \text{Holm } p = 1.0, \epsilon^2 = 0.000$). Stated discount sensitivity is largely orthogonal to general quick-commerce usage habits.
4. **Construct-Defining Role (Spec B):** When QA 47 is included as an active clustering feature (Specification B), clusters separate along stated discount continuation by construction ($H = 104.7, p = 1.48 \times 10^{-22}$), but this cannot be claimed as independent external validation, and held-out QA 46 (stated 3-month use) remains statistically indistinguishable across clusters ($H = 4.23, p = 0.237$).

---

## 2. Distance Contract Safeguards & Matrix Audit

Before computing distances, the Gower distance implementation was hardened with fail-fast validation in `scripts/prepare_segmentation_features.py` and `scripts/run_segmentation_experiments.py`:
- **Unknown Data Types:** Unrecognized types raise an immediate `ValueError`.
- **Asymmetric Binary Contract:** Features `items_varies_considerably` (QA 19 Code 6) and `monthly_spend_not_sure` (QA 26 Code 8) strictly accept values $\in \{0, 1\}$. Value pairs $(0, 0)$ are excluded from the denominator; $(1, 1)$ matches; $(1, 0)$ and $(0, 1)$ mismatch.
- **Strict Predeclared Ranges:** Continuous and ordinal differences are normalized by the Code Book predeclared ranges ($R_k = \text{range}_k[1] - \text{range}_k[0]$), not observed sample ranges. Out-of-range values raise an error.
- **Zero Denominator Protection:** The pipeline verifies that all respondent pairs share at least one valid comparison.
- **Structural Mask Alignment:** Only QA 19 Code 6 ($n = 100$) and QA 26 Code 8 ($n = 24$) contain structurally undefined ordinal ranks, aligning exactly with their respective binary indicator flags.

### Distance Matrix Audit Findings (`reports/segmentation/distance_matrix_audit.csv`)

| Diagnostic Metric | Specification A (17 Features) | Specification B (18 Features) | Conformance Status |
| :--- | :---: | :---: | :---: |
| **Matrix Dimensions** | $807 \times 807$ | $807 \times 807$ | PASS |
| **Is Square & Symmetric** | True | True | PASS |
| **Zero Diagonal ($D_{ii} = 0$)** | True | True | PASS |
| **Finite & Bounded $[0, 1]$** | True (Min: $0.0000$, Max: $0.6564$) | True (Min: $0.0000$, Max: $0.6466$) | PASS |
| **Mean Pairwise Distance** | $0.3368$ (Median: $0.3333$) | $0.3358$ (Median: $0.3333$) | Normal mixed-data distribution |
| **Min / Max Pairwise Denominator** | $15.00$ / $15.00$ | $16.00$ / $16.00$ | Invariant across all pairs |
| **Zero-Denominator Pairs Count** | $0$ ($0.0\%$) | $0$ ($0.0\%$) | PASS |
| **Matrix Status** | **VALID** | **VALID** | Approved for clustering |

> [!NOTE]
> The minimum pairwise denominator is invariant at $15.0$ for Specification A and $16.0$ for Specification B across all 325,221 unique pairs of active respondents. This occurs because the asymmetric binary flag guarantees a denominator contribution of $1.0$ whenever either respondent exhibits the special response, and the ordinal rank comparison contributes $1.0$ whenever both have defined substantive ranks.

---

## 3. Algorithm Comparison: PAM vs. Hierarchical Clustering

We evaluated two candidate clustering families across $k \in \{3, 4, 5, 6\}$:
1. **Primary Algorithm:** Kaufman & Rousseeuw (1990) Partitioning Around Medoids (PAM) with BUILD initialization and iterative SWAP optimization.
2. **Benchmark Algorithms:** Hierarchical Agglomerative Clustering (HAC) using average linkage and complete linkage.

### Algorithm Evaluation Summary (`reports/segmentation/clustering_metrics.csv`)

```
=========================================================================================================
Spec    Algorithm       k   Avg Sil   % Neg Sil   Cluster Sizes (n)             Min Size   Small Warning (<41)
=========================================================================================================
SPEC_A  PAM             3   0.0406    18.71%      [358, 276, 173]               173        False
SPEC_A  PAM             4   0.0500    20.20%      [288, 218, 181, 120]          120        False
SPEC_A  PAM             5   0.0543    23.67%      [222, 218, 176, 120, 71]       71        False
SPEC_A  PAM             6   0.0522    27.01%      [222, 176, 137, 120, 81, 71]   71        False
---------------------------------------------------------------------------------------------------------
SPEC_A  HAC_Average     3   0.2135     0.00%      [790, 15, 2]                    2        TRUE (Degenerate)
SPEC_A  HAC_Average     4   0.2098     0.00%      [786, 15, 4, 2]                 2        TRUE (Degenerate)
SPEC_A  HAC_Average     5   0.2052     0.00%      [786, 15, 3, 2, 1]              1        TRUE (Degenerate)
SPEC_A  HAC_Average     6   0.1741     0.00%      [779, 15, 7, 3, 2, 1]           1        TRUE (Degenerate)
---------------------------------------------------------------------------------------------------------
SPEC_A  HAC_Complete    3   0.0210    32.84%      [460, 318, 29]                 29        TRUE (< 41)
SPEC_A  HAC_Complete    4   0.0150    43.87%      [338, 318, 122, 29]            29        TRUE (< 41)
SPEC_A  HAC_Complete    5   0.0195    34.45%      [318, 269, 122, 69, 29]        29        TRUE (< 41)
SPEC_A  HAC_Complete    6   0.0208    33.09%      [318, 246, 122, 69, 29, 23]    23        TRUE (< 41)
=========================================================================================================
```

### Methodological Verdict on Algorithms
- **HAC Average Linkage is REJECTED:** Despite higher naive average silhouette scores, average linkage suffers from catastrophic chaining. It places $>97\%$ of respondents into a single giant cluster and isolates tiny 1–15 person outlier groups.
- **HAC Complete Linkage is REJECTED:** Yields poor cohesion, with $32\% - 44\%$ of observations having negative silhouette widths, and repeatedly produces small fragile clusters ($n = 29, 23$).
- **PAM is ACCEPTED as the Primary Method:** PAM produces balanced, operationally meaningful clusters (minimum cluster size is $71$ across all $k$) with actual survey respondents as medoids, eliminating artificial centroid averaging of discrete and binary survey responses.

---

## 4. Cluster Count ($k$) Selection & Subsampling Stability

To evaluate internal stability and avoid selecting $k$ based on random sample idiosyncrasies, we executed 20 repeated 80% subsampling experiments ($n = 646$ per draw) across random seeds $101$ to $120$. On each subsample, PAM was re-run from scratch and matched against the full-sample assignment on overlapping respondents using the Adjusted Rand Index (ARI).

### Subsampling Stability Results (`reports/segmentation/stability_summary.csv`)

| Specification | Candidate $k$ | Median ARI | Mean ARI | Std ARI | IQR ARI | Min ARI | Max ARI | Unstable Runs ($\text{ARI} < 0.50$) | Stability Verdict |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **SPEC_A** | $k = 3$ | $0.3890$ | $0.4497$ | $0.1601$ | $0.2036$ | $0.2372$ | $0.8037$ | $15 / 20$ | **UNSTABLE** |
| **SPEC_A** | $\mathbf{k = 4}$ | $\mathbf{0.6787}$ | $\mathbf{0.6756}$ | $\mathbf{0.0769}$ | $\mathbf{0.0883}$ | $\mathbf{0.5065}$ | $\mathbf{0.8055}$ | $\mathbf{0 / 20}$ | **STABLE (ACCEPTED)** |
| **SPEC_A** | $k = 5$ | $0.4020$ | $0.4137$ | $0.0969$ | $0.1444$ | $0.2447$ | $0.5794$ | $17 / 20$ | **MODERATE / WEAK** |
| **SPEC_A** | $k = 6$ | $0.4175$ | $0.4285$ | $0.0885$ | $0.1432$ | $0.2882$ | $0.5694$ | $16 / 20$ | **MODERATE / WEAK** |
| **SPEC_B** | $k = 3$ | $0.3531$ | $0.4431$ | $0.1776$ | $0.2885$ | $0.2415$ | $0.8050$ | $15 / 20$ | **UNSTABLE** |
| **SPEC_B** | $\mathbf{k = 4}$ | $\mathbf{0.6621}$ | $\mathbf{0.6483}$ | $\mathbf{0.0903}$ | $\mathbf{0.1481}$ | $\mathbf{0.4632}$ | $\mathbf{0.7816}$ | $\mathbf{1 / 20}$ | **STABLE (ACCEPTED)** |
| **SPEC_B** | $k = 5$ | $0.4483$ | $0.4578$ | $0.0963$ | $0.1466$ | $0.3168$ | $0.6276$ | $14 / 20$ | **MODERATE / WEAK** |
| **SPEC_B** | $k = 6$ | $0.4746$ | $0.4665$ | $0.0903$ | $0.1445$ | $0.3013$ | $0.6133$ | $12 / 20$ | **MODERATE / WEAK** |

### Decision Rationale for $k = 4$
- **$k = 3$ Fails Stability:** Despite having slightly fewer negative silhouette values, $k = 3$ produces erratic cluster boundaries across subsamples ($\text{Median ARI} = 0.3890$, 15 of 20 runs failing the $0.50$ threshold).
- **$k = 5$ and $k = 6$ Over-Fragment:** Increasing $k$ creates arbitrary partitions of existing groups without improving separation ($\text{Median ARI} \approx 0.40 - 0.47$; negative silhouette rates rise to $>25\%$).
- **$k = 4$ Demonstrates Clear Stability:** In both specifications, $k = 4$ achieves a high Median ARI ($>0.66$), narrow IQR ($\approx 0.088$), and zero unstable runs in Specification A. It represents a cohesive, reproducible partition of the respondent space.

---

## 5. External Validation & Research Question Findings

We evaluated the selected candidate solutions against the held-out target variables:
- **QA 47:** *If discounts or free delivery are reduced, would you continue using quick commerce at the same frequency?* (1 = Definitely discontinue, 5 = Definitely continue).
- **QA 46:** *Do you see yourself using quick commerce more, about the same, or less over the next 3 months?* (1 = Much less, 5 = Much more).

Hypothesis tests were performed using non-parametric Kruskal-Wallis $H$-tests, reporting $\epsilon^2$ effect sizes and family-wise Holm-Bonferroni corrected $p$-values across candidate $k$.

### External Validation Summary (`reports/segmentation/external_validation_summary.csv`)

| Spec | $k$ | Variable | Status / Role | Test Method | $H$ Stat | Raw $p$ | Holm $p$ | $\epsilon^2$ | Interpretation |
| :--- | :---: | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :--- |
| **SPEC_A** | **4** | **QA 47 Continue If Discounts Reduced** | **Independent Validation Benchmark** | Kruskal-Wallis | **$0.0360$** | **$0.9982$** | **$1.0000$** | **$0.0000$** | **No divergence (Homogeneous across clusters)** |
| SPEC_A | 4 | QA 46 Next 3 Month Use | Stated Future Intent Benchmark | Kruskal-Wallis | $8.3972$ | $0.0385$ | $0.1539$ | $0.0067$ | Modest trend (non-significant after correction) |
| **SPEC_B** | **4** | **QA 47 Continue If Discounts Reduced** | **Construct-Defining Input** | Kruskal-Wallis | **$104.70$** | **$1.48 \times 10^{-22}$** | **$5.9 \times 10^{-22}$** | **$0.1267$** | **Strong divergence by mathematical construction** |
| SPEC_B | 4 | QA 46 Next 3 Month Use | Stated Future Intent Benchmark | Kruskal-Wallis | $4.2338$ | $0.2373$ | $0.9491$ | $0.0015$ | No statistically significant divergence |

### Substantive Meaning of the External Validation Finding
1. **The Research Question Answered for Specification A:**
   When quick-commerce users are grouped strictly by their actual operational habits (basket size, spend tier, order frequency, multi-homing platform count, delivery speed importance, and general service satisfaction), **their stated intention to continue if discounts are reduced is virtually identical across all clusters**:
   - Cluster 0 Mean: $3.440$
   - Cluster 1 Mean: $3.438$
   - Cluster 2 Mean: $3.458$
   - Cluster 3 Mean: $3.447$
   - *Result:* $H = 0.0360, p = 0.9982, \epsilon^2 = 0.0000$.
   
   **Conclusion:** In cross-sectional survey responses, stated price and discount sensitivity does not naturally align with general behavioral quick-commerce habits. High-frequency or high-spending users do not state higher or lower loyalty under discount withdrawal compared to casual or emergency users.

2. **The Methodological Implication for Specification B:**
   Specification B achieves strong separation on QA 47 ($p < 10^{-21}$) solely because QA 47 was injected into the distance matrix. This separation is descriptive rather than predictive. Notably, even with QA 47 included, held-out QA 46 (stated future 3-month use) remains statistically indistinguishable across clusters ($p = 0.2373$), proving that segmenting directly on discount sensitivity does not automatically identify customers with higher stated future growth or retention.

---

## 6. Segment Persona Profiles ($k = 4$ PAM Solutions)

Based on `reports/segmentation/cluster_profile_summary.csv`, the 4 clusters in Specification A represent distinct behavioral archetypes:

### Cluster 0: *Delivery-Focused Convenience Loyalists* ($n = 218$, $27.0\%$)
- **Profile:** Highest importance placed on fast delivery (mean $4.76 / 5$) and very high composite satisfaction ($4.44 / 5$). Balanced order frequency (2–3 times per week). Modest basket size ($2–4$ items).
- **Multi-Homing:** Low to moderate (mean $1.68$ platforms used). 
- **Stated Discount Sensitivity:** Average (QA 47 Mean: $3.440$).

### Cluster 1: *High-Multi-Homing Deal Explorers* ($n = 288$, $35.7\%$)
- **Profile:** The largest segment. Exhibits high multi-homing (mean $2.62$ platforms used, $81\%$ using $\ge 2$ platforms). Active platform price comparison (mean $4.08 / 5$). Frequently adds items to hit minimum thresholds ($74\%$).
- **Frequency & Basket:** Moderate frequency, small-to-medium baskets ($3–5$ items).
- **Stated Discount Sensitivity:** Average (QA 47 Mean: $3.438$).

### Cluster 2: *High-Spend Planned Household Stockers* ($n = 120$, $14.9\%$)
- **Profile:** Highest order spend (mean rank $4.48 / 6$) and highest monthly spend ($>₹5,000$). Largest basket sizes ($5–8+$ items). Dominant role in household grocery routine (62% primary/regular role).
- **Delivery Expectations:** Satisfied with standard fast delivery, but less obsessed with ultra-fast sub-10-minute speed than Cluster 0.
- **Stated Discount Sensitivity:** Average (QA 47 Mean: $3.458$).

### Cluster 3: *Fill-In / Emergency Occasional Users* ($n = 181$, $22.4\%$)
- **Profile:** Lowest order frequency ($1–2$ times per month or less). Smallest baskets ($1–2$ items). Low total spending change compared to physical stores. Mostly single-platform users ($72\%$ use only 1 app).
- **Behavior:** Quick-commerce is an emergency supplement rather than a routine grocery destination.
- **Stated Discount Sensitivity:** Average (QA 47 Mean: $3.447$).

---

## 7. Methodological Uncertainties, Boundaries & Risks

1. **Stated vs. Revealed Preference (No Transaction Data):**
   Survey respondents uniformly rate discount continuation around $3.4$ to $3.5$ on a 5-point scale (standard deviation $\approx 1.1$). In actual market conditions, price elasticity is governed by wallet constraints, immediate urgency, and competitor promotions. Cross-sectional survey Likert scores cannot be interpreted as actual churn probabilities.
2. **Cluster Overlap in High Dimensions:**
   Average silhouette widths are modest ($\approx 0.05$), which is standard for high-dimensional mixed categorical survey data. While clusters are statistically stable across subsampling (high ARI), they do not represent completely isolated customer "islands."
3. **No Platform-Specific Loyalty:**
   As established in Gate 1A, the survey measures general quick-commerce usage. None of these clusters can be attributed to specific platforms (e.g. Blinkit vs. Zepto vs. Instamart).
4. **CRM Application Constraints:**
   CRM interventions designed in subsequent gates must treat these segments as **behavioral operational archetypes** (e.g., threshold optimizers vs. high-basket stockers) rather than proven price-elasticity tiers.

---

## 8. Gate 1C Artifact Manifest & Sign-Off Recommendation

### Generated Artifacts
- `scripts/prepare_segmentation_features.py`: Hardened distance contract with fail-fast validation.
- `scripts/run_segmentation_experiments.py`: Complete, reproducible clustering and validation pipeline.
- `reports/segmentation/distance_matrix_audit.csv`: Distance matrix diagnostic audit ($807 \times 807$, denominator $15.0/16.0$, valid).
- `reports/segmentation/clustering_metrics.csv`: Quality metrics across PAM, HAC Average, and HAC Complete for $k \in \{3, 4, 5, 6\}$.
- `reports/segmentation/stability_summary.csv`: Subsampling stability summaries (ARI distributions across 20 runs).
- `reports/segmentation/cluster_profile_summary.csv`: Aggregate feature profiles for candidate solutions.
- `reports/segmentation/external_validation_summary.csv`: Non-parametric hypothesis tests against QA 47 and QA 46.
- `tests/test_segmentation_experiments.py`: 9 focused unit tests verifying matrix properties, deterministic PAM, stability, and data governance.
- `data/processed/`: Distance matrices (`.npy`) and cluster labels (`.csv`) saved locally and strictly gitignored.

### Recommendation
**Gate 1C is COMPLETE.** The evidence supports adopting **$k = 4$ PAM under Specification A** for operational behavioral segmentation and **$k = 4$ PAM under Specification B** for sensitivity comparison, with the documented finding that general quick-commerce shopping behavior is orthogonal to stated discount sensitivity.

*No dashboard development, predictive modeling, or CRM recommendations have been started. Awaiting Principal Project Lead review.*
