# Gate 1D — Lifecycle-Based CRM Decision Analysis Protocol

**Status:** Approved project-lead direction; implementation and empirical execution pending  
**Parent gate:** Gate 1C clustering experiment (exploratory / not approved as a hard segmentation)  
**Target population:** 1,263 survey respondents, analysed under the eligibility rules below  
**Data contract:** Use only the locally provisioned survey workbook and accompanying questionnaire/codebook. Never commit row-level records, respondent IDs, labels, or derived microdata to Git.

## 1. Project-lead decision

**Do not restart the project, change datasets, or search for a more attractive clustering algorithm.** Continue with the current dataset and turn the work into a lifecycle-based, evidence-led CRM decision framework. The clustering work is retained as a documented exploratory test, including its negative finding, but it must not drive persona claims or the primary recommendations.

This is a practical applied CRM project, not a claim of algorithmic novelty. Established mixed-data clustering methods and stability diagnostics are already in the literature. Indian quick-commerce studies have already investigated adoption frameworks and loyalty drivers using survey/SEM designs. Our defensible contribution is to connect the three lifecycle populations to their stated intentions, non-use barriers, and preferred improvement levers, then test whether the exploratory cluster labels add useful decision information beyond these simple observable groups.

### Approved working title

**Beyond Discounts: A Lifecycle-Based CRM Decision Framework for Indian Quick Commerce**

The original title may remain as a subtitle in presentation materials, but the report should not imply that stable, validated customer personas have been established.

### Primary research question

> Which lifecycle-based CRM actions are most strongly supported by Indian quick-commerce consumers’ stated future-use intentions, discount-reduction continuation intentions, non-use barriers, and preferred service improvements?

### Supporting questions

1. How do never-users, previous users, and current users differ in **stated** future-use intention and preferred improvement?
2. Among current users, which observed behaviour and experience measures are associated with stated willingness to continue if discounts are reduced?
3. Which non-use barriers are most frequently reported by never-users and previous users, and how uncertain are those comparisons?
4. Do the exploratory cluster labels reveal a practically meaningful difference in continuation intention or preferred improvement beyond what the lifecycle cohort already tells us?

## 2. Evidence boundaries that must never be crossed

- **QA46** is a self-reported likelihood of using quick commerce in the next three months. It is not observed purchase behaviour.
- **QA47** is a self-reported intention to continue using quick commerce if discounts were reduced, and it is substantive only for current users (codes 1–5; n=807). Call it *discount-reduction continuation intention*. Do not call it observed churn, churn probability, proven price elasticity, or actual retention.
- **QA48** records reasons given by non-current respondents at survey time. It does not establish why a previous user stopped ordering.
- **QA49** is a single preferred improvement, not an experimentally measured response to a price change or service intervention.
- Do not claim causal impact, actual retention uplift, actual customer lifetime value, national representativeness, firm/platform-specific satisfaction, or transaction-level price elasticity.
- The survey workbook was published on Mendeley Data in October 2026 under CC BY 4.0. The public record describes the questionnaire and files but does not adequately establish the actual recruitment process, fieldwork dates, or sampling frame. Cite the data creator and report the unresolved provenance limitation; never imply our team recruited the respondents.
- The sample is education- and urban-skewed according to the existing audit. Findings describe this observed sample, not every Indian consumer.

## 3. Fixed analysis populations

| Cohort | Definition | n | CRM lens | Outcomes allowed |
|---|---|---:|---|---|
| Never-users | Ever ordered=0 AND order frequency=Never | 376 | Adoption / trial barrier reduction | QA46, QA48, QA49 |
| Previous users | Ever ordered=1 AND current order frequency=Never | 80 | Exploratory reactivation | QA46, QA48, QA49 |
| Current users | Ever ordered=1 AND current order frequency is not Never | 807 | Retention / value proposition | QA47, QA46, QA49 and eligible behaviour/experience predictors |

Keep those exact subgroup counts and routing definitions consistent in every output. “Previous users” means self-reported past use with no current ordering; it does not imply an observed churn event. The workbook’s frequency option “less than once a month” remains inside the current-user cohort under the existing rule and must not be silently reclassified.

