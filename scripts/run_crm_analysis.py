#!/usr/bin/env python3
"""Gate 1D: lifecycle-based CRM evidence analysis for the quick-commerce survey.

Outputs are aggregate-only. QA46/QA47 are stated intentions, QA48 is a stated
current non-use reason, and QA49 is a single stated preference; none is a
transactional outcome or causal treatment effect.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from typing import Any

import numpy as np
import pandas as pd
from scipy import stats
import statsmodels.api as sm
from statsmodels.miscmodels.ordinal_model import OrderedModel


DEFAULT_FILE = os.path.join("data", "raw", "survey", "Data.xlsx")
DEFAULT_SHEET = "Data"
DEFAULT_OUT = os.path.join("reports", "crm", "tables")
EXPECTED_SHAPE = (1263, 130)
EXPECTED_COHORTS = {"Never User": 376, "Previous User": 80, "Current Active User": 807}

QA46_LABELS = {
    1: "Very unlikely",
    2: "Unlikely",
    3: "Not sure",
    4: "Likely",
    5: "Very likely",
}
QA49_LABELS = {
    1: "Lower product prices",
    2: "More discounts and coupons",
    3: "Lower or no delivery fees",
    4: "Better product quality and freshness",
    5: "Wider product range / assortment",
    6: "More reliable product availability",
    7: "Faster delivery times",
    8: "Better refunds / customer support",
    9: "Service availability in my area",
    10: "None / I do not intend to use it",
}
QA49_ACTION_FAMILIES = {
    1: "Product price / promotions",
    2: "Product price / promotions",
    3: "Fees / delivery charges",
    4: "Non-price product / service proposition",
    5: "Non-price product / service proposition",
    6: "Non-price product / service proposition",
    7: "Non-price product / service proposition",
    8: "Non-price product / service proposition",
    9: "Non-price product / service proposition",
    10: "No selected improvement / no intention",
}
QA48_BARRIERS = [
    ("Reason Service Unavailable", "Service not available in my area"),
    ("Reason Prefer Physical", "Prefer shopping in physical stores"),
    ("Reason Prices High", "Prices are too high"),
    ("Reason Delivery Fees", "Delivery charges / fees too high"),
    ("Reason Distrust Quality", "Do not trust product quality"),
    ("Reason Prefer Inspect", "Prefer to inspect products before purchase"),
    ("Reason Impulsive Spending Concern", "Concern about excessive / impulsive spending"),
    ("Reason No Need Rapid", "Do not need rapid delivery"),
    ("Reason Privacy Payment Concern", "Privacy / digital payment concerns"),
    ("Reason Unfamiliar Apps", "Unfamiliar with the apps"),
]
PLATFORM_COLS = [
    "Used Blinkit", "Used Zepto", "Used Swiggy Instamart",
    "Used BigBasket BBNow", "Used Flipkart Minutes", "Used Amazon Rapid",
]
QA47_PREDICTOR_NUMERIC = [
    "Order Frequency",
    "Discount Overspend",
    "Threshold Extra Items",
    "Compare Platform Prices",
    "Compare Physical Prices",
    "Fast Delivery Importance",
    "platforms_used_count",
    "service_satisfaction_composite",
]
QA47_PREDICTOR_CATEGORICAL = ["Shopping Routine Role"]
QA47_TREND_TERMS = [
    "Order Frequency", "Discount Overspend", "Threshold Extra Items",
    "Compare Platform Prices", "Compare Physical Prices", "Fast Delivery Importance",
    "platforms_used_count", "service_satisfaction_composite",
]


def parse_arguments(args=None):
    parser = argparse.ArgumentParser(description="Run the Gate 1D lifecycle-based CRM evidence analysis.")
    parser.add_argument("--file", default=DEFAULT_FILE, help="Path to the source survey workbook.")
    parser.add_argument("--sheet", default=DEFAULT_SHEET, help="Worksheet name.")
    parser.add_argument("--out-dir", default=DEFAULT_OUT, help="Directory for aggregate-only CSV outputs.")
    parser.add_argument("--mc-resamples", type=int, default=10000, help="Monte Carlo tables for QA49 tests.")
    parser.add_argument("--seed", type=int, default=20261017, help="Deterministic random seed.")
    parser.add_argument("--skip-model", action="store_true", help="Generate descriptive/inference tables but skip ordinal-model fitting.")
    return parser.parse_args(args)


def derive_cohorts(df: pd.DataFrame, *, strict: bool = False) -> pd.DataFrame:
    """Derive the three source-defined cohorts and predeclared analysis variables."""
    source_shape = df.shape
    required = [
        "Ever Ordered through a Quick-Commerce Platform", "Order Frequency",
        "Next 3 Month Use", "Continue If Discounts Reduced", "Improvement",
        "Shopping Routine Role", *PLATFORM_COLS,
        "Discount Overspend", "Threshold Extra Items", "Compare Platform Prices",
        "Compare Physical Prices", "Fast Delivery Importance",
        "Overall Satisfaction", "Product Quality Satisfaction",
        "Delivery Reliability Satisfaction", "Value Money Satisfaction",
        *[col for col, _ in QA48_BARRIERS],
    ]
    missing = sorted(set(required) - set(df.columns))
    if missing:
        raise ValueError(f"Required survey columns are missing: {missing}")

    out = df.copy()
    ever = pd.to_numeric(out["Ever Ordered through a Quick-Commerce Platform"], errors="coerce")
    freq = pd.to_numeric(out["Order Frequency"], errors="coerce")
    condition_never = (ever == 0) & (freq == 1)
    condition_previous = (ever == 1) & (freq == 1)
    condition_current = (ever == 1) & (freq > 1)

    cohort = pd.Series("Unknown", index=out.index, dtype="object")
    cohort.loc[condition_never] = "Never User"
    cohort.loc[condition_previous] = "Previous User"
    cohort.loc[condition_current] = "Current Active User"
    if (cohort == "Unknown").any():
        unknown_rows = int((cohort == "Unknown").sum())
        raise ValueError(f"{unknown_rows} rows could not be assigned to one of the three verified cohorts.")
    out["user_subgroup"] = cohort

    if strict:
        if source_shape != EXPECTED_SHAPE:
            raise ValueError(f"Unexpected source workbook shape {source_shape}; expected {EXPECTED_SHAPE}.")
        observed = out["user_subgroup"].value_counts().to_dict()
        if observed != EXPECTED_COHORTS:
            raise ValueError(f"Cohort counts do not match the audited baseline: {observed}")
    if not out["Next 3 Month Use"].isin([1, 2, 3, 4, 5]).all():
        raise ValueError("QA46 must contain substantive values 1..5 for all respondents.")
    if not out["Improvement"].isin(range(1, 11)).all():
        raise ValueError("QA49 must contain substantive values 1..10 for all respondents.")

    current = out["user_subgroup"] == "Current Active User"
    noncurrent = ~current
    if not out.loc[current, "Continue If Discounts Reduced"].isin([1, 2, 3, 4, 5]).all():
        raise ValueError("QA47 must contain values 1..5 for the current-user cohort.")
    if not out.loc[noncurrent, "Continue If Discounts Reduced"].eq(6).all():
        raise ValueError("QA47 routing failed: non-current respondents should have source-defined code 6.")

    current_mask = out["user_subgroup"] == "Current Active User"
    current_domains = {
        "Order Frequency": set(range(2, 8)),
        "Shopping Routine Role": set(range(1, 6)),
        "Discount Overspend": set(range(1, 6)),
        "Threshold Extra Items": set(range(1, 6)),
        "Compare Platform Prices": set(range(1, 6)),
        "Compare Physical Prices": set(range(1, 6)),
        "Fast Delivery Importance": set(range(1, 6)),
    }
    for column, allowed in current_domains.items():
        if not out.loc[current_mask, column].isin(allowed).all():
            raise ValueError(f"Current-user predictor {column!r} contains an out-of-domain or skip-coded value.")
    for column in PLATFORM_COLS:
        if not out[column].isin([0, 1]).all():
            raise ValueError(f"Platform footprint column {column!r} must be binary.")
    for column, _ in QA48_BARRIERS:
        if not out[column].isin([0, 1]).all():
            raise ValueError(f"QA48 barrier column {column!r} must be binary.")

    out["platforms_used_count"] = out[PLATFORM_COLS].apply(pd.to_numeric, errors="coerce").sum(axis=1)
    satisfaction_cols = [
        "Overall Satisfaction", "Product Quality Satisfaction",
        "Delivery Reliability Satisfaction", "Value Money Satisfaction",
    ]
    for column in satisfaction_cols:
        if not out.loc[current_mask, column].isin([1, 2, 3, 4, 5]).all():
            raise ValueError(f"Current-user satisfaction item {column!r} contains an out-of-domain or skip-coded value.")
    out["service_satisfaction_composite"] = out[satisfaction_cols].apply(
        pd.to_numeric, errors="coerce"
    ).mean(axis=1)
    out["qa47_tier"] = pd.Series(pd.NA, index=out.index, dtype="object")
    out.loc[current & out["Continue If Discounts Reduced"].isin([1, 2]), "qa47_tier"] = "Lower intention (1-2)"
    out.loc[current & out["Continue If Discounts Reduced"].eq(3), "qa47_tier"] = "Uncertain (3)"
    out.loc[current & out["Continue If Discounts Reduced"].isin([4, 5]), "qa47_tier"] = "Higher intention (4-5)"
    out["qa49_action_family"] = out["Improvement"].map(QA49_ACTION_FAMILIES)
    return out


def wilson_ci(successes: int, total: int, alpha: float = 0.05) -> tuple[float, float]:
    """Wilson score interval for a binomial proportion, returned on a 0..1 scale."""
    if total <= 0:
        return (float("nan"), float("nan"))
    z = float(stats.norm.ppf(1 - alpha / 2))
    p = successes / total
    denom = 1 + z * z / total
    centre = (p + z * z / (2 * total)) / denom
    half = z * np.sqrt((p * (1 - p) / total) + (z * z / (4 * total * total))) / denom
    return (max(0.0, centre - half), min(1.0, centre + half))


def _distribution_rows(df: pd.DataFrame, *, group_name: str, column: str, labels: dict[int, str],
                       codes: list[int], value_name: str) -> list[dict[str, Any]]:
    n = len(df)
    rows = []
    for code in codes:
        count = int((df[column] == code).sum())
        lo, hi = wilson_ci(count, n)
        rows.append({
            "group": group_name, "measure": value_name, "response_code": int(code),
            "response_label": labels[int(code)], "n_group": int(n), "count": count,
            "share": count / n if n else np.nan, "percent": 100 * count / n if n else np.nan,
            "ci95_low_percent": 100 * lo, "ci95_high_percent": 100 * hi,
        })
    return rows


def build_qa46_distribution(df: pd.DataFrame) -> pd.DataFrame:
    labels = QA46_LABELS
    groups = [
        ("All respondents", df),
        ("Never users", df[df["user_subgroup"] == "Never User"]),
        ("Previous users", df[df["user_subgroup"] == "Previous User"]),
        ("Current-user cohort", df[df["user_subgroup"] == "Current Active User"]),
    ]
    rows = []
    for name, group in groups:
        rows.extend(_distribution_rows(group, group_name=name, column="Next 3 Month Use",
                                      labels=labels, codes=list(range(1, 6)), value_name="QA46 stated future-use intention"))
    return pd.DataFrame(rows)


def build_qa49_distributions(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    groups = [
        ("All respondents", df),
        ("Never users", df[df["user_subgroup"] == "Never User"]),
        ("Previous users", df[df["user_subgroup"] == "Previous User"]),
        ("Current-user cohort", df[df["user_subgroup"] == "Current Active User"]),
        ("Current-user: lower QA47 intention (1-2)", df[(df["user_subgroup"] == "Current Active User") & df["qa47_tier"].eq("Lower intention (1-2)")]),
        ("Current-user: uncertain QA47 intention (3)", df[(df["user_subgroup"] == "Current Active User") & df["qa47_tier"].eq("Uncertain (3)")]),
        ("Current-user: higher QA47 intention (4-5)", df[(df["user_subgroup"] == "Current Active User") & df["qa47_tier"].eq("Higher intention (4-5)")]),
    ]
    option_rows = []
    family_rows = []
    family_labels = {
        "Product price / promotions": "Product price / promotions",
        "Fees / delivery charges": "Fees / delivery charges",
        "Non-price product / service proposition": "Non-price product / service proposition",
        "No selected improvement / no intention": "No selected improvement / no intention",
    }
    family_codes = {
        "Product price / promotions": [1, 2],
        "Fees / delivery charges": [3],
        "Non-price product / service proposition": [4, 5, 6, 7, 8, 9],
        "No selected improvement / no intention": [10],
    }
    for name, group in groups:
        option_rows.extend(_distribution_rows(group, group_name=name, column="Improvement",
            labels=QA49_LABELS, codes=list(range(1, 11)), value_name="QA49 single preferred improvement"))
        n = len(group)
        for family, codes in family_codes.items():
            count = int(group["Improvement"].isin(codes).sum())
            lo, hi = wilson_ci(count, n)
            family_rows.append({
                "group": name, "action_family": family, "n_group": n, "count": count,
                "share": count / n if n else np.nan, "percent": 100 * count / n if n else np.nan,
                "ci95_low_percent": 100 * lo, "ci95_high_percent": 100 * hi,
                "options_in_family": ",".join(map(str, codes)),
            })
    return pd.DataFrame(option_rows), pd.DataFrame(family_rows)


def holm_adjust(p_values: list[float]) -> list[float]:
    """Holm step-down family-wise adjusted p-values, returned in input order."""
    p = np.asarray(p_values, dtype=float)
    if not len(p):
        return []
    if np.any(~np.isfinite(p)) or np.any((p < 0) | (p > 1)):
        raise ValueError("p-values must be finite and in [0,1].")
    order = np.argsort(p)
    adjusted_sorted = np.maximum.accumulate((len(p) - np.arange(len(p))) * p[order])
    adjusted_sorted = np.minimum(adjusted_sorted, 1.0)
    adjusted = np.empty(len(p), dtype=float)
    adjusted[order] = adjusted_sorted
    return adjusted.tolist()


def newcombe_difference_ci(success_a: int, total_a: int, success_b: int, total_b: int) -> tuple[float, float]:
    """Newcombe hybrid-score 95% interval for p_a - p_b."""
    p_a = success_a / total_a if total_a else np.nan
    p_b = success_b / total_b if total_b else np.nan
    if not np.isfinite(p_a) or not np.isfinite(p_b):
        return (float("nan"), float("nan"))
    a_lo, a_hi = wilson_ci(success_a, total_a)
    b_lo, b_hi = wilson_ci(success_b, total_b)
    d = p_a - p_b
    lower = d - np.sqrt((p_a - a_lo) ** 2 + (b_hi - p_b) ** 2)
    upper = d + np.sqrt((a_hi - p_a) ** 2 + (p_b - b_lo) ** 2)
    return (max(-1.0, lower), min(1.0, upper))


def build_qa48_tables(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    never = df[df["user_subgroup"] == "Never User"]
    previous = df[df["user_subgroup"] == "Previous User"]
    prevalence_rows = []
    test_rows = []
    raw_p_values = []
    for col, label in QA48_BARRIERS:
        # Source questionnaire is multi-response; percentages are not intended to sum to 100%.
        n_never = len(never)
        n_prev = len(previous)
        cnt_never = int((never[col] == 1).sum())
        cnt_prev = int((previous[col] == 1).sum())
        lo_n, hi_n = wilson_ci(cnt_never, n_never)
        lo_p, hi_p = wilson_ci(cnt_prev, n_prev)
        prevalence_rows.extend([
            {"cohort": "Never users", "barrier": label, "source_column": col, "n": n_never,
             "count": cnt_never, "percent": 100 * cnt_never / n_never,
             "ci95_low_percent": 100 * lo_n, "ci95_high_percent": 100 * hi_n},
            {"cohort": "Previous users", "barrier": label, "source_column": col, "n": n_prev,
             "count": cnt_prev, "percent": 100 * cnt_prev / n_prev,
             "ci95_low_percent": 100 * lo_p, "ci95_high_percent": 100 * hi_p},
        ])
        table = np.array([[cnt_never, n_never - cnt_never], [cnt_prev, n_prev - cnt_prev]], dtype=int)
        odds, p = stats.fisher_exact(table, alternative="two-sided")
        diff_lo, diff_hi = newcombe_difference_ci(cnt_prev, n_prev, cnt_never, n_never)
        raw_p_values.append(float(p))
        test_rows.append({
            "barrier": label, "source_column": col,
            "never_n": n_never, "never_count": cnt_never, "never_percent": 100 * cnt_never / n_never,
            "previous_n": n_prev, "previous_count": cnt_prev, "previous_percent": 100 * cnt_prev / n_prev,
            "difference_prev_minus_never_pp": 100 * (cnt_prev / n_prev - cnt_never / n_never),
            "difference_ci95_low_pp": 100 * diff_lo, "difference_ci95_high_pp": 100 * diff_hi,
            "odds_ratio_prev_vs_never": float(odds), "fisher_exact_p_value": float(p),
            "interpretation_limit": "A reported current non-use barrier does not establish why a previous user stopped; non-significance is not equivalence."
        })
    adjusted = holm_adjust(raw_p_values)
    for row, padj in zip(test_rows, adjusted):
        row["holm_adjusted_p_value"] = padj
        row["significant_after_holm_0_05"] = bool(padj < 0.05)
    return pd.DataFrame(prevalence_rows), pd.DataFrame(test_rows)


def monte_carlo_chi_square(table: np.ndarray, *, n_resamples: int = 10000, seed: int = 20261017) -> dict[str, Any]:
    """Pearson test of independence with fixed-margin Monte Carlo calibration."""
    table = np.asarray(table, dtype=int)
    if table.ndim != 2:
        raise ValueError("Contingency table must be two-dimensional.")
    # Drop empty margins so no zero expected counts enter the statistic.
    table = table[table.sum(axis=1) > 0, :]
    table = table[:, table.sum(axis=0) > 0]
    if table.shape[0] < 2 or table.shape[1] < 2:
        raise ValueError("At least two non-empty rows and columns are required.")
    if n_resamples < 999:
        raise ValueError("Use at least 999 Monte Carlo resamples for decision-report inference.")
    n = int(table.sum())
    rows = table.sum(axis=1)
    cols = table.sum(axis=0)
    expected = np.outer(rows, cols) / n
    observed_stat = float(np.sum((table - expected) ** 2 / expected))
    df = int((table.shape[0] - 1) * (table.shape[1] - 1))
    rng = np.random.default_rng(seed)
    try:
        from scipy.stats import random_table
        simulations = random_table.rvs(rows, cols, size=n_resamples, random_state=rng)
        stats_sim = np.sum((simulations - expected[None, :, :]) ** 2 / expected[None, :, :], axis=(1, 2))
        p_value = (int(np.count_nonzero(stats_sim >= observed_stat - 1e-12)) + 1) / (n_resamples + 1)
        method = "Pearson chi-square statistic; fixed-margin Monte Carlo random-table test"
    except (ImportError, AttributeError):
        # Fallback: permutation of group labels preserves row totals and the overall response distribution.
        labels = np.repeat(np.arange(table.shape[0]), rows)
        outcomes = np.concatenate([np.repeat(np.arange(table.shape[1]), table[i]) for i in range(table.shape[0])])
        count_ge = 0
        for _ in range(n_resamples):
            perm = rng.permutation(labels)
            sim = np.zeros_like(table)
            np.add.at(sim, (perm, outcomes), 1)
            sim_expected = np.outer(sim.sum(axis=1), sim.sum(axis=0)) / n
            sim_stat = float(np.sum((sim - sim_expected) ** 2 / sim_expected))
            count_ge += sim_stat >= observed_stat - 1e-12
        p_value = (count_ge + 1) / (n_resamples + 1)
        method = "Pearson chi-square statistic; label-permutation Monte Carlo test"
    cramers_v = float(np.sqrt(observed_stat / (n * min(table.shape[0] - 1, table.shape[1] - 1))))
    return {
        "n": n, "rows": int(table.shape[0]), "columns": int(table.shape[1]),
        "pearson_chi2_statistic": observed_stat, "asymptotic_df": df,
        "asymptotic_p_value_reference_only": float(stats.chi2.sf(observed_stat, df)),
        "monte_carlo_p_value": float(p_value), "monte_carlo_resamples": int(n_resamples),
        "min_expected_cell": float(expected.min()), "cramers_v": cramers_v, "test_method": method,
    }


def build_qa49_association_tests(df: pd.DataFrame, *, n_resamples: int, seed: int) -> pd.DataFrame:
    groups = [
        ("Never users", df[df["user_subgroup"] == "Never User"]),
        ("Previous users", df[df["user_subgroup"] == "Previous User"]),
        ("Current-user cohort", df[df["user_subgroup"] == "Current Active User"]),
    ]
    full = pd.crosstab(df["user_subgroup"], df["Improvement"]).reindex(
        index=["Never User", "Previous User", "Current Active User"], columns=list(range(1, 11)), fill_value=0
    )
    # Build each action-family column once: several QA49 options map to the same family.
    action = pd.DataFrame({family: df.loc[df["qa49_action_family"] == family].groupby("user_subgroup").size()
                           for family in dict.fromkeys(QA49_ACTION_FAMILIES.values())}).reindex(
        index=["Never User", "Previous User", "Current Active User"], fill_value=0
    )
    current = df[df["user_subgroup"] == "Current Active User"]
    tier_order = ["Lower intention (1-2)", "Uncertain (3)", "Higher intention (4-5)"]
    tier_full = pd.crosstab(current["qa47_tier"], current["Improvement"]).reindex(
        index=tier_order, columns=list(range(1, 11)), fill_value=0
    )
    tier_action = pd.DataFrame({
        family: current.loc[current["qa49_action_family"] == family].groupby("qa47_tier").size()
        for family in dict.fromkeys(QA49_ACTION_FAMILIES.values())
    }).reindex(index=tier_order, fill_value=0)

    tests = [
        ("Lifecycle cohort × QA49 option (10 categories)", full.to_numpy(), seed),
        ("Lifecycle cohort × QA49 action family (4 groups)", action.to_numpy(), seed + 1),
        ("Current-user QA47 tier × QA49 option (10 categories)", tier_full.to_numpy(), seed + 2),
        ("Current-user QA47 tier × QA49 action family (4 groups)", tier_action.to_numpy(), seed + 3),
    ]
    out = []
    for comparison, table, test_seed in tests:
        test = monte_carlo_chi_square(table, n_resamples=n_resamples, seed=test_seed)
        out.append({"comparison": comparison, **test})
    return pd.DataFrame(out)


def run_parallel_slopes_diagnostic(y: np.ndarray, X: pd.DataFrame) -> dict[str, Any]:
    """Joint robust Wald test for equal slopes across four cumulative binary logits.

    This is a transparent parallel-slopes diagnostic. It is not labelled as the
    exact Brant test implementation; the sandwich covariance accounts for the
    same respondent contributing to multiple cumulative splits.
    """
    design = sm.add_constant(X.astype(float), has_constant="add").to_numpy(dtype=float)
    thresholds = sorted(np.unique(y))
    if len(thresholds) < 3:
        return {"status": "INCONCLUSIVE", "detail": "Fewer than three observed outcome categories."}
    cuts = thresholds[:-1]
    k_models, n, p = len(cuts), design.shape[0], design.shape[1]
    estimates, scores, breads = [], [], []
    try:
        for cut in cuts:
            binary_y = (y > cut).astype(int)
            model = sm.GLM(binary_y, design, family=sm.families.Binomial())
            fit = model.fit(maxiter=200, disp=0)
            if not bool(fit.converged) or not np.isfinite(fit.params).all():
                return {"status": "INCONCLUSIVE", "detail": f"Cumulative logit did not converge at cut {cut}."}
            prob = np.asarray(fit.predict(design), dtype=float)
            prob = np.clip(prob, 1e-8, 1 - 1e-8)
            weight = prob * (1 - prob)
            hessian = design.T @ (design * weight[:, None])
            breads.append(np.linalg.pinv(hessian))
            score_i = design * (binary_y - prob)[:, None]
            scores.append(score_i)
            estimates.append(np.asarray(fit.params, dtype=float))
        # Each respondent contributes a stacked score vector across thresholds.
        stacked_scores = np.concatenate(scores, axis=1)
        meat = stacked_scores.T @ stacked_scores
        bread = np.zeros((k_models * p, k_models * p), dtype=float)
        for j, inv_hessian in enumerate(breads):
            sl = slice(j * p, (j + 1) * p)
            bread[sl, sl] = inv_hessian
        covariance = bread @ meat @ bread
        beta = np.concatenate(estimates)
        # Do not constrain the distinct intercepts; test slope equality only.
        restrictions = []
        for model_index in range(1, k_models):
            for predictor_index in range(1, p):
                row = np.zeros(k_models * p, dtype=float)
                row[model_index * p + predictor_index] = 1.0
                row[predictor_index] = -1.0
                restrictions.append(row)
        R = np.vstack(restrictions)
        diff = R @ beta
        cov_diff = R @ covariance @ R.T
        rank = int(np.linalg.matrix_rank(cov_diff, tol=1e-10))
        if rank == 0:
            return {"status": "INCONCLUSIVE", "detail": "Parallel-slopes covariance matrix is rank zero."}
        wald = float(diff @ np.linalg.pinv(cov_diff) @ diff)
        p_value = float(stats.chi2.sf(wald, rank))
        return {
            "status": "COMPLETED", "method": "Stacked cumulative-logit slope-equality Wald test with respondent-level sandwich covariance",
            "n": int(n), "threshold_models": int(k_models), "slope_parameters_per_model": int(p - 1),
            "wald_chi2": wald, "df": rank, "p_value": p_value,
            "interpretation_limit": "Diagnostic for the proportional-odds/parallel-slopes assumption; interpret alongside model fit and sensitivity analysis."
        }
    except Exception as exc:
        return {"status": "INCONCLUSIVE", "detail": f"{type(exc).__name__}: {str(exc)[:240]}"}


def _fit_ordered_model(y: pd.Series, X: pd.DataFrame, *, distribution: str, model_name: str) -> tuple[Any | None, dict[str, Any]]:
    try:
        if X.columns.duplicated().any():
            raise ValueError("Design matrix contains duplicate predictor names.")
        if not np.isfinite(X.to_numpy(dtype=float)).all():
            raise ValueError("Design matrix has non-finite values.")
        model = OrderedModel(y.astype(int), X.astype(float), distr=distribution)
        result = model.fit(method="bfgs", maxiter=1000, disp=False)
        converged = bool(result.mle_retvals.get("converged", False))
        info = {
            "model": model_name, "distribution": distribution, "status": "COMPLETED" if converged else "NON_CONVERGED",
            "n": int(result.nobs), "log_likelihood": float(result.llf),
            "aic": float(result.aic), "bic": float(result.bic), "n_predictors": int(X.shape[1]),
            "converged": converged, "optimizer": str(result.mle_retvals.get("fopt", "")),
            "detail": "",
        }
        return result, info
    except Exception as exc:
        return None, {
            "model": model_name, "distribution": distribution, "status": "FAILED",
            "n": int(len(y)), "log_likelihood": np.nan, "aic": np.nan, "bic": np.nan,
            "n_predictors": int(X.shape[1]), "converged": False, "optimizer": "",
            "detail": f"{type(exc).__name__}: {str(exc)[:240]}",
        }


def _coefficient_rows(result: Any, model_name: str) -> list[dict[str, Any]]:
    params = result.params
    standard_errors = result.bse
    pvalues = result.pvalues
    conf = result.conf_int()
    rows = []
    threshold_names = set(str(x) for x in getattr(result.model, "labels", []))
    for term in params.index:
        name = str(term)
        is_threshold = "/" in name or name in threshold_names or name.lower().startswith("threshold")
        coef = float(params[term])
        se = float(standard_errors[term])
        lo, hi = map(float, conf.loc[term].tolist())
        rows.append({
            "model": model_name, "term": name, "term_type": "outcome threshold" if is_threshold else "predictor",
            "coefficient": coef, "standard_error": se, "z_statistic": float(coef / se) if se else np.nan,
            "p_value": float(pvalues[term]), "odds_ratio": np.nan if is_threshold else float(np.exp(np.clip(coef, -30, 30))),
            "or_ci95_low": np.nan if is_threshold else float(np.exp(np.clip(lo, -30, 30))),
            "or_ci95_high": np.nan if is_threshold else float(np.exp(np.clip(hi, -30, 30))),
            "interpretation": ("Threshold/cutpoint parameter, not a CRM predictor." if is_threshold else
              "Adjusted association with higher QA47 stated-continuation response under the proportional-odds specification; not causal.")
        })
    return rows


def fit_multinomial_sensitivity(y: pd.Series, X: pd.DataFrame, model_name: str) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Fit multinomial logit as a sensitivity alternative when parallel slopes are rejected."""
    try:
        design = sm.add_constant(X.astype(float), has_constant="add")
        observed_categories = sorted(pd.unique(y.astype(int)))
        category_to_code = {category: code for code, category in enumerate(observed_categories)}
        encoded_y = y.astype(int).map(category_to_code)
        result = sm.MNLogit(encoded_y, design).fit(method="newton", maxiter=1000, disp=False)
        converged = bool(result.mle_retvals.get("converged", False))
        info = {
            "model": model_name,
            "distribution": "multinomial logit",
            "status": "COMPLETED" if converged else "NON_CONVERGED",
            "n": int(result.nobs),
            "log_likelihood": float(result.llf),
            "aic": float(result.aic),
            "bic": float(result.bic),
            "n_predictors": int(X.shape[1]),
            "converged": converged,
            "optimizer": str(result.mle_retvals.get("fopt", "")),
            "detail": "Reference response category is QA47=" + str(observed_categories[0]) + ". Category-specific odds are not proportional-odds ratios.",
        }
        if not converged:
            return info, []
        params = np.asarray(result.params, dtype=float)
        standard_errors = np.asarray(result.bse, dtype=float)
        pvalues = np.asarray(result.pvalues, dtype=float)
        exog_names = list(result.model.exog_names)
        rows = []
        for outcome_index in range(params.shape[1]):
            category = observed_categories[outcome_index + 1]
            for term_index, term in enumerate(exog_names):
                coef = float(params[term_index, outcome_index])
                se = float(standard_errors[term_index, outcome_index])
                lo, hi = coef - 1.96 * se, coef + 1.96 * se
                rows.append({
                    "model": model_name,
                    "response_category_vs_reference": f"QA47={category} vs QA47={observed_categories[0]}",
                    "term": str(term),
                    "coefficient": coef,
                    "standard_error": se,
                    "p_value": float(pvalues[term_index, outcome_index]),
                    "relative_odds_ratio": float(np.exp(np.clip(coef, -30, 30))),
                    "or_ci95_low": float(np.exp(np.clip(lo, -30, 30))),
                    "or_ci95_high": float(np.exp(np.clip(hi, -30, 30))),
                    "interpretation_limit": "Category-specific relative odds from a sensitivity model; adjusted association, not causal."
                })
        return info, rows
    except Exception as exc:
        return {
            "model": model_name, "distribution": "multinomial logit", "status": "FAILED",
            "n": int(len(y)), "log_likelihood": np.nan, "aic": np.nan, "bic": np.nan,
            "n_predictors": int(X.shape[1]), "converged": False, "optimizer": "",
            "detail": f"{type(exc).__name__}: {str(exc)[:240]}",
        }, []


