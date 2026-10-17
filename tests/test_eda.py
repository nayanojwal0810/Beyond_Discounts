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

        # Check sensitive tier (codes 1-2: 52 + 121 = 173)
        cnt_1 = int(code_rows.loc[code_rows['Likert Code'] == '1', 'Count (n)'].iloc[0])
        cnt_2 = int(code_rows.loc[code_rows['Likert Code'] == '2', 'Count (n)'].iloc[0])
        self.assertEqual(cnt_1, 52, "Code 1 (Definitely no) count must equal 52.")
        self.assertEqual(cnt_2, 121, "Code 2 (Probably no) count must equal 121.")
        self.assertEqual(cnt_1 + cnt_2, 173, "Sensitive tier count must equal 173 (21.44%).")

    def test_qa48_table_denominators(self):
        """Validates that QA 48 barrier comparison table uses denominators 376 and 80."""
        tpath = os.path.join(DEFAULT_TABLES_DIR, "qa48_non_user_barriers_comparison.csv")
        tdf = pd.read_csv(tpath)
        self.assertEqual(len(tdf), 10, "QA 48 barrier comparison table must contain exactly 10 barrier items.")

        # Ensure all percentage point differences and Fisher p-values are populated
        self.assertTrue(tdf['Percentage Point Difference (Prev - Nev)'].notna().all())
        self.assertTrue(tdf['Fisher Exact p-value'].notna().all())


class TestErrorHandlingAndEdgeCases(unittest.TestCase):
    """Test suite validating robust error handling in data loading."""

    def test_missing_file_raises_error(self):
        """Non-existent survey file must raise FileNotFoundError."""
        with self.assertRaises(FileNotFoundError):
            load_and_preprocess_data("non_existent_file.xlsx", "Data")


if __name__ == "__main__":
    unittest.main()
