# Gate 1D — Lifecycle-Based CRM Decision Analysis Plan

**Project:** Beyond Discounts: A Lifecycle-Based CRM Decision Framework for Indian Quick Commerce  
**Status:** Analytical direction approved; implementation drafted in `scripts/run_crm_analysis.py`; synthetic tests pending CI; real-data results not yet produced  
**Data:** Chandra, *A Large-Scale Survey Dataset on Quick-Commerce Adoption* (Mendeley Data, DOI 10.17632/cw88nb7822.1; repository record declares CC BY 4.0).  
**Unit of analysis:** One survey respondent.  
**Study type:** Cross-sectional secondary analysis of self-reported survey responses.

## 1. Why this is the strongest project direction

The project should be useful even if unsupervised clustering does not reveal well-separated, actionable personas. The business decision is how to prioritise different kinds of customer engagement with the evidence available—not how to force every respondent into a catchy segment name.

Quick-commerce research on adoption and loyalty already exists. For example, Balasundaram et al. (2025) analysed adoption intentions among 487 urban Indian consumers using SEM, and Singh et al. (2025) studied loyalty among 460 urban consumers, reporting perceived value as their strongest factor. The India CX Report 2025 also discusses grocery experience, product availability, price transparency, delivery, quality and refunds. We therefore will **not** claim that survey-based quick-commerce loyalty research or customer segmentation itself is unique. Our applied contribution is to connect three questionnaire-defined lifecycle cohorts with stated intentions, barriers, one preferred improvement, and a transparent test of whether exploratory clusters add decision value beyond those simpler distinctions.