## 4. Gate 1C technical remediation — mandatory before Gate 1D is signed off

Fix and test the following before accepting new analytical outputs:

1. **Preserve full-precision p-values through multiplicity correction.** `evaluate_external_validation()` currently rounds a raw p-value to six decimals before `apply_multiple_testing_corrections()` uses it. Keep full precision internally and round only when exporting/displaying. A reported 0.000000 is not an acceptable representation of an exact zero probability.
2. **Separate resampling failures from measured instability.** `run_subsampling_stability()` currently catches any exception and records ARI=0.0, thereby mixing implementation failure with measured instability. Save a row-level, aggregate-safe resample audit (seed, n sampled, ARI when valid, status, failure class/message without data rows) and report failures separately. Failed runs must not silently become ARI observations.
3. **Make stability summaries auditable.** Derive aggregate stability metrics from the saved successful per-run ARIs. Test the summary from synthetic run records instead of relying only on hard-coded expected numbers.
4. **Validate profiles by identity, not text coincidence.** Persona/cluster tests must assert the specific cluster-to-profile values and totals, not merely check that numbers occur somewhere in Markdown.
5. **Correct metric language.** Replace “price elasticity” with “stated discount-reduction continuation intention.” Replace “platform promiscuity vs single-app loyalty” with “historical platform-repertoire breadth / multi-homing footprint”; the survey does not prove loyalty.
6. **Add the missing QA49 cluster profile.** The feature-spec metadata reserves QA49 for post-cluster action profiling, but current committed cluster profiles do not actually include QA49 distributions. Include it only in the post-cluster/holdout layer; never add it to the clustering features retroactively.
7. **Document construct redundancy.** Related variables such as discount-induced overspending, adding items to meet thresholds, and cross-platform price comparison can share signal. Do not optimize their weights to obtain a better silhouette. For Gate 1D regression, use a predeclared compact predictor specification and a documented redundancy sensitivity check.
8. **Reproducibility clean-up.** Add pinned dependencies, clear local data provisioning steps, synthetic fixtures that run from a clean clone, and an automated test workflow. Update the stale README gate badge, command list, and repository tree. Explicitly label the earlier app-review-corpus feasibility material as historical/superseded while retaining the audit trail. Keep `data/raw/` and `data/processed/` respondent-level artifacts out of Git.

**Exit criterion:** all fixes have targeted tests; the full suite is executed against the provisioned workbook; the report records the test command, environment, and actual result. A worker’s test claim is not the same as independent reproduction by the project lead.

## 5. Gate 1D analytical work order

### 5.1 Cohort-wide stated future-use intention (QA46)

- Produce the 1–5 response distribution and 95% confidence intervals for all respondents and separately for the three lifecycle cohorts.
- Report denominators on every table/figure.
- For cohort differences, use an omnibus ordinal/rank-based comparison with an effect size, then only predeclared pairwise comparisons with Holm adjustment. Include uncertainty; do not use a p-value alone to imply commercial importance.
- Keep age/education/location skews in the interpretation. Do not manufacture population weights without a documented sampling design and defensible target margins.

**Required outputs**
- `reports/crm/qa46_intention_by_lifecycle.csv`
- `reports/crm/qa46_lifecycle_comparisons.csv`
- A compact figure showing the 5-category distribution, not only a mean bar chart.

### 5.2 Non-use barriers (QA48): never-users versus previous users

- Estimate each barrier’s prevalence within each cohort using its own valid denominator (n=376 and n=80).
- Include 95% proportion confidence intervals and the percentage-point difference with an interval.
- Use Fisher’s exact test where cell counts are sparse; apply Holm correction across the 10 predeclared barrier comparisons.
- Present all barriers descriptively even when tests are non-significant. Non-significance is not proof that the two groups are equivalent. The smaller previous-user group is especially uncertain.
- Phrase this as “barriers selected by non-current users,” not “causes of churn.”