def fit_qa47_models(df: pd.DataFrame, out_dir: str) -> None:
    """Fit pre-specified ordered-logit model and sensitivity checks on current-user respondents."""
    current = df[df["user_subgroup"] == "Current Active User"].copy()
    y = current["Continue If Discounts Reduced"].astype(int)
    numeric = current[QA47_PREDICTOR_NUMERIC].apply(pd.to_numeric, errors="coerce")
    categorical = pd.get_dummies(current[QA47_PREDICTOR_CATEGORICAL].astype("category"),
                                 prefix=QA47_PREDICTOR_CATEGORICAL, drop_first=True, dtype=float)
    X = pd.concat([numeric.reset_index(drop=True), categorical.reset_index(drop=True)], axis=1)
    y = y.reset_index(drop=True)
    if X.isna().any().any() or not np.isfinite(X.to_numpy(dtype=float)).all():
        raise ValueError("QA47 model features contain missing or non-finite values after documented preprocessing.")
    model_rows, coefficient_rows, diagnostic_rows, comparison_rows = [], [], [], []
    multinomial_rows, multinomial_status_rows = [], []
    base_result, base_info = _fit_ordered_model(y, X, distribution="logit", model_name="QA47 ordered logit — prespecified trend model")
    model_rows.append(base_info)
    base_diagnostic = {"status": "INCONCLUSIVE", "detail": "Main ordered-logit model did not converge."}
    if base_result is not None and base_info["converged"]:
        coefficient_rows.extend(_coefficient_rows(base_result, base_info["model"]))
        base_diagnostic = run_parallel_slopes_diagnostic(y.to_numpy(), X)
        diagnostic_rows.append({"model": base_info["model"], "diagnostic": "Parallel-slopes assumption", **base_diagnostic})
    else:
        diagnostic_rows.append({"model": base_info["model"], "diagnostic": "Parallel-slopes assumption",
                                "status": "INCONCLUSIVE", "detail": base_diagnostic["detail"]})

    # Pre-specified fallback: if the main model's parallel-slopes diagnostic rejects,
    # fit a multinomial alternative rather than interpreting a violated PO model as definitive.
    if base_diagnostic.get("status") == "COMPLETED" and base_diagnostic.get("p_value", 1.0) < 0.05:
        mn_info, multinomial_rows = fit_multinomial_sensitivity(
            y, X, model_name="QA47 multinomial logit — triggered by parallel-slopes diagnostic"
        )
        model_rows.append(mn_info)
        multinomial_status_rows.append({
            "status": mn_info["status"], "trigger": "Parallel-slopes diagnostic p < 0.05",
            "diagnostic_p_value": float(base_diagnostic["p_value"]), "detail": mn_info["detail"]
        })
    elif base_diagnostic.get("status") == "COMPLETED":
        multinomial_status_rows.append({
            "status": "NOT_TRIGGERED", "trigger": "Parallel-slopes diagnostic did not reject at 0.05",
            "diagnostic_p_value": float(base_diagnostic.get("p_value", np.nan)),
            "detail": "The pre-specified multinomial fallback was not triggered; this is not proof that proportional odds is true."
        })
    else:
        multinomial_status_rows.append({
            "status": "NOT_RUN", "trigger": "Parallel-slopes diagnostic inconclusive",
            "diagnostic_p_value": np.nan,
            "detail": "Assumption status is unresolved; do not treat the ordered-logit interpretation as definitive."
        })

    # Sensitivity model: categorical coding for ordinal predictors tests whether trend coding masks non-linear relationships.
    sensitivity_numeric = current[["platforms_used_count", "service_satisfaction_composite"]].apply(pd.to_numeric, errors="coerce")
    ordinal_as_categories = [
        "Order Frequency", "Discount Overspend", "Threshold Extra Items",
        "Compare Platform Prices", "Compare Physical Prices", "Fast Delivery Importance",
    ]
    categorical_sensitivity = pd.get_dummies(
        current[ordinal_as_categories + QA47_PREDICTOR_CATEGORICAL].astype("category"),
        prefix=ordinal_as_categories + QA47_PREDICTOR_CATEGORICAL,
        drop_first=True, dtype=float,
    )
    X_cat = pd.concat([sensitivity_numeric.reset_index(drop=True), categorical_sensitivity.reset_index(drop=True)], axis=1)
    cat_result, cat_info = _fit_ordered_model(y, X_cat, distribution="logit", model_name="QA47 ordered logit — categorical-coding sensitivity")
    model_rows.append(cat_info)
    if cat_result is not None and cat_info["converged"]:
        coefficient_rows.extend(_coefficient_rows(cat_result, cat_info["model"]))
        diagnostic_rows.append({"model": cat_info["model"], "diagnostic": "Parallel-slopes assumption",
                                **run_parallel_slopes_diagnostic(y.to_numpy(), X_cat)})
    else:
        diagnostic_rows.append({"model": cat_info["model"], "diagnostic": "Parallel-slopes assumption",
                                "status": "INCONCLUSIVE", "detail": "Categorical sensitivity model did not converge."})

    # Alternative link sensitivity; not selected based on p-value.
    probit_result, probit_info = _fit_ordered_model(y, X, distribution="probit", model_name="QA47 ordered probit — link sensitivity")
    model_rows.append(probit_info)
    if probit_result is not None and probit_info["converged"]:
        coefficient_rows.extend(_coefficient_rows(probit_result, probit_info["model"]))

    # Add QA49 grouped preference as a pre-specified second model to assess incremental association.
    family = pd.get_dummies(current["qa49_action_family"].astype("category"), prefix="QA49_family", drop_first=True, dtype=float)
    X_plus = pd.concat([X.reset_index(drop=True), family.reset_index(drop=True)], axis=1)
    plus_result, plus_info = _fit_ordered_model(y, X_plus, distribution="logit", model_name="QA47 ordered logit — plus QA49 action family")
    model_rows.append(plus_info)
    if plus_result is not None and plus_info["converged"]:
        coefficient_rows.extend(_coefficient_rows(plus_result, plus_info["model"]))
        if base_result is not None and base_info["converged"]:
            lr_stat = max(0.0, 2 * (float(plus_result.llf) - float(base_result.llf)))
            df_diff = int(len(plus_result.params) - len(base_result.params))
            lr_p = float(stats.chi2.sf(lr_stat, df_diff)) if df_diff > 0 else np.nan
            comparison_rows.append({
                "comparison": "Trend model vs trend model + QA49 action family",
                "n": int(len(y)), "log_likelihood_base": float(base_result.llf),
                "log_likelihood_plus_QA49": float(plus_result.llf), "lr_statistic": lr_stat,
                "df_difference": df_diff, "likelihood_ratio_p_value": lr_p,
                "aic_base": float(base_result.aic), "aic_plus_QA49": float(plus_result.aic),
                "interpretation_limit": "Incremental associational check only; QA49 is a concurrent stated preference, not a randomized intervention."
            })

    pd.DataFrame(model_rows).to_csv(os.path.join(out_dir, "qa47_model_fit_summary.csv"), index=False)
    pd.DataFrame(coefficient_rows).to_csv(os.path.join(out_dir, "qa47_model_coefficients.csv"), index=False)
    pd.DataFrame(diagnostic_rows).to_csv(os.path.join(out_dir, "qa47_model_diagnostics.csv"), index=False)
    pd.DataFrame(comparison_rows).to_csv(os.path.join(out_dir, "qa47_model_comparison.csv"), index=False)
    pd.DataFrame(multinomial_status_rows).to_csv(os.path.join(out_dir, "qa47_multinomial_sensitivity_status.csv"), index=False)
    pd.DataFrame(multinomial_rows).to_csv(os.path.join(out_dir, "qa47_multinomial_sensitivity.csv"), index=False)


