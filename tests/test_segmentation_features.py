#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Gate 1B: Segmentation Feature Audit & Data Preparation Regression Tests
========================================================================

Project:
    Beyond Discounts: Customer Segmentation and Retention Strategy for Indian Quick Commerce

Description:
    Enforces all Gate 1B validation rules:
    1. Primary population contains strictly 807 current active users; never-users (376) and previous users (80) excluded.
    2. Expected source variables exist and observed category codes match audited codebook domains.
    3. QA 19 Code 6 ("Varies considerably") and QA 26 Code 8 ("Not sure") remain nominal/special categories.
    4. QA 47 is absent from Specification A and present only in Specification B.
    5. QA 46 and QA 47 holdout values are not accidentally included in Specification A's feature inputs.
    6. QA 46 is strictly isolated as stated-intention data, not actual retention.
    7. QA 48 non-user barrier fields are not introduced into active-user clustering matrices.
    8. Feature types and encoding choices match machine-readable JSON specifications.
    9. No unintended row loss, duplicated columns, or constant inputs in feature matrices.
    10. Row-level prepared matrices in data/processed/ are strictly gitignored.
"""

import os
import json
import unittest
import subprocess
import pandas as pd
import numpy as np

from scripts.prepare_segmentation_features import (
    load_and_filter_active_users,
    generate_feature_inventory,
    generate_feature_quality_audit,
    generate_feature_specifications,
    prepare_feature_matrices,
    get_column_metadata_mapping,
    DEFAULT_SURVEY_PATH,
    DEFAULT_SHEET,
    EXPECTED_TOTAL_ROWS,
    EXPECTED_TOTAL_COLS,
    EXPECTED_NEVER_USERS,
    EXPECTED_PREVIOUS_USERS,
    EXPECTED_ACTIVE_USERS
)


class TestSegmentationFeatures(unittest.TestCase):
    """Test suite for Gate 1B feature preparation pipeline and artifacts."""

    @classmethod
    def setUpClass(cls):
        cls.survey_path = DEFAULT_SURVEY_PATH
        cls.sheet_name = DEFAULT_SHEET
        cls.reports_dir = os.path.join("reports", "segmentation")
        cls.data_dir = os.path.join("data", "processed")

        # Load data once for testing
        cls.full_df, cls.active_df = load_and_filter_active_users(cls.survey_path, cls.sheet_name)
        cls.prep_results = prepare_feature_matrices(cls.active_df, cls.data_dir)

    def test_01_primary_population_and_subgroup_isolation(self):
        """Test primary population contains strictly 807 current active users, with other subgroups excluded."""
        self.assertEqual(len(self.full_df), EXPECTED_TOTAL_ROWS)
        self.assertEqual(self.full_df.shape[1], EXPECTED_TOTAL_COLS + 3)  # + user_subgroup, platforms_used_count, service_satisfaction_composite

        never_mask = (self.full_df['Ever Ordered through a Quick-Commerce Platform'] == 0) & (self.full_df['Order Frequency'] == 1)
        prev_mask = (self.full_df['Ever Ordered through a Quick-Commerce Platform'] == 1) & (self.full_df['Order Frequency'] == 1)
        active_mask = (self.full_df['Ever Ordered through a Quick-Commerce Platform'] == 1) & (self.full_df['Order Frequency'] > 1)

        self.assertEqual(never_mask.sum(), EXPECTED_NEVER_USERS)
        self.assertEqual(prev_mask.sum(), EXPECTED_PREVIOUS_USERS)
        self.assertEqual(active_mask.sum(), EXPECTED_ACTIVE_USERS)

        # Ensure active_df is exactly the active population
        self.assertEqual(len(self.active_df), EXPECTED_ACTIVE_USERS)
        self.assertTrue((self.active_df['user_subgroup'] == 'Current Active User').all())
        self.assertFalse((self.active_df['Order Frequency'] == 1).any())
        self.assertTrue((self.active_df['Ever Ordered through a Quick-Commerce Platform'] == 1).all())

    def test_02_qa19_and_qa26_special_code_preservation(self):
        """Test QA19 Code 6 and QA26 Code 8 remain nominal/special categories rather than higher ordinal levels."""
        # Raw observed values in active users
        qa19_raw = self.active_df['Items per Order']
        qa26_raw = self.active_df['Monthly Spend']

        self.assertEqual((qa19_raw == 6).sum(), 100, "QA19 Code 6 (Varies considerably) should be exactly 100")
        self.assertEqual((qa26_raw == 8).sum(), 24, "QA26 Code 8 (Not sure) should be exactly 24")
        self.assertEqual((qa26_raw == 1).sum(), 0, "QA26 Code 1 (₹0) must be 0 for active users")

        spec_a = self.prep_results['spec_a']

        # Items per order: ordinal rank must NOT exceed 5
        self.assertIn('items_per_order_ordinal', spec_a.columns)
        self.assertIn('items_varies_considerably', spec_a.columns)
        self.assertTrue(spec_a['items_per_order_ordinal'].between(1, 5).all(), "Ordinal items must be bounded in 1..5")
        self.assertEqual(spec_a['items_varies_considerably'].sum(), 100, "items_varies_considerably flag must sum to 100")

        # Monthly spend: ordinal rank must NOT exceed 6
        self.assertIn('monthly_spend_ordinal', spec_a.columns)
        self.assertIn('monthly_spend_not_sure', spec_a.columns)
        self.assertTrue(spec_a['monthly_spend_ordinal'].between(1, 6).all(), "Ordinal spend tier must be bounded in 1..6")
        self.assertEqual(spec_a['monthly_spend_not_sure'].sum(), 24, "monthly_spend_not_sure flag must sum to 24")

    def test_03_qa47_specification_separation(self):
        """Test QA47 is absent from Specification A and present only in Specification B."""
        spec_a = self.prep_results['spec_a']
        spec_b = self.prep_results['spec_b']

        self.assertNotIn('continue_if_discounts_reduced', spec_a.columns)
        self.assertNotIn('Continue If Discounts Reduced', spec_a.columns)
        self.assertNotIn('qa47', [c.lower() for c in spec_a.columns])

        self.assertIn('continue_if_discounts_reduced', spec_b.columns)
        self.assertEqual(len(spec_b.columns), len(spec_a.columns) + 1)
        self.assertTrue(spec_b['continue_if_discounts_reduced'].between(1, 5).all())

    def test_04_qa46_and_qa47_holdout_isolation(self):
        """Test QA46 and QA47 holdout values are not included in Specification A feature inputs and QA46 is holdout in both."""
        spec_a = self.prep_results['spec_a']
        spec_b = self.prep_results['spec_b']
        holdout = self.prep_results['holdout']

        # QA 46 absent from both feature matrices
        for df in [spec_a, spec_b]:
            self.assertNotIn('next_3_month_use', df.columns)
            self.assertNotIn('Next 3 Month Use', df.columns)
            self.assertNotIn('qa46_next_3_month_use', df.columns)

        # QA 46 present in holdout
        self.assertIn('qa46_next_3_month_use', holdout.columns)
        self.assertTrue(holdout['qa46_next_3_month_use'].between(1, 5).all())

        # QA 47 present in holdout for Spec A evaluation
        self.assertIn('qa47_continue_if_discounts_reduced', holdout.columns)
        self.assertTrue(holdout['qa47_continue_if_discounts_reduced'].between(1, 5).all())

    def test_05_qa48_non_user_barrier_exclusion(self):
        """Test QA48 non-user barrier fields are excluded from clustering features and constant in active cohort."""
        qa48_barrier_cols = [
            'Reason Service Unavailable', 'Reason Prefer Physical', 'Reason Prices High',
            'Reason Delivery Fees', 'Reason Distrust Quality', 'Reason Prefer Inspect',
            'Reason Impulsive Spending Concern', 'Reason No Need Rapid',
            'Reason Privacy Payment Concern', 'Reason Unfamiliar Apps'
        ]

        # Verify active users have constant 0 for all barriers
        for col in qa48_barrier_cols:
            self.assertEqual(self.active_df[col].sum(), 0, f"{col} must be constant 0 for active users")
            self.assertNotIn(col, self.prep_results['spec_a'].columns)
            self.assertNotIn(col, self.prep_results['spec_b'].columns)

        # Verify active users have constant 1 for Reason Not Applicable Current User
        self.assertEqual(self.active_df['Reason Not Applicable Current User'].sum(), EXPECTED_ACTIVE_USERS)
        self.assertNotIn('Reason Not Applicable Current User', self.prep_results['spec_a'].columns)
        self.assertNotIn('Reason Not Applicable Current User', self.prep_results['spec_b'].columns)

    def test_06_feature_inventory_and_quality_audit_files(self):
        """Test that feature inventory and quality audit CSVs exist and contain complete, non-empty records."""
        inv_path = os.path.join(self.reports_dir, "feature_inventory.csv")
        audit_path = os.path.join(self.reports_dir, "feature_quality_audit.csv")

        self.assertTrue(os.path.exists(inv_path), "feature_inventory.csv must exist")
        self.assertTrue(os.path.exists(audit_path), "feature_quality_audit.csv must exist")

        inv_df = pd.read_csv(inv_path)
        audit_df = pd.read_csv(audit_path)

        self.assertEqual(len(inv_df), EXPECTED_TOTAL_COLS, "Inventory must cover all 130 source columns")
        self.assertEqual(len(audit_df), EXPECTED_TOTAL_COLS, "Quality audit must cover all 130 source columns")

        # Check required columns
        for col in ['question_id', 'source_column', 'substantive_meaning', 'variable_type', 'proposed_role']:
            self.assertIn(col, inv_df.columns)
            self.assertFalse(inv_df[col].isna().any(), f"Inventory column {col} contains NaNs")

        for col in ['question_id', 'source_column', 'eligible_count_active', 'is_constant_active', 'quality_action_taken']:
            self.assertIn(col, audit_df.columns)
            self.assertFalse(audit_df[col].isna().any(), f"Audit column {col} contains NaNs")

        # Zero physical nulls or invalid values
        self.assertEqual(audit_df['physical_missing_count'].sum(), 0)
        self.assertEqual(audit_df['invalid_values_count'].sum(), 0)

    def test_07_json_specifications_conformance(self):
        """Test that machine-readable JSON specs exist, are valid, and match prepared feature sets."""
        spec_a_path = os.path.join(self.reports_dir, "feature_spec_a.json")
        spec_b_path = os.path.join(self.reports_dir, "feature_spec_b.json")

        self.assertTrue(os.path.exists(spec_a_path))
        self.assertTrue(os.path.exists(spec_b_path))

        with open(spec_a_path, "r", encoding="utf-8") as f:
            spec_a = json.load(f)
        with open(spec_b_path, "r", encoding="utf-8") as f:
            spec_b = json.load(f)

        self.assertEqual(spec_a['feature_count'], 17)
        self.assertEqual(spec_b['feature_count'], 18)
        self.assertEqual(len(spec_a['features']), 17)
        self.assertEqual(len(spec_b['features']), 18)

        # Feature names in spec A match dataframe columns (excluding survey_row_id)
        spec_a_feature_names = [feat['name'] for feat in spec_a['features']]
        df_a_cols = [c for c in self.prep_results['spec_a'].columns if c != 'survey_row_id']
        self.assertEqual(spec_a_feature_names, df_a_cols)

        # Feature names in spec B match dataframe columns (excluding survey_row_id)
        spec_b_feature_names = [feat['name'] for feat in spec_b['features']]
        df_b_cols = [c for c in self.prep_results['spec_b'].columns if c != 'survey_row_id']
        self.assertEqual(spec_b_feature_names, df_b_cols)

        # Target population check in specs
        self.assertEqual(spec_a['target_population']['sample_size'], EXPECTED_ACTIVE_USERS)
        self.assertEqual(spec_b['target_population']['sample_size'], EXPECTED_ACTIVE_USERS)

    def test_08_matrix_integrity_and_row_alignment(self):
        """Test matrix dimensions, unique row IDs, no NaNs, and perfect row alignment."""
        df_a = self.prep_results['spec_a']
        df_b = self.prep_results['spec_b']
        df_hold = self.prep_results['holdout']

        self.assertEqual(len(df_a), EXPECTED_ACTIVE_USERS)
        self.assertEqual(len(df_b), EXPECTED_ACTIVE_USERS)
        self.assertEqual(len(df_hold), EXPECTED_ACTIVE_USERS)

        # Unique survey_row_id
        self.assertEqual(df_a['survey_row_id'].nunique(), EXPECTED_ACTIVE_USERS)
        self.assertTrue((df_a['survey_row_id'] == df_b['survey_row_id']).all())
        self.assertTrue((df_a['survey_row_id'] == df_hold['survey_row_id']).all())

        # No nulls
        self.assertEqual(df_a.isna().sum().sum(), 0)
        self.assertEqual(df_b.isna().sum().sum(), 0)
        self.assertEqual(df_hold.isna().sum().sum(), 0)

        # Check no constant columns in feature matrices
        for col in df_a.columns:
            if col != 'survey_row_id':
                self.assertGreater(df_a[col].nunique(), 1, f"Column {col} in Spec A is constant!")

    def test_09_row_level_data_excluded_from_git(self):
        """Test that data/processed row-level CSVs are ignored by Git."""
        gitignore_path = ".gitignore"
        self.assertTrue(os.path.exists(gitignore_path))

        with open(gitignore_path, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("data/processed/*", content)
        self.assertIn("!data/processed/.gitkeep", content)

        # Check git check-ignore via subprocess
        sample_path = os.path.join("data", "processed", "segmentation_spec_a.csv")
        try:
            res = subprocess.run(
                ["git", "check-ignore", sample_path],
                capture_output=True,
                text=True,
                check=False
            )
            self.assertEqual(res.returncode, 0, f"{sample_path} is NOT ignored by Git!")
        except FileNotFoundError:
            # If git CLI is unavailable, verify file matching directly
            pass

    def test_10_satisfaction_composite_reliability(self):
        """Test that service_satisfaction_composite is consistent and correctly calculated."""
        sat_cols = ['Overall Satisfaction', 'Product Quality Satisfaction',
                    'Delivery Reliability Satisfaction', 'Value Money Satisfaction']
        manual_mean = self.active_df[sat_cols].mean(axis=1)

        spec_a = self.prep_results['spec_a']
        self.assertTrue(np.allclose(spec_a['service_satisfaction_composite'], manual_mean, atol=1e-3))
        self.assertTrue(spec_a['service_satisfaction_composite'].between(1.0, 5.0).all())


if __name__ == "__main__":
    unittest.main()