**Required outputs**
- `reports/crm/qa48_barrier_prevalence.csv`
- `reports/crm/qa48_never_vs_previous_tests.csv`
- A plot of within-cohort prevalence with confidence intervals.

### 5.3 Preferred improvement (QA49): primary action-prioritisation analysis

Retain the full 10 response options in all primary tables. Also present a clearly labelled decision-view grouping, using the codebook-defined options:

- **Product price / discounts:** options 1–2.
- **Delivery-fee economics:** option 3.
- **Non-price product, service, and availability improvements:** options 4–9.
- **No stated improvement / no intention:** option 10.

This grouping is a dashboard summary convenience, not a validated latent scale. It must never replace the full 10-option results in the report.

Analyse QA49 for:
1. Full sample (N=1,263).
2. Each lifecycle cohort.
3. Current users cross-tabulated by the QA47 operational tiers: lower (1–2), uncertain (3), higher (4–5).

For cohort and QA47-tier comparisons, report cell counts, within-group percentages, confidence intervals where useful, an omnibus association test appropriate to cell sparsity (Monte Carlo/exact approach where needed), and Cramér’s V. Keep full-option findings distinct from grouped-action sensitivity results. Do not claim that choosing an improvement predicts a causal response to implementing it.

**Required outputs**
- `reports/crm/qa49_improvement_full_sample.csv`
- `reports/crm/qa49_improvement_by_lifecycle.csv`
- `reports/crm/qa49_improvement_by_qa47_tier.csv`
- `reports/crm/qa49_association_tests.csv`
- A 100% stacked distribution figure plus one clear decision table.

### 5.4 Current-user continuation model (QA47): compact, interpretable ordinal analysis

**Population:** current users only (n=807), QA47 codes 1–5. Exclude the explicit N/A code. Do not recode the outcome into binary “churn risk” as the primary analysis.

Use a predeclared cumulative-logit/proportional-odds ordinal model as the primary adjusted association model. Confirm outcome-category counts, predictor coding, sparse levels, multicollinearity/redundancy, convergence, and the proportional-odds assumption before interpretation. Do not use stepwise selection or univariate p-value screening to choose predictors.

**Predeclared construct blocks**
- **Adjustment block:** only demographic covariates with usable, defensibly coded variation. Report the sample’s skew; adjustment does not remove non-probability sampling bias.
- **Usage context:** current order frequency (QA15) and usage tenure/duration (QA13).
- **Value and promotion behaviour:** the discount-overspend item (QA28), threshold-extra-items item (QA29), and platform/physical-store price-comparison items (QA33–34). Diagnose redundancy and keep interpretation at the observed-item level rather than inventing an unvalidated “discount sensitivity scale.”
- **Service experience:** the existing QA37–40 satisfaction composite, conditional on the already documented reliability and a fresh item-level check. Do not include the composite and its component items simultaneously.
- **Use context / value priority:** QA35 speed importance and QA43 shopping-routine role; add QA49 only as a final incremental block using the predeclared four action-view categories above, if category counts support stable estimation.

Fit nested models: adjustment-only; add usage/value/service constructs; then add QA49 action preference. Report log-likelihood, AIC, likelihood-ratio comparison for nested specifications, estimates as odds ratios with 95% confidence intervals, and an omnibus test for multi-level predictors. The odds-ratio direction must be verified against category ordering by a tiny simulated unit test before fitting the real data. Adjust for multiple testing across predeclared construct-level tests; do not report every uncorrected coefficient p-value as a discovery.

Test proportional odds. If it is materially violated, do not silently present the standard ordered-logit estimates as valid. Fit a documented alternative (partial proportional odds where a tested, reproducible implementation is available; otherwise multinomial logit as an explicitly less efficient sensitivity analysis), compare practical conclusions, and state the limitation. Keep the ordinal model interpretable; do not switch to a large black-box classifier merely to increase complexity.

**Required outputs**
- `reports/crm/qa47_model_specification.md`
- `reports/crm/qa47_ordinal_model_terms.csv`
- `reports/crm/qa47_model_comparison.csv`
- `reports/crm/qa47_model_diagnostics.json`
- `reports/crm/qa47_model_effects.png` (odds ratios with confidence intervals; if OR interpretation is not valid under the chosen fallback, relabel accordingly).

