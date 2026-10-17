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
    2. QA 19 Codes 1–5 have correct ordinal ranks 1–5; Code 6 has undefined ordinal rank (NaN) and items_varies_considerably = 1.
    3. QA 26 Codes 2–7 have correct ordinal ranks 1–6; Code 8 has undefined ordinal rank (NaN) and monthly_spend_not_sure = 1.
    4. Placement and count of structurally undefined ranks match raw survey responses exactly.
    5. No unexpected missing values appear in other features, and no respondent rows are lost (n=807).
    6. Nominal QA 43 (Shopping Routine Role) is explicitly typed as nominal in JSON specifications.
    7. All 130 source columns have Code Book-backed valid-domain definitions.
    8. Dynamic invalid-value validation detects injected invalid codes.
    9. QA 48 non-use barriers have eligible_count_active = 0 and ineligible_skip_count_active = 807.
    10. Specification A excludes QA 47; Specification B includes QA 47; QA 46 is holdout in both.
    11. Row-level prepared data in data/processed/ are strictly gitignored.
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
    get_codebook_domains,
    validate_survey_domains,
    compute_pairwise_gower_distance,
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
        self.assertEqual(self.full_df.shape[1], EXPECTED_TOTAL_COLS + 3)

        never_mask = (self.full_df['Ever Ordered through a Quick-Commerce Platform'] == 0) & (self.full_df['Order Frequency'] == 1)
        prev_mask = (self.full_df['Ever Ordered through a Quick-Commerce Platform'] == 1) & (self.full_df['Order Frequency'] == 1)
        active_mask = (self.full_df['Ever Ordered through a Quick-Commerce Platform'] == 1) & (self.full_df['Order Frequency'] > 1)

        self.assertEqual(never_mask.sum(), EXPECTED_NEVER_USERS)
        self.assertEqual(prev_mask.sum(), EXPECTED_PREVIOUS_USERS)
        self.assertEqual(active_mask.sum(), EXPECTED_ACTIVE_USERS)

        self.assertEqual(len(self.active_df), EXPECTED_ACTIVE_USERS)
        self.assertTrue((self.active_df['user_subgroup'] == 'Current Active User').all())
        self.assertFalse((self.active_df['Order Frequency'] == 1).any())
        self.assertTrue((self.active_df['Ever Ordered through a Quick-Commerce Platform'] == 1).all())

    def test_02_qa19_and_qa26_special_code_preservation(self):
        """Test QA19 Code 6 and QA26 Code 8 have structurally undefined ranks (NaN) and valid binary indicators."""
        qa19_raw = self.active_df['Items per Order']
        qa26_raw = self.active_df['Monthly Spend']

        self.assertEqual((qa19_raw == 6).sum(), 100, "QA19 Code 6 (Varies considerably) should be exactly 100")
        self.assertEqual((qa26_raw == 8).sum(), 24, "QA26 Code 8 (Not sure) should be exactly 24")
        self.assertEqual((qa26_raw == 1).sum(), 0, "QA26 Code 1 (₹0) must be 0 for active users")

        spec_a = self.prep_results['spec_a']

        # QA 19: Items per Order
        self.assertIn('items_per_order_ordinal', spec_a.columns)
        self.assertIn('items_varies_considerably', spec_a.columns)

        # Code 6 must have NaN rank
        self.assertEqual(spec_a['items_per_order_ordinal'].isna().sum(), 100)
        self.assertEqual(spec_a['items_varies_considerably'].sum(), 100)
        # NaN positions must match exactly where raw QA 19 == 6
        expected_qa19_nan_mask = (qa19_raw == 6).values
        actual_qa19_nan_mask = spec_a['items_per_order_ordinal'].isna().values
        self.assertTrue(np.array_equal(expected_qa19_nan_mask, actual_qa19_nan_mask))

        # Substantive ranks must be bounded in 1.0..5.0
        non_nan_items = spec_a['items_per_order_ordinal'].dropna()
        self.assertEqual(len(non_nan_items), 707)
        self.assertTrue(non_nan_items.isin([1.0, 2.0, 3.0, 4.0, 5.0]).all())

        # QA 26: Monthly Spend
        self.assertIn('monthly_spend_ordinal', spec_a.columns)
        self.assertIn('monthly_spend_not_sure', spec_a.columns)

        # Code 8 must have NaN rank
        self.assertEqual(spec_a['monthly_spend_ordinal'].isna().sum(), 24)
        self.assertEqual(spec_a['monthly_spend_not_sure'].sum(), 24)
        # NaN positions must match exactly where raw QA 26 == 8
        expected_qa26_nan_mask = (qa26_raw == 8).values
        actual_qa26_nan_mask = spec_a['monthly_spend_ordinal'].isna().values
        self.assertTrue(np.array_equal(expected_qa26_nan_mask, actual_qa26_nan_mask))

        # Substantive ranks must be bounded in 1.0..6.0 (source codes 2..7 mapped to 1..6)
        non_nan_spend = spec_a['monthly_spend_ordinal'].dropna()
        self.assertEqual(len(non_nan_spend), 783)
        self.assertTrue(non_nan_spend.isin([1.0, 2.0, 3.0, 4.0, 5.0, 6.0]).all())

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

        for df in [spec_a, spec_b]:
            self.assertNotIn('next_3_month_use', df.columns)
            self.assertNotIn('Next 3 Month Use', df.columns)
            self.assertNotIn('qa46_next_3_month_use', df.columns)

        self.assertIn('qa46_next_3_month_use', holdout.columns)
        self.assertTrue(holdout['qa46_next_3_month_use'].between(1, 5).all())

        self.assertIn('qa47_continue_if_discounts_reduced', holdout.columns)
        self.assertTrue(holdout['qa47_continue_if_discounts_reduced'].between(1, 5).all())

    def test_05_qa48_non_user_barrier_exclusion_and_eligibility(self):
        """Test QA48 non-user barrier fields have eligible_count_active = 0, are skip-coded, and excluded from clustering."""
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

        # Verify skip flag
        self.assertEqual(self.active_df['Reason Not Applicable Current User'].sum(), EXPECTED_ACTIVE_USERS)
        self.assertNotIn('Reason Not Applicable Current User', self.prep_results['spec_a'].columns)
        self.assertNotIn('Reason Not Applicable Current User', self.prep_results['spec_b'].columns)

        # Verify quality audit reports eligible_count_active = 0 and ineligible_skip_count_active = 807
        audit_path = os.path.join(self.reports_dir, "feature_quality_audit.csv")
        audit_df = pd.read_csv(audit_path)
        qa48_audit = audit_df[audit_df['source_column'].isin(qa48_barrier_cols)]

        self.assertEqual(len(qa48_audit), 10)
        self.assertTrue((qa48_audit['eligible_count_active'] == 0).all(), "All QA48 barrier columns must report eligible_count_active = 0")
        self.assertTrue((qa48_audit['ineligible_skip_count_active'] == EXPECTED_ACTIVE_USERS).all(), "All QA48 barrier columns must report ineligible_skip_count_active = 807")

        # Skip flag row
        skip_flag_row = audit_df[audit_df['source_column'] == 'Reason Not Applicable Current User'].iloc[0]
        self.assertEqual(skip_flag_row['eligible_count_active'], EXPECTED_ACTIVE_USERS)
        self.assertEqual(skip_flag_row['ineligible_skip_count_active'], 0)

    def test_06_feature_inventory_and_quality_audit_files(self):
        """Test that feature inventory and quality audit CSVs exist, cover all 130 columns, and have dynamic validation."""
        inv_path = os.path.join(self.reports_dir, "feature_inventory.csv")
        audit_path = os.path.join(self.reports_dir, "feature_quality_audit.csv")

        self.assertTrue(os.path.exists(inv_path), "feature_inventory.csv must exist")
        self.assertTrue(os.path.exists(audit_path), "feature_quality_audit.csv must exist")

        inv_df = pd.read_csv(inv_path)
        audit_df = pd.read_csv(audit_path)

        self.assertEqual(len(inv_df), EXPECTED_TOTAL_COLS, "Inventory must cover all 130 source columns")
        self.assertEqual(len(audit_df), EXPECTED_TOTAL_COLS, "Quality audit must cover all 130 source columns")

        for col in ['question_id', 'source_column', 'substantive_meaning', 'variable_type', 'proposed_role', 'allowed_domain_source', 'allowed_domain_active']:
            self.assertIn(col, inv_df.columns)
            self.assertFalse(inv_df[col].isna().any(), f"Inventory column {col} contains NaNs")

        for col in ['question_id', 'source_column', 'eligible_count_active', 'ineligible_skip_count_active', 'invalid_values_count_source', 'invalid_values_count_active']:
            self.assertIn(col, audit_df.columns)
            self.assertFalse(audit_df[col].isna().any(), f"Audit column {col} contains NaNs")

        # Zero physical missing values and zero invalid values in audited dataset
        self.assertEqual(audit_df['physical_missing_count'].sum(), 0)
        self.assertEqual(audit_df['invalid_values_count_source'].sum(), 0)
        self.assertEqual(audit_df['invalid_values_count_active'].sum(), 0)

    def test_07_json_specifications_conformance(self):
        """Test that machine-readable JSON specs exist, match prepared feature sets, and type QA43 as nominal."""
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

        # QA 43 must be explicitly nominal
        qa43_spec_a = next(feat for feat in spec_a['features'] if feat['name'] == 'shopping_routine_role')
        self.assertEqual(qa43_spec_a['data_type'], 'nominal')

        # QA 19 and QA 26 special code handling in spec
        qa19_spec_a = next(feat for feat in spec_a['features'] if feat['name'] == 'items_per_order_ordinal')
        self.assertIn('NaN', qa19_spec_a['special_codes'])
        self.assertIn('items_varies_considerably', qa19_spec_a['special_codes'])

        qa26_spec_a = next(feat for feat in spec_a['features'] if feat['name'] == 'monthly_spend_ordinal')
        self.assertIn('NaN', qa26_spec_a['special_codes'])
        self.assertIn('monthly_spend_not_sure', qa26_spec_a['special_codes'])

    def test_08_matrix_integrity_and_controlled_missingness(self):
        """Test matrix dimensions, unique row IDs, perfect alignment, and strictly controlled missingness."""
        df_a = self.prep_results['spec_a']
        df_b = self.prep_results['spec_b']
        df_hold = self.prep_results['holdout']

        self.assertEqual(len(df_a), EXPECTED_ACTIVE_USERS)
        self.assertEqual(len(df_b), EXPECTED_ACTIVE_USERS)
        self.assertEqual(len(df_hold), EXPECTED_ACTIVE_USERS)

        self.assertEqual(df_a['survey_row_id'].nunique(), EXPECTED_ACTIVE_USERS)
        self.assertTrue((df_a['survey_row_id'] == df_b['survey_row_id']).all())
        self.assertTrue((df_a['survey_row_id'] == df_hold['survey_row_id']).all())

        # Permitted NaNs strictly in items_per_order_ordinal (100) and monthly_spend_ordinal (24)
        expected_nan_cols = {'items_per_order_ordinal': 100, 'monthly_spend_ordinal': 24}
        for col in df_a.columns:
            if col in expected_nan_cols:
                self.assertEqual(df_a[col].isna().sum(), expected_nan_cols[col])
            else:
                self.assertEqual(df_a[col].isna().sum(), 0, f"Unexpected NaN in Spec A column '{col}'!")

        for col in df_b.columns:
            if col in expected_nan_cols:
                self.assertEqual(df_b[col].isna().sum(), expected_nan_cols[col])
            else:
                self.assertEqual(df_b[col].isna().sum(), 0, f"Unexpected NaN in Spec B column '{col}'!")

        # Holdout matrix must have ZERO NaNs
        self.assertEqual(df_hold.isna().sum().sum(), 0, "Holdout matrix contains unexpected NaNs!")

    def test_09_row_level_data_excluded_from_git(self):
        """Test that data/processed row-level CSVs are ignored by Git."""
        gitignore_path = ".gitignore"
        self.assertTrue(os.path.exists(gitignore_path))

        with open(gitignore_path, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("data/processed/*", content)
        self.assertIn("!data/processed/.gitkeep", content)

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
            pass

    def test_10_satisfaction_composite_reliability(self):
        """Test that service_satisfaction_composite is consistent and correctly calculated."""
        sat_cols = ['Overall Satisfaction', 'Product Quality Satisfaction',
                    'Delivery Reliability Satisfaction', 'Value Money Satisfaction']
        manual_mean = self.active_df[sat_cols].mean(axis=1)

        spec_a = self.prep_results['spec_a']
        self.assertTrue(np.allclose(spec_a['service_satisfaction_composite'], manual_mean, atol=1e-3))
        self.assertTrue(spec_a['service_satisfaction_composite'].between(1.0, 5.0).all())

    def test_11_dynamic_invalid_value_detection(self):
        """Test that dynamic domain auditing detects injected invalid values and identifies the exact column."""
        codebook_domains = get_codebook_domains()
        active_domains_dict = {col: codebook_domains[col]['active'] for col in codebook_domains if col in self.active_df.columns}

        # Baseline clean check
        clean_invalid = validate_survey_domains(self.active_df[[c for c in self.active_df.columns if c in active_domains_dict]], active_domains_dict)
        self.assertEqual(sum(clean_invalid.values()), 0, "Clean active dataset must have zero invalid codes")

        # Corrupt a temporary copy
        corrupted_df = self.active_df.copy()
        corrupted_df.loc[0, 'Order Frequency'] = 99         # Allowed is [2..7]
        corrupted_df.loc[5, 'Monthly Spend'] = -1           # Allowed is [2..8]
        corrupted_df.loc[10, 'Used Blinkit'] = 3            # Allowed is [0..1]
        corrupted_df.loc[15, 'Fast Delivery Importance'] = 0 # Allowed is [1..5]

        corrupt_invalid = validate_survey_domains(corrupted_df[[c for c in corrupted_df.columns if c in active_domains_dict]], active_domains_dict)
        self.assertEqual(corrupt_invalid['Order Frequency'], 1)
        self.assertEqual(corrupt_invalid['Monthly Spend'], 1)
        self.assertEqual(corrupt_invalid['Used Blinkit'], 1)
        self.assertEqual(corrupt_invalid['Fast Delivery Importance'], 1)
        self.assertEqual(sum(corrupt_invalid.values()), 4)

    def test_12_all_130_columns_have_codebook_domains(self):
        """Test that every single source column in Data.xlsx has an explicit Code Book domain definition."""
        codebook_domains = get_codebook_domains()
        self.assertEqual(len(codebook_domains), EXPECTED_TOTAL_COLS)

        for col in self.full_df.columns:
            if col in ['user_subgroup', 'platforms_used_count', 'service_satisfaction_composite']:
                continue
            self.assertIn(col, codebook_domains, f"Column '{col}' is missing from Code Book domain definitions!")
            self.assertIn('source', codebook_domains[col])
            self.assertIn('active', codebook_domains[col])
            self.assertGreater(len(codebook_domains[col]['source']), 0)
            self.assertGreater(len(codebook_domains[col]['active']), 0)


class TestPairwiseGowerContract(unittest.TestCase):
    """
    Focused unit tests for Gate 1C Gower pairwise feature-weighting and distance contract.
    Tests verify:
    - QA19 basket size: ordinary/ordinary, special/special, ordinary/special.
    - QA26 monthly spend: ordinary/ordinary, special/special, ordinary/special.
    - Asymmetric binary rules: (0, 0) omitted from denominator, (1, 1) match, (1, 0) mismatch.
    - Construct weight invariance across all respondent pair combinations.
    - Symmetry, identity, boundedness [0, 1].
    - Zero denominator failure with clear ValueError.
    - Machine-readable specification typing as asymmetric_binary.
    """

    def setUp(self):
        self.qa19_ord = {
            "name": "items_per_order_ordinal",
            "feature_id": "feat_06",
            "data_type": "ordinal",
            "range": [1.0, 5.0]  # R = 4.0
        }
        self.qa19_asym = {
            "name": "items_varies_considerably",
            "feature_id": "feat_07",
            "data_type": "asymmetric_binary",
            "range": [0, 1]
        }
        self.qa26_ord = {
            "name": "monthly_spend_ordinal",
            "feature_id": "feat_04",
            "data_type": "ordinal",
            "range": [1.0, 6.0]  # R = 5.0
        }
        self.qa26_asym = {
            "name": "monthly_spend_not_sure",
            "feature_id": "feat_05",
            "data_type": "asymmetric_binary",
            "range": [0, 1]
        }
        self.baseline_ord = {
            "name": "order_spend",
            "feature_id": "feat_03",
            "data_type": "ordinal",
            "range": [1.0, 7.0]  # R = 6.0
        }

    def test_01_qa19_ordinary_ordinary_pair(self):
        """Ordinary/Ordinary QA19: ordinal ranks compared, (0, 0) flag omitted from denominator."""
        r1 = {"items_per_order_ordinal": 2.0, "items_varies_considerably": 0}
        r2 = {"items_per_order_ordinal": 4.0, "items_varies_considerably": 0}

        dist, num, den = compute_pairwise_gower_distance(
            r1, r2, [self.qa19_ord, self.qa19_asym], return_details=True
        )
        # Denominator must ONLY sum eligible feature weights: 1.0 (ordinal), flag (0,0) is omitted (0.0)
        self.assertEqual(den, 1.0, "QA19 Ordinary/Ordinary pair must have denominator = 1.0, NOT 2.0")
        # Ordinal distance: |2 - 4| / 4.0 = 0.5 -> similarity = 0.5 -> distance = 0.5
        self.assertAlmostEqual(num, 0.5)
        self.assertAlmostEqual(dist, 0.5)

    def test_02_qa19_special_special_pair(self):
        """Special/Special QA19: ordinal omitted (NaN), (1, 1) flag included as match."""
        r1 = {"items_per_order_ordinal": np.nan, "items_varies_considerably": 1}
        r2 = {"items_per_order_ordinal": np.nan, "items_varies_considerably": 1}

        dist, num, den = compute_pairwise_gower_distance(
            r1, r2, [self.qa19_ord, self.qa19_asym], return_details=True
        )
        self.assertEqual(den, 1.0, "QA19 Special/Special pair must have denominator = 1.0")
        self.assertAlmostEqual(num, 1.0, "Special/Special flag match must have numerator = 1.0")
        self.assertAlmostEqual(dist, 0.0, "Identical special volatility must have distance = 0.0")

    def test_03_qa19_ordinary_special_pair(self):
        """Ordinary/Special QA19: ordinal omitted (one NaN), (0, 1) flag included as mismatch."""
        r1 = {"items_per_order_ordinal": 3.0, "items_varies_considerably": 0}
        r2 = {"items_per_order_ordinal": np.nan, "items_varies_considerably": 1}

        dist, num, den = compute_pairwise_gower_distance(
            r1, r2, [self.qa19_ord, self.qa19_asym], return_details=True
        )
        self.assertEqual(den, 1.0, "QA19 Ordinary/Special pair must have denominator = 1.0")
        self.assertAlmostEqual(num, 0.0, "Ordinary/Special mismatch must have numerator = 0.0")
        self.assertAlmostEqual(dist, 1.0, "Ordinary vs Special volatility must have distance = 1.0")

    def test_04_qa26_ordinary_ordinary_pair(self):
        """Ordinary/Ordinary QA26: ordinal spend ranks compared, (0, 0) flag omitted from denominator."""
        r1 = {"monthly_spend_ordinal": 2.0, "monthly_spend_not_sure": 0}
        r2 = {"monthly_spend_ordinal": 5.0, "monthly_spend_not_sure": 0}

        dist, num, den = compute_pairwise_gower_distance(
            r1, r2, [self.qa26_ord, self.qa26_asym], return_details=True
        )
        self.assertEqual(den, 1.0, "QA26 Ordinary/Ordinary pair must have denominator = 1.0, NOT 2.0")
        # Ordinal distance: |2 - 5| / 5.0 = 0.6 -> similarity = 0.4 -> distance = 0.6
        self.assertAlmostEqual(num, 0.4)
        self.assertAlmostEqual(dist, 0.6)

    def test_05_qa26_special_special_pair(self):
        """Special/Special QA26: ordinal omitted (NaN), (1, 1) flag included as match."""
        r1 = {"monthly_spend_ordinal": np.nan, "monthly_spend_not_sure": 1}
        r2 = {"monthly_spend_ordinal": np.nan, "monthly_spend_not_sure": 1}

        dist, num, den = compute_pairwise_gower_distance(
            r1, r2, [self.qa26_ord, self.qa26_asym], return_details=True
        )
        self.assertEqual(den, 1.0, "QA26 Special/Special pair must have denominator = 1.0")
        self.assertAlmostEqual(num, 1.0, "Special/Special uncertainty match must have numerator = 1.0")
        self.assertAlmostEqual(dist, 0.0, "Identical uncertainty must have distance = 0.0")

    def test_06_qa26_ordinary_special_pair(self):
        """Ordinary/Special QA26: ordinal omitted (one NaN), (1, 0) flag included as mismatch."""
        r1 = {"monthly_spend_ordinal": np.nan, "monthly_spend_not_sure": 1}
        r2 = {"monthly_spend_ordinal": 4.0, "monthly_spend_not_sure": 0}

        dist, num, den = compute_pairwise_gower_distance(
            r1, r2, [self.qa26_ord, self.qa26_asym], return_details=True
        )
        self.assertEqual(den, 1.0, "QA26 Ordinary/Special pair must have denominator = 1.0")
        self.assertAlmostEqual(num, 0.0, "Ordinary/Special uncertainty mismatch must have numerator = 0.0")
        self.assertAlmostEqual(dist, 1.0, "Defined spend vs uncertain spend must have distance = 1.0")

    def test_07_construct_weight_invariance_across_all_pair_types(self):
        """Verify that across all 9 combinations of ordinary/special across QA19 and QA26, denominator weight is constant."""
        specs = [self.qa19_ord, self.qa19_asym, self.qa26_ord, self.qa26_asym, self.baseline_ord]

        # 3 candidate respondent profiles:
        # P1: Ordinary basket (rank 1), Ordinary spend (rank 2), Baseline spend (rank 3)
        p1 = {"items_per_order_ordinal": 1.0, "items_varies_considerably": 0,
              "monthly_spend_ordinal": 2.0, "monthly_spend_not_sure": 0, "order_spend": 3.0}
        # P2: Special basket (Code 6), Ordinary spend (rank 5), Baseline spend (rank 3)
        p2 = {"items_per_order_ordinal": np.nan, "items_varies_considerably": 1,
              "monthly_spend_ordinal": 5.0, "monthly_spend_not_sure": 0, "order_spend": 3.0}
        # P3: Special basket (Code 6), Special spend (Code 8), Baseline spend (rank 6)
        p3 = {"items_per_order_ordinal": np.nan, "items_varies_considerably": 1,
              "monthly_spend_ordinal": np.nan, "monthly_spend_not_sure": 1, "order_spend": 6.0}

        pairs = [(p1, p1), (p1, p2), (p1, p3), (p2, p2), (p2, p3), (p3, p3)]

        for ra, rb in pairs:
            dist, num, den = compute_pairwise_gower_distance(ra, rb, specs, return_details=True)
            # In ALL pairs, QA19 contributes 1.0, QA26 contributes 1.0, baseline contributes 1.0 -> total = 3.0
            self.assertEqual(den, 3.0, f"Denominator must remain invariant at 3.0 for all pair combinations, got {den}")
            self.assertTrue(0.0 <= dist <= 1.0, f"Distance must be bounded in [0, 1], got {dist}")

    def test_08_mathematical_properties_symmetry_identity_boundedness(self):
        """Verify symmetry D(r1, r2) == D(r2, r1), identity D(r1, r1) == 0.0, and bounds [0, 1]."""
        specs = [self.qa19_ord, self.qa19_asym, self.qa26_ord, self.qa26_asym]

        r_ord1 = {"items_per_order_ordinal": 1.0, "items_varies_considerably": 0,
                  "monthly_spend_ordinal": 3.0, "monthly_spend_not_sure": 0}
        r_ord2 = {"items_per_order_ordinal": 5.0, "items_varies_considerably": 0,
                  "monthly_spend_ordinal": 1.0, "monthly_spend_not_sure": 0}
        r_spec1 = {"items_per_order_ordinal": np.nan, "items_varies_considerably": 1,
                   "monthly_spend_ordinal": np.nan, "monthly_spend_not_sure": 1}

        # Identity
        self.assertAlmostEqual(compute_pairwise_gower_distance(r_ord1, r_ord1, specs), 0.0)
        self.assertAlmostEqual(compute_pairwise_gower_distance(r_spec1, r_spec1, specs), 0.0)

        # Symmetry
        d12 = compute_pairwise_gower_distance(r_ord1, r_ord2, specs)
        d21 = compute_pairwise_gower_distance(r_ord2, r_ord1, specs)
        self.assertAlmostEqual(d12, d21, places=7)

        d1s = compute_pairwise_gower_distance(r_ord1, r_spec1, specs)
        ds1 = compute_pairwise_gower_distance(r_spec1, r_ord1, specs)
        self.assertAlmostEqual(d1s, ds1, places=7)

        # Boundedness
        self.assertTrue(0.0 <= d12 <= 1.0)
        self.assertTrue(0.0 <= d1s <= 1.0)

    def test_09_zero_denominator_fails_clearly(self):
        """Verify that when a pair has no comparable features, compute_pairwise_gower_distance raises ValueError."""
        # Two respondents where ordinal is NaN and flags are both 0 (jointly absent asymmetric binary)
        r_empty1 = {"items_per_order_ordinal": np.nan, "items_varies_considerably": 0}
        r_empty2 = {"items_per_order_ordinal": np.nan, "items_varies_considerably": 0}

        with self.assertRaises(ValueError) as ctx:
            compute_pairwise_gower_distance(r_empty1, r_empty2, [self.qa19_ord, self.qa19_asym])

        self.assertIn("denominator is zero", str(ctx.exception).lower())

    def test_10_machine_readable_specifications_asymmetric_binary(self):
        """Verify feature_spec_a.json and feature_spec_b.json declare asymmetric_binary and pairwise contract."""
        reports_dir = os.path.join("reports", "segmentation")
        path_a = os.path.join(reports_dir, "feature_spec_a.json")
        path_b = os.path.join(reports_dir, "feature_spec_b.json")

        self.assertTrue(os.path.exists(path_a), "feature_spec_a.json must exist")
        self.assertTrue(os.path.exists(path_b), "feature_spec_b.json must exist")

        with open(path_a, "r", encoding="utf-8") as f:
            spec_a = json.load(f)
        with open(path_b, "r", encoding="utf-8") as f:
            spec_b = json.load(f)

        for spec, name in [(spec_a, "Specification A"), (spec_b, "Specification B")]:
            qa19_flag = next(f for f in spec['features'] if f['name'] == 'items_varies_considerably')
            qa26_flag = next(f for f in spec['features'] if f['name'] == 'monthly_spend_not_sure')

            self.assertEqual(qa19_flag['data_type'], 'asymmetric_binary',
                             f"{name}: items_varies_considerably must have data_type 'asymmetric_binary'")
            self.assertEqual(qa26_flag['data_type'], 'asymmetric_binary',
                             f"{name}: monthly_spend_not_sure must have data_type 'asymmetric_binary'")

            # Check pairwise_gower_contract presence
            rec_method = spec.get('recommended_clustering_methodology', {})
            self.assertIn('pairwise_gower_contract', rec_method,
                          f"{name}: pairwise_gower_contract must be present in recommended_clustering_methodology")
            contract = rec_method['pairwise_gower_contract']
            self.assertIn('denominator_rule', contract)
            self.assertIn('qa19_basket_size_contract', contract)
            self.assertIn('qa26_monthly_spend_contract', contract)
            self.assertIn('construct_weight_invariance', contract)


if __name__ == "__main__":
    unittest.main()