References:
- [Balasundaram et al. (2025), *Digital Immediacy Adoption Framework*](https://doi.org/10.1177/09721509251374606) — Indian urban q-commerce adoption, survey n=487, SEM.
- [Singh et al. (2025), *Determinants of Consumer Loyalty in Quick Commerce*](https://ijapt.org/index.php/journal/article/view/12) — survey n=460, SEM, perceived value strongest in that study.
- [KPMG India, *India CX Report 2025: Grocery*](https://kpmg.com/in/en/insights/2025/03/india-cx-report-2025/retail/grocery.html) — industry context on value, inventory, quality, delivery and service resolution.
- [Gower (1971), *A General Coefficient of Similarity and Some of Its Properties*](https://doi.org/10.2307/2528823) — basis for mixed-type dissimilarity.
- [Kaufman & Rousseeuw (1990), *Finding Groups in Data*](https://doi.org/10.1002/9780470316801) — foundational clustering reference.
- [Brant (1990), *Assessing Proportionality in the Proportional Odds Model*](https://pubmed.ncbi.nlm.nih.gov/2085632/) — assumption checking for ordinal logistic regression.
- [Statsmodels OrderedModel documentation](https://www.statsmodels.org/stable/generated/statsmodels.miscmodels.ordinal_model.OrderedModel.html) — ordered outcomes without assuming equal spacing between response codes.
- [Gower/PAM and mixed-type segmentation, 2024 methodological study](https://bmcmedresmethodol.biomedcentral.com/articles/10.1186/s12874-024-02427-8) — an example of weighting and feature-importance approaches for mixed data.
- [Recent Gower/consensus clustering method (2026)](https://www.mdpi.com/2227-7390/14/8/1294) — reinforces that clustering quality and subsampling stability require evaluation rather than assumption.

This reference list establishes initial positioning; the final report still needs a broader, critically synthesised related-work section with 15+ verified works before writing is considered complete.

## 2. Research question and supporting questions

### Primary research question

**Which lifecycle-based CRM actions are best supported by the observed sample's stated future-use intentions, discount-reduction continuation intentions, non-use barriers, and preferred service improvements?**

### Supporting questions

1. Which adoption, reactivation and retention needs differ descriptively across the three user cohorts?
2. Which measured behaviors and attitudes are associated with current users' stated intention to continue at the same frequency if discounts/promotions are reduced?
3. How do single-choice improvement preferences vary across lifecycle cohorts and stated continuation-intention tiers?
4. Do the exploratory unsupervised clusters demonstrate enough separation, stability and independent outcome differentiation to add useful CRM decision information beyond lifecycle cohort and stated-intention tiers?

These questions separate a business decision from a claim of novelty. Negative findings are acceptable when they change the recommended method or scope.

## 3. The cohort-first CRM framework

Use these labels in charts, tables and the dashboard. Keep the source-derived filters in the data dictionary.

| CRM audience | Survey-defined cohort | n | Primary use of evidence | Wording boundary |
|---|---|---:|---|---|
| Adoption prospects | Never ordered; currently report “never” | 376 | QA46 future-use intention; QA48 non-use barriers; QA49 preferred improvement | Barriers and preferences suggest hypotheses to test, not proven acquisition levers |
| Reactivation prospects | Ordered before; currently report “never” | 80 | QA46 future-use intention; QA48 current non-use reasons; QA49 preferred improvement | Call “previous users,” not verified churned/lapsed accounts; QA48 does not prove why they stopped |
| Current-user retention audience | Ever ordered and frequency response above “never” | 807 | QA47 discount-reduction continuation intention; QA49 preferred improvement; QA46 as secondary stated intention | Do not imply all respondents recently purchased or are transactionally active |

The current-user group is questionnaire-defined and includes its lowest-frequency response category. Therefore, the report should say **current-user cohort** rather than use “active customers” as a business-operational claim.

## 4. Outcome definitions and analytical contract

| Measure | Population / scale | Primary interpretation | Not permitted |
|---|---|---|---|
| QA46 — next-three-month use | All 1,263; ordered 1–5 | Stated future-use intention | Actual repeat use, conversion, retention |
| QA47 — continue if discounts reduce | Current-user cohort n=807; ordered 1–5 | Stated continuation intention under a hypothetical reduction in discounts/promotions | Real price elasticity, observed churn, causal impact of removing discounts |
| QA48 — reasons for non-use | Never + previous-user cohorts n=456; multi-response indicators | Stated reasons for current non-use | Proof of historical lapse cause or mutually exclusive causes |
| QA49 — preferred improvement | All 1,263; one categorical choice from 10 options | Single top stated preference | Actual demand, willingness to pay, guaranteed response to an intervention |
| QA12 — platforms ever used | Survey's historical use footprint | Historical platform-repertoire breadth | Loyalty, current multi-homing, or switching behavior without further evidence |

Treat the 1–5 items as ordered categorical outcomes. Do not presume equal spacing between adjacent response categories.

## 5. Analysis work packages

### 1D-A. Current-user continuation-intention model (primary adjusted analysis)

**Population:** 807 current-user respondents with substantive QA47 values.

**Outcome:** QA47 on its original 1–5 ordinal scale. The main result should be interpretable adjusted associations, not a black-box churn score.

**Pre-specified predictor blocks:**
- Usage and routine: QA15 order-frequency category and QA43 shopping-routine role.
- Price/promotion behaviors: QA28 discount-induced overspend, QA29 adding items to meet thresholds, QA33 cross-platform price comparison, and QA34 comparison with physical-store prices.
- Convenience: QA35 importance of fast delivery.
- Experience: documented QA37–QA40 composite, provided its codebook mapping and reliability calculation reproduce.
- Platform repertoire: QA12 count of platforms ever used; label it historically, not as current loyalty.
- Additional exploratory feature, only if defensible before model fitting: QA44 impulse/unplanned purchase tendency.

Keep the initial model parsimonious. Encode nominal predictors as categories, inspect outcome/category counts and collinearity, and report any excluded categories explicitly. Do not select variables by repeatedly trying models until significance appears.

**Models and checks:**
1. Fit an intercept-only ordinal-logit baseline.
2. Fit the pre-specified ordered-logit model with documented reference categories.
3. Report coefficients, odds ratios, 95% confidence intervals, raw p-values and Holm-adjusted p-values across predictor coefficients within each fitted model; show model sample size and explain the odds ratio for higher stated response categories.
4. Assess the proportional-odds/parallel-lines assumption. If it fails, use a defensible alternative (e.g. partial proportional odds if available and tested) or multinomial/threshold-specific sensitivity analysis rather than ignore the violation.
5. Conduct a pre-defined sensitivity check, such as ordered probit or a defensible alternative coding of the QA47 tiers. Do not use multiple versions as a significance hunt.
6. If a model includes QA49 preferred improvement, add it only as a clearly labeled second model to assess incremental association; QA49 is a stated preference, not a treatment assignment.
7. Do not describe associations as causal effects. Only introduce cross-validation if the project explicitly evaluates prediction; if so, report calibration and compare with the simple baseline, not just accuracy.

**Deliverables:** model specification JSON/CSV; fitted-model summary; coefficient and confidence-interval table; diagnostic/assumption results; sensitivity-analysis table; narrative that distinguishes effect magnitude from statistical significance.

### 1D-B. QA46 stated future-use intention across cohorts

Report the full five-category distribution, central tendency as supplementary description, and 95% uncertainty intervals by each cohort. Use an ordinal group comparison or a carefully specified ordinal model; report effect sizes and the three cohort denominators.

A cohort difference is descriptive/associational. The current-user cohort may naturally report greater intent because its members have used the category; that is not a causal lifecycle effect.

### 1D-C. QA48 non-use-barrier comparison

Compare prevalence of each barrier among never-users (n=376) and previous users (n=80). Show denominator and 95% interval for each prevalence. For group comparisons, use Fisher's exact test when sparse expected cells make asymptotic chi-square unreliable, and correct the predeclared family of barrier tests using Holm. Report the absolute percentage-point difference and its interval when feasible.

Do not interpret a non-significant comparison as equivalence. The smaller previous-user cohort may have limited precision. A barrier cited now by a previous user is not definitive evidence of the reason for their earlier discontinuation.

### 1D-D. QA49 preferred improvement — the core CRM translation analysis

Produce these views:
1. Full 10-option distribution across the entire sample.
2. Full 10-option distribution within each of the three lifecycle cohorts.
3. Current-user QA49 distribution by QA47 tier (codes 1–2 lower stated continuation intention; 3 uncertain; 4–5 higher stated continuation intention).
4. The same views using predeclared grouped action families for decision-making, while preserving the full response-option table in the appendix.

Pre-declared display groupings:
- **Product price / promotion:** QA49 options 1–2.
- **Fees / delivery charges:** option 3.
- **Non-price product and service proposition:** options 4–9 (quality/freshness, assortment, reliable availability, speed, refunds/support, and local availability).
- **No selected improvement / no intention:** option 10.

For comparisons, use an omnibus association test with exact/Monte Carlo inference if cell sparsity makes asymptotic chi-square questionable. Report Cramér's V and uncertainty, and use adjusted post-hoc comparisons only if the omnibus analysis justifies them. The groups above are a communication aid, not proof those choices have identical meanings.

**Preliminary signal from the currently committed aggregate summaries (must be regenerated after Gate 1C.1):** about 31.2% selected product price/promotion, 14.3% selected fee reduction, 50.0% selected one of the non-price product/service options, and 4.5% selected “none.” Non-price options were selected by roughly half of each lifecycle cohort. Treat these as stated preferences—not intervention effects—and revalidate the values during the next local run.

### 1D-E. Does unsupervised clustering add decision value?

Do not make more algorithms the main project. Use the existing Spec A clustering as an exploratory benchmark because QA47 was held out from its defining features. Spec B includes QA47 and must never be validated against QA47 as though that were independent evidence.

The comparison should answer whether clusters are meaningfully separated, reproducible and associated with *independent* outcomes or preferred improvement choices. Compare them against the simpler lifecycle cohorts using:
- internal separation and negative-silhouette rates;
- successful resampling stability with failed runs accounted for;
- independent QA46 differences after multiplicity correction;
- QA49 preference distribution / effect size by cluster; and
- whether the resulting action matrix actually recommends different, evidence-supported actions.

If no clear added value is shown, document that finding and keep lifecycle-based CRM segmentation. Run one alternative method (for example, an explicitly specified latent-class model) only if a methodological reason remains after 1D-A–1D-D; define variables, class-count selection, minimum class size, multiple initialisations and stability checks before fitting. Do not select an alternative just because it returns nicer personas.

## 6. Statistical reporting standard

- Pre-register the primary hypotheses and test families before fitting the models.
- Show denominators and missing/routing rules with every result.
- Report estimates, effect sizes and 95% uncertainty intervals alongside p-values.
- Apply Holm correction within the explicitly defined family of related inferential tests.
- Use exact or Monte Carlo procedures when small expected cell counts invalidate a simple chi-square approximation.
- Do not describe a non-significant finding as “no relationship,” “identical,” or “homogeneous.”
- Do not remove outliers/categories or change coding after seeing which choice improves significance without recording it as sensitivity analysis.
- Separate **descriptive**, **associational**, **exploratory**, and **pilot-candidate** findings. Nothing in this cross-sectional survey is causal evidence.

## 7. Evidence-to-action matrix

The final Gate 1D output is a decision matrix, not a list of invented personas. Each proposed action must include:

| Field | Requirement |
|---|---|
| Audience | Explicit lifecycle cohort and, for current users, the relevant QA47 intention tier where justified |
| Evidence | Source variable, denominator, prevalence or adjusted estimate, uncertainty |
| Need / barrier | Only what the survey item actually captures |
| Candidate CRM response | A proposed message, value proposition or experience improvement—not a proven successful treatment |
| Evidence strength | Descriptive / associational / exploratory / pilot candidate |
| Limitation | Sampling, self-report, small subgroup, multiple testing, or missing outcome |
| Validation design | A real platform would test the candidate through a controlled campaign or service experiment |
| Success metric | Actual conversion/repeat orders, contribution margin, unsubscribes/complaints or service KPIs—measured by the company, not inferred from this survey |

A plausible pilot design compares an explicitly defined non-price service/value message or fee-transparency proposition with a conventional discount-led message, stratifies or randomises eligible real customers, and measures actual incremental repeat orders and contribution margin. This survey can help nominate hypotheses for that experiment; it cannot tell us the campaign uplift.

## 8. Dashboard and final report — only after analysis approval

### Dashboard (Gate 2)
Build an evidence-linked CRM decision cockpit with:
- lifecycle cohort sizes and QA46/QA47 response distributions;
- QA48 barrier prevalence and uncertainty;
- QA49 preferences overall, by cohort and by current-user QA47 tier;
- the adjusted QA47 association model and diagnostics;
- optional clustering quality and incremental-utility comparison;
- an evidence badge/label that distinguishes descriptive associations from untested pilot ideas.

Avoid flashy hard-persona cards when clusters are weak. Each displayed insight must link back to a source table, denominator and interpretation limit.

### Final report (Gate 3)
Write after the analysis is frozen: research context, 15+ critically synthesised related works, source/provenance and sampling limitation, coding/routing decisions, hypotheses, methods, results and effect sizes, clustering negative findings, CRM decision matrix, pilot-test recommendations, dashboard, reproducibility instructions and limitations. The literature review must distinguish direct Indian q-commerce evidence from adjacent e-commerce/customer-segmentation methods; do not inflate source relevance.

## 9. Implementation status

The initial implementation is in `scripts/run_crm_analysis.py`. It writes aggregate-only QA46 distributions and cohort comparison, QA48 barrier prevalence and Fisher/Holm comparisons, QA49 full-option/action-family distributions and fixed-margin Monte Carlo association tests, plus current-user QA47 ordered-logit models, categorical-coding/link sensitivity checks, a parallel-slopes diagnostic, and a conditional multinomial sensitivity path if parallel slopes are rejected. No real-workbook outputs are accepted until the script is run locally after Gate 1C.1; convergence and diagnostic results must be examined rather than assumed.

## 9. Gate sequence and sign-off

| Gate | Deliverable | Approval condition |
|---|---|---|
| 1C.1 | Correct p-value precision, stability failure accounting, regression tests, reproducible rerun | All tests and regenerated outputs reconcile; no row-level data in Git |
| 1D | Ordinal association model + QA46/48/49 lifecycle analysis + evidence-tagged decision matrix | Definitions and denominators verified; uncertainty and limitations reported; no causal overclaim |
| 1E (conditional) | One bounded alternative segmentation sensitivity check, only if it addresses a decision gap | Pre-specified method and stability rules; added decision value assessed independently |
| 2 | Dashboard | All views trace to frozen aggregate tables and explain uncertainty |
| 3 | Final academic report / presentation | Literature review verified; conclusions match tables; no unsupported platform-specific or causal claims |

**Immediate next task:** verify the draft CI checks, then have the implementation worker execute Gate 1C.1 locally using the untracked source workbook, return exact test output, regenerated `stability_runs.csv`, artifact diff, environment versions and commit SHA. Once Gate 1C.1 is approved, run `python scripts/run_crm_analysis.py --file data/raw/survey/Data.xlsx --sheet Data --out-dir reports/crm/tables` and review all generated outputs before dashboard work. The script's synthetic test fixtures are software tests only and must never be reported as survey results.