**Interpretation rule:** model estimates are conditional associations with stated intention in this cross-sectional sample. They are not causal intervention effects or validated individual churn predictions.

### 5.5 Bounded check: do exploratory clusters add CRM decision value?

Do not launch a new algorithm search. Use the existing preselected Specification A PAM k=4 labels as an exploratory diagnostic only, because Specification A excluded QA47 and QA46 from construction. First repair the missing QA49 post-cluster profiling.

- Reproduce the QA47 distribution by cluster, showing all five response categories and effect size. The existing near-identical means/omnibus result are evidence against claiming distinct discount-reduction continuation types.
- Analyse full-option QA49 by cluster and the four-category decision-view grouping as a prespecified sensitivity. Use an appropriate sparse-cell/Monte Carlo association test and Cramér’s V; show uncertainty and actual cluster sizes.
- Compare the size and interpretability of any cluster association with the easier lifecycle/QA47-tier results. Do not name hard personas unless evidence supports separation, stability, external differentiation, and actual decision value. Given the existing silhouette and stability findings, the default is to **not deploy cluster labels in the main CRM recommendation** unless new, independently reported evidence materially changes the decision.
- Specification B includes QA47 as an input, so any QA47 difference under Spec B is circular and may be shown only as construct-defining description. It is not independent validation.

**Required output:** `reports/crm/cluster_incremental_value_audit.md` plus a QA49 cluster cross-tab and test table.

## 6. CRM decision matrix — the central business deliverable

Create `reports/crm/CRM_DECISION_MATRIX.csv` and explain the recommendations in `reports/crm/CRM_DECISION_BRIEF.md`. One row per lifecycle × evidence-supported intention/need profile where sample counts permit.

Every proposed action must specify:
- target cohort and count/share (within the sample, not market sizing);
- observed stated-intention tier or barrier/preferred improvement;
- supporting evidence and denominator;
- confidence interval / effect size or explicit “descriptive only” flag;
- proposed CRM action (adoption, exploratory reactivation, or retention);
- operational owner/lever (e.g. transparent basket price, fee clarity, quality assurance, availability, refunds/support, onboarding/availability);
- what the survey supports versus what must be tested in a pilot;
- outcome metric to collect in a future experiment (actual repeat order, reactivation, incremental margin, repeat frequency, or opt-out), not just survey intention.

Potential actions are **pilot candidates**, not proven best interventions. For example, if quality/availability/service improvements are the leading preferences in a cohort, recommend testing an operational value proposition rather than claiming it will outperform discounts. Do not recommend blanket discount cuts from QA47 responses alone.

## 7. Statistical and reporting rules

- Make the analysis plan executable and deterministic; log software versions and random seeds.
- Report exact denominators, item coding, eligibility, effect sizes and 95% confidence intervals where estimable.
- Correct planned families of hypothesis tests with Holm. Clearly distinguish primary from exploratory analyses.
- Use bootstrap intervals only where the resampling unit and procedure are justified; report failed fits/resamples separately rather than converting failures into numerical values.
- Show distributions for ordinal variables. Means may be supplementary, not the only summary.
- Do not use “significant” as a synonym for “important.” Report effect magnitude and uncertainty.
- Do not treat the absence of a significant effect as proof of equivalence.
- Keep aggregate tables/figures only in version control. No row-level respondent, cluster, predicted probability or label exports may be committed.
- Make every chart traceable to a committed aggregate table and every recommendation traceable to a specific output row.

## 8. Gate 1D acceptance checklist

Gate 1D is complete only when all items are checked by a reproducible run:

