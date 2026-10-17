#!/usr/bin/env python3
"""
tests/test_audit_survey_data.py

Unit and integration tests for scripts/audit_survey_data.py.
Verifies survey schema validation, binary indicator constraints,
codebook range validation, logical consistency, and usage-status triangulation
(the 80-record previous-user issue).

All test fixtures in this file are EXPLICITLY SYNTHETIC unit-test fixtures.
They are NOT business data and must never be conflated with real survey records.
"""

import os
import sys
import unittest
import pandas as pd
import numpy as np

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from scripts.audit_survey_data import (
    audit_survey_dataframe,
    resolve_survey_path,
    compute_file_sha256,
    SINGLE_SELECT_RANGES
)


class TestAuditSurveyData(unittest.TestCase):
    """Test suite validating survey data audit behavior on synthetic fixtures."""

    def setUp(self):
        """Builds a minimal synthetic baseline DataFrame adhering to survey schema."""
        self.base_row = {
            'Age Group': 2,
            'Gender': 1,
            'Education': 3,
            'Occupation': 2,
            'Personal Income': 4,
            'Area of Residence': 1,
            'Region': 1,
            'Household Size': 3,
            'Awareness of Quick Commerce Services': 1,
            'Ever Ordered through a Quick-Commerce Platform': 1,
            'Aware Blinkit': 1,
            'Aware Zepto': 1,
            'Aware Swiggy Instamart': 1,
            'Aware BigBasket BBNow': 0,
            'Aware Flipkart Minutes': 0,
            'Aware Amazon Rapid': 0,
            'Aware Other': 0,
            'Aware None': 0,
            'Used Blinkit': 1,
            'Used Zepto': 0,
            'Used Swiggy Instamart': 0,
            'Used BigBasket BBNow': 0,
            'Used Flipkart Minutes': 0,
            'Used Amazon Rapid': 0,
            'Used Never Used': 0,
            'Usage Duration': 5,
            ' First Trial Reason': 2,  # Header with leading space
            ' Order Frequency': 4,     # Header with leading space
            'Common Days': 2,
            'Common Time': 3,
            'Reason Forgotten Item': 1,
            'Reason Urgent Need': 1,
            'Reason Grocery Topup': 0,
            'Reason Snacks Beverages': 0,
            'Reason Planned Convenience': 0,
            'Reason Late Night': 0,
            'Reason Hosting Guests': 0,
            'Reason Avoid Travel Queues': 0,
            'Reason Promotion Discount': 0,
            'Reason Not Applicable': 0,
            'Items per Order': 2,
            'Expected Delivery': 1,
            'Spontaneous Frequency': 3,
            'Category Fresh Fruit Veg': 1,
            'Category Milk Dairy': 1,
            'Category Bread Eggs Breakfast': 0,
            'Category Packaged Groceries': 0,
            'Category Snacks Confectionery': 0,
            'Category Beverages': 0,
            'Category Personal Care': 0,
            'Category Beauty Grooming': 0,
            'Category Household Cleaning': 0,
            'Category Baby Care': 0,
            'Category Pet Care': 0,
            'Category OTC Health Wellness': 0,
            'Category Stationery': 0,
            'Category Mobile Electronic Accessories': 0,
            'Category Small Household Kitchen': 0,
            'Category Ready Eat Cook': 0,
            'Category Festival Occasion': 0,
            'Category Not Applicable': 0,
            'Most Frequent Category': 1,
            'Physical Fresh Fruit Veg': 0,
            'Physical Dairy Breakfast': 0,
            'Physical Packaged Groceries': 0,
            'Physical Snacks Beverages': 0,
            'Physical Personal Care Beauty': 0,
            'Physical Household Cleaning': 0,
            'Physical Electronic Accessories': 0,
            'Physical No Clear Preference': 1,
            'Order Spend': 3,
            'Monthly Spend': 4,
            'Total Spending Change': 3,
            'Discount Overspend': 2,
            'Threshold Extra Items': 3,
            'Payment Method': 1,
            'Factor Delivery Speed': 1,
            'Factor Product Availability': 1,
            'Factor Lower Prices': 0,
            'Factor Discounts Coupon': 0,
            ' Factor Low Delivery Fee': 0,
            'Factor Low Min Order': 0,
            'Factor App Usability': 0,
            'Factor Past Experience': 0,
            'Factor Product Quality': 0,
            'Factor Brand Trust': 0,
            'Factor Payment Options': 0,
            'Factor Customer Support': 0,
            'Factor Return Refund': 0,
            'Most Important Factor': 1,
            'Compare Platform Prices': 2,
            'Compare Physical Prices': 2,
            'Fast Delivery Importance ': 4,
            'Problem Out of Stock': 0,
            'Problem Wrong Item': 0,
            'Problem Damaged Product': 0,
            'Problem Poor Fresh Produce': 0,
            'Problem Late Delivery': 0,
            'Problem Higher Price': 0,
            'Problem Unexpected Fees': 0,
            'Problem Order Cancellation': 0,
            'Problem Refund Delay': 0,
            'Problem Payment Issue': 0,
            'Problem App Technical': 0,
            'Problem Customer Service': 0,
            ' Problem No Major Problem': 1,
            'Problem Not Applicable': 0,
            'Overall Satisfaction': 4,
            'Product Quality Satisfaction': 4,
            'Delivery Reliability Satisfaction': 4,
            'Value Money Satisfaction': 4,
            'Kirana Visit Change': 3,
            'Supermarket Visit Change': 3,
            'Shopping Routine Role': 3,
            'Unplanned Purchase': 3,
            'New Brand Trial': 3,
            'Next 3 Month Use': 4,
            'Continue If Discounts Reduced': 4,
            'Reason Service Unavailable': 0,
            'Reason Prefer Physical': 0,
            'Reason Prices High': 0,
            'Reason Delivery Fees': 0,
            'Reason Distrust Quality': 0,
            'Reason Prefer Inspect': 0,
            'Reason Impulsive Spending Concern': 0,
            'Reason No Need Rapid': 0,
            'Reason Privacy Payment Concern': 0,
            'Reason Unfamiliar Apps': 0,
            'Reason Not Applicable Current User': 1,
            'Improvement': 3
        }

    def test_nonexistent_explicit_path_fails(self):
        """Verifies that nonexistent survey file path raises SystemExit(1) without silent fallback."""
        with self.assertRaises(SystemExit) as cm:
            resolve_survey_path("nonexistent_survey_path_xyz_999.xlsx")
        self.assertEqual(cm.exception.code, 1)

    def test_whitespace_header_detection(self):
        """Verifies that columns with leading or trailing whitespaces are flagged."""
        synthetic_df = pd.DataFrame([self.base_row])
        result = audit_survey_dataframe(synthetic_df)
        ws_cols = result['whitespace_column_names']

        self.assertIn(' First Trial Reason', ws_cols)
        self.assertIn(' Order Frequency', ws_cols)
        self.assertIn('Fast Delivery Importance ', ws_cols)

    def test_binary_indicator_violations(self):
        """Verifies that multi-select dummy indicator variables flag non-binary values."""
        bad_row = dict(self.base_row)
        bad_row['Used Blinkit'] = 2  # Invalid dummy code
        bad_row['Aware Zepto'] = -1  # Invalid dummy code

        synthetic_df = pd.DataFrame([bad_row])
        result = audit_survey_dataframe(synthetic_df)
        violations = result['binary_column_violations']

        self.assertIn('Used Blinkit', violations)
        self.assertIn(2, violations['Used Blinkit'])
        self.assertIn('Aware Zepto', violations)
        self.assertIn(-1, violations['Aware Zepto'])

    def test_range_violations_on_single_select(self):
        """Verifies that single-select questions flag codes outside the codebook range."""
        bad_row = dict(self.base_row)
        bad_row['Age Group'] = 9       # Max allowed is 6
        bad_row['Overall Satisfaction'] = 0  # Min allowed is 1

        synthetic_df = pd.DataFrame([bad_row])
        result = audit_survey_dataframe(synthetic_df)
        rv = result['range_violations']

        self.assertIn('Age Group', rv)
        self.assertEqual(rv['Age Group']['invalid_count'], 1)
        self.assertIn('Overall Satisfaction', rv)
        self.assertEqual(rv['Overall Satisfaction']['invalid_count'], 1)

    def test_logical_conflicts_detection(self):
        """
        Verifies detection of mutually exclusive answer conflicts:
        - Aware None == 1 while Aware Blinkit == 1
        - Used Never Used == 1 while Used Blinkit == 1
        - Problem No Major Problem == 1 while Problem Late Delivery == 1
        """
        conflict_row = dict(self.base_row)
        conflict_row['Aware None'] = 1
        conflict_row['Aware Blinkit'] = 1  # Conflict!
        conflict_row['Used Never Used'] = 1
        conflict_row['Used Blinkit'] = 1   # Conflict!
        conflict_row[' Problem No Major Problem'] = 1
        conflict_row['Problem Late Delivery'] = 1  # Conflict!

        synthetic_df = pd.DataFrame([conflict_row])
        result = audit_survey_dataframe(synthetic_df)
        lc = result['logical_conflicts']

        self.assertEqual(lc['aware_none_conflict'], 1)
        self.assertEqual(lc['used_never_vs_used_platforms'], 1)
        self.assertEqual(lc['problem_no_major_conflict'], 1)

    def test_usage_status_triangulation_and_previous_users(self):
        """
        Verifies usage-status triangulation across the three distinct subgroups:
        1. Never User: Ever Ordered = 0, Order Frequency = 1
        2. Previous User: Ever Ordered = 1, Order Frequency = 1 (Never)
        3. Current User: Ever Ordered = 1, Order Frequency > 1
        Also verifies tracking of mislabeled satisfaction codes (Code 6).
        """
        # 1. Never user
        never_row = dict(self.base_row)
        never_row['Ever Ordered through a Quick-Commerce Platform'] = 0
        never_row['Used Blinkit'] = 0
        never_row['Used Never Used'] = 1
        never_row['Usage Duration'] = 1
        never_row[' First Trial Reason'] = 8
        never_row[' Order Frequency'] = 1
        never_row['Overall Satisfaction'] = 6
        never_row['Reason Not Applicable Current User'] = 0
        never_row['Reason Prefer Physical'] = 1

        # 2. Previous user (The 80-record scenario)
        prev_row = dict(self.base_row)
        prev_row['Ever Ordered through a Quick-Commerce Platform'] = 1
        prev_row['Used Blinkit'] = 1
        prev_row['Used Never Used'] = 0
        prev_row['Usage Duration'] = 5  # 1-2 years
        prev_row[' First Trial Reason'] = 2  # Faster delivery
        prev_row[' Order Frequency'] = 1     # Current frequency: Never!
        prev_row['Overall Satisfaction'] = 6  # Coded as "never used"!
        prev_row['Reason Not Applicable Current User'] = 0
        prev_row['Reason Delivery Fees'] = 1  # Provided churn reason!

        # 3. Current active user
        current_row = dict(self.base_row)
        current_row['Ever Ordered through a Quick-Commerce Platform'] = 1
        current_row['Used Blinkit'] = 1
        current_row['Used Never Used'] = 0
        current_row['Usage Duration'] = 4
        current_row[' First Trial Reason'] = 4
        current_row[' Order Frequency'] = 5   # 2-3 times/week
        current_row['Overall Satisfaction'] = 4
        current_row['Reason Not Applicable Current User'] = 1

        synthetic_df = pd.DataFrame([never_row, prev_row, current_row])
        result = audit_survey_dataframe(synthetic_df)
        us = result['usage_status_audit']

        self.assertEqual(us['never_users_count'], 1, "Expected exactly 1 never-user")
        self.assertEqual(us['previous_users_count'], 1, "Expected exactly 1 previous-user")
        self.assertEqual(us['current_users_count'], 1, "Expected exactly 1 current-user")
        self.assertEqual(us['inconsistent_never_count'], 0)
        self.assertEqual(us['previous_users_satisfaction_mislabeled_as_never_used']['Overall Satisfaction'], 1)
        self.assertEqual(us['previous_users_reasons_for_not_using']['Reason Delivery Fees'], 1)


if __name__ == '__main__':
    unittest.main()
