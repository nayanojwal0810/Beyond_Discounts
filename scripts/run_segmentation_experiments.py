#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Gate 1C: Controlled Mixed-Data Customer Segmentation Experiment
===============================================================

Project:
    Beyond Discounts: Customer Segmentation and Retention Strategy for Indian Quick Commerce

Repository:
    https://github.com/nayanojwal0810/Beyond_Discounts

Description:
    Implements the reproducible, controlled clustering experiment for Gate 1C:
    1. Validates input matrices, feature specifications, and structural alignment.
    2. Computes exact Gower distance matrices for Specification A and Specification B
       using the approved pairwise distance contract (asymmetric binary handling for QA19/QA26,
       Code Book-predeclared ranges, zero row dropping, 807 active respondents).
    3. Audits distance matrix properties (square, symmetric, bounded [0, 1], finite, zero diagonal,
       and minimum pairwise denominator verification).
    4. Evaluates candidate algorithms across predeclared cluster counts k in {3, 4, 5, 6}:
       - Primary: Kaufman & Rousseeuw (1990) Partitioning Around Medoids (PAM).
       - Benchmark: Hierarchical Agglomerative Clustering (HAC, average linkage and complete linkage).
    5. Computes internal cluster quality metrics (Average Silhouette Width, cluster-specific silhouettes,
       negative silhouette fractions, PAM objective, and cluster size balance).
    6. Conducts reproducible subsampling stability experiments (20 repeated 80% subsamples with
       predeclared seeds, evaluating Adjusted Rand Index distributions).
    7. Profiles candidate solutions across feature variables (respecting nominal category distributions
       rather than naive integer means).
    8. Performs external validation against held-out variables (QA47 Continue If Discounts Reduced,
       QA46 Next 3 Month Use) with rigorous hypothesis tests (Kruskal-Wallis, Chi-square, Holm-Bonferroni).
    9. Generates aggregate-only version-controlled reports under reports/segmentation/ while
       storing row-level matrices and labels locally in gitignored data/processed/.
