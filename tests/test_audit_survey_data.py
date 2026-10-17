#!/usr/bin/env python3
"""
tests/test_audit_survey_data.py

Unit and integration tests for scripts/audit_survey_data.py.
Verifies survey schema validation, dimension checks, mandatory columns,
duplicate normalized headers, sheet parameter pass-through, binary indicator constraints,
codebook range validation, handling of null cells vs explicit not-applicable codes,
subgroup derivation (never-users, previous-users, current-users),
QA46 universal availability, QA47 current-user exclusivity, QA48/QA49 non-current availability,
and error exit codes on audit failure.

CRITICAL NOTICE:
All test fixtures in this file are EXPLICITLY SYNTHETIC unit-test fixtures.
They are NOT business survey data and must NEVER be conflated with real survey records.
"""

import os
import sys
import unittest
import tempfile
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
    run_survey_audit,
    SINGLE_SELECT_RANGES,
    MANDATORY_COLUMNS,
    EXPECTED_ROWS,
    EXPECTED_COLS
)


class TestAuditSurveyData(unittest.TestCase):
    """Test suite validating survey data audit behavior on synthetic fixtures."""

    def setUp(self):
        """Builds a minimal synthetic baseline dictionary adhering to survey schema."""
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

    def test_missing_mandatory_columns_triggers_failure(self):
        """Verifies that dropping a mandatory column reports blocking error and sets status FAILED."""
        synthetic_df = pd.DataFrame([self.base_row])
        # Drop mandatory columns
        synthetic_df = synthetic_df.drop(columns=['Overall Satisfaction', 'Continue If Discounts Reduced'])
        result = audit_survey_dataframe(synthetic_df, enforce_dimensions=False)

        self.assertEqual(result['status'], 'FAILED')
        self.assertIn('Overall Satisfaction', result['missing_mandatory_columns'])
        self.assertIn('Continue If Discounts Reduced', result['missing_mandatory_columns'])
        self.assertTrue(any("Missing mandatory required columns" in err for err in result['blocking_errors']))

    def test_duplicate_headers_after_normalization_triggers_failure(self):
        """Verifies that duplicate column headers after whitespace trimming are caught as blocking error."""
        # Create a DataFrame with two columns that become identical after strip()
        df = pd.DataFrame([[1, 2]], columns=['Age Group', ' Age Group '])
        result = audit_survey_dataframe(df, enforce_dimensions=False)

        self.assertEqual(result['status'], 'FAILED')
        self.assertIn('Age Group', result['duplicate_normalized_headers'])
        self.assertTrue(any("Duplicate column headers after normalization" in err for err in result['blocking_errors']))

    def test_whitespace_header_detection(self):
        """Verifies that columns with leading or trailing whitespaces are flagged."""
        synthetic_df = pd.DataFrame([self.base_row])
        result = audit_survey_dataframe(synthetic_df, enforce_dimensions=False)
        ws_cols = result['whitespace_column_names']

        self.assertIn(' First Trial Reason', ws_cols)
        self.assertIn(' Order Frequency', ws_cols)
        self.assertIn('Fast Delivery Importance ', ws_cols)

    def test_physical_null_cells_vs_explicit_na_codes(self):
        """
        Verifies distinction between physical blank/null cells (which fail the audit)
        and legitimate skip/not-applicable codes (e.g. Code 6 in satisfaction or QA47).
        """
        # Baseline with explicit N/A codes (Code 6) should not count as physical nulls
        na_code_row = dict(self.base_row)
        na_code_row['Overall Satisfaction'] = 6
        na_code_row['Continue If Discounts Reduced'] = 6
        df_na = pd.DataFrame([na_code_row])
        res_na = audit_survey_dataframe(df_na, enforce_dimensions=False)
        self.assertEqual(res_na['total_null_cells'], 0)
        self.assertEqual(res_na['completeness_and_missingness']['physical_blank_cells'], 0)

        # Baseline with actual NaN/null should trigger physical null count and FAILED status
        null_row = dict(self.base_row)
        null_row['Overall Satisfaction'] = np.nan
        df_null = pd.DataFrame([null_row])
        res_null = audit_survey_dataframe(df_null, enforce_dimensions=False)
        self.assertEqual(res_null['total_null_cells'], 1)
        self.assertEqual(res_null['status'], 'FAILED')

    def test_binary_indicator_violations(self):
        """Verifies that multi-select dummy indicator variables flag non-binary values."""
        bad_row = dict(self.base_row)
        bad_row['Used Blinkit'] = 2  # Invalid dummy code
        bad_row['Aware Zepto'] = -1  # Invalid dummy code

        synthetic_df = pd.DataFrame([bad_row])
        result = audit_survey_dataframe(synthetic_df, enforce_dimensions=False)
        violations = result['binary_column_violations']

        self.assertIn('Used Blinkit', violations)
        self.assertIn(2, violations['Used Blinkit']['invalid_values'])
        self.assertEqual(result['status'], 'FAILED')

    def test_range_violations_on_single_select(self):
        """Verifies that single-select questions flag codes outside the codebook range or non-integers."""
        bad_row = dict(self.base_row)
        bad_row['Age Group'] = 9       # Max allowed is 6
        bad_row['Overall Satisfaction'] = 0  # Min allowed is 1
        bad_row[' Order Frequency'] = 2.5     # Non-integer float (updates existing key)

        synthetic_df = pd.DataFrame([bad_row])
        result = audit_survey_dataframe(synthetic_df, enforce_dimensions=False)
        rv = result['range_violations']

        self.assertIn('Age Group', rv)
        self.assertEqual(rv['Age Group']['invalid_count'], 1)
        self.assertIn('Overall Satisfaction', rv)
        self.assertEqual(rv['Overall Satisfaction']['invalid_count'], 1)
        self.assertEqual(result['status'], 'FAILED')

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
        result = audit_survey_dataframe(synthetic_df, enforce_dimensions=False)
        lc = result['logical_conflicts']

        self.assertEqual(lc['aware_none_conflict'], 1)
        self.assertEqual(lc['used_never_vs_used_platforms'], 1)
        self.assertEqual(lc['problem_no_major_conflict'], 1)
        self.assertEqual(result['status'], 'FAILED')

    def test_subgroups_and_qa46_qa47_routing(self):
        """
        Verifies usage-status triangulation and routing logic:
        1. Never User (Ever=0, Freq=1):
           - QA46 is substantive (1-5)
           - QA47 is explicit N/A (Code 6)
           - QA48 reasons for non-use are available
        2. Previous User (Ever=1, Freq=1):
           - QA46 is substantive (1-5)
           - QA47 is explicit N/A (Code 6)
           - QA48 reasons for non-use are available
           - Satisfaction fields (QA37-40) are mislabeled as Code 6
        3. Current Active User (Ever=1, Freq>1):
           - QA46 is substantive (1-5)
           - QA47 is substantive (1-5)
           - QA48 Reason Not Applicable Current User == 1
        """
        # 1. Never user
        never_row = dict(self.base_row)
        never_row['Ever Ordered through a Quick-Commerce Platform'] = 0
        never_row['Used Blinkit'] = 0
        never_row['Used Never Used'] = 1
        never_row['Usage Duration'] = 1
        never_row[' First Trial Reason'] = 8
        never_row[' Order Frequency'] = 1     # Current frequency: Never
        never_row['Overall Satisfaction'] = 6
        never_row['Next 3 Month Use'] = 2     # QA46 substantive intention!
        never_row['Continue If Discounts Reduced'] = 6  # QA47 explicit N/A!
        never_row['Reason Not Applicable Current User'] = 0
        never_row['Reason Prefer Physical'] = 1
        never_row['Improvement'] = 1

        # 2. Previous user (The 80-record scenario)
        prev_row = dict(self.base_row)
        prev_row['Ever Ordered through a Quick-Commerce Platform'] = 1
        prev_row['Used Blinkit'] = 1
        prev_row['Used Never Used'] = 0
        prev_row['Usage Duration'] = 5
        prev_row[' First Trial Reason'] = 2
        prev_row[' Order Frequency'] = 1     # Current frequency: Never
        prev_row['Overall Satisfaction'] = 6  # Mislabeled as never used!
        prev_row['Next 3 Month Use'] = 3     # QA46 substantive intention!
        prev_row['Continue If Discounts Reduced'] = 6  # QA47 explicit N/A!
        prev_row['Reason Not Applicable Current User'] = 0
        prev_row['Reason Delivery Fees'] = 1  # Lapsed user reason!
        prev_row['Improvement'] = 4

        # 3. Current active user
        current_row = dict(self.base_row)
        current_row['Ever Ordered through a Quick-Commerce Platform'] = 1
        current_row['Used Blinkit'] = 1
        current_row['Used Never Used'] = 0
        current_row['Usage Duration'] = 4
        current_row[' First Trial Reason'] = 4
        current_row[' Order Frequency'] = 5   # Current frequency: Active
        current_row['Overall Satisfaction'] = 4
        current_row['Next 3 Month Use'] = 5   # QA46 substantive intention!
        current_row['Continue If Discounts Reduced'] = 4  # QA47 substantive continuation!
        current_row['Reason Not Applicable Current User'] = 1
        current_row['Improvement'] = 2

        synthetic_df = pd.DataFrame([never_row, prev_row, current_row])
        result = audit_survey_dataframe(synthetic_df, enforce_dimensions=False)
        us = result['usage_status_audit']
        rt = result['questionnaire_routing']

        # Subgroup counts
        self.assertEqual(us['never_users_count'], 1)
        self.assertEqual(us['previous_users_count'], 1)
        self.assertEqual(us['current_users_count'], 1)

        # QA46: All 3 have substantive (1-5) responses
        self.assertEqual(rt['qa46_future_use_intention']['substantive_total_1_to_5'], 3)
        self.assertEqual(rt['qa46_future_use_intention']['never_users_substantive'], 1)
        self.assertEqual(rt['qa46_future_use_intention']['previous_users_substantive'], 1)
        self.assertEqual(rt['qa46_future_use_intention']['current_users_substantive'], 1)

        # QA47: Current user has substantive 1-5; non-current users have N/A (Code 6)
        self.assertEqual(rt['qa47_discount_continuation']['current_users_substantive_1_to_5'], 1)
        self.assertEqual(rt['qa47_discount_continuation']['non_current_users_na_code_6'], 2)

        # QA48: Both never-user and previous-user provided substantive non-use reasons
        self.assertEqual(us['previous_users_reasons_for_not_using']['Reason Delivery Fees'], 1)
        self.assertEqual(us['never_users_reasons_for_not_using']['Reason Prefer Physical'], 1)

    def test_functional_sheet_argument(self):
        """Verifies that the --sheet argument is properly passed through to read_excel."""
        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            # Write two distinct sheets
            with pd.ExcelWriter(tmp_path, engine='openpyxl') as writer:
                df1 = pd.DataFrame({'Sheet1_Col': [1, 2]})
                df2 = pd.DataFrame([self.base_row])
                df1.to_excel(writer, sheet_name='Sheet1', index=False)
                df2.to_excel(writer, sheet_name='CustomSurveySheet', index=False)

            # Reading Sheet1 should fail schema checks (missing mandatory columns)
            with self.assertRaises(SystemExit) as cm:
                run_survey_audit(file_path=tmp_path, sheet_name='Sheet1', no_output=True)
            self.assertEqual(cm.exception.code, 1)

            # Reading nonexistent sheet should raise SystemExit(1)
            with self.assertRaises(SystemExit) as cm_none:
                run_survey_audit(file_path=tmp_path, sheet_name='NonExistentSheet', no_output=True)
            self.assertEqual(cm_none.exception.code, 1)
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def test_audit_failure_exit_behavior(self):
        """Verifies that run_survey_audit exits with non-zero code on blocking audit failure."""
        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            # Create a workbook with blocking errors (out of range code)
            bad_row = dict(self.base_row)
            bad_row['Age Group'] = 999
            df = pd.DataFrame([bad_row])
            df.to_excel(tmp_path, sheet_name='Data', index=False)

            with self.assertRaises(SystemExit) as cm:
                run_survey_audit(file_path=tmp_path, sheet_name='Data', no_output=True)
            self.assertEqual(cm.exception.code, 1)
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)


if __name__ == '__main__':
    unittest.main()
