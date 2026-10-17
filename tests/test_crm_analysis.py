import os
import tempfile
import unittest

import numpy as np
import pandas as pd

from scripts.run_crm_analysis import (
    QA48_BARRIERS,
    PLATFORM_COLS,
    derive_cohorts,
    holm_adjust,
    monte_carlo_chi_square,
    run_analysis,
    run_parallel_slopes_diagnostic,
    _fit_ordered_model,
)


def make_synthetic_survey(seed=64, n_never=30, n_previous=20, n_current=120):
    """Create synthetic-only responses to test code paths, never survey findings."""
    rng = np.random.default_rng(seed)
    n = n_never + n_previous + n_current
    never = np.arange(0, n_never)
    previous = np.arange(n_never, n_never + n_previous)
    current = np.arange(n_never + n_previous, n)

    df = pd.DataFrame({
        "Ever Ordered through a Quick-Commerce Platform": np.r_[
            np.zeros(n_never, dtype=int), np.ones(n_previous + n_current, dtype=int)
        ],
        "Order Frequency": np.r_[
            np.ones(n_never + n_previous, dtype=int),
            2 + (np.arange(n_current) % 6)
        ],
        "Next 3 Month Use": rng.integers(1, 6, size=n),
        "Continue If Discounts Reduced": np.r_[
            np.full(n_never + n_previous, 6, dtype=int),
            1 + (np.arange(n_current) % 5)
        ],
        "Improvement": rng.integers(1, 11, size=n),
        "Shopping Routine Role": np.r_[
            np.full(n_never + n_previous, 6, dtype=int),
            rng.integers(1, 6, size=n_current)
        ],
    })

    for col in PLATFORM_COLS:
        values = rng.binomial(1, 0.45, size=n)
        values[never] = 0
        df[col] = values

    for col in [
        "Discount Overspend", "Threshold Extra Items", "Compare Platform Prices",
        "Compare Physical Prices", "Fast Delivery Importance",
    ]:
        values = np.r_[np.full(n_never + n_previous, 6), rng.integers(1, 6, size=n_current)]
        df[col] = values.astype(int)

    # Source-defined N/A code for non-current respondents on the satisfaction battery.
    for col in [
        "Overall Satisfaction", "Product Quality Satisfaction",
        "Delivery Reliability Satisfaction", "Value Money Satisfaction",
    ]:
        df[col] = np.r_[
            np.full(n_never + n_previous, 6), rng.integers(1, 6, size=n_current)
        ].astype(int)

    for col, _ in QA48_BARRIERS:
        # Binary multi-response indicators. These are synthetic and intentionally varied.
        df[col] = rng.binomial(1, 0.25, size=n)

    return df


