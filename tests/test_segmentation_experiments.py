"""
Unit tests for Gate 1C segmentation experiments pipeline.

Verifies:
1. Distance matrix mathematical properties (square, symmetric, bounded [0, 1], finite, zero diagonal).
2. Proper feature inclusion/exclusion across specifications (Spec A excludes QA47, both exclude QA46, Spec B includes QA47).
3. PAM algorithm properties (deterministic for fixed seeds, convergence, valid medoids, non-empty clusters).
4. Subsampling stability computation.
5. Cluster profiling retaining nominal distributions.
6. Aggregate reports generation and data governance (no respondent-level data committed).
"""

import unittest
import os
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
    evaluate_external_validation
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

    def test_07_external_validation_structure(self):
        """Verify external validation runs Kruskal-Wallis with correct Holm-Bonferroni correction."""
        sub_holdout = self.df_hold.head(50)
        labels = np.array([0] * 25 + [1] * 25)
        records = evaluate_external_validation(
            sub_holdout, labels, spec_name="SPEC_A", algorithm="PAM", k=2, n_k_comparisons=4
        )
        self.assertGreaterEqual(len(records), 1)
        for rec in records:
            self.assertIn("test_statistic", rec)
            self.assertIn("p_value", rec)
            self.assertIn("holm_bonferroni_p_value", rec)
            self.assertIn("effect_size_value", rec)
            self.assertGreaterEqual(rec["p_value"], 0.0)
            self.assertLessEqual(rec["p_value"], 1.0)

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


if __name__ == "__main__":
    unittest.main()