def run_analysis(df: pd.DataFrame, out_dir: str, *, mc_resamples: int = 10000, seed: int = 20261017,
                 strict: bool = False, skip_model: bool = False,
                 source_file_name: str = "Data.xlsx") -> dict[str, pd.DataFrame]:
    os.makedirs(out_dir, exist_ok=True)
    data = derive_cohorts(df, strict=strict)

    qa46 = build_qa46_distribution(data)
    qa46.to_csv(os.path.join(out_dir, "qa46_intention_distribution.csv"), index=False)
    cohort_frames = [data[data["user_subgroup"] == key]["Next 3 Month Use"].astype(int)
                     for key in ["Never User", "Previous User", "Current Active User"]]
    kw_stat, kw_p = stats.kruskal(*cohort_frames)
    n_total, groups_n = len(data), len(cohort_frames)
    epsilon_sq = max(0.0, (float(kw_stat) - groups_n + 1) / (n_total - groups_n))
    pd.DataFrame([{
        "outcome": "QA46 stated future-use intention", "test": "Kruskal-Wallis",
        "n": n_total, "h_statistic": float(kw_stat), "p_value": float(kw_p),
        "epsilon_squared": epsilon_sq,
        "interpretation_limit": "Cohort association only; does not estimate a causal lifecycle effect or actual future use."
    }]).to_csv(os.path.join(out_dir, "qa46_cohort_test.csv"), index=False)

    qa49_options, qa49_families = build_qa49_distributions(data)
    qa49_options.to_csv(os.path.join(out_dir, "qa49_preference_distribution.csv"), index=False)
    qa49_families.to_csv(os.path.join(out_dir, "qa49_action_family_distribution.csv"), index=False)
    qa49_tests = build_qa49_association_tests(data, n_resamples=mc_resamples, seed=seed)
    qa49_tests.to_csv(os.path.join(out_dir, "qa49_association_tests.csv"), index=False)

    qa48_prevalence, qa48_comparison = build_qa48_tables(data)
    qa48_prevalence.to_csv(os.path.join(out_dir, "qa48_barrier_prevalence.csv"), index=False)
    qa48_comparison.to_csv(os.path.join(out_dir, "qa48_barrier_comparison.csv"), index=False)

    metadata = pd.DataFrame([{
        "analysis_run_utc": datetime.now(timezone.utc).isoformat(),
        "source_file_name": os.path.basename(source_file_name),
        "rows": int(len(data)), "columns_in_source": int(len(df.columns)),
        "cohort_never_users": int((data["user_subgroup"] == "Never User").sum()),
        "cohort_previous_users": int((data["user_subgroup"] == "Previous User").sum()),
        "cohort_current_user": int((data["user_subgroup"] == "Current Active User").sum()),
        "qa46_scope": "All respondents; stated future-use intention codes 1..5",
        "qa47_scope": "Current-user cohort only; stated intention under hypothetical discount/promotion reduction",
        "qa48_scope": "Never-users and previous users; multi-response current non-use barriers",
        "qa49_scope": "All respondents; one stated preferred improvement choice",
        "causal_claim": False,
        "national_representativeness_claim": False,
        "monte_carlo_resamples": int(mc_resamples), "random_seed": int(seed),
    }])
    metadata.to_csv(os.path.join(out_dir, "crm_analysis_run_metadata.csv"), index=False)
    if not skip_model:
        fit_qa47_models(data, out_dir)

    return {"qa46_distribution": qa46, "qa49_options": qa49_options,
            "qa49_families": qa49_families, "qa48_prevalence": qa48_prevalence,
            "qa48_comparison": qa48_comparison, "qa49_tests": qa49_tests}


def main(args=None) -> int:
    parsed = parse_arguments(args)
    if not os.path.exists(parsed.file):
        raise FileNotFoundError(
            f"Survey workbook not found: {parsed.file}. Place the source workbook locally; never substitute another dataset."
        )
    if parsed.mc_resamples < 999:
        raise ValueError("--mc-resamples must be >= 999.")
    df = pd.read_excel(parsed.file, sheet_name=parsed.sheet)
    df.columns = [str(column).strip() for column in df.columns]
    if df.shape != EXPECTED_SHAPE:
        raise ValueError(f"Unexpected workbook shape {df.shape}; expected {EXPECTED_SHAPE}.")
    run_analysis(df, parsed.out_dir, mc_resamples=parsed.mc_resamples, seed=parsed.seed, strict=True,
                 skip_model=parsed.skip_model, source_file_name=parsed.file)
    print(f"Gate 1D aggregate outputs written to {parsed.out_dir}")
    print("QA46/QA47 are stated intentions, QA48 is stated current non-use, and QA49 is a stated preference.")
    print("No row-level data or respondent assignments are written by this script.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