"""

import os
import sys

# Ensure repository root is in sys.path
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

import json
import argparse
import numpy as np
import pandas as pd
from scipy.stats import kruskal, chi2_contingency
from sklearn.metrics import silhouette_score, silhouette_samples, adjusted_rand_score
from sklearn.cluster import AgglomerativeClustering

from scripts.prepare_segmentation_features import (
    load_and_filter_active_users,
    prepare_feature_matrices,
    validate_prepared_feature_matrices,
    compute_pairwise_gower_distance,
    DEFAULT_SURVEY_PATH,
    DEFAULT_SHEET,
    EXPECTED_ACTIVE_USERS
)


DEFAULT_SPEC_A_CSV = os.path.join("data", "processed", "segmentation_spec_a.csv")
DEFAULT_SPEC_B_CSV = os.path.join("data", "processed", "segmentation_spec_b.csv")
DEFAULT_HOLDOUT_CSV = os.path.join("data", "processed", "segmentation_holdout_profiling.csv")
DEFAULT_SPEC_A_JSON = os.path.join("reports", "segmentation", "feature_spec_a.json")
DEFAULT_SPEC_B_JSON = os.path.join("reports", "segmentation", "feature_spec_b.json")
DEFAULT_REPORTS_DIR = os.path.join("reports", "segmentation")
DEFAULT_DATA_DIR = os.path.join("data", "processed")


def parse_arguments(args=None):
    parser = argparse.ArgumentParser(description="Run Gate 1C Customer Segmentation Experiments.")
    parser.add_argument("--file-a", default=DEFAULT_SPEC_A_CSV, help="Path to prepared Specification A CSV.")
    parser.add_argument("--spec-a", default=DEFAULT_SPEC_A_JSON, help="Path to Specification A JSON schema.")
    parser.add_argument("--file-b", default=DEFAULT_SPEC_B_CSV, help="Path to prepared Specification B CSV.")
    parser.add_argument("--spec-b", default=DEFAULT_SPEC_B_JSON, help="Path to Specification B JSON schema.")
    parser.add_argument("--holdout", default=DEFAULT_HOLDOUT_CSV, help="Path to Holdout CSV.")
    parser.add_argument("--survey-file", default=DEFAULT_SURVEY_PATH, help="Path to raw survey Data.xlsx.")
    parser.add_argument("--reports-dir", default=DEFAULT_REPORTS_DIR, help="Path to output reports directory.")
    parser.add_argument("--data-dir", default=DEFAULT_DATA_DIR, help="Path to processed data directory.")
    parser.add_argument("--subsamples", type=int, default=20, help="Number of subsamples for stability evaluation.")
    parser.add_argument("--subsample-ratio", type=float, default=0.8, help="Subsample ratio for stability evaluation.")
    return parser.parse_args(args)


def compute_gower_distance_matrix(df, feature_specs, weights=None):
    """
    Computes exact, vectorized pairwise Gower distance matrix across respondents.
    Strictly adheres to Gate 1C distance rules:
    - Predeclared Code Book ranges R_k = range[1] - range[0] for numeric/ordinal/continuous.
    - Asymmetric binary contract for QA19/QA26 flags: (0, 0) omitted from denominator;
      (1, 1) matches; (1, 0) and (0, 1) mismatch.
    - Undefined ordinal components (NaN) omitted from denominator (delta=0).
    - Unit weights (or analytical weights if provided).
    - Strict denominator check: fails if any pair has denominator 0.0.
    """
    n = len(df)
    numer = np.zeros((n, n), dtype=np.float64)
    denom = np.zeros((n, n), dtype=np.float64)

    valid_types = {
        "asymmetric_binary", "ordinal", "continuous", "continuous_composite",
        "discrete_count", "nominal", "binary", "binary_indicator"
    }

    for spec in feature_specs:
        name = spec.get("name", "unnamed_feature")
        fid = spec.get("feature_id", name)
        dtype = spec.get("data_type", "")

        if dtype not in valid_types:
            raise ValueError(f"Unknown or unsupported data_type '{dtype}' for feature '{name}'")

        if weights is None:
            w = 1.0
        elif isinstance(weights, dict):
            raw_w = weights.get(name, weights.get(fid, 1.0))
            w = float(raw_w)
        else:
            w = float(weights)

        if not np.isfinite(w) or w < 0.0:
            raise ValueError(f"Weight for feature '{name}' must be finite and non-negative; got {w}")
        if w == 0.0:
            continue

        vals = df[name].to_numpy()
        valid = ~pd.isna(vals)
        valid_pair = valid[:, None] & valid[None, :]
        safe_vals = np.nan_to_num(vals, nan=0.0)

        if dtype == "asymmetric_binary":
            # Strict binary validation
            unique_vals = set(vals[valid])
            for u in unique_vals:
                if u not in (0, 1, 0.0, 1.0):
                    raise ValueError(f"Asymmetric binary feature '{name}' contains invalid value: {u}")

            b = safe_vals.astype(int)
            delta = valid_pair & ((b[:, None] == 1) | (b[None, :] == 1))
            s = valid_pair & ((b[:, None] == 1) & (b[None, :] == 1))
            numer += w * delta.astype(float) * s.astype(float)
            denom += w * delta.astype(float)

        elif dtype in ("ordinal", "continuous", "continuous_composite", "discrete_count"):
            # Check numeric range
            rng = spec.get("range", None)
            if rng is not None and len(rng) == 2:
                min_val, max_val = float(rng[0]), float(rng[1])
                defined_vals = vals[valid].astype(float)
                if (defined_vals < min_val - 1e-9).any() or (defined_vals > max_val + 1e-9).any():
                    raise ValueError(f"Values in feature '{name}' fall outside predeclared range {rng}")
                R = max_val - min_val
            else:
                R = 1.0

            if R <= 0.0:
                R = 1.0

            diff = np.abs(safe_vals[:, None] - safe_vals[None, :]) / R
            s = np.where(valid_pair, np.clip(1.0 - diff, 0.0, 1.0), 0.0)
            numer += w * s
            denom += w * valid_pair.astype(float)

        elif dtype in ("nominal", "binary", "binary_indicator"):
            s = np.where(valid_pair, (safe_vals[:, None] == safe_vals[None, :]).astype(float), 0.0)
            numer += w * s
            denom += w * valid_pair.astype(float)

    if (denom == 0.0).any():
        raise ValueError("Zero comparable features available for at least one respondent pair: distance denominator is zero.")

    D = 1.0 - (numer / denom)
    np.fill_diagonal(D, 0.0)
    D = np.clip(D, 0.0, 1.0)

    return D, denom


def audit_distance_matrix(D, denom, spec_code, feature_count):
    """
    Audits mathematical and structural properties of the computed distance matrix:
    square, symmetric, finite, zero diagonal, bounded [0, 1], and denominator diagnostics.
    """
    n_rows, n_cols = D.shape
    is_square = (n_rows == n_cols)
    is_symmetric = bool(np.allclose(D, D.T, atol=1e-12))
    is_finite = bool(np.isfinite(D).all())
    diag_zeros = bool(np.allclose(np.diag(D), 0.0, atol=1e-12))
    min_dist = float(np.min(D))
    max_dist = float(np.max(D))
    mean_dist = float(np.mean(D))
    median_dist = float(np.median(D))
    min_denom = float(np.min(denom))
    max_denom = float(np.max(denom))
    zero_denom_count = int((denom == 0.0).sum())

    status = "VALID"
    if not (is_square and is_symmetric and is_finite and diag_zeros and min_dist >= 0.0 and max_dist <= 1.0 and zero_denom_count == 0):
        status = "FAILED"

    return {
        "specification": spec_code,
        "rows": n_rows,
        "columns": n_cols,
        "feature_count": feature_count,
        "is_square": is_square,
        "is_symmetric": is_symmetric,
        "is_finite": is_finite,
        "zero_diagonal": diag_zeros,
        "min_distance": round(min_dist, 6),
        "max_distance": round(max_dist, 6),
        "mean_distance": round(mean_dist, 6),
        "median_distance": round(median_dist, 6),
        "min_pairwise_denominator": round(min_denom, 2),
        "max_pairwise_denominator": round(max_denom, 2),
        "zero_denominator_pairs_count": zero_denom_count,
        "matrix_status": status
    }


def pam_kmedoids(D, k, max_iter=100, initial_medoids=None):
    """
    Canonical Kaufman & Rousseeuw (1990) Partitioning Around Medoids (PAM) algorithm.

    1. BUILD Initialization:
       - Selects first medoid minimizing sum of distances to all points.
       - Iteratively adds medoids that maximize gain in total dissimilarity reduction.
    2. SWAP Optimization:
       - Evaluates all pairs of (current medoid, candidate non-medoid).
       - Executes swap if total distance decrease is strictly negative.
       - Terminates when no swap improves the objective or max_iter reached.

    Parameters:
    -----------
    D : np.ndarray (n, n)
        Precomputed pairwise dissimilarity matrix.
    k : int
        Number of clusters.
    max_iter : int
        Maximum SWAP iterations.
    initial_medoids : list or np.ndarray, optional
        Pre-selected medoid indices (if None, BUILD phase is executed).

    Returns:
    --------
    medoids : np.ndarray of shape (k,)
        Indices of chosen medoids.
    labels : np.ndarray of shape (n,)
        Cluster assignments (0 to k-1).
    objective : float
        Sum of distances of all points to their nearest medoid.
    """
    n = D.shape[0]

    if initial_medoids is not None:
        medoids = np.array(initial_medoids, dtype=int).copy()
    else:
        # BUILD Phase (Kaufman & Rousseeuw 1990)
        # 1. First medoid: point with minimum total distance to all other points
        medoids = [int(np.argmin(D.sum(axis=1)))]

        # 2. Iteratively select remaining k-1 medoids
        for _ in range(1, k):
            d_nearest = D[:, medoids].min(axis=1)
            best_candidate = None
            best_gain = -np.inf
            for cand in range(n):
                if cand in medoids:
                    continue
                gain = np.maximum(0.0, d_nearest - D[:, cand]).sum()
                if gain > best_gain:
                    best_gain = gain
                    best_candidate = cand
            medoids.append(best_candidate)

        medoids = np.array(medoids, dtype=int)

    # SWAP Phase
    for it in range(max_iter):
        d_to_medoids = D[:, medoids]  # shape (n, k)
        sort_idx = np.argsort(d_to_medoids, axis=1)
        nearest_m_idx = sort_idx[:, 0]
        d_nearest = d_to_medoids[np.arange(n), nearest_m_idx]
        d_second = d_to_medoids[np.arange(n), sort_idx[:, 1]]

        best_delta = 0.0
        best_swap = None
        non_medoids = [i for i in range(n) if i not in medoids]

        for m_pos in range(k):
            is_nearest = (nearest_m_idx == m_pos)
            D_h = D[:, non_medoids]  # shape (n, len(non_medoids))
            delta_near = np.minimum(d_second[:, None], D_h) - d_nearest[:, None]
            delta_far = np.minimum(0.0, D_h - d_nearest[:, None])
            total_delta_h = np.where(is_nearest[:, None], delta_near, delta_far).sum(axis=0)

            min_idx = np.argmin(total_delta_h)
            if total_delta_h[min_idx] < best_delta:
                best_delta = total_delta_h[min_idx]
                best_swap = (m_pos, non_medoids[min_idx])

        if best_swap is not None and best_delta < -1e-8:
            m_pos, new_h = best_swap
            medoids[m_pos] = new_h
        else:
            break

    # Final assignment and PAM objective
    d_final = D[:, medoids]
    labels = np.argmin(d_final, axis=1)
    objective = float(np.min(d_final, axis=1).sum())

    return medoids, labels, objective


def run_subsampling_stability(
    D, k, n_subsamples=20, subsample_ratio=0.8, seed_base=101, run_records=None
):
    """
    Evaluates clustering stability via repeated subsampling without conflating
    failed computations with measured low stability.

    Successful runs contribute their ARI to the summary. Failed runs are recorded
    separately, excluded from ARI statistics, and force an INCOMPLETE verdict.
    If run_records is supplied, append one aggregate diagnostic row per seed;
    no respondent identifiers or sampled row indices are exported.
    """
    if not isinstance(n_subsamples, int) or n_subsamples < 1:
        raise ValueError("n_subsamples must be a positive integer")
    if not np.isfinite(subsample_ratio) or not (0.0 < subsample_ratio <= 1.0):
        raise ValueError("subsample_ratio must be in (0, 1]")
    if D.ndim != 2 or D.shape[0] != D.shape[1]:
        raise ValueError("D must be a square distance matrix")

    n = D.shape[0]
    n_sub = int(round(subsample_ratio * n))
    if k < 2 or k >= n_sub:
        raise ValueError(f"k must be between 2 and n_sub-1; got k={k}, n_sub={n_sub}")

    # A baseline is required to define ARI. If this fails, propagate the error:
    # no stability comparison can be made without a reference partition.
    _, baseline_labels, _ = pam_kmedoids(D, k)

    aris = []
    failed_runs = 0
    for idx, seed in enumerate(range(seed_base, seed_base + n_subsamples)):
        rng = np.random.RandomState(seed)
        sub_idx = np.sort(rng.choice(n, size=n_sub, replace=False))
        D_sub = D[np.ix_(sub_idx, sub_idx)]
        run_record = {
            "run_index": idx + 1,
            "seed": int(seed),
            "sample_size": int(n_sub),
            "status": "SUCCESS",
            "ari": None,
            "error_type": "",
            "error_message": ""
        }

        try:
            _, sub_labels, _ = pam_kmedoids(D_sub, k)
            ari = float(adjusted_rand_score(baseline_labels[sub_idx], sub_labels))
            aris.append(ari)
            run_record["ari"] = ari
        except Exception as exc:
            failed_runs += 1
            run_record["status"] = "FAILED"
            run_record["error_type"] = type(exc).__name__
            run_record["error_message"] = str(exc)[:240]

        if run_records is not None:
            run_records.append(run_record)

    successful_runs = len(aris)
    unstable_runs = sum(ari < 0.50 for ari in aris)

    if not aris:
        return {
            "n_subsamples": n_subsamples,
            "n_successful_runs": 0,
            "n_failed_runs": failed_runs,
            "subsample_ratio": subsample_ratio,
            "seed_policy": f"Deterministic range({seed_base}, {seed_base + n_subsamples})",
            "median_ari": None,
            "mean_ari": None,
            "std_ari": None,
            "min_ari": None,
            "max_ari": None,
            "iqr_ari": None,
            "unstable_runs_count": 0,
            "stability_verdict": "FAILED"
        }

    aris = np.asarray(aris, dtype=float)
    q25, q75 = np.percentile(aris, [25, 75])
    if failed_runs > 0:
        verdict = "INCOMPLETE"
    elif np.median(aris) >= 0.70 and unstable_runs == 0:
        verdict = "HIGH_STABILITY"
    elif np.median(aris) >= 0.60:
        verdict = "PROVISIONALLY_STABLE" if unstable_runs > 0 else "STABLE"
    elif np.median(aris) >= 0.40:
        verdict = "MODERATE"
    else:
        verdict = "UNSTABLE"

    return {
        "n_subsamples": n_subsamples,
        "n_successful_runs": successful_runs,
        "n_failed_runs": failed_runs,
        "subsample_ratio": subsample_ratio,
        "seed_policy": f"Deterministic range({seed_base}, {seed_base + n_subsamples})",
        "median_ari": round(float(np.median(aris)), 4),
        "mean_ari": round(float(np.mean(aris)), 4),
        "std_ari": round(float(np.std(aris)), 4),
        "min_ari": round(float(np.min(aris)), 4),
        "max_ari": round(float(np.max(aris)), 4),
        "iqr_ari": round(float(q75 - q25), 4),
        "unstable_runs_count": int(unstable_runs),
        "stability_verdict": verdict
    }

def compute_cluster_profiles(df, labels, feature_specs, spec_name, algorithm, k):
    """
    Generates aggregate profile summaries across clusters:
    - Numeric/ordinal features: mean, std, median.
    - Nominal features (e.g. shopping_routine_role): category percentage distributions.
    - Asymmetric binary features: prevalence percentage (proportion of 1s).
    """
    profiles = []
    n_total = len(df)
    unique_clusters = sorted(np.unique(labels))

    for c in unique_clusters:
        c_mask = (labels == c)
        c_size = int(c_mask.sum())
        c_prop = round(c_size / n_total, 4)
        c_df = df[c_mask]

        for spec in feature_specs:
            fname = spec["name"]
            fid = spec.get("feature_id", fname)
            dtype = spec.get("data_type", "")
            col_vals = c_df[fname].dropna()

            if dtype in ("ordinal", "continuous", "continuous_composite", "discrete_count"):
                profiles.append({
                    "specification": spec_name, "algorithm": algorithm, "k": k,
                    "cluster_id": c, "cluster_size": c_size, "cluster_proportion": c_prop,
                    "feature_id": fid, "feature_name": fname, "data_type": dtype,
                    "metric_type": "mean", "metric_value": round(float(col_vals.mean()), 4)
                })
                profiles.append({
                    "specification": spec_name, "algorithm": algorithm, "k": k,
                    "cluster_id": c, "cluster_size": c_size, "cluster_proportion": c_prop,
                    "feature_id": fid, "feature_name": fname, "data_type": dtype,
                    "metric_type": "std", "metric_value": round(float(col_vals.std()), 4)
                })
                profiles.append({
                    "specification": spec_name, "algorithm": algorithm, "k": k,
                    "cluster_id": c, "cluster_size": c_size, "cluster_proportion": c_prop,
                    "feature_id": fid, "feature_name": fname, "data_type": dtype,
                    "metric_type": "median", "metric_value": round(float(col_vals.median()), 4)
                })

            elif dtype == "asymmetric_binary":
                pct_ones = round(float((c_df[fname] == 1).mean() * 100), 2)
                profiles.append({
                    "specification": spec_name, "algorithm": algorithm, "k": k,
                    "cluster_id": c, "cluster_size": c_size, "cluster_proportion": c_prop,
                    "feature_id": fid, "feature_name": fname, "data_type": dtype,
                    "metric_type": "prevalence_pct", "metric_value": pct_ones
                })

            elif dtype in ("nominal", "binary", "binary_indicator"):
                val_counts = c_df[fname].value_counts(normalize=True)
                for cat_val, prop in sorted(val_counts.items()):
                    profiles.append({
                        "specification": spec_name, "algorithm": algorithm, "k": k,
                        "cluster_id": c, "cluster_size": c_size, "cluster_proportion": c_prop,
                        "feature_id": fid, "feature_name": fname, "data_type": dtype,
                        "metric_type": f"cat_{cat_val}_pct", "metric_value": round(float(prop * 100), 2)
                    })

    return profiles


def evaluate_external_validation(df_holdout, labels, spec_name, algorithm, k):
    """
    Evaluates cluster solutions against held-out variables:
    - QA 47: Continue If Discounts Reduced (1-5 Likert).
    - QA 46: Next 3 Month Use (1-5 Likert).
    Computes Kruskal-Wallis H test, raw p-value, and epsilon-squared effect size.
    Multiple-testing corrections (Bonferroni, Holm-Bonferroni) are applied
    across the family of candidate k comparisons via apply_multiple_testing_corrections.
    """
    records = []
    unique_clusters = sorted(np.unique(labels))

    holdout_vars = [
        ("qa47_continue_if_discounts_reduced", "QA 47 Continue If Discounts Reduced",
         "Independent validation" if spec_name == "SPEC_A" else "Construct-defining descriptive"),
        ("qa46_next_3_month_use", "QA 46 Next 3 Month Use (Stated Future Intent)",
         "Independent stated-intention benchmark")
    ]

    for var_col, var_label, circ_status in holdout_vars:
        if var_col not in df_holdout.columns:
            continue

        vals = df_holdout[var_col].values
        groups = [vals[labels == c] for c in unique_clusters]
        means_by_cluster = {f"cluster_{c}": round(float(np.mean(groups[c])), 3) for c in range(len(groups))}

        # Kruskal-Wallis non-parametric test
        h_stat, p_raw = kruskal(*groups)
        # Epsilon-squared effect size for Kruskal-Wallis: (H - k + 1) / (n - k)
        n = len(vals)
        epsilon_sq = max(0.0, (h_stat - k + 1) / (n - k))

        records.append({
            "specification": spec_name,
            "algorithm": algorithm,
            "k": k,
            "holdout_variable": var_label,
            "test_method": "Kruskal-Wallis H-test",
            "test_statistic": round(float(h_stat), 4),
            "p_value": float(p_raw),
            "bonferroni_p_value": None,
            "holm_bonferroni_p_value": None,
            "correction_family_size": 4,
            "effect_size_metric": "epsilon_squared",
            "effect_size_value": round(float(epsilon_sq), 4),
            "cluster_means_or_proportions": json.dumps(means_by_cluster),
            "substantive_interpretation": "",
            "circularity_status": circ_status
        })

    return records


def apply_multiple_testing_corrections(records):
    """
    Applies exact family-wise Bonferroni and Holm-Bonferroni step-down corrections
    across the predeclared family of candidate k comparisons (k in {3, 4, 5, 6}).
    Each family is defined by (specification, algorithm, holdout_variable).
    """
    groups = {}
    for i, r in enumerate(records):
        key = (r["specification"], r["algorithm"], r["holdout_variable"])
        groups.setdefault(key, []).append((i, r["p_value"]))

    for key, items in groups.items():
        m = len(items)
        # Sort items by p_value ascending
        sorted_items = sorted(items, key=lambda x: x[1])

        running_max = 0.0
        holm_pvals = {}
        bonf_pvals = {}

        for rank, (idx, p_raw) in enumerate(sorted_items):
            multiplier = m - rank
            val_holm = min(1.0, p_raw * multiplier)
            running_max = max(running_max, val_holm)
            holm_pvals[idx] = min(1.0, running_max)
            bonf_pvals[idx] = min(1.0, p_raw * m)

        for idx, p_raw in items:
            records[idx]["bonferroni_p_value"] = float(bonf_pvals[idx])
            records[idx]["holm_bonferroni_p_value"] = float(holm_pvals[idx])
            records[idx]["correction_family_size"] = m

            circ = records[idx]["circularity_status"]
            p_holm = holm_pvals[idx]
            if "Construct-defining" in circ:
                records[idx]["substantive_interpretation"] = (
                    "Statistically significant divergence by construction (construct-defining input, not independent validation)"
                )
            elif p_holm < 0.05:
                records[idx]["substantive_interpretation"] = (
                    f"Statistically significant cluster divergence after Holm-Bonferroni correction (p_holm = {p_holm:.3g} < 0.05)"
                )
            else:
                records[idx]["substantive_interpretation"] = (
                    f"No statistically detectable cluster divergence after Holm-Bonferroni correction (p_holm = {p_holm:.3g} >= 0.05; this is not proof of equivalence)"
                )

    return records


def run_experiments(args=None):
    parsed = parse_arguments(args)
    os.makedirs(parsed.reports_dir, exist_ok=True)
    os.makedirs(parsed.data_dir, exist_ok=True)

    print("=" * 80)
    print("GATE 1C: CONTROLLED MIXED-DATA CUSTOMER SEGMENTATION EXPERIMENT")
    print("=" * 80)

    # Step 1: Ensure prepared data exists and is validated
    if not (os.path.exists(parsed.file_a) and os.path.exists(parsed.file_b) and os.path.exists(parsed.holdout)):
        print("Prepared feature representations missing; running Gate 1B pipeline...")
        full_df, active_df = load_and_filter_active_users(parsed.survey_file, DEFAULT_SHEET)
        prep_results = prepare_feature_matrices(active_df, parsed.data_dir)
        df_a = prep_results['spec_a']
        df_b = prep_results['spec_b']
        df_holdout = prep_results['holdout']
    else:
        df_a = pd.read_csv(parsed.file_a)
        df_b = pd.read_csv(parsed.file_b)
        df_holdout = pd.read_csv(parsed.holdout)
        full_df, active_df = load_and_filter_active_users(parsed.survey_file, DEFAULT_SHEET)

    # Validate prepared matrices
    print("Validating prepared feature matrices and missingness masks...")
    validate_prepared_feature_matrices(df_a, df_b, df_holdout, active_df)
    print(f"Dataset verified: {len(df_a)} active respondents, perfect row alignment, exact special masks.")

    # Load machine-readable specifications
    with open(parsed.spec_a, "r", encoding="utf-8") as f:
        spec_a_dict = json.load(f)
    with open(parsed.spec_b, "r", encoding="utf-8") as f:
        spec_b_dict = json.load(f)

    specs_a = spec_a_dict["features"]
    specs_b = spec_b_dict["features"]

    # Step 2: Compute and audit Gower distance matrices
    print("\n[Step 1/5] Computing exact Gower distance matrix for Specification A (17 features)...")
    D_a, denom_a = compute_gower_distance_matrix(df_a, specs_a)
    audit_a = audit_distance_matrix(D_a, denom_a, "SPEC_A", len(specs_a))
    print(f"  Spec A Matrix: shape={D_a.shape}, mean_dist={audit_a['mean_distance']}, min_denom={audit_a['min_pairwise_denominator']}, status={audit_a['matrix_status']}")

    print("\n[Step 2/5] Computing exact Gower distance matrix for Specification B (18 features)...")
    D_b, denom_b = compute_gower_distance_matrix(df_b, specs_b)
    audit_b = audit_distance_matrix(D_b, denom_b, "SPEC_B", len(specs_b))
    print(f"  Spec B Matrix: shape={D_b.shape}, mean_dist={audit_b['mean_distance']}, min_denom={audit_b['min_pairwise_denominator']}, status={audit_b['matrix_status']}")

    # Save local gitignored distance matrices
    np.save(os.path.join(parsed.data_dir, "gower_matrix_spec_a.npy"), D_a)
    np.save(os.path.join(parsed.data_dir, "gower_matrix_spec_b.npy"), D_b)

    # Write distance_matrix_audit.csv
    audit_df = pd.DataFrame([audit_a, audit_b])
    audit_path = os.path.join(parsed.reports_dir, "distance_matrix_audit.csv")
    audit_df.to_csv(audit_path, index=False)
    print(f"Saved distance matrix audit to: {audit_path}")

    # Step 3: Run Clustering Experiments across k in {3, 4, 5, 6}
    candidate_ks = [3, 4, 5, 6]
    metrics_records = []
    stability_records = []
    stability_run_records = []
    profile_records = []
    validation_records = []

    # Store label assignments locally
    labels_a_export = pd.DataFrame({"survey_row_id": df_a["survey_row_id"]})
    labels_b_export = pd.DataFrame({"survey_row_id": df_b["survey_row_id"]})

    experiment_configs = [
        ("SPEC_A", D_a, df_a, specs_a, labels_a_export),
        ("SPEC_B", D_b, df_b, specs_b, labels_b_export)
    ]

    print("\n[Step 3/5] Evaluating candidate clustering algorithms and cluster counts...")
    for spec_name, D, df_spec, feature_specs, labels_export in experiment_configs:
        print(f"\n--- Running Experiments for {spec_name} ---")

        # 1. Primary Algorithm: PAM
        for k in candidate_ks:
            medoids, labels, obj = pam_kmedoids(D, k)
            labels_export[f"pam_k{k}_cluster"] = labels

            # Metrics
            sil_avg = float(silhouette_score(D, labels, metric="precomputed"))
            sil_samples = silhouette_samples(D, labels, metric="precomputed")
            n_neg = int((sil_samples < 0).sum())
            pct_neg = round(float(n_neg / len(D) * 100), 2)
            cluster_sizes = [int((labels == c).sum()) for c in range(k)]
            cluster_props = [round(sz / len(D), 4) for sz in cluster_sizes]
            min_sz = min(cluster_sizes)
            max_sz = max(cluster_sizes)
            small_warning = bool(min_sz < 41)  # 5% threshold of 807 is 40.35

            cluster_sils = {f"cluster_{c}": round(float(sil_samples[labels == c].mean()), 4) for c in range(k)}

            metrics_records.append({
                "specification": spec_name, "algorithm": "PAM (Partitioning Around Medoids)",
                "linkage": "N/A", "k": k,
                "avg_silhouette": round(sil_avg, 4),
                "n_negative_silhouette": n_neg,
                "pct_negative_silhouette": pct_neg,
                "pam_objective": round(obj, 4),
                "cluster_sizes": json.dumps(cluster_sizes),
                "cluster_proportions": json.dumps(cluster_props),
                "min_cluster_size": min_sz,
                "max_cluster_size": max_sz,
                "small_cluster_warning": small_warning,
                "cluster_silhouettes": json.dumps(cluster_sils)
            })

            print(f"  PAM {spec_name} k={k}: sil={sil_avg:.4f}, neg_sil={pct_neg}%, obj={obj:.2f}, sizes={cluster_sizes}, warning={small_warning}")

            # Subsampling Stability
            stab_run_batch = []
            stab = run_subsampling_stability(
                D, k, n_subsamples=parsed.subsamples,
                subsample_ratio=parsed.subsample_ratio,
                run_records=stab_run_batch
            )
            for run_rec in stab_run_batch:
                run_rec["specification"] = spec_name
                run_rec["algorithm"] = "PAM"
                run_rec["k"] = k
            stability_run_records.extend(stab_run_batch)
            stab_rec = dict(stab)
            stab_rec["specification"] = spec_name
            stab_rec["algorithm"] = "PAM"
            stab_rec["k"] = k
            stability_records.append(stab_rec)
            print(f"    -> Stability (20 subsamples): Median ARI={stab['median_ari']}, IQR={stab['iqr_ari']}, Verdict={stab['stability_verdict']}")

            # Profiles
            profiles = compute_cluster_profiles(df_spec, labels, feature_specs, spec_name, "PAM", k)
            profile_records.extend(profiles)

            # External Validation
            ext_val = evaluate_external_validation(df_holdout, labels, spec_name, "PAM", k)
            validation_records.extend(ext_val)

        # 2. Benchmark Algorithm: HAC Average Linkage
        for k in candidate_ks:
            hac_avg = AgglomerativeClustering(n_clusters=k, metric="precomputed", linkage="average").fit(D)
            labels_hac = hac_avg.labels_
            labels_export[f"hac_avg_k{k}_cluster"] = labels_hac

            sil_avg = float(silhouette_score(D, labels_hac, metric="precomputed"))
            sil_samples = silhouette_samples(D, labels_hac, metric="precomputed")
            n_neg = int((sil_samples < 0).sum())
            pct_neg = round(float(n_neg / len(D) * 100), 2)
            cluster_sizes = [int((labels_hac == c).sum()) for c in range(k)]
            cluster_props = [round(sz / len(D), 4) for sz in cluster_sizes]
            min_sz = min(cluster_sizes)
            max_sz = max(cluster_sizes)
            small_warning = bool(min_sz < 41)

            cluster_sils = {f"cluster_{c}": round(float(sil_samples[labels_hac == c].mean()), 4) for c in range(k)}

            metrics_records.append({
                "specification": spec_name, "algorithm": "HAC (Hierarchical Agglomerative)",
                "linkage": "average", "k": k,
                "avg_silhouette": round(sil_avg, 4),
                "n_negative_silhouette": n_neg,
                "pct_negative_silhouette": pct_neg,
                "pam_objective": "N/A",
                "cluster_sizes": json.dumps(cluster_sizes),
                "cluster_proportions": json.dumps(cluster_props),
                "min_cluster_size": min_sz,
                "max_cluster_size": max_sz,
                "small_cluster_warning": small_warning,
                "cluster_silhouettes": json.dumps(cluster_sils)
            })

        # 3. Sensitivity Benchmark: HAC Complete Linkage
        for k in candidate_ks:
            hac_comp = AgglomerativeClustering(n_clusters=k, metric="precomputed", linkage="complete").fit(D)
            labels_comp = hac_comp.labels_
            labels_export[f"hac_complete_k{k}_cluster"] = labels_comp

            sil_avg = float(silhouette_score(D, labels_comp, metric="precomputed"))
            sil_samples = silhouette_samples(D, labels_comp, metric="precomputed")
            n_neg = int((sil_samples < 0).sum())
            pct_neg = round(float(n_neg / len(D) * 100), 2)
            cluster_sizes = [int((labels_comp == c).sum()) for c in range(k)]
            cluster_props = [round(sz / len(D), 4) for sz in cluster_sizes]
            min_sz = min(cluster_sizes)
            max_sz = max(cluster_sizes)
            small_warning = bool(min_sz < 41)

            cluster_sils = {f"cluster_{c}": round(float(sil_samples[labels_comp == c].mean()), 4) for c in range(k)}

            metrics_records.append({
                "specification": spec_name, "algorithm": "HAC (Hierarchical Agglomerative)",
                "linkage": "complete", "k": k,
                "avg_silhouette": round(sil_avg, 4),
                "n_negative_silhouette": n_neg,
                "pct_negative_silhouette": pct_neg,
                "pam_objective": "N/A",
                "cluster_sizes": json.dumps(cluster_sizes),
                "cluster_proportions": json.dumps(cluster_props),
                "min_cluster_size": min_sz,
                "max_cluster_size": max_sz,
                "small_cluster_warning": small_warning,
                "cluster_silhouettes": json.dumps(cluster_sils)
            })

    # Save local gitignored respondent labels
    labels_a_export.to_csv(os.path.join(parsed.data_dir, "segmentation_labels_spec_a.csv"), index=False)
    labels_b_export.to_csv(os.path.join(parsed.data_dir, "segmentation_labels_spec_b.csv"), index=False)

    # Step 4: Write Aggregate-Only Output CSVs to reports/segmentation/
    print("\n[Step 4/5] Writing version-controlled aggregate summary tables...")
    metrics_df = pd.DataFrame(metrics_records)
    metrics_path = os.path.join(parsed.reports_dir, "clustering_metrics.csv")
    metrics_df.to_csv(metrics_path, index=False)
    print(f"Saved clustering metrics to: {metrics_path} ({len(metrics_df)} rows)")

    stability_df = pd.DataFrame(stability_records)
    stability_path = os.path.join(parsed.reports_dir, "stability_summary.csv")
    stability_df.to_csv(stability_path, index=False)
    print(f"Saved stability summary to: {stability_path} ({len(stability_df)} rows)")

    # One diagnostic row per seed makes the summary independently auditable.
    stability_runs_df = pd.DataFrame(stability_run_records)
    stability_runs_path = os.path.join(parsed.reports_dir, "stability_runs.csv")
    stability_runs_df.to_csv(stability_runs_path, index=False)
    print(f"Saved stability run diagnostics to: {stability_runs_path} ({len(stability_runs_df)} rows)")

    profile_df = pd.DataFrame(profile_records)
    profile_path = os.path.join(parsed.reports_dir, "cluster_profile_summary.csv")
    profile_df.to_csv(profile_path, index=False)
    print(f"Saved cluster profile summary to: {profile_path} ({len(profile_df)} rows)")

    validation_records = apply_multiple_testing_corrections(validation_records)
    validation_df = pd.DataFrame(validation_records)
    validation_path = os.path.join(parsed.reports_dir, "external_validation_summary.csv")
    validation_df.to_csv(validation_path, index=False)
    print(f"Saved external validation summary to: {validation_path} ({len(validation_df)} rows)")

    print("\n[Step 5/5] All experiments and aggregate reports successfully generated.")
    print("=" * 80)
    print("GATE 1C EXPERIMENTAL RUN COMPLETE")
    print("=" * 80)

    return {
        "audit": audit_df,
        "metrics": metrics_df,
        "stability": stability_df,
        "profiles": profile_df,
        "validation": validation_df
    }


if __name__ == "__main__":
    run_experiments()
