# Gate 1C.1 — Local Execution Task for the Implementation Worker

**Role:** implement and execute only; do not make analytical decisions or close the gate.  
**Repository:** `nayanojwal0810/Beyond_Discounts`  
**Branch:** `review/gate-1c1-crm-decision`  
**Status:** awaiting local execution with the source workbook. GitHub CI currently tests software paths with synthetic-only fixtures; that is not the real-data validation.

## Non-negotiable constraints

1. Use the already-provisioned source workbook at `data/raw/survey/Data.xlsx`, with its existing codebook and questionnaire. Do not download, substitute, merge or synthesize a replacement dataset.
2. Never commit `Data.xlsx`, `Code Book.docx`, `Questionairre.docx`, any row-level response, prepared distance matrix, individual cluster assignment, or other respondent-level derivative.
3. Never manually edit generated CSVs/JSON/PNG tables to match prose. Fix source code, rerun and report resulting differences.
4. Do not change the accepted cohort definitions, feature selection, response coding, statistical threshold, model predictors, or the project research question without the Principal Project Lead's approval.
5. Do not create personas or claim the current clusters are deployable. QA47 is stated continuation intention under a hypothetical reduction in discounts/promotions; QA46 is stated future-use intention; QA48 describes current non-use reasons; QA49 is one preferred improvement choice. None is observed purchase/churn or a causal intervention outcome.
6. Keep the pull request a draft. Do not merge, rename the branch, close the gate, or start dashboard/final-report styling.

## Step 1 — Environment

From the repository root, switch to this branch and sync it:

```bash
git fetch origin
git switch review/gate-1c1-crm-decision
git pull --ff-only origin review/gate-1c1-crm-decision
python --version
python -m pip install -r requirements.txt
```

Use Python 3.13 for the same interpreter line as the CI test environment. Record the Python and installed direct-dependency versions in the execution log.

## Step 2 — Run the pipeline in order

Run from the repository root and save terminal output to a separate local log (do not add the log if it contains any respondent-level data):

```bash
python scripts/audit_survey_data.py --file data/raw/survey/Data.xlsx --sheet Data --output docs/gates/GATE_0_SURVEY_AUDIT_SUMMARY.json
python scripts/run_eda.py --file data/raw/survey/Data.xlsx --sheet Data
python scripts/run_segmentation_experiments.py --survey-file data/raw/survey/Data.xlsx --validation-resamples 9999
python -m unittest discover -s tests -v
python scripts/run_crm_analysis.py --file data/raw/survey/Data.xlsx --sheet Data --out-dir reports/crm/tables --mc-resamples 10000 --seed 20261017
```

Do not run the CRM analysis before checking the segmentation pipeline has completed and the prepared holdout aligns. If a command fails, capture the exact error, fix the underlying cause, rerun from the earliest affected stage, and report the failure; do not conceal or skip it.

## Step 3 — Gate 1C.1 verification

Confirm all the following and report actual observed counts:

- [ ] Audit verifies the source workbook's shape, column semantics and special routing/codebook rules.
- [ ] Full test suite passes with the source workbook and regenerated local artifacts available.
- [ ] Feature preparation produces Spec A, Spec B and held-out QA46/QA47/QA49 data with aligned row counts/order.
- [ ] `stability_runs.csv` contains 160 diagnostic rows when all eight PAM configurations complete (2 specifications × 4 candidate k values × 20 resamples). Successful/failure counts in `stability_summary.csv` reconcile with it; no failure is represented as ARI = 0.
- [ ] `external_validation_summary.csv` includes QA46, QA47 and QA49 for the applicable Spec A/B PAM solutions. QA47 under Spec B is explicitly **construct-defining**, not independent validation.
- [ ] `cluster_preferred_improvement_profile.csv` contains 10 preferred-improvement options for each cluster in each PAM solution (360 rows expected across both specifications and k = 3, 4, 5, 6, assuming all configurations finish).
- [ ] Raw and Holm/Bonferroni-adjusted p-values remain unrounded through corrections; output precision is a presentation choice only.
- [ ] Generated aggregate tables and the segmentation decision report match. No unsupported statement of equivalence or validated CRM personas remains.
- [ ] `git status --short` and `git ls-files data/raw data/processed` show no raw/row-level files staged or tracked.

If any criterion fails, the gate remains **OPEN**. Do not declare success based only on successful script exit if artifacts are missing or disagree.

## Step 4 — Gate 1D real-data model and output audit

After Step 3 passes:

- [ ] Run the CRM script with the exact command above.
- [ ] Inspect `crm_analysis_run_metadata.csv` for the actual row/column/cohort counts and date.
- [ ] Inspect all QA46 response-category distributions, cohort test and uncertainty estimates.
- [ ] Inspect QA48 counts, prevalence intervals, Fisher tests and Holm corrections; preserve the distinction between current non-use barriers and the reason someone historically stopped ordering.
- [ ] Inspect QA49 full 10-option distributions, planned action-family distributions and all four Monte Carlo omnibus comparisons with Holm-adjusted p-values, denominators, Cramér's V and minimum expected count.
- [ ] Inspect `qa47_model_fit_summary.csv`: primary ordered-logit convergence, sensitivity model convergence, sample size and fit metrics.
- [ ] Inspect `qa47_model_diagnostics.csv` and `qa47_multinomial_sensitivity_status.csv`: if parallel slopes are rejected, confirm the conditional multinomial model is fit; if diagnostic status is inconclusive, label the ordered-logit interpretation unresolved rather than assume the assumption holds.
- [ ] Inspect QA49-added model comparison; interpret it as concurrent associational evidence only.
- [ ] Confirm generated output contains no respondent identifiers or row-level values.

Report findings neutrally, including null/weak results, model failures, warnings and any deviations. Do not invent personas or campaign-uplift claims.

## Step 5 — Return evidence for Principal Project Lead review

Provide:
1. Branch and current commit SHA.
2. Python and dependency versions.
3. Exact commands used and complete test summary.
4. Counts/status of all expected output files, including 160 stability rows and 360 QA49 cluster-profile rows if all configurations complete.
5. Warnings, resample failures, model convergence/assumption status and any deviations.
6. Generated-artifact diff from tracked aggregates/reports (do not include raw or row-level files).
7. Confirmation that no raw or row-level data were staged/tracked.

**Final rule:** the implementation worker reports evidence; only the Principal Project Lead can approve Gate 1C.1 or Gate 1D. Do not begin the dashboard until the decision matrix and statistical outputs are accepted.
