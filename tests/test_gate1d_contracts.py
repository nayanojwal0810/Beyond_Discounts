"""Synthetic contract tests for Gate 1C technical controls used by Gate 1D.

These tests must run without the private/local survey workbook or prepared respondent matrices.
"""
import unittest
from unittest.mock import patch

import numpy as np
import pandas as pd

from scripts.run_segmentation_experiments import (
    apply_multiple_testing_corrections,
    compute_post_cluster_categorical_profiles,
    run_subsampling_stability,
)


class TestGate1DContracts(unittest.TestCase):
    def test_multiple_testing_preserves_small_p_value_precision(self):
        records = [
            {
                "specification": "SPEC_A",
                "algorithm": "PAM",
                "holdout_variable": "QA47",
                "p_value": 1e-10,
                "circularity_status": "Independent validation",
            },
            {
                "specification": "SPEC_A",
                "algorithm": "PAM",
                "holdout_variable": "QA47",
                "p_value": 0.02,
                "circularity_status": "Independent validation",
            },
        ]

        corrected = apply_multiple_testing_corrections(records)

        self.assertGreater(corrected[0]["p_value"], 0.0)
        self.assertGreater(corrected[0]["holm_bonferroni_p_value"], 0.0)
        self.assertAlmostEqual(corrected[0]["holm_bonferroni_p_value"], 2e-10, delta=1e-15)
        self.assertAlmostEqual(corrected[1]["holm_bonferroni_p_value"], 0.02, places=10)

    def test_failed_stability_runs_are_not_encoded_as_zero_ari(self):
        distance_matrix = np.zeros((5, 5), dtype=float)
        baseline_labels = np.array([0, 0, 1, 1, 1])
        mocked_results = [
            (np.array([0, 2]), baseline_labels, 1.0),
            RuntimeError("synthetic resample failure"),
            RuntimeError("synthetic resample failure"),
        ]

        with patch(
            "scripts.run_segmentation_experiments.pam_kmedoids",
            side_effect=mocked_results,
        ):
            result = run_subsampling_stability(
                distance_matrix,
                k=2,
                n_subsamples=2,
                subsample_ratio=0.8,
                seed_base=50,
            )

        self.assertEqual(result["n_subsamples"], 2)
        self.assertEqual(result["successful_runs_count"], 0)
        self.assertEqual(result["failed_runs_count"], 2)
        self.assertIsNone(result["median_ari"])
        self.assertEqual(result["stability_verdict"], "FAILED")
        self.assertTrue(all(row["status"] == "failed" for row in result["run_records"]))
        self.assertTrue(all(row["ari"] is None for row in result["run_records"]))

    def test_post_cluster_qa49_profile_has_all_categories_and_reconciles(self):
        holdout = pd.DataFrame(
            {
                "survey_row_id": list(range(101, 109)),
                "qa49_preferred_improvement": [1, 1, 2, 10, 3, 3, 4, 4],
            }
        )
        labels = np.array([0, 0, 0, 0, 1, 1, 1, 1])

        profiles = compute_post_cluster_categorical_profiles(
            holdout,
            labels,
            spec_name="SPEC_A",
            algorithm="PAM",
            k=2,
            reference_row_ids=holdout["survey_row_id"].to_numpy(),
        )
        prof = pd.DataFrame(profiles)

        self.assertEqual(len(prof), 2 * 10 * 2)  # 2 clusters x 10 categories x count/pct
        for cluster_id in (0, 1):
            part = prof[prof["cluster_id"] == cluster_id]
            pct = part[part["metric_type"].str.endswith("_pct")]
            counts = part[part["metric_type"].str.endswith("_count")]
            self.assertEqual(len(pct), 10)
            self.assertEqual(len(counts), 10)
            self.assertAlmostEqual(float(pct["metric_value"].sum()), 100.0, places=3)
            self.assertEqual(int(counts["metric_value"].sum()), 4)
            self.assertTrue((part["feature_name"] == "qa49_preferred_improvement").all())

    def test_post_cluster_profile_rejects_misaligned_row_ids(self):
        holdout = pd.DataFrame(
            {
                "survey_row_id": [1, 2, 3, 4],
                "qa49_preferred_improvement": [1, 2, 3, 4],
            }
        )
        with self.assertRaisesRegex(ValueError, "do not align"):
            compute_post_cluster_categorical_profiles(
                holdout,
                np.array([0, 0, 1, 1]),
                spec_name="SPEC_A",
                algorithm="PAM",
                k=2,
                reference_row_ids=np.array([4, 3, 2, 1]),
            )


if __name__ == "__main__":
    unittest.main()
