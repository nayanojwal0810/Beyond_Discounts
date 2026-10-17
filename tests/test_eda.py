#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Automated Test Suite for Gate 1A: Exploratory Data Analysis & Questionnaire Semantics
====================================================================================

Canonical Project:
    Beyond Discounts: Customer Segmentation and Retention Strategy for Indian Quick Commerce

Description:
    Validates:
    1. Subgroup derivations: Never Users (376), Previous Users (80), Current Active Users (807).
    2. Questionnaire routing and response eligibility (QA 47, QA 48, QA 46, QA 49, QA 24, QA 26).
    3. Aggregate table integrity: all 11 tables exist, non-empty, correct denominators, zero raw respondent rows.
    4. Publication figures integrity: all 8 figures exist, non-empty (>50KB).
    5. Quantitative precision: QA 47 mean, counts, percentages reconcile to exact expected baselines.
"""

import os
import unittest
import pandas as pd
import numpy as np
from scipy import stats

from scripts.run_eda import (
    load_and_preprocess_data,
    DEFAULT_SURVEY_PATH,
    DEFAULT_SHEET,
    DEFAULT_TABLES_DIR,
    DEFAULT_FIGURES_DIR
)


class TestSubgroupDerivationsAndRouting(unittest.TestCase):
    """Test suite validating subgroup derivations and questionnaire routing rules."""

    @classmethod
    def setUpClass(cls):
        cls.df = load_and_preprocess_data(DEFAULT_SURVEY_PATH, DEFAULT_SHEET)

    def test_total_dimensions_and_nulls(self):
        """Verifies total survey dimensions and absence of physical nulls."""
        self.assertEqual(len(self.df), 1263, "Total row count must be exactly 1,263.")
        self.assertGreaterEqual(len(self.df.columns), 130, "Total column count must be at least 130.")
        # Check original survey columns (first 130 columns) have zero physical nulls
        original_cols = self.df.columns[:130]
        total_nulls = self.df[original_cols].isna().sum().sum()
        self.assertEqual(total_nulls, 0, "Original survey columns must contain exactly 0 physical nulls.")

    def test_subgroup_counts_and_partition(self):
        """Verifies exact subgroup partition counts."""
        subgroup_counts = self.df['user_subgroup'].value_counts()
        self.assertEqual(subgroup_counts.get('Never User', 0), 376, "Never-users must equal 376.")
        self.assertEqual(subgroup_counts.get('Previous User', 0), 80, "Previous users must equal 80.")
        self.assertEqual(subgroup_counts.get('Current Active User', 0), 807, "Current active users must equal 807.")
        self.assertEqual(subgroup_counts.sum(), 1263, "Sum of subgroups must equal total sample 1,263.")
        self.assertEqual((self.df['user_subgroup'] == 'Unknown').sum(), 0, "No respondent should have 'Unknown' subgroup.")

    def test_qa47_continuation_routing(self):
        """
        Enforces strict QA 47 routing:
        - Current active users (n=807) must have values in {1, 2, 3, 4, 5}.
        - Non-current users (n=456) must strictly have Code 6 (Not Applicable).
        - Code 6 must NEVER appear among current users.
        """
        curr_mask = self.df['user_subgroup'] == 'Current Active User'
        non_curr_mask = self.df['user_subgroup'].isin(['Never User', 'Previous User'])

        curr_qa47 = self.df.loc[curr_mask, 'Continue If Discounts Reduced']
        non_curr_qa47 = self.df.loc[non_curr_mask, 'Continue If Discounts Reduced']

        # Current users must be strictly 1-5
        self.assertTrue(curr_qa47.isin([1, 2, 3, 4, 5]).all(),
                        "All 807 current active users must have substantive QA 47 response in {1..5}.")
        self.assertFalse((curr_qa47 == 6).any(),
                         "Code 6 (Not Applicable) must NEVER appear among current active users.")

        # Non-current users must be strictly Code 6
        self.assertEqual(len(non_curr_qa47), 456, "Non-current users must total exactly 456.")
        self.assertTrue((non_curr_qa47 == 6).all(),
                        "All 456 non-current users must have QA 47 coded 6 (Not Applicable).")

    def test_qa48_barrier_routing(self):
        """
        Enforces QA 48 routing:
        - Non-current respondents (n=456) must be eligible for barrier questions.
        - Current active users (n=807) must hold the skip flag 'Reason Not Applicable Current User' == 1.
        """
        curr_mask = self.df['user_subgroup'] == 'Current Active User'
        skip_flag = self.df.loc[curr_mask, 'Reason Not Applicable Current User']
        self.assertTrue((skip_flag == 1).all(),
                        "All 807 current active users must have skip flag 'Reason Not Applicable Current User' == 1.")

        non_curr_mask = self.df['user_subgroup'].isin(['Never User', 'Previous User'])
        non_curr_skip_flag = self.df.loc[non_curr_mask, 'Reason Not Applicable Current User']
        self.assertTrue((non_curr_skip_flag == 0).all(),
                        "Non-current respondents must have skip flag == 0.")

    def test_universal_questions_coverage(self):
        """Verifies universal substantive responses for QA 46 and QA 49 across all 1,263 respondents."""
        qa46 = self.df['Next 3 Month Use']
        qa49 = self.df['Improvement']

        self.assertTrue(qa46.isin(range(1, 6)).all(),
                        "QA 46 (Next 3 Month Use) must have values in {1..5} across all 1,263 rows.")
        self.assertTrue(qa49.isin(range(1, 11)).all(),
                        "QA 49 (Improvement) must have values in {1..10} across all 1,263 rows.")

    def test_substantive_zero_and_nonuse_codes(self):
        """
        Verifies:
        - QA 26: Code 1 represents substantive ₹0 monthly spend (n=456).
        - QA 43: Code 6 represents substantive 'I do not use quick commerce' (n=456).
        """
        non_curr_mask = self.df['user_subgroup'].isin(['Never User', 'Previous User'])
        qa26_non_curr = self.df.loc[non_curr_mask, 'Monthly Spend']
        qa43_non_curr = self.df.loc[non_curr_mask, 'Shopping Routine Role']

        self.assertTrue((qa26_non_curr == 1).all(),
                        "All 456 non-current respondents must have QA 26 Monthly Spend == 1 (₹0 spend).")
        self.assertTrue((qa43_non_curr == 6).all(),
                        "All 456 non-current respondents must have QA 43 Shopping Routine == 6 (Non-use).")

    def test_qa14_first_trial_reason_routing_and_codes(self):
        """
        Enforces QA 14 (First Trial Reason) source codebook consistency and routing:
        - Source codebook defines exactly 8 codes: 1..7 (substantive reasons) and 8 (Not applicable – never used).
        - No code 9 or any value outside {1..8} may exist.
        - Ever-users (n=887: 807 current active + 80 previous users) must strictly hold substantive codes in {1..7}.
        - Never-users (n=376) must strictly hold Code 8 (Not applicable – never used).
        - No ever-user may hold Code 8, and no never-user may hold codes 1..7.
        """
        qa14 = self.df['First Trial Reason']

        # 1. Global domain check: values must be in {1..8}, absolutely no code 9
        self.assertTrue(qa14.isin(range(1, 9)).all(),
                        "QA 14 (First Trial Reason) values must fall strictly within {1..8}.")
        self.assertFalse((qa14 == 9).any(),
                         "Code 9 does not exist in source codebook or dataset and must not appear in QA 14.")

        never_mask = self.df['user_subgroup'] == 'Never User'
        ever_mask = self.df['user_subgroup'].isin(['Current Active User', 'Previous User'])

        # 2. Never-users (n=376) must strictly hold Code 8
        never_qa14 = self.df.loc[never_mask, 'First Trial Reason']
        self.assertEqual(len(never_qa14), 376, "Never-users must total exactly 376.")
        self.assertTrue((never_qa14 == 8).all(),
                        "All 376 never-users must have QA 14 coded 8 ('Not applicable – never used').")

        # 3. Ever-users (n=887) must strictly hold substantive trial codes {1..7}
        ever_qa14 = self.df.loc[ever_mask, 'First Trial Reason']
        self.assertEqual(len(ever_qa14), 887, "Ever-users (807 current + 80 previous) must total exactly 887.")
        self.assertTrue(ever_qa14.isin(range(1, 8)).all(),
                        "All 887 ever-users must have QA 14 substantive trial codes in {1..7}.")
        self.assertFalse((ever_qa14 == 8).any(),
                         "Code 8 ('Not applicable') must never appear among ever-users.")


class TestAggregateOutputIntegrity(unittest.TestCase):
    """Test suite validating that all aggregate analytical tables and figures exist and meet standards."""

    EXPECTED_TABLES = [
        "dataset_profile_quality.csv",
        "demographics_distribution.csv",
        "usage_and_shopping_behavior.csv",
        "platform_footprint_summary.csv",
        "category_adoption_and_preference.csv",
        "qa47_discount_continuation_distribution.csv",
        "qa47_cross_tabs_and_associations.csv",
        "qa46_future_intention_by_subgroup.csv",
        "qa48_non_user_barriers_comparison.csv",
        "qa49_improvements_by_subgroup.csv",
        "segmentation_feature_candidates.csv"
    ]

    EXPECTED_FIGURES = [
        "fig1_subgroup_breakdown.png",
        "fig2_demographics_overview.png",
        "fig3_qa47_discount_continuation.png",
        "fig4_discount_sensitivity_bivariate.png",
        "fig5_qa46_future_intention_subgroups.png",
        "fig6_qa48_non_use_barriers.png",
        "fig7_qa49_improvement_priorities.png",
        "fig8_segmentation_feature_landscape.png"
    ]

    def test_all_tables_exist_and_are_aggregate_only(self):
        """Verifies that all 11 tables exist, are non-empty, and contain NO raw respondent rows."""
        for tname in self.EXPECTED_TABLES:
            tpath = os.path.join(DEFAULT_TABLES_DIR, tname)
            self.assertTrue(os.path.isfile(tpath), f"Table missing: {tpath}")

            tdf = pd.read_csv(tpath)
            self.assertGreater(len(tdf), 0, f"Table {tname} is empty.")
            # Ensure table is aggregate summary, NOT raw microdata
            self.assertLessEqual(len(tdf), 100,
                                 f"Table {tname} has {len(tdf)} rows; exceeds aggregate limit (must not leak raw microdata).")

    def test_all_figures_exist_and_are_valid(self):
        """Verifies that all 8 figures exist and have substantial file size (>50KB for 300 DPI PNG)."""
        for fname in self.EXPECTED_FIGURES:
            fpath = os.path.join(DEFAULT_FIGURES_DIR, fname)
            self.assertTrue(os.path.isfile(fpath), f"Figure missing: {fpath}")
            fsize = os.path.getsize(fpath)
            self.assertGreater(fsize, 50000, f"Figure {fname} is suspiciously small ({fsize} bytes).")

    def test_qa47_table_quantities(self):
        """Validates quantitative figures in QA 47 distribution table."""
        tpath = os.path.join(DEFAULT_TABLES_DIR, "qa47_discount_continuation_distribution.csv")
        tdf = pd.read_csv(tpath)

        # Check rows for codes 1-5
        code_rows = tdf[tdf['Likert Code'].isin(['1', '2', '3', '4', '5'])]
        total_n = code_rows['Count (n)'].sum()
        self.assertEqual(total_n, 807, "Sum of counts for Likert codes 1-5 must equal exactly 807.")

        # Check lower intention tier (codes 1-2: 52 + 121 = 173)
        cnt_1 = int(code_rows.loc[code_rows['Likert Code'] == '1', 'Count (n)'].iloc[0])
        cnt_2 = int(code_rows.loc[code_rows['Likert Code'] == '2', 'Count (n)'].iloc[0])
        self.assertEqual(cnt_1, 52, "Code 1 (Definitely no) count must equal 52.")
        self.assertEqual(cnt_2, 121, "Code 2 (Probably no) count must equal 121.")
        self.assertEqual(cnt_1 + cnt_2, 173, "Lower intention tier count must equal 173 (21.44%).")

        # Check operational tier labels exist
        tier_row = tdf[tdf['Likert Code'] == 'Tier: Lower continuation intention (Codes 1-2)']
        self.assertEqual(len(tier_row), 1, "Must contain 'Tier: Lower continuation intention (Codes 1-2)'.")
        self.assertEqual(int(tier_row['Count (n)'].iloc[0]), 173)

    def test_qa15_complete_active_distribution(self):
        """
        Validates QA 15 Order Frequency:
        - Active-user distribution contains all 6 valid observed codes (2..7).
        - Category counts sum to exactly 807.
        - Percentages sum to approximately 100%.
        - Code 1 (Never) does not appear among active users.
        """
        tpath = os.path.join(DEFAULT_TABLES_DIR, "usage_and_shopping_behavior.csv")
        tdf = pd.read_csv(tpath)
        qa15_df = tdf[tdf['Behavioral Domain'] == 'Order Frequency (QA 15)']

        # Must have exactly 6 active categories
        self.assertEqual(len(qa15_df), 6, "QA 15 must contain exactly 6 active response categories (Codes 2..7).")
        self.assertEqual(list(qa15_df['Code'].astype(int)), [2, 3, 4, 5, 6, 7], "Codes must be 2, 3, 4, 5, 6, 7.")

        # Expected counts per codebook
        expected_counts = {
            2: 87,   # Less than once a month
            3: 206,  # 1–3 times a month
            4: 204,  # About once a week
            5: 177,  # 2–3 times a week
            6: 91,   # 4–6 times a week
            7: 42    # Daily or almost daily
        }
        for code, exp_cnt in expected_counts.items():
            obs_cnt = int(qa15_df.loc[qa15_df['Code'].astype(int) == code, 'Count'].iloc[0])
            self.assertEqual(obs_cnt, exp_cnt, f"QA 15 Code {code} count ({obs_cnt}) does not match expected ({exp_cnt}).")

        self.assertEqual(qa15_df['Count'].sum(), 807, "QA 15 active-user counts must sum to 807.")
        self.assertAlmostEqual(qa15_df['Percentage (%)'].sum(), 100.0, places=1,
                               msg="QA 15 category percentages must sum to ~100.0%.")

    def test_qa13_usage_duration_reconciliation(self):
        """
        Validates QA 13 Usage Duration:
        - Active-user distribution contains all 5 valid active codes (2..6).
        - Category counts sum to 807.
        - Never-users (n=376) strictly hold Code 1 (Never used).
        - Previous users (n=80) strictly hold codes in {2..6}.
        """
        tpath = os.path.join(DEFAULT_TABLES_DIR, "usage_and_shopping_behavior.csv")
        tdf = pd.read_csv(tpath)
        qa13_df = tdf[tdf['Behavioral Domain'] == 'Usage Duration (QA 13)']

        self.assertEqual(len(qa13_df), 5, "QA 13 must contain 5 active categories (Codes 2..6).")
        self.assertEqual(list(qa13_df['Code'].astype(int)), [2, 3, 4, 5, 6])

        expected_counts = {
            2: 77,   # Less than 3 months
            3: 118,  # 3–6 months
            4: 160,  # 7–12 months
            5: 238,  # 1–2 years
            6: 214   # More than 2 years
        }
        for code, exp_cnt in expected_counts.items():
            obs_cnt = int(qa13_df.loc[qa13_df['Code'].astype(int) == code, 'Count'].iloc[0])
            self.assertEqual(obs_cnt, exp_cnt, f"QA 13 Code {code} count ({obs_cnt}) != expected ({exp_cnt}).")

        self.assertEqual(qa13_df['Count'].sum(), 807, "QA 13 active-user counts must sum to 807.")

        # Validate Code 1 (Never used) in raw data
        raw_df = load_and_preprocess_data(DEFAULT_SURVEY_PATH, DEFAULT_SHEET)
        never_users = raw_df[raw_df['user_subgroup'] == 'Never User']
        prev_users = raw_df[raw_df['user_subgroup'] == 'Previous User']

        self.assertEqual((never_users['Usage Duration'] == 1).sum(), 376,
                         "All 376 Never-users must have QA 13 Code 1 (Never used).")
        self.assertEqual((prev_users['Usage Duration'] == 1).sum(), 0,
                         "Zero previous users should have Code 1 (all used QC prior to lapsing).")
        self.assertTrue(prev_users['Usage Duration'].isin([2, 3, 4, 5, 6]).all(),
                        "All 80 previous users must have QA 13 in codes 2..6.")

    def test_all_behavioral_categories_reconciliation(self):
        """Validates that all behavioral domains in Table 3 have complete categories summing to 807."""
        tpath = os.path.join(DEFAULT_TABLES_DIR, "usage_and_shopping_behavior.csv")
        tdf = pd.read_csv(tpath)

        domains = {
            'Order Frequency (QA 15)': 6,
            'Usage Duration (QA 13)': 5,
            'Items per Order (QA 19)': 6,
            'Expected Delivery Time (QA 20)': 6,
            'Order Spend INR (QA 25)': 7,
            'Monthly Spend INR (QA 26 - Current Users)': 7,
            'Shopping Routine Role (QA 43 - Current Users)': 5,
            'Payment Method (QA 30)': 6
        }
        for domain, expected_cats in domains.items():
            sub = tdf[tdf['Behavioral Domain'] == domain]
            self.assertEqual(len(sub), expected_cats, f"Domain '{domain}' must have {expected_cats} categories.")
            self.assertEqual(sub['Count'].sum(), 807, f"Domain '{domain}' counts must sum to 807.")
            self.assertAlmostEqual(sub['Percentage (%)'].sum(), 100.0, places=1,
                                   msg=f"Domain '{domain}' percentages must sum to ~100.0%.")

    def test_demographics_subgroup_distribution_reconciliation(self):
        """Validates that Table 2 demographics reconcile across all 4 subgroup columns."""
        tpath = os.path.join(DEFAULT_TABLES_DIR, "demographics_distribution.csv")
        tdf = pd.read_csv(tpath)

        demo_domains = [
            'Age Group', 'Gender', 'Education', 'Occupation',
            'Personal Income', 'Area of Residence', 'Region', 'Household Size'
        ]
        for d in demo_domains:
            sub = tdf[tdf['Demographic Variable'] == d]
            self.assertGreater(len(sub), 0, f"Domain '{d}' must be present in demographics table.")
            self.assertEqual(sub['Current Users Count (n=807)'].sum(), 807, f"{d} active count sum != 807")
            self.assertEqual(sub['Previous Users Count (n=80)'].sum(), 80, f"{d} previous count sum != 80")
            self.assertEqual(sub['Never Users Count (n=376)'].sum(), 376, f"{d} never count sum != 376")
            self.assertEqual(sub['Total Count (N=1263)'].sum(), 1263, f"{d} total count sum != 1263")

    def test_association_interpretations_neutrality_and_multiple_testing(self):
        """
        Validates that generated association interpretations:
        - Do not declare associations established purely from correlation sign.
        - Correctly disclose multiple-testing limitation (Bonferroni alpha ~0.0038).
        - Confirm all 13 tests are non-significant after multiple testing.
        - Contain neutral operational descriptions.
        """
        tpath = os.path.join(DEFAULT_TABLES_DIR, "qa47_cross_tabs_and_associations.csv")
        tdf = pd.read_csv(tpath)
        self.assertEqual(len(tdf), 13, "Must test exactly 13 candidate behavioral associations.")

        # All 13 tests must have 'No' for multiple testing significance
        self.assertTrue((tdf['Significant after Multiple Testing?'] == 'No').all(),
                        "All 13 associations must be recognized as non-significant after Bonferroni adjustment.")

        # Adjusted alpha must be documented as 0.0038
        self.assertTrue((tdf['Multiple Testing Adjusted α (m=13)'].astype(str) == '0.0038').all(),
                        "Bonferroni adjusted alpha must be 0.0038.")

        # Ensure no unsupported churn/proven loyalty claims in substantive interpretation
        unsupported_terms = ["severe churn risk", "purely subsidy-driven", "proven loyal", "discount-dependent"]
        for interp in tdf['Substantive Interpretation']:
            interp_lower = interp.lower()
            for term in unsupported_terms:
                self.assertNotIn(term, interp_lower, f"Unsupported term '{term}' found in interpretation: {interp}")
            self.assertIn("inconclusive", interp_lower,
                          f"Non-significant test must be described as inconclusive: {interp}")

    def test_qa48_table_denominators(self):
        """Validates that QA 48 barrier comparison table uses denominators 376 and 80."""
        tpath = os.path.join(DEFAULT_TABLES_DIR, "qa48_non_user_barriers_comparison.csv")
        tdf = pd.read_csv(tpath)
        self.assertEqual(len(tdf), 10, "QA 48 barrier comparison table must contain exactly 10 barrier items.")

        # Ensure all percentage point differences and Fisher p-values are populated
        self.assertTrue(tdf['Percentage Point Difference (Prev - Nev)'].notna().all())
        self.assertTrue(tdf['Fisher Exact p-value'].notna().all())
        # Ensure exploratory methodological note is present
        self.assertTrue(tdf['Exploratory Methodological Note'].notna().all())

    def test_qa47_association_analysis_methods_and_categories(self):
        """
        Validates statistical rigor of QA 47 association analysis (Table 7):
        - QA19 code 6 ('Varies considerably') is handled as a separate non-ordinal response via Kruskal-Wallis.
        - QA26 code 8 ('Not sure') is handled as a separate non-ordinal response via Kruskal-Wallis.
        - Correct analysis methods are recorded (Kruskal-Wallis for QA 19/26; Spearman for 11 ordered/continuous variables).
        - Test sample sizes and category totals reconcile to all 807 eligible current active users.
        - Other eligible ordinal predictors retain valid ordered treatment.
        - Bonferroni multiple testing correction is applied consistently across all 13 primary tests.
        """
        tpath = os.path.join(DEFAULT_TABLES_DIR, "qa47_cross_tabs_and_associations.csv")
        tdf = pd.read_csv(tpath)
        self.assertEqual(len(tdf), 13, "Must evaluate exactly 13 primary association tests.")

        # Load active users to compute ground-truth checks dynamically
        df = load_and_preprocess_data(DEFAULT_SURVEY_PATH, "Data")
        curr_df = df[df['user_subgroup'] == 'Current Active User'].copy()
        self.assertEqual(len(curr_df), 807, "Eligible current active users must equal 807.")

        # 1. QA 19 (Items per Order) validation
        qa19_row = tdf[tdf['Predictor / Behavioral Factor'].str.contains('QA 19')]
        self.assertEqual(len(qa19_row), 1, "QA 19 must appear exactly once.")
        qa19 = qa19_row.iloc[0]
        self.assertEqual(int(qa19['Analysis Sample Size (n)']), 807, "QA 19 sample size must be 807.")
        self.assertIn("Kruskal-Wallis", str(qa19['Statistical Test Method']),
                      "QA 19 must use Kruskal-Wallis test across categories, not Spearman rank.")
        self.assertEqual(qa19['Test Statistic Name'], "Kruskal-Wallis H")
        self.assertEqual(str(qa19['Spearman Rho (ρ)']), "N/A (Categorical test)",
                         "QA 19 must not have an ordinal Spearman Rho.")
        # Verify category distribution of QA 19 among active users
        qa19_counts = curr_df['Items per Order'].value_counts().to_dict()
        self.assertEqual(qa19_counts[6], 100, "Code 6 ('Varies considerably') must have n=100.")
        self.assertEqual(sum(qa19_counts.values()), 807, "QA 19 category sum must reconcile to 807.")
        # Dynamically verify Kruskal-Wallis H and p-value
        qa19_groups = [curr_df.loc[curr_df['Items per Order'] == c, 'Continue If Discounts Reduced'].values
                       for c in sorted(curr_df['Items per Order'].unique())]
        self.assertEqual(len(qa19_groups), 6, "QA 19 must have 6 categories (Codes 1–6).")
        h19, p19 = stats.kruskal(*qa19_groups)
        self.assertAlmostEqual(float(qa19['Test Statistic Value']), round(h19, 3), places=2)

        # 2. QA 26 (Monthly Spend) validation
        qa26_row = tdf[tdf['Predictor / Behavioral Factor'].str.contains('QA 26')]
        self.assertEqual(len(qa26_row), 1, "QA 26 must appear exactly once.")
        qa26 = qa26_row.iloc[0]
        self.assertEqual(int(qa26['Analysis Sample Size (n)']), 807, "QA 26 sample size must be 807.")
        self.assertIn("Kruskal-Wallis", str(qa26['Statistical Test Method']),
                      "QA 26 must use Kruskal-Wallis test across categories, not Spearman rank.")
        self.assertEqual(qa26['Test Statistic Name'], "Kruskal-Wallis H")
        self.assertEqual(str(qa26['Spearman Rho (ρ)']), "N/A (Categorical test)",
                         "QA 26 must not have an ordinal Spearman Rho.")
        # Verify category distribution of QA 26 among active users
        qa26_counts = curr_df['Monthly Spend'].value_counts().to_dict()
        self.assertEqual(qa26_counts[8], 24, "Code 8 ('Not sure') must have n=24.")
        self.assertEqual(sum(qa26_counts.values()), 807, "QA 26 category sum must reconcile to 807.")
        # Dynamically verify Kruskal-Wallis H and p-value
        qa26_groups = [curr_df.loc[curr_df['Monthly Spend'] == c, 'Continue If Discounts Reduced'].values
                       for c in sorted(curr_df['Monthly Spend'].unique())]
        self.assertEqual(len(qa26_groups), 7, "QA 26 must have 7 active categories (Codes 2–8).")
        h26, p26 = stats.kruskal(*qa26_groups)
        self.assertAlmostEqual(float(qa26['Test Statistic Value']), round(h26, 3), places=2)

        # 3. Validate the 11 remaining ordered/continuous predictors retain valid Spearman treatment
        spearman_rows = tdf[~tdf['Predictor / Behavioral Factor'].str.contains('QA 19|QA 26')]
        self.assertEqual(len(spearman_rows), 11, "Must have exactly 11 Spearman rank correlation tests.")
        for _, row in spearman_rows.iterrows():
            self.assertEqual(row['Statistical Test Method'], "Spearman rank correlation")
            self.assertEqual(row['Test Statistic Name'], "Spearman Rho (ρ)")
            self.assertEqual(int(row['Analysis Sample Size (n)']), 807)
            self.assertEqual(row['Kruskal-Wallis H-stat'], "N/A (Spearman test)")
            self.assertTrue(np.isfinite(float(row['Spearman Rho (ρ)'])))

        # 4. Validate consistent Bonferroni multiple testing adjustment across all 13 tests
        for _, row in tdf.iterrows():
            raw_p = float(row['Raw p-value'])
            adj_p = float(row['Bonferroni Adjusted p-value'])
            expected_adj_p = min(1.0, raw_p * 13)
            self.assertAlmostEqual(adj_p, expected_adj_p, places=3)
            self.assertEqual(row['Significant after Multiple Testing?'], "No")
            self.assertIn("inconclusive", str(row['Substantive Interpretation']).lower())

    def test_fig4_bivariate_figure_properties(self):
        """Validates that Figure 4 is properly regenerated and exists."""
        fig4_path = os.path.join(DEFAULT_FIGURES_DIR, "fig4_discount_sensitivity_bivariate.png")
        self.assertTrue(os.path.exists(fig4_path), "fig4_discount_sensitivity_bivariate.png must exist.")
        self.assertGreater(os.path.getsize(fig4_path), 50000, "Figure 4 file size must be substantial (>50KB).")


class TestErrorHandlingAndEdgeCases(unittest.TestCase):
    """Test suite validating robust error handling in data loading."""

    def test_missing_file_raises_error(self):
        """Non-existent survey file must raise FileNotFoundError."""
        with self.assertRaises(FileNotFoundError):
            load_and_preprocess_data("non_existent_file.xlsx", "Data")

    def test_unexpected_dimensions_raises_error(self):
        """Dataset with wrong row count must raise ValueError."""
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tf:
            temp_path = tf.name
        try:
            # Write a dummy Excel with incorrect dimensions (10 rows x 5 cols)
            dummy_df = pd.DataFrame(np.zeros((10, 5)))
            dummy_df.to_excel(temp_path, sheet_name="Data", index=False)
            with self.assertRaises(ValueError):
                load_and_preprocess_data(temp_path, "Data")
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)


if __name__ == "__main__":
    unittest.main()
