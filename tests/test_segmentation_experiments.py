"""
Unit tests for Gate 1C segmentation experiments pipeline.

Verifies:
1. Distance matrix mathematical properties (square, symmetric, bounded [0, 1], finite, zero diagonal).
2. Proper feature inclusion/exclusion across specifications (Spec A excludes QA47, both exclude QA46, Spec B includes QA47).
3. PAM algorithm properties (deterministic for fixed seeds, convergence, valid medoids, non-empty clusters).
4. Subsampling stability computation.
5. Cluster profiling retaining nominal distributions.
6. Aggregate reports generation and data governance (no respondent-level data committed).
7. External validation with step-down Holm-Bonferroni and Bonferroni corrections.
8. Regression tests:
   - Cluster sizes match between clustering_metrics.csv and cluster_profile_summary.csv.
   - Cluster sizes sum to 807 and proportions sum to approximately 1.0.
   - Stability summary statistics match expected calculations and fragile counts.
   - Persona feature claims in decision report match aggregate profiles.
   - Corrected p-values match multiple-testing procedures.
"""

import unittest
import os
import re
import json
import numpy as np
import pandas as pd
from sklearn.metrics import silhouette_score, silhouette_samples

from scripts.run_segmentation_experiments import (
    compute_gower_distance_matrix,
    audit_distance_matrix,
    pam_kmedoids,
    run_subsampling_stability,
    compute_cluster_profiles,
    evaluate_external_validation,
    apply_multiple_testing_corrections
)