class TestCRMAnalysis(unittest.TestCase):
    def setUp(self):
        self.df = make_synthetic_survey()

    def test_cohort_partition_and_qa47_tiers(self):
        data = derive_cohorts(self.df)
        counts = data["user_subgroup"].value_counts().to_dict()
        self.assertEqual(counts, {
            "Current Active User": 120,
            "Never User": 30,
            "Previous User": 20,
        })
        tier_counts = data.loc[data["user_subgroup"] == "Current Active User", "qa47_tier"].value_counts()
        self.assertEqual(int(tier_counts["Lower intention (1-2)"]), 48)
        self.assertEqual(int(tier_counts["Uncertain (3)"]), 24)
        self.assertEqual(int(tier_counts["Higher intention (4-5)"]), 48)

    def test_strict_shape_check_uses_original_source_columns(self):
        """A valid-shaped source passes schema/cohort checks after internal columns are derived."""
        source = make_synthetic_survey(
            seed=65, n_never=376, n_previous=80, n_current=807
        )
        for index in range(130 - source.shape[1]):
            source[f"unused_source_column_{index:03d}"] = 0
        self.assertEqual(source.shape, (1263, 130))
        data = derive_cohorts(source, strict=True)
        self.assertEqual(len(data), 1263)
        self.assertEqual(data["user_subgroup"].value_counts().to_dict(), {
            "Current Active User": 807, "Never User": 376, "Previous User": 80
        })

    def test_holm_adjustment_preserves_input_order_and_small_values(self):
        p = [0.03, 1e-10, 0.2, 0.01]
        adjusted = holm_adjust(p)
        self.assertAlmostEqual(adjusted[1], 4e-10)
        self.assertAlmostEqual(adjusted[3], 0.03)
        self.assertAlmostEqual(adjusted[0], 0.06)
        self.assertAlmostEqual(adjusted[2], 0.2)

    def test_monte_carlo_independence_test_returns_valid_values(self):
        table = np.array([[24, 12, 9], [10, 20, 15], [8, 14, 28]])
        out = monte_carlo_chi_square(table, n_resamples=999, seed=7)
        self.assertEqual(out["n"], int(table.sum()))
        self.assertGreaterEqual(out["monte_carlo_p_value"], 1 / 1000)
        self.assertLessEqual(out["monte_carlo_p_value"], 1.0)
        self.assertGreaterEqual(out["cramers_v"], 0.0)
        self.assertLessEqual(out["cramers_v"], 1.0)

    def test_parallel_slopes_diagnostic_is_explicit_about_status(self):
        rng = np.random.default_rng(8)
        n = 600
        x = rng.normal(size=n)
        latent = 0.65 * x + rng.logistic(size=n)
        y = np.digitize(latent, [-1.2, -0.4, 0.4, 1.2]) + 1
        X = pd.DataFrame({"x": x})
        out = run_parallel_slopes_diagnostic(y, X)
        self.assertIn(out["status"], {"COMPLETED", "INCONCLUSIVE"})
        if out["status"] == "COMPLETED":
            self.assertTrue(np.isfinite(out["wald_chi2"]))
            self.assertTrue(0 <= out["p_value"] <= 1)

    def test_ordered_model_helper_fits_synthetic_ordinal_outcome(self):
        rng = np.random.default_rng(10)
        n = 400
        x = rng.normal(size=n)
        latent = 0.6 * x + rng.logistic(size=n)
        y = pd.Series(np.digitize(latent, [-1.2, -0.4, 0.4, 1.2]) + 1)
        result, info = _fit_ordered_model(
            y, pd.DataFrame({"x": x}), distribution="logit", model_name="synthetic-only test"
        )
        self.assertIsNotNone(result, msg=info.get("detail", "ordered model failed"))
        self.assertEqual(info["status"], "COMPLETED")
        self.assertTrue(np.isfinite(info["aic"]))

    def test_qa47_model_pipeline_writes_fit_and_assumption_diagnostics(self):
        """Exercise the full model-selection/reporting path using randomized synthetic-only data."""
        from scripts.run_crm_analysis import fit_qa47_models
        source = make_synthetic_survey(seed=71, n_never=376, n_previous=80, n_current=807)
        data = derive_cohorts(source)
        with tempfile.TemporaryDirectory() as tmp:
            fit_qa47_models(data, tmp)
            fit_path = os.path.join(tmp, "qa47_model_fit_summary.csv")
            coef_path = os.path.join(tmp, "qa47_model_coefficients.csv")
            diag_path = os.path.join(tmp, "qa47_model_diagnostics.csv")
            status_path = os.path.join(tmp, "qa47_multinomial_sensitivity_status.csv")
            self.assertTrue(os.path.exists(fit_path))
            self.assertTrue(os.path.exists(coef_path))
            self.assertTrue(os.path.exists(diag_path))
            self.assertTrue(os.path.exists(status_path))
            fit = pd.read_csv(fit_path)
            self.assertGreaterEqual(len(fit), 3)
            primary = fit[fit["model"] == "QA47 ordered logit — prespecified trend model"]
            self.assertEqual(len(primary), 1)
            self.assertEqual(int(primary.iloc[0]["n"]), 807)
            diagnostics = pd.read_csv(diag_path)
            self.assertGreaterEqual(len(diagnostics), 2)
            self.assertTrue(set(diagnostics["status"]).issubset({"COMPLETED", "INCONCLUSIVE"}))
            self.assertTrue(os.path.exists(os.path.join(tmp, "qa47_multinomial_sensitivity.csv")))

    def test_analysis_writes_only_aggregate_tables_without_model(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = run_analysis(
                self.df, tmp, mc_resamples=999, seed=29, strict=False, skip_model=True,
                source_file_name="synthetic_fixture.xlsx"
            )
            expected = [
                "qa46_intention_distribution.csv",
                "qa46_cohort_test.csv",
                "qa49_preference_distribution.csv",
                "qa49_action_family_distribution.csv",
                "qa49_association_tests.csv",
                "qa48_barrier_prevalence.csv",
                "qa48_barrier_comparison.csv",
                "crm_analysis_run_metadata.csv",
            ]
            for filename in expected:
                self.assertTrue(os.path.exists(os.path.join(tmp, filename)), filename)
            self.assertEqual(len(out["qa46_distribution"]), 20)
            self.assertEqual(len(out["qa49_options"]), 70)
            self.assertEqual(len(out["qa49_families"]), 28)
            self.assertEqual(len(out["qa48_prevalence"]), 20)
            self.assertEqual(len(out["qa48_comparison"]), 10)
            qa49_tests = out["qa49_tests"]
            self.assertEqual(len(qa49_tests), 4)
            self.assertIn("holm_adjusted_p_value", qa49_tests.columns)
            self.assertTrue(
                (qa49_tests["holm_adjusted_p_value"] >= qa49_tests["monte_carlo_p_value"]).all()
            )
            self.assertTrue(qa49_tests["significant_after_holm_0_05"].isin([True, False]).all())
            saved_files = os.listdir(tmp)
            self.assertFalse(any("respondent" in name.lower() or "assignment" in name.lower() for name in saved_files))
            metadata = pd.read_csv(os.path.join(tmp, "crm_analysis_run_metadata.csv"))
            self.assertEqual(metadata.loc[0, "source_file_name"], "synthetic_fixture.xlsx")
            self.assertFalse(bool(metadata.loc[0, "causal_claim"]))


if __name__ == "__main__":
    unittest.main()