- [ ] Gate 1C technical defects above are fixed and covered by regression tests.
- [ ] Full test suite passes from a documented clean setup, including synthetic fixtures.
- [ ] QA46, QA48 and QA49 analyses are generated from the workbook and pass denominator/routing assertions.
- [ ] QA47 ordinal model has documented specification, convergence and assumption checks; an explicit fallback is reported if needed.
- [ ] QA49 post-cluster profiling exists; Spec B circularity is clearly labelled.
- [ ] All corrections use full-precision p-values internally.
- [ ] Tables reconcile to cohort counts and row/column totals; no empty, duplicated or unexplained categories.
- [ ] CRM decision matrix contains evidence tags and pilot-validation metrics.
- [ ] Report has explicit provenance, sample, cross-sectional and stated-intention limitations.
- [ ] README accurately identifies current gate and reproduction path.
- [ ] No dashboard or polished final report is started until this gate is approved.

## 9. Literature and methodological anchors

These sources establish that existing methods are acceptable tools, not project novelty claims:

1. Chandra, A. (2026). *A Large-Scale Survey Dataset on Quick-Commerce Adoption, Ordering Patterns, Product Categories and Spending Behaviour among Indian Consumers*. Mendeley Data, V1. [DOI: 10.17632/cw88nb7822.1](https://data.mendeley.com/datasets/cw88nb7822/1). Source description, question instrument, files and license; actual sampling details remain unresolved.
2. Balasundaram, E. et al. (2025). *Digital Immediacy Adoption Framework (DiIA-F): Explaining Q-commerce Adoption in Indian Urban Centres*. Global Business Review. [https://doi.org/10.1177/09721509251374606](https://doi.org/10.1177/09721509251374606). Prior Indian adoption research using a survey and SEM.
3. Singh, S. et al. (2025). *Determinants of Consumer Loyalty in Quick Commerce: An Economic and Behavioral Perspective*. International Journal of Economic Practices and Theories. [Article](https://ijapt.org/index.php/journal/article/view/12). Prior survey/SEM work covering service quality, expectations, personalization, sustainability and perceived value.
4. Liu, P. et al. (2024). *A modified and weighted Gower distance-based clustering analysis for mixed type data: a simulation and empirical analyses*. BMC Medical Research Methodology, 24, 305. [https://doi.org/10.1186/s12874-024-02427-8](https://doi.org/10.1186/s12874-024-02427-8). Established mixed-data clustering and feature-weighting research.
5. *Subsampling-Based Consensus Hierarchical Clustering for Robust Customer Segmentation with Mixed-Type Data* (2026). Mathematics, 14(8), 1294. [https://doi.org/10.3390/math14081294](https://doi.org/10.3390/math14081294). Recent example combining Gower distance, comparison algorithms, internal metrics and resampling-based stability. Its implementation choices must be critically evaluated; do not copy methods mechanically.
6. Homburg, C. et al. / related market-segmentation stability literature; see *Stability of market segmentation with cluster analysis – A methodological approach* (2014). [ScienceDirect record](https://www.sciencedirect.com/science/article/pii/S0950329313002309). Supports treating segment stability as an empirical question, not an assumption.
7. CASRAI Editorial Board (2026). *Ordinal Logistic Regression and the Proportional-Odds Assumption*. [Guide](https://casrai.org/guides/ordinal-logistic-regression-proportional-odds). Practical specification and assumption-checking guidance for ordinal outcomes.
8. Statsmodels. *OrderedModel* documentation. [Documentation](https://www.statsmodels.org/dev/generated/statsmodels.miscmodels.ordinal_model.OrderedModel.html). Python model reference; verify package version and limitations in the chosen environment.

The final report must expand the related-work section beyond these anchors, include at least 15 carefully verified, relevant sources, and map each source to a construct, method, finding, or limitation actually used in this project. Do not pad the bibliography with generic or unverifiable citations.

## 10. Stop conditions

Stop and report a negative finding—do not invent a workaround—if:
- no defensible QA47 adjusted association model converges or assumptions cannot be checked;
- QA49 associations are too weak/uncertain to distinguish preferred CRM levers;
- lifecycle differences disappear or are practically negligible after uncertainty is shown;
- cluster labels add no meaningful information beyond lifecycle cohorts;
- the sample-provenance limitations prevent broader market claims.

A strong final project can conclude that **a simple lifecycle decision framework is better supported than hard unsupervised personas**. That is a result, not a failure.
