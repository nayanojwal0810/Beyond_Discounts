# Gate 1C: Controlled Mixed-Data Customer Segmentation Experiment Decision Report

**Project:** Beyond Discounts: Customer Segmentation and Retention Strategy for Indian Quick Commerce  
**Repository:** [nayanojwal0810/Beyond_Discounts](https://github.com/nayanojwal0810/Beyond_Discounts)  
**Branch:** `main`  
**Gate:** Gate 1C — Controlled Mixed-Data Customer Segmentation Experiment
**Status:** COMPLETE / AUDITED / AWAITING PRINCIPAL REVIEW

---

## 1. Executive Summary & Core Research Question

Gate 1C tests whether the prepared survey data ($N = 1,263$ total; $n = 807$ verified current active quick-commerce users) supports stable, useful, and interpretable customer segments, answering the central research question:

> *Do current active quick-commerce users differ in their behaviour and attitudes in ways that correspond to different stated continuation intentions if discounts are reduced?*

### Scope and Population Boundaries
- **Clustering Population:** Exactly $n = 807$ verified active quick-commerce users ($\text{QA 10} = 1 \text{ [Ever Ordered]} \land \text{QA 15} \in [2, 7] \text{ [Current Frequency] > Never}$).
- **Excluded Subgroups:** Never-users ($n = 376$) and previous users ($n = 80$) remain separate descriptive populations and are strictly excluded from clustering inputs.
- **Empirical Boundaries:** Data is cross-sectional survey responses reflecting stated perceptions and intentions. It contains no transaction telemetry, repeat-purchase logs, or observed churn. No causal claims are asserted.

---

## 2. Definitive Methodological Decision: Provisionally Usable Only

Based on the joint evaluation of internal cluster cohesion, subsampling stability distributions, cluster sizes, and external validation evidence:

> **DECISION:** **The customer segmentation is ONLY PROVISIONALLY USABLE as exploratory behavioral archetypes, and is NOT a dependable, hard customer partition.**

### Supporting Evidence for the Decision:
1. **Weak Internal Separation:** In the selected Specification A, PAM $k=4$ solution, the average silhouette width is **$0.0500$**, with **$20.20\%$ negative silhouette observations** ($163$ out of $807$ respondents). Clusters exhibit substantial geometric overlap in the high-dimensional mixed-data space rather than distinct, isolated groupings.
2. **Fragile Subsampling Stability:** While the median Adjusted Rand Index (ARI) across 20 repeated 80% subsamples is **$0.6787$**, **8 of 20 subsamples ($40.0\%$) produce an ARI below $0.50$**, with a minimum ARI of **$0.2853$** and standard deviation of **$0.2771$**. When the respondent pool is perturbed by 20%, cluster assignments change substantially in 40% of cases.
3. **Orthogonality of Stated Discount Continuation (QA 47):** Clusters formed from general quick-commerce shopping habits (Specification A) exhibit **zero statistically significant divergence** in stated willingness to continue if discounts are reduced ($H = 0.0364, p = 0.9982, \text{Holm } p = 1.0000, \epsilon^2 = 0.0000$). Cluster means are practically identical: $3.440, 3.438, 3.458, 3.447$. General behavioral habits cannot serve as an organic proxy for stated price sensitivity.
4. **Non-Significant Stated Future Intent (QA 46):** While held-out stated 3-month use intention (QA 46) shows raw variation ($H = 8.3952, p_{\text{raw}} = 0.0385$), after family-wise Holm-Bonferroni correction across the 4 candidate $k$ comparisons, the difference is **not statistically significant** ($p_{\text{Holm}} = 0.1541, \epsilon^2 = 0.0067$).

---

## 3. Distance Matrix Audit Results

Before clustering, the distance implementation was hardened with fail-fast validations (rejecting unknown types, non-binary values in asymmetric flags, negative or non-finite weights, and out-of-range values). The matrices were audited in `reports/segmentation/distance_matrix_audit.csv`:

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

---

## 4. Candidate Algorithms & Quality Metrics

We evaluated Kaufman & Rousseeuw (1990) Partitioning Around Medoids (PAM) against Hierarchical Agglomerative Clustering (HAC Average and Complete Linkage) across candidate cluster counts $k \in \{3, 4, 5, 6\}$.

### Metric Summary (`reports/segmentation/clustering_metrics.csv`)

| Spec | Algorithm | Linkage | $k$ | Avg Sil | % Neg Sil | PAM Objective | Cluster Sizes ($n$) | Proportions | Min Size | Small Warning ($<41$) |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :--- | :--- | :---: | :---: |
| SPEC_A | PAM | N/A | $3$ | $0.0406$ | $18.71\%$ | $186.9261$ | $[289, 288, 230]$ | $[0.3581, 0.3569, 0.2850]$ | $230$ | False |
| **SPEC_A** | **PAM** | **N/A** | $\mathbf{4}$ | $\mathbf{0.0500}$ | $\mathbf{20.20\%}$ | $\mathbf{180.1869}$ | $\mathbf{[243, 224, 179, 161]}$ | $\mathbf{[0.3011, 0.2776, 0.2218, 0.1995]}$ | $\mathbf{161}$ | **False** |
| SPEC_A | PAM | N/A | $5$ | $0.0543$ | $23.67\%$ | $175.3994$ | $[209, 183, 158, 128, 129]$ | $[0.2590, 0.2268, 0.1958, 0.1586, 0.1599]$ | $128$ | False |
| SPEC_A | PAM | N/A | $6$ | $0.0522$ | $27.01\%$ | $171.9175$ | $[197, 167, 119, 119, 118, 87]$ | $[0.2441, 0.2069, 0.1475, 0.1475, 0.1462, 0.1078]$ | $87$ | False |
| SPEC_A | HAC | average | $3$ | $0.0795$ | $19.08\%$ | N/A | $[790, 15, 2]$ | $[0.9789, 0.0186, 0.0025]$ | $2$ | **TRUE (Chaining)** |
| SPEC_A | HAC | average | $4$ | $0.0406$ | $33.58\%$ | N/A | $[787, 15, 2, 3]$ | $[0.9752, 0.0186, 0.0025, 0.0037]$ | $2$ | **TRUE (Chaining)** |
| SPEC_A | HAC | average | $5$ | $0.0543$ | $26.39\%$ | N/A | $[694, 15, 2, 3, 93]$ | $[0.8600, 0.0186, 0.0025, 0.0037, 0.1152]$ | $2$ | **TRUE (Chaining)** |
| SPEC_A | HAC | average | $6$ | $0.0303$ | $34.94\%$ | N/A | $[689, 15, 5, 3, 93, 2]$ | $[0.8538, 0.0186, 0.0062, 0.0037, 0.1152, 0.0025]$ | $2$ | **TRUE (Chaining)** |
| SPEC_A | HAC | complete| $3$ | $0.0150$ | $40.15\%$ | N/A | $[477, 257, 73]$ | $[0.5911, 0.3185, 0.0905]$ | $73$ | False |
| SPEC_A | HAC | complete| $4$ | $0.0190$ | $38.54\%$ | N/A | $[202, 275, 73, 257]$ | $[0.2503, 0.3408, 0.0905, 0.3185]$ | $73$ | False |
| SPEC_A | HAC | complete| $5$ | $0.0156$ | $44.61\%$ | N/A | $[275, 257, 73, 79, 123]$ | $[0.3408, 0.3185, 0.0905, 0.0979, 0.1524]$ | $73$ | False |
| SPEC_A | HAC | complete| $6$ | $0.0173$ | $43.74\%$ | N/A | $[257, 129, 73, 79, 123, 146]$ | $[0.3185, 0.1599, 0.0905, 0.0979, 0.1524, 0.1809]$ | $73$ | False |
| SPEC_B | PAM | N/A | $3$ | $0.0425$ | $16.60\%$ | $189.4846$ | $[309, 273, 225]$ | $[0.3829, 0.3383, 0.2788]$ | $225$ | False |
| **SPEC_B** | **PAM** | **N/A** | $\mathbf{4}$ | $\mathbf{0.0430}$ | $\mathbf{22.43\%}$ | $\mathbf{182.6159}$ | $\mathbf{[266, 210, 174, 157]}$ | $\mathbf{[0.3296, 0.2602, 0.2156, 0.1945]}$ | $\mathbf{157}$ | **False** |
| SPEC_B | PAM | N/A | $5$ | $0.0492$ | $25.28\%$ | $177.7305$ | $[213, 190, 137, 131, 136]$ | $[0.2639, 0.2354, 0.1698, 0.1623, 0.1685]$ | $131$ | False |
| SPEC_B | PAM | N/A | $6$ | $0.0496$ | $25.77\%$ | $174.3516$ | $[198, 180, 71, 109, 121, 128]$ | $[0.2454, 0.2230, 0.0880, 0.1351, 0.1499, 0.1586]$ | $71$ | False |

### Algorithm Rejections:
- **HAC Average Linkage is REJECTED:** Severely degrades due to chaining on mixed Gower distances, grouping $>97\%$ of respondents into one cluster and isolating tiny clusters ($n=2, 3$).
- **HAC Complete Linkage is REJECTED:** Extremely high negative silhouette rates ($38\% - 45\%$) and negligible cohesion ($\text{silhouette} < 0.02$).

---

## 5. Subsampling Stability Analysis

Stability was evaluated through 20 repeated 80% subsamples ($n = 646$) using seeds $101$ to $120$ (`reports/segmentation/stability_summary.csv`):

| Spec | $k$ | Median ARI | Mean ARI | Std ARI | Min ARI | Max ARI | IQR ARI | Unstable Runs ($\text{ARI} < 0.50$) | Stability Verdict |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **SPEC_A** | $3$ | $0.3890$ | $0.4493$ | $0.2497$ | $0.0400$ | $1.0000$ | $0.3159$ | $11 / 20$ ($55\%$) | **UNSTABLE** |
| **SPEC_A** | $\mathbf{4}$ | $\mathbf{0.6787}$ | $\mathbf{0.6425}$ | $\mathbf{0.2771}$ | $\mathbf{0.2853}$ | $\mathbf{1.0000}$ | $\mathbf{0.6302}$ | $\mathbf{8 / 20}$ ($\mathbf{40\%}$) | **PROVISIONALLY_STABLE** |
| **SPEC_A** | $5$ | $0.4020$ | $0.4866$ | $0.2351$ | $0.1988$ | $1.0000$ | $0.3537$ | $13 / 20$ ($65\%$) | **MODERATE / WEAK** |
| **SPEC_A** | $6$ | $0.4175$ | $0.4749$ | $0.1959$ | $0.1847$ | $1.0000$ | $0.2452$ | $12 / 20$ ($60\%$) | **MODERATE / WEAK** |
| **SPEC_B** | $3$ | $0.3531$ | $0.4903$ | $0.3469$ | $0.0724$ | $1.0000$ | $0.8115$ | $14 / 20$ ($70\%$) | **UNSTABLE** |
| **SPEC_B** | $\mathbf{4}$ | $\mathbf{0.6621}$ | $\mathbf{0.5768}$ | $\mathbf{0.2879}$ | $\mathbf{0.0836}$ | $\mathbf{1.0000}$ | $\mathbf{0.3715}$ | $\mathbf{8 / 20}$ ($\mathbf{40\%}$) | **PROVISIONALLY_STABLE** |
| **SPEC_B** | $5$ | $0.4483$ | $0.4848$ | $0.2193$ | $0.1348$ | $1.0000$ | $0.3169$ | $12 / 20$ ($60\%$) | **MODERATE / WEAK** |
| **SPEC_B** | $6$ | $0.4746$ | $0.4782$ | $0.2252$ | $0.1334$ | $1.0000$ | $0.3405$ | $11 / 20$ ($55\%$) | **MODERATE / WEAK** |

### Stability Evaluation:
Candidate $k=4$ has the highest median stability ($\text{ARI} = 0.6787$ in Spec A, $0.6621$ in Spec B), whereas $k=3, 5, 6$ have median ARIs $< 0.48$. However, because 8 of 20 subsamples fall below $0.50$ ARI, $k=4$ cannot be labeled unqualifiedly stable. It is strictly **provisionally stable**.

---

## 6. External Validation Results

External validation was evaluated against held-out variables across candidate $k$ ($m = 4$ comparisons per family). Both single-step Bonferroni and step-down Holm-Bonferroni corrections were applied (`reports/segmentation/external_validation_summary.csv`):

| Spec | $k$ | Variable | Status | Test Method | $H$ Stat | Raw $p$ | Bonf $p$ | Holm $p$ | $\epsilon^2$ | Interpretation |
| :--- | :---: | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **SPEC_A** | **4** | **QA 47 Continue If Discounts Reduced** | **Independent Validation Benchmark** | Kruskal-Wallis | **$0.0364$** | **$0.9982$** | **$1.0000$** | **$1.0000$** | **$0.0000$** | **Homogeneous across clusters (No divergence)** |
| SPEC_A | 4 | QA 46 Next 3 Month Use | Stated Future Intent Benchmark | Kruskal-Wallis | $8.3952$ | $0.0385$ | $0.1541$ | $0.1541$ | $0.0067$ | Non-significant after Holm-Bonferroni correction |
| **SPEC_B** | **4** | **QA 47 Continue If Discounts Reduced** | **Construct-Defining Input** | Kruskal-Wallis | **$104.75$** | **$0.0000$** | **$0.0000$** | **$0.0000$** | **$0.1267$** | **Significant by construction (descriptive only)** |
| SPEC_B | 4 | QA 46 Next 3 Month Use | Stated Future Intent Benchmark | Kruskal-Wallis | $4.2348$ | $0.2372$ | $0.9488$ | $0.6293$ | $0.0015$ | Non-significant after Holm-Bonferroni correction |

### Held-Out Means for Selected Specification A ($k=4$):
- **QA 47 Continue If Discounts Reduced (Scale 1–5):**
  - Cluster 0: $3.440$
  - Cluster 1: $3.438$
  - Cluster 2: $3.458$
  - Cluster 3: $3.447$
  - *Result:* Difference across clusters is $0.020$ on a 5-point scale. Stated discount sensitivity is totally invariant across behavioral segments.
- **QA 46 Next 3 Month Use (Scale 1–5):**
  - Cluster 0: $3.588$
  - Cluster 1: $3.661$
  - Cluster 2: $3.899$
  - Cluster 3: $3.764$
  - *Result:* Raw $p = 0.0385$, but after step-down Holm-Bonferroni correction across $k \in \{3, 4, 5, 6\}$, $p_{\text{Holm}} = 0.1541 \ge 0.05$. It does not survive family-wise correction.

---

## 7. Reconciled Segment Persona Archetypes (Specification A, PAM, $k=4$)

All persona descriptions are built strictly from `reports/segmentation/cluster_profile_summary.csv` ($N_{\text{active}} = 807$).

### Reconciliation Table: Cluster Sizes & Key Profile Means

| Metric / Feature | Cluster 0 | Cluster 1 | Cluster 2 | Cluster 3 | Source Column in Profiles |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **Cluster Size ($n$)** | **$243$** | **$224$** | **$179$** | **$161$** | `cluster_size` (Sum = $807$) |
| **Cluster Proportion** | **$30.11\%$** | **$27.76\%$** | **$22.18\%$** | **$19.95\%$** | `cluster_proportion` (Sum = $1.0000$) |
| **Order Frequency (Mean)** | $4.28$ | $3.77$ | $4.05$ | $4.49$ | `order_frequency` |
| **Usage Duration (Mean)** | $4.01$ | $5.09$ | $4.68$ | $4.16$ | `usage_duration` |
| **Monthly Spend Tier (Mean)** | $2.74$ | $2.14$ | $2.75$ | $2.87$ | `monthly_spend_ordinal` |
| **Items Per Order (Mean)** | $2.76$ | $2.38$ | $2.72$ | $2.64$ | `items_per_order_ordinal` |
| **Platforms Used Count (Mean)** | $2.55$ | $2.16$ | $2.37$ | $2.12$ | `platforms_used_count` |
| **Physical Price Compare (Mean)** | $2.10$ | $3.44$ | $2.90$ | $2.78$ | `compare_physical_prices` |
| **Platform Price Compare (Mean)** | $3.13$ | $3.09$ | $3.49$ | $3.19$ | `compare_platform_prices` |
| **Fast Delivery Importance (Mean)** | $3.88$ | $3.49$ | $3.34$ | $3.91$ | `fast_delivery_importance` |
| **Composite Satisfaction (Mean)** | $3.76$ | $3.89$ | $3.99$ | $3.82$ | `service_satisfaction_composite` |
| **Discount Overspend (Mean)** | $2.94$ | $3.01$ | $3.04$ | $3.49$ | `discount_overspend` |
| **Shopping Routine Dominant Category** | Cat 3 ($65.84\%$) | Cat 3 ($63.39\%$) | Cat 2 ($70.39\%$) | Cat 4 ($69.57\%$) | `shopping_routine_role` |

### Substantive Behavioral Persona Archetypes:

1. **Cluster 0: *Multi-App Emergency Fill-in Shoppers* ($n = 243$, $30.11\%$)**
   - **Routine Role:** $65.84\%$ cite Category 3 (Emergency / fill-in purchases).
   - **Multi-Homing:** Highest platforms used count (mean $2.55$).
   - **Price Habits:** Lowest physical store price comparison (mean $2.10$).
   - **Service Expectations:** Fast delivery importance mean $3.88$; satisfaction mean $3.76$.

2. **Cluster 1: *Long-Tenured Price-Conscious Light Spenders* ($n = 224$, $27.76\%$)**
   - **Routine Role:** $63.39\%$ cite Category 3 (Emergency / fill-in purchases).
   - **Tenure & Spend:** Longest usage duration (mean $5.09$); lowest monthly spend ordinal ($2.14$); smallest items per order ($2.38$).
   - **Price Habits:** Highest physical store price comparison (mean $3.44$); lowest threshold extra item additions ($2.46$).
   - **Service Expectations:** Fast delivery importance mean $3.49$; satisfaction mean $3.89$.

3. **Cluster 2: *Regular Supplementers & Cross-Platform Comparers* ($n = 179$, $22.18\%$)**
   - **Routine Role:** $70.39\%$ cite Category 2 (Regular supplement for specific items).
   - **Price Habits:** Highest cross-platform price comparison (mean $3.49$).
   - **Service Expectations:** Highest composite satisfaction (mean $3.99$); lowest fast-delivery urgency (mean $3.34$).

4. **Cluster 3: *High-Frequency Busy Convenience Overspenders* ($n = 161$, $19.95\%$)**
   - **Routine Role:** $69.57\%$ cite Category 4 (Occasional convenience when busy).
   - **Order Dynamics:** Highest order frequency (mean $4.49$); highest monthly spend tier ($2.87$).
   - **Discount Reaction:** Highest discount-induced overspending (mean $3.49$); highest unplanned purchases ($3.37$).
   - **Service Expectations:** Highest fast delivery importance (mean $3.91$); lowest multi-homing ($2.12$).

---

## 8. Methodological Limitations & Analytical Next Steps

### Limitations:
1. **Clusters Are Overlapping Archetypes, Not Hard Partitions:** Given the silhouette width of $0.0500$ and 40% subsampling instability, these clusters must not be treated as discrete segments for rigid CRM decision logic.
2. **Discount Sensitivity Is Orthogonal to Behavioral Habits:** In this survey, customers who buy frequently or spend heavily state the same continuation intention if discounts are reduced as light, emergency buyers.
3. **No Platform Attribution:** Data reflects the quick-commerce industry generally; platform-specific loyalty cannot be inferred.

### Methodological Recommendation for Gate 2:
- Do not build rule-based CRM logic predicated on hard cluster assignment.
- Treat the 4 clusters provisionally as exploratory customer archetypes.
- Model price sensitivity (QA 47) and future intent (QA 46) directly using continuous predictive models (e.g., elastic net or gradient boosting) rather than cluster-conditioned averages.

*No dashboard development, CRM recommendations, or final reports have been initiated. Gate 1C is complete and submitted for Principal Project Lead review.*
