# Gate 1C: Controlled Mixed-Data Customer Segmentation Experiment Decision Report

**Project:** Beyond Discounts: Customer Segmentation and Retention Strategy for Indian Quick Commerce  
**Repository:** [nayanojwal0810/Beyond_Discounts](https://github.com/nayanojwal0810/Beyond_Discounts)  
**Branch:** `review/gate-1c1-crm-decision`  
**Gate:** Gate 1C — Controlled Mixed-Data Customer Segmentation Experiment
**Status:** PRELIMINARY AGGREGATES FROM PRIOR RUN — GATE 1C.1 OPEN; revised code must be rerun

---

## 1. Executive Summary & Core Research Question

The original Gate 1C experiment tested whether the questionnaire-defined current-user cohort ($n=807$) could be usefully partitioned. The aggregate figures below are from the previously committed run and have not yet been regenerated with the current branch fixes. The project's primary research question is now lifecycle-based:

> *Which lifecycle-based CRM actions are best supported by the observed sample's stated future-use intentions, discount-reduction continuation intentions, non-use barriers, and preferred service improvements?*
>
> *Do exploratory behavioral clusters add actionable differentiation beyond lifecycle cohorts?*

### Scope and Population Boundaries
- **Clustering Population:** Exactly $n = 807$ respondents in the questionnaire-defined current-user cohort ($\text{QA 10} = 1 \text{ [Ever Ordered]} \land \text{QA 15} \in [2, 7] \text{ [Current Frequency] > Never}$).
- **Excluded Subgroups:** Never-users ($n = 376$) and previous users ($n = 80$) remain separate descriptive populations and are strictly excluded from clustering inputs.
- **Empirical Boundaries:** Data is cross-sectional survey responses reflecting stated perceptions and intentions. It contains no transaction telemetry, repeat-purchase logs, or observed churn. No causal claims are asserted.

---

## 2. Methodological Decision: Exploratory Only; Not Approved for CRM Targeting

Based on the joint evaluation of internal cluster cohesion, subsampling stability distributions, cluster sizes, and external validation evidence:

> **DECISION:** **Do not use the current hard clusters as operational CRM segments.** They may be retained as an exploratory method comparison only. The primary CRM analysis will use questionnaire-defined lifecycle cohorts and stated-intention / preference measures.

### Supporting Evidence for the Decision:
1. **Weak Internal Separation:** In the selected Specification A, PAM $k=4$ solution, the average silhouette width is **$0.0500$**, with **$20.20\%$ negative silhouette observations** ($163$ out of $807$ respondents). Clusters exhibit substantial geometric overlap in the high-dimensional mixed-data space rather than distinct, isolated groupings.
2. **Fragile Subsampling Stability:** While the median Adjusted Rand Index (ARI) across 20 repeated 80% subsamples is **$0.6787$**, **8 of 20 subsamples ($40.0\%$) produce an ARI below $0.50$**, with a minimum ARI of **$0.2853$** and standard deviation of **$0.2771$**. When the respondent pool is perturbed by 20%, cluster assignments change substantially in 40% of cases.
3. **No detectable QA47 difference in the current Spec A test:** The current committed output shows very similar cluster means ($3.440, 3.438, 3.458, 3.447$), with Kruskal–Wallis $H=0.0364$, raw $p=0.9982$, Holm-adjusted $p=1.0000$, and reported $\epsilon^2=0.0000$. This is evidence that this particular solution did not differentiate QA47 in this sample; it is **not** a formal equivalence test and does not prove behavioral factors are unrelated to continuation intention in every model.
4. **QA46 result does not survive correction:** The previous aggregate report recorded raw $p=0.0385$, Holm-adjusted $p=0.1541$, and $\epsilon^2=0.0067$. The current conclusion is that the evidence was insufficient to establish a difference after the predeclared correction; this is not proof of equal future-use intentions.

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
| **SPEC_A** | **4** | **QA 47 Continue If Discounts Reduced** | **Independent stated-intention benchmark** | Kruskal-Wallis | **$0.0364$** | **$0.9982$** | **$1.0000$** | **$1.0000$** | **$0.0000$** | **No detectable difference; equivalence not established** |
| SPEC_A | 4 | QA 46 Next 3 Month Use | Stated Future Intent Benchmark | Kruskal-Wallis | $8.3952$ | $0.0385$ | $0.1541$ | $0.1541$ | $0.0067$ | Non-significant after Holm-Bonferroni correction |
| **SPEC_B** | **4** | **QA 47 Continue If Discounts Reduced** | **Construct-defining input** | Kruskal-Wallis | **$104.75$** | **Reported as 0.0000 after prior rounding** | **Reported as 0.0000 after prior rounding** | **Reported as 0.0000 after prior rounding** | **$0.1267$** | **Circular/construct-defining; exact p-values must be regenerated** |
| SPEC_B | 4 | QA 46 Next 3 Month Use | Stated Future Intent Benchmark | Kruskal-Wallis | $4.2348$ | $0.2372$ | $0.9488$ | $0.6293$ | $0.0015$ | Non-significant after Holm-Bonferroni correction |

### Held-Out Means for Selected Specification A ($k=4$):
- **QA 47 Continue If Discounts Reduced (Scale 1–5):**
  - Cluster 0: $3.440$
  - Cluster 1: $3.438$
  - Cluster 2: $3.458$
  - Cluster 3: $3.447$
  - *Interpretation:* The largest gap between these means is only $0.020$ on this 5-point scale in the previously committed output. That test found no detectable difference; without an equivalence margin and an equivalence test, do not conclude that continuation intention is invariant across all behavior-based partitions.
- **QA 46 Next 3 Month Use (Scale 1–5):**
  - Cluster 0: $3.588$
  - Cluster 1: $3.661$
  - Cluster 2: $3.899$
  - Cluster 3: $3.764$
  - *Result:* Raw $p = 0.0385$, but after step-down Holm-Bonferroni correction across $k \in \{3, 4, 5, 6\}$, $p_{\text{Holm}} = 0.1541 \ge 0.05$. It does not survive family-wise correction.

---

## 7. Exploratory Cluster Profiles — Not CRM Personas

The following values are from the **previously committed aggregate profile table** and must be regenerated after the revised code passes verification. They are retained to show what the clustering produced, not to justify operational targeting. No custom persona names are assigned because the separation is weak and resampling variability is material.

### Specification A, PAM, k=4 — descriptive profile only

| Metric / feature | Cluster 0 | Cluster 1 | Cluster 2 | Cluster 3 | Interpretation boundary |
|---|---:|---:|---:|---:|---|
| Cluster size | 243 | 224 | 179 | 161 | Adds to 807; not verified customer-list sizes for deployment |
| Cluster proportion | 30.11% | 27.76% | 22.18% | 19.95% | Sample shares in this particular fitted partition |
| Order frequency mean (coded ordinal) | 4.28 | 3.77 | 4.05 | 4.49 | Higher codes denote more frequent self-reported ordering |
| Usage duration mean (coded ordinal) | 4.01 | 5.09 | 4.68 | 4.16 | Survey-coded tenure category; not a transactional tenure measure |
| Monthly spend tier mean (coded ordinal) | 2.74 | 2.14 | 2.75 | 2.87 | Ordinal code summary, not average rupee spend |
| Items per order mean (coded ordinal) | 2.76 | 2.38 | 2.72 | 2.64 | Undefined “varies considerably” responses handled separately in distance |
| Platforms ever used count mean | 2.55 | 2.16 | 2.37 | 2.12 | Historical platform-repertoire breadth; not current loyalty/multi-homing |
| Physical-store price comparison mean | 2.10 | 3.44 | 2.90 | 2.78 | Self-reported frequency scale |
| Cross-platform price comparison mean | 3.13 | 3.09 | 3.49 | 3.19 | Self-reported frequency scale |
| Fast-delivery importance mean | 3.88 | 3.49 | 3.34 | 3.91 | Stated importance, not willingness to pay a measured premium |
| Service satisfaction composite mean | 3.76 | 3.89 | 3.99 | 3.82 | Category-level service ratings |
| Discount-induced overspend mean | 2.94 | 3.01 | 3.04 | 3.49 | Self-reported tendency |
| Dominant shopping-routine code | 3 (65.84%) | 3 (63.39%) | 2 (70.39%) | 4 (69.57%) | Code meanings per the feature spec: 2 = some grocery replacement; 3 = top-up; 4 = urgent/emergency use |

**What may be said:** the fitted clusters show some descriptive differences in the measured feature means. **What may not be said:** that these are validated customer personas, they have distinct QA47 continuation intention, they will respond differently to CRM interventions, or their assignment should determine an individual offer.

Before any further interpretation, the team must (a) regenerate these aggregate statistics from current source data, (b) check feature/category labels against the codebook, (c) add QA49 preference profiles, and (d) show added decision value beyond lifecycle cohorts. Even after that, targeting use would require independent validation and eventually a real campaign experiment.

---

## 8. Methodological Limitations & Next Gate

### Limitations
1. **Weak separation and uncertain reproducibility:** Spec A PAM k=4's prior mean silhouette is 0.0500; 20.20% of observations have negative silhouettes. Eight of 20 subsamples had ARI below 0.50. These metrics do not support hard CRM targeting.
2. **Independent outcome differentiation has not been established:** In the previous run, Spec A k=4 showed no detectable difference in QA47 after the chosen test; QA46 did not survive the family correction. Non-significance is not equivalence.
3. **QA49 is a missing clustering deliverable:** The feature specification reserves QA49 for post-cluster CRM profiling, but the current committed cluster-profile output does not include QA49. That gap must be closed before any segment-level action claim.
4. **No platform attribution or transactional outcomes:** The data are category-level self-report. It contains no verified platform-specific churn, repeat-purchase logs, customer-level transaction RFM/CLV, or causal campaign-uplift outcome.
5. **Sampling limitations:** The documented sampling frame and recruitment method are unresolved. Interpret estimates as the observed sample, not a nationally representative Indian customer population.

### Required technical sign-off (Gate 1C.1)
The revised code now preserves p-value precision through corrections and separates failed subsamples from measured ARI. A regression test and per-seed stability output were added. **Neither the complete suite nor the real-workbook end-to-end rerun has been independently executed by the project lead yet.** Treat all metrics in this report as prior-run output until regenerated.

Gate 1C.1 closes only when tests pass; the regenerated run writes and validates stability run diagnostics; p-values and corrections reconcile; all aggregate reports and text reconcile; the QA49 omission is decided/resolved; and raw/row-level data remain outside Git.

### Next approved analytical gate (Gate 1D)
Proceed with a lifecycle-first CRM evidence analysis, in this order:
1. QA49 preference distribution overall, by cohort and—among current users—by QA47 intention tier.
2. QA46 stated future-use comparison across never-users, previous users, and current-user cohort, with effect sizes and confidence intervals.
3. QA48 multi-response non-use barriers by never/previous-user cohort using uncertainty intervals and appropriate sparse-cell inference.
4. A pre-specified ordinal-logit model for QA47 among the 807 current-user cohort, including a proportional-odds/parallel-lines diagnostic and a documented alternative only if the assumption fails.
5. An evidence-tagged decision matrix that separates descriptive findings, adjusted associations, exploratory observations and pilot candidates.
6. A bounded comparison of whether Spec A clusters add independent QA46/QA49 differentiation beyond lifecycle cohorts. Do not continue testing algorithms to find attractive personas.

Build the dashboard only after Gate 1D outputs and recommendations have been checked. Then write the final report with a critically synthesised 15+ work literature review, transparent method/reporting, limitations and a practical future A/B test plan. The survey can nominate candidate interventions; only a real experiment with actual transaction outcomes can estimate campaign uplift.

*Current status: revised code and documentation are in a review branch. Gate 1C.1 is OPEN pending automated CI results and a local end-to-end run with the source workbook.*