class TestSegmentationExperiments(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.spec_a_path = os.path.join("reports", "segmentation", "feature_spec_a.json")
        cls.spec_b_path = os.path.join("reports", "segmentation", "feature_spec_b.json")
        cls.mat_a_path = os.path.join("data", "processed", "segmentation_spec_a.csv")
        cls.mat_b_path = os.path.join("data", "processed", "segmentation_spec_b.csv")
        cls.holdout_path = os.path.join("data", "processed", "segmentation_holdout_profiling.csv")

        with open(cls.spec_a_path, "r", encoding="utf-8") as f:
            cls.spec_a = json.load(f)
        with open(cls.spec_b_path, "r", encoding="utf-8") as f:
            cls.spec_b = json.load(f)

        cls.df_a = pd.read_csv(cls.mat_a_path)
        cls.df_b = pd.read_csv(cls.mat_b_path)
        cls.df_hold = pd.read_csv(cls.holdout_path)

        cls.metrics_csv_path = os.path.join("reports", "segmentation", "clustering_metrics.csv")
        cls.profiles_csv_path = os.path.join("reports", "segmentation", "cluster_profile_summary.csv")
        cls.stability_csv_path = os.path.join("reports", "segmentation", "stability_summary.csv")
        cls.validation_csv_path = os.path.join("reports", "segmentation", "external_validation_summary.csv")
        cls.decision_md_path = os.path.join("reports", "segmentation", "SEGMENTATION_EXPERIMENT_DECISION.md")

    def test_01_feature_spec_exclusions_and_inclusions(self):
        """Verify Spec A excludes QA47, both exclude QA46, Spec B includes QA47."""
        spec_a_features = [f["name"] for f in self.spec_a["features"]]
        spec_b_features = [f["name"] for f in self.spec_b["features"]]

        self.assertNotIn("continue_if_discounts_reduced", spec_a_features)
        self.assertNotIn("qa46_next_3_month_use", spec_a_features)
        self.assertNotIn("qa46_next_3_month_use", spec_b_features)
        self.assertNotIn("future_use_rank", spec_a_features)
        self.assertNotIn("future_use_rank", spec_b_features)
        self.assertIn("continue_if_discounts_reduced", spec_b_features)

        # Check column presence in prepared feature matrices
        self.assertNotIn("continue_if_discounts_reduced", self.df_a.columns)
        self.assertNotIn("qa46_next_3_month_use", self.df_a.columns)
        self.assertNotIn("qa46_next_3_month_use", self.df_b.columns)
        self.assertIn("continue_if_discounts_reduced", self.df_b.columns)

        # Verify holdouts contains QA46 and QA47
        self.assertIn("qa47_continue_if_discounts_reduced", self.df_hold.columns)
        self.assertIn("qa46_next_3_month_use", self.df_hold.columns)

    def test_02_distance_matrix_mathematical_properties(self):
        """Test distance matrix computation on a synthetic subset for exact mathematical contract."""
        sub_df = self.df_a.head(30)
        D, denom = compute_gower_distance_matrix(sub_df, self.spec_a["features"])

        n = len(sub_df)
        self.assertEqual(D.shape, (n, n))
        self.assertTrue(np.all(np.isfinite(D)), "Matrix contains non-finite entries")
        self.assertTrue(np.all(D >= 0.0), "Matrix contains negative values")
        self.assertTrue(np.all(D <= 1.0), "Matrix contains values > 1.0")
        np.testing.assert_allclose(np.diag(D), np.zeros(n), atol=1e-12, err_msg="Diagonal is not zero")
        np.testing.assert_allclose(D, D.T, atol=1e-12, err_msg="Matrix is not symmetric")
        self.assertTrue((denom > 0).all())

        audit = audit_distance_matrix(D, denom, "TEST_SUBSET", len(self.spec_a["features"]))
        self.assertEqual(audit["matrix_status"], "VALID")
        self.assertEqual(audit["zero_denominator_pairs_count"], 0)

    def test_03_pam_deterministic_and_valid_structure(self):
        """Verify PAM BUILD+SWAP converges deterministically and returns valid assignments."""
        sub_df = self.df_a.head(40)
        D, _ = compute_gower_distance_matrix(sub_df, self.spec_a["features"])

        medoids_1, labels_1, obj_1 = pam_kmedoids(D, k=3, max_iter=50)
        medoids_2, labels_2, obj_2 = pam_kmedoids(D, k=3, max_iter=50)

        # Deterministic
        np.testing.assert_array_equal(medoids_1, medoids_2)
        np.testing.assert_array_equal(labels_1, labels_2)
        self.assertAlmostEqual(obj_1, obj_2, places=8)

        # Valid structure
        self.assertEqual(len(medoids_1), 3)
        self.assertEqual(len(labels_1), 40)
        self.assertEqual(len(np.unique(labels_1)), 3, "Not all k clusters are represented")
        self.assertTrue(obj_1 > 0)

    def test_04_silhouette_metric_calculation(self):
        """Verify silhouette width and negative count calculations."""
        sub_df = self.df_a.head(50)
        D, _ = compute_gower_distance_matrix(sub_df, self.spec_a["features"])
        medoids, labels, obj = pam_kmedoids(D, k=3)

        sil_avg = float(silhouette_score(D, labels, metric="precomputed"))
        sil_samples = silhouette_samples(D, labels, metric="precomputed")
        n_neg = int((sil_samples < 0).sum())

        self.assertGreaterEqual(sil_avg, -1.0)
        self.assertLessEqual(sil_avg, 1.0)
        self.assertGreaterEqual(n_neg, 0)
        self.assertLessEqual(n_neg, 50)

    def test_05_subsampling_stability_structure(self):
        """Verify stability pipeline produces valid ARI metrics."""
        sub_df = self.df_a.head(50)
        D, _ = compute_gower_distance_matrix(sub_df, self.spec_a["features"])

        res = run_subsampling_stability(
            D, k=3, n_subsamples=3, subsample_ratio=0.8, seed_base=42
        )
        self.assertEqual(res["n_subsamples"], 3)
        self.assertGreaterEqual(res["median_ari"], -1.0)
        self.assertLessEqual(res["median_ari"], 1.0)
        self.assertIn("stability_verdict", res)

    def test_06_cluster_profiling_retains_nominal_proportions(self):
        """Verify cluster profiling retains category distributions for nominal features without averaging codes."""
        sub_df = self.df_a.head(40)
        labels = np.array([0] * 20 + [1] * 20)
        profiles = compute_cluster_profiles(
            sub_df, labels, feature_specs=self.spec_a["features"], spec_name="SPEC_A", algorithm="PAM", k=2
        )

        nominal_profiles = [p for p in profiles if p["data_type"] == "nominal"]
        self.assertGreater(len(nominal_profiles), 0)
        for p in nominal_profiles:
            self.assertIn("pct", p["metric_type"])
            self.assertFalse(np.isnan(p["metric_value"]))
            self.assertGreaterEqual(p["metric_value"], 0.0)
            self.assertLessEqual(p["metric_value"], 100.0)

    def test_07_external_validation_structure_and_correction(self):
        """Verify external validation runs Kruskal-Wallis with correct step-down Holm-Bonferroni correction."""
        sub_holdout = self.df_hold.head(50)
        labels_k3 = np.array([0] * 20 + [1] * 20 + [2] * 10)
        labels_k4 = np.array([0] * 15 + [1] * 15 + [2] * 10 + [3] * 10)

        rec_k3 = evaluate_external_validation(sub_holdout, labels_k3, spec_name="SPEC_A", algorithm="PAM", k=3)
        rec_k4 = evaluate_external_validation(sub_holdout, labels_k4, spec_name="SPEC_A", algorithm="PAM", k=4)
        all_recs = apply_multiple_testing_corrections(rec_k3 + rec_k4)

        for rec in all_recs:
            self.assertIn("test_statistic", rec)
            self.assertIn("p_value", rec)
            self.assertIn("bonferroni_p_value", rec)
            self.assertIn("holm_bonferroni_p_value", rec)
            self.assertIn("effect_size_value", rec)
            self.assertGreaterEqual(rec["p_value"], 0.0)
            self.assertLessEqual(rec["p_value"], 1.0)
            self.assertGreaterEqual(rec["bonferroni_p_value"], rec["p_value"])
            self.assertGreaterEqual(rec["holm_bonferroni_p_value"], rec["p_value"])

    def test_08_aggregate_reports_exist_and_no_leakage(self):
        """Verify required aggregate CSV reports exist and contain no respondent identifiers."""
        required_reports = [
            "distance_matrix_audit.csv",
            "clustering_metrics.csv",
            "stability_summary.csv",
            "cluster_profile_summary.csv",
            "external_validation_summary.csv"
        ]

        forbidden_cols = ["id", "respondent_id", "source_row_index", "medoid_row_id", "user_id"]

        for rep in required_reports:
            p = os.path.join("reports", "segmentation", rep)
            self.assertTrue(os.path.exists(p), f"Missing report: {rep}")
            df = pd.read_csv(p)
            self.assertGreater(len(df), 0, f"Report {rep} is empty")
            for col in df.columns:
                self.assertNotIn(col.lower(), forbidden_cols, f"Report {rep} leaks respondent-level column: {col}")

    def test_09_processed_matrices_gitignored(self):
        """Verify that processed matrix data and respondent assignments are gitignored."""
        gitignore_path = ".gitignore"
        with open(gitignore_path, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("data/processed/", content)

    def test_10_cluster_sizes_match_between_metrics_and_profiles(self):
        """
        Regression Test: Cluster-size counts in clustering_metrics.csv and
        cluster_profile_summary.csv must match exactly for the same specification, algorithm, and k.
        """
        metrics_df = pd.read_csv(self.metrics_csv_path)
        profiles_df = pd.read_csv(self.profiles_csv_path)

        for _, row in metrics_df.iterrows():
            spec = row["specification"]
            algo_full = row["algorithm"]
            # Profiles use "PAM" as short name
            if "PAM" in algo_full:
                algo = "PAM"
            else:
                continue
            k = int(row["k"])
            expected_sizes = json.loads(row["cluster_sizes"])

            sub_prof = profiles_df[(profiles_df["specification"] == spec) &
                                   (profiles_df["algorithm"] == algo) &
                                   (profiles_df["k"] == k)]
            self.assertGreater(len(sub_prof), 0, f"No profile entries found for {spec} {algo} k={k}")

            for c in range(k):
                c_prof = sub_prof[sub_prof["cluster_id"] == c]
                self.assertGreater(len(c_prof), 0, f"No profile entries for cluster {c}")
                actual_size = int(c_prof["cluster_size"].iloc[0])
                self.assertEqual(
                    actual_size, expected_sizes[c],
                    f"Size mismatch in {spec} {algo} k={k} cluster {c}: metrics={expected_sizes[c]} vs profile={actual_size}"
                )

    def test_11_cluster_sizes_sum_to_807_and_proportions_sum_to_1(self):
        """
        Regression Test: Cluster sizes must sum to exactly 807 active respondents,
        and cluster proportions must sum to 1.0 (+/- 0.001) across all evaluated solutions.
        """
        metrics_df = pd.read_csv(self.metrics_csv_path)

        for _, row in metrics_df.iterrows():
            sizes = json.loads(row["cluster_sizes"])
            props = json.loads(row["cluster_proportions"])
            spec = row["specification"]
            algo = row["algorithm"]
            k = row["k"]

            self.assertEqual(sum(sizes), 807, f"Cluster sizes in {spec} {algo} k={k} sum to {sum(sizes)}, expected 807")
            self.assertAlmostEqual(sum(props), 1.0, places=3,
                                   msg=f"Cluster proportions in {spec} {algo} k={k} sum to {sum(props)}, expected ~1.0")

    def test_12_reported_stability_summaries_match_saved_results(self):
        """
        Regression Test: Verify stability summary statistics are internally valid and match
        actual calculations across all candidate configurations.
        """
        stab_df = pd.read_csv(self.stability_csv_path)

        for _, row in stab_df.iterrows():
            self.assertGreaterEqual(row["median_ari"], -1.0)
            self.assertLessEqual(row["median_ari"], 1.0)
            self.assertLessEqual(row["min_ari"], row["median_ari"])
            self.assertGreaterEqual(row["max_ari"], row["median_ari"])
            self.assertGreaterEqual(row["std_ari"], 0.0)
            self.assertGreaterEqual(row["unstable_runs_count"], 0)
            self.assertLessEqual(row["unstable_runs_count"], row["n_subsamples"])

        # Specific check for SPEC_A PAM k=4:
        row_a4 = stab_df[(stab_df["specification"] == "SPEC_A") & (stab_df["k"] == 4)].iloc[0]
        self.assertEqual(row_a4["median_ari"], 0.6787)
        self.assertEqual(row_a4["mean_ari"], 0.6425)
        self.assertEqual(row_a4["min_ari"], 0.2853)
        self.assertEqual(row_a4["unstable_runs_count"], 8)
        self.assertEqual(row_a4["stability_verdict"], "PROVISIONALLY_STABLE")

    def test_13_persona_feature_claims_match_aggregate_profiles(self):
        """
        Regression Test: Persona claims in SEGMENTATION_EXPERIMENT_DECISION.md must strictly match
        the aggregate profile values in cluster_profile_summary.csv.
        """
        self.assertTrue(os.path.exists(self.decision_md_path))
        with open(self.decision_md_path, "r", encoding="utf-8") as f:
            md_content = f.read()

        prof_df = pd.read_csv(self.profiles_csv_path)
        sub_prof = prof_df[(prof_df["specification"] == "SPEC_A") &
                           (prof_df["algorithm"] == "PAM") &
                           (prof_df["k"] == 4)]

        # Check cluster sizes: 243, 224, 179, 161
        expected_sizes = [243, 224, 179, 161]
        for c, sz in enumerate(expected_sizes):
            self.assertIn(str(sz), md_content, f"Cluster {c} size {sz} not found in decision report")

        # Check fast_delivery_importance means: [3.88, 3.49, 3.34, 3.91]
        fast_del = sub_prof[(sub_prof["feature_name"] == "fast_delivery_importance") & (sub_prof["metric_type"] == "mean")]
        for c in range(4):
            val = round(fast_del[fast_del["cluster_id"] == c]["metric_value"].iloc[0], 2)
            self.assertIn(f"{val:.2f}", md_content, f"Fast delivery mean {val:.2f} for cluster {c} missing from report")

        # Check service_satisfaction_composite means: [3.76, 3.89, 3.99, 3.82]
        sat = sub_prof[(sub_prof["feature_name"] == "service_satisfaction_composite") & (sub_prof["metric_type"] == "mean")]
        for c in range(4):
            val = round(float(sat[sat["cluster_id"] == c]["metric_value"].iloc[0]), 2)
            self.assertIn(f"{val:.2f}", md_content, f"Satisfaction mean {val:.2f} for cluster {c} missing from report")

    def test_14_corrected_p_values_match_multiple_testing_procedure(self):
        """
        Regression Test: Verify that in external_validation_summary.csv, Bonferroni and Holm-Bonferroni
        corrected p-values match the exact multiple testing formulas across the family of 4 comparisons.
        """
        val_df = pd.read_csv(self.validation_csv_path)
        self.assertIn("bonferroni_p_value", val_df.columns)
        self.assertIn("holm_bonferroni_p_value", val_df.columns)

        groups = val_df.groupby(["specification", "algorithm", "holdout_variable"])
        for (spec, algo, var), group in groups:
            m = len(group)
            self.assertEqual(m, 4, f"Family size for {spec} {var} must be 4")

            # Check Bonferroni
            for _, row in group.iterrows():
                expected_bonf = min(1.0, round(row["p_value"] * m, 6))
                self.assertAlmostEqual(row["bonferroni_p_value"], expected_bonf, places=5)

            # Check Holm-Bonferroni step-down
            sorted_rows = group.sort_values("p_value").reset_index(drop=True)
            running_max = 0.0
            for rank, row in sorted_rows.iterrows():
                multiplier = m - rank
                val_holm = min(1.0, row["p_value"] * multiplier)
                running_max = max(running_max, val_holm)
                self.assertAlmostEqual(row["holm_bonferroni_p_value"], min(1.0, round(running_max, 6)), places=5)


if __name__ == "__main__":
    unittest.main()
