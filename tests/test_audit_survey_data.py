#!/usr/bin/env python3
"""
tests/test_audit_survey_data.py

Unit and integration tests for scripts/audit_survey_data.py.
Verifies survey schema validation, full 130-column manifest checking, dimension checks,
mandatory columns, duplicate normalized headers, sheet parameter pass-through,
binary indicator constraints, codebook range validation, handling of null cells vs
explicit not-applicable codes, subgroup derivation (never-users, previous-users, current-users),
QA46 universal availability, QA47 current-user exclusivity with negative routing tests,
QA16-QA45 skip-logic negative tests against codebook rules, QA49 improvement coverage,
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
    EXPECTED_COLUMN_MANIFEST_130,
    EXPECTED_ROWS,
    EXPECTED_COLS
)


class TestAuditSurveyData(unittest.TestCase):
    """Test suite validating survey data audit behavior on synthetic fixtures."""

    def setUp(self):
        """Builds a minimal synthetic baseline dictionary adhering strictly to the 130-column survey schema."""
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
            ' First Trial Reason': 2,  # Header with leading space (tested for whitespace detection)
            ' Order Frequency': 4,     # Header with leading space (active current user)
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
        synthetic_df = synthetic_df.drop(columns=['Overall Satisfaction', 'Continue If Discounts Reduced'])
        result = audit_survey_dataframe(synthetic_df, enforce_dimensions=False, enforce_full_manifest=False)

        self.assertEqual(result['status'], 'FAILED')
        self.assertIn('Overall Satisfaction', result['missing_mandatory_columns'])
        self.assertIn('Continue If Discounts Reduced', result['missing_mandatory_columns'])
        self.assertTrue(any("Missing mandatory required columns" in err for err in result['blocking_errors']))

    def test_duplicate_headers_after_normalization_triggers_failure(self):
        """Verifies that duplicate column headers after whitespace trimming are caught as blocking error."""
        df = pd.DataFrame([[1, 2]], columns=['Age Group', ' Age Group '])
        result = audit_survey_dataframe(df, enforce_dimensions=False, enforce_full_manifest=False)

        self.assertEqual(result['status'], 'FAILED')
        self.assertIn('Age Group', result['duplicate_normalized_headers'])
        self.assertTrue(any("Duplicate column headers after normalization" in err for err in result['blocking_errors']))

    def test_whitespace_header_detection(self):
        """Verifies that columns with leading or trailing whitespaces are flagged in warnings."""
        synthetic_df = pd.DataFrame([self.base_row])
        result = audit_survey_dataframe(synthetic_df, enforce_dimensions=False, enforce_full_manifest=False)
        ws_cols = result['whitespace_column_names']

        self.assertIn(' First Trial Reason', ws_cols)
        self.assertIn(' Order Frequency', ws_cols)
        self.assertIn('Fast Delivery Importance ', ws_cols)

    def test_schema_manifest_unexpected_column_replacement(self):
        """
        Regression test: Verifies that removing an expected non-mandatory column and
        replacing it with an unrelated column (keeping total columns at 130) fails the audit.
        """
        # Create a dictionary with all 130 manifest columns
        full_row = {c: 1 for c in EXPECTED_COLUMN_MANIFEST_130}
        # Replace non-mandatory column 'Aware Other' with 'Unrelated_Replacement_Col'
        del full_row['Aware Other']
        full_row['Unrelated_Replacement_Col'] = 99

        df = pd.DataFrame([full_row])
        self.assertEqual(len(df.columns), 130, "Total column count must remain exactly 130")

        result = audit_survey_dataframe(df, enforce_dimensions=False, enforce_full_manifest=True)
        self.assertEqual(result['status'], 'FAILED')
        manifest_res = result['schema_manifest_validation']
        self.assertIn('Aware Other', manifest_res['missing_manifest_columns'])
        self.assertIn('Unrelated_Replacement_Col', manifest_res['unexpected_extra_columns'])
        self.assertTrue(any("Full schema manifest failed" in err for err in result['blocking_errors']))

    def test_physical_null_cells_vs_explicit_na_codes(self):
        """
        Verifies distinction between physical blank/null cells (which fail the audit)
        and legitimate skip/not-applicable codes (e.g. Code 6 in satisfaction or QA47).
        """
        na_code_row = dict(self.base_row)
        na_code_row['Overall Satisfaction'] = 6
        na_code_row['Continue If Discounts Reduced'] = 6
        df_na = pd.DataFrame([na_code_row])
        res_na = audit_survey_dataframe(df_na, enforce_dimensions=False, enforce_full_manifest=False)
        self.assertEqual(res_na['total_null_cells'], 0)
        self.assertEqual(res_na['completeness_and_missingness']['physical_blank_cells'], 0)

        null_row = dict(self.base_row)
        null_row['Overall Satisfaction'] = np.nan
        df_null = pd.DataFrame([null_row])
        res_null = audit_survey_dataframe(df_null, enforce_dimensions=False, enforce_full_manifest=False)
        self.assertEqual(res_null['total_null_cells'], 1)
        self.assertEqual(res_null['status'], 'FAILED')

    def test_binary_indicator_violations(self):
        """Verifies that multi-select dummy indicator variables flag non-binary values."""
        bad_row = dict(self.base_row)
        bad_row['Used Blinkit'] = 2  # Invalid dummy code
        bad_row['Aware Zepto'] = -1  # Invalid dummy code

        synthetic_df = pd.DataFrame([bad_row])
        result = audit_survey_dataframe(synthetic_df, enforce_dimensions=False, enforce_full_manifest=False)
        violations = result['binary_column_violations']

        self.assertIn('Used Blinkit', violations)
        self.assertIn(2, violations['Used Blinkit']['invalid_values'])
        self.assertEqual(result['status'], 'FAILED')

    def test_range_violations_on_single_select(self):
        """Verifies that single-select questions flag codes outside the codebook range or non-integers."""
        bad_row = dict(self.base_row)
        bad_row['Age Group'] = 9           # Max allowed is 6
        bad_row['Overall Satisfaction'] = 0  # Min allowed is 1
        bad_row[' Order Frequency'] = 2.5   # Non-integer float

        synthetic_df = pd.DataFrame([bad_row])
        result = audit_survey_dataframe(synthetic_df, enforce_dimensions=False, enforce_full_manifest=False)
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
        result = audit_survey_dataframe(synthetic_df, enforce_dimensions=False, enforce_full_manifest=False)
        lc = result['logical_conflicts']

        self.assertEqual(lc['aware_none_conflict'], 1)
        self.assertEqual(lc['used_never_vs_used_platforms'], 1)
        self.assertEqual(lc['problem_no_major_conflict'], 1)
        self.assertEqual(result['status'], 'FAILED')

    def test_subgroups_and_qa46_qa47_positive_routing(self):
        """
        Positive test: Verifies correct usage-status derivation and routing across the 3 subgroups:
        1. Never User (Ever=0, Freq=1): QA46 substantive, QA47=6 (N/A), QA48 available
        2. Previous User (Ever=1, Freq=1): QA46 substantive, QA47=6 (N/A), QA48 available, QA37-40=6
        3. Current Active User (Ever=1, Freq>1): QA46 substantive, QA47 substantive (1-5), QA48 flag=1
        """
        never_row = dict(self.base_row)
        never_row['Ever Ordered through a Quick-Commerce Platform'] = 0
        never_row['Used Blinkit'] = 0
        never_row['Used Never Used'] = 1
        never_row['Usage Duration'] = 1
        never_row[' First Trial Reason'] = 8
        never_row[' Order Frequency'] = 1     # Current frequency: Never
        never_row['Common Days'] = 5
        never_row['Common Time'] = 7
        never_row['Reason Not Applicable'] = 1
        never_row['Reason Forgotten Item'] = 0
        never_row['Reason Urgent Need'] = 0
        never_row['Items per Order'] = 7
        never_row['Expected Delivery'] = 7
        never_row['Spontaneous Frequency'] = 6
        never_row['Category Not Applicable'] = 1
        never_row['Category Fresh Fruit Veg'] = 0
        never_row['Category Milk Dairy'] = 0
        never_row['Most Frequent Category'] = 8
        never_row['Order Spend'] = 8
        never_row['Monthly Spend'] = 1
        never_row['Total Spending Change'] = 6
        never_row['Discount Overspend'] = 6
        never_row['Threshold Extra Items'] = 6
        never_row['Payment Method'] = 7
        never_row['Factor Delivery Speed'] = 0
        never_row['Factor Product Availability'] = 0
        never_row['Most Important Factor'] = 9
        never_row['Compare Platform Prices'] = 6
        never_row['Compare Physical Prices'] = 6
        never_row['Fast Delivery Importance '] = 6
        never_row[' Problem No Major Problem'] = 0
        never_row['Problem Not Applicable'] = 1
        never_row['Overall Satisfaction'] = 6
        never_row['Product Quality Satisfaction'] = 6
        never_row['Delivery Reliability Satisfaction'] = 6
        never_row['Value Money Satisfaction'] = 6
        never_row['Kirana Visit Change'] = 7
        never_row['Supermarket Visit Change'] = 7
        never_row['Shopping Routine Role'] = 6
        never_row['Unplanned Purchase'] = 6
        never_row['New Brand Trial'] = 6
        never_row['Next 3 Month Use'] = 2     # QA46 substantive intention
        never_row['Continue If Discounts Reduced'] = 6  # QA47 explicit N/A
        never_row['Reason Not Applicable Current User'] = 0
        never_row['Reason Prefer Physical'] = 1
        never_row['Improvement'] = 1

        prev_row = dict(never_row)
        prev_row['Ever Ordered through a Quick-Commerce Platform'] = 1
        prev_row['Used Blinkit'] = 1
        prev_row['Used Never Used'] = 0
        prev_row['Usage Duration'] = 5
        prev_row[' First Trial Reason'] = 2
        prev_row['Next 3 Month Use'] = 3
        prev_row['Reason Delivery Fees'] = 1
        prev_row['Improvement'] = 4

        current_row = dict(self.base_row)
        current_row['Ever Ordered through a Quick-Commerce Platform'] = 1
        current_row['Used Blinkit'] = 1
        current_row['Used Never Used'] = 0
        current_row['Usage Duration'] = 4
        current_row[' First Trial Reason'] = 4
        current_row[' Order Frequency'] = 5   # Current frequency: Active
        current_row['Overall Satisfaction'] = 4
        current_row['Next 3 Month Use'] = 5   # QA46 substantive intention
        current_row['Continue If Discounts Reduced'] = 4  # QA47 substantive continuation
        current_row['Reason Not Applicable Current User'] = 1
        current_row['Improvement'] = 2

        synthetic_df = pd.DataFrame([never_row, prev_row, current_row])
        result = audit_survey_dataframe(synthetic_df, enforce_dimensions=False, enforce_full_manifest=False)
        us = result['usage_status_audit']
        rt = result['questionnaire_routing']

        self.assertEqual(us['never_users_count'], 1)
        self.assertEqual(us['previous_users_count'], 1)
        self.assertEqual(us['current_users_count'], 1)
        self.assertEqual(rt['qa46_future_use_intention']['substantive_total_1_to_5'], 3)
        self.assertEqual(rt['qa47_discount_continuation']['current_users_substantive_1_to_5'], 1)
        self.assertEqual(rt['qa47_discount_continuation']['non_current_users_with_code_6'], 2)
        self.assertEqual(rt['non_current_respondents_count'], 2)
        self.assertEqual(rt['substantive_non_use_or_zero_spend_variables']['qa26_monthly_spend_zero_code_1_count'], 2)
        self.assertEqual(rt['substantive_non_use_or_zero_spend_variables']['qa43_shopping_routine_non_use_code_6_count'], 2)
        self.assertFalse(rt['physical_store_preferences_qa24']['has_source_na_code'])
        self.assertEqual(len(rt['qa16_to_qa45_routing_violations']), 0)
        self.assertEqual(len(rt['qa16_to_qa45_skip_violations']), 0)
        self.assertEqual(result['status'], 'SUCCESS_WITH_WARNINGS')

    def test_qa47_routing_violations_fail_audit(self):
        """
        Negative tests for QA47 (Continue If Discounts Reduced):
        - Current active user with Code 6 fails validation.
        - Non-current user with substantive value (1-5) fails validation.
        - Ambiguous usage status (Ever=0, Freq>1) fails validation.
        """
        # Case A: Current active user with Code 6
        bad_curr = dict(self.base_row)
        bad_curr['Continue If Discounts Reduced'] = 6  # VIOLATION: Current user cannot have Code 6
        df_a = pd.DataFrame([bad_curr])
        res_a = audit_survey_dataframe(df_a, enforce_dimensions=False, enforce_full_manifest=False)
        self.assertEqual(res_a['status'], 'FAILED')
        self.assertTrue(any("QA47 Routing Violation" in err for err in res_a['blocking_errors']))
        self.assertEqual(res_a['questionnaire_routing']['qa47_discount_continuation']['current_users_with_code_6_violation'], 1)

        # Case B: Non-current user with substantive Likert response (e.g. 4)
        bad_non_curr = dict(self.base_row)
        bad_non_curr[' Order Frequency'] = 1
        bad_non_curr['Continue If Discounts Reduced'] = 4  # VIOLATION: Non-current user must be Code 6
        df_b = pd.DataFrame([bad_non_curr])
        res_b = audit_survey_dataframe(df_b, enforce_dimensions=False, enforce_full_manifest=False)
        self.assertEqual(res_b['status'], 'FAILED')
        self.assertTrue(any("QA47 Routing Violation" in err for err in res_b['blocking_errors']))
        self.assertEqual(res_b['questionnaire_routing']['qa47_discount_continuation']['non_current_users_substantive_violation'], 1)

        # Case C: Ambiguous usage status (Ever=0 but Order Frequency=4)
        ambiguous_row = dict(self.base_row)
        ambiguous_row['Ever Ordered through a Quick-Commerce Platform'] = 0
        ambiguous_row[' Order Frequency'] = 4  # INCONSISTENCY: Never ordered but orders 4 times/week!
        df_c = pd.DataFrame([ambiguous_row])
        res_c = audit_survey_dataframe(df_c, enforce_dimensions=False, enforce_full_manifest=False)
        self.assertEqual(res_c['status'], 'FAILED')
        self.assertTrue(any("Inconsistent respondents" in err for err in res_c['blocking_errors']))

    def test_qa16_to_qa45_skip_logic_negative_violations(self):
        """
        Negative tests for QA16-QA45 skip logic:
        - Non-current respondent with substantive satisfaction score (e.g. 4 instead of 6) fails.
        - Non-current respondent with substantive category indicator (instead of Category Not Applicable=1) fails.
        - Non-current respondent with substantive problem indicator (instead of Problem Not Applicable=1) fails.
        - Current user with Reason Not Applicable Current User != 1 fails.
        """
        # Baseline non-current row
        non_curr = dict(self.base_row)
        non_curr[' Order Frequency'] = 1
        non_curr['Common Days'] = 5
        non_curr['Common Time'] = 7
        non_curr['Reason Not Applicable'] = 1
        non_curr['Reason Forgotten Item'] = 0
        non_curr['Reason Urgent Need'] = 0
        non_curr['Items per Order'] = 7
        non_curr['Expected Delivery'] = 7
        non_curr['Spontaneous Frequency'] = 6
        non_curr['Category Not Applicable'] = 1
        non_curr['Category Fresh Fruit Veg'] = 0
        non_curr['Category Milk Dairy'] = 0
        non_curr['Most Frequent Category'] = 8
        non_curr['Order Spend'] = 8
        non_curr['Monthly Spend'] = 1
        non_curr['Total Spending Change'] = 6
        non_curr['Discount Overspend'] = 6
        non_curr['Threshold Extra Items'] = 6
        non_curr['Payment Method'] = 7
        non_curr['Factor Delivery Speed'] = 0
        non_curr['Factor Product Availability'] = 0
        non_curr['Most Important Factor'] = 9
        non_curr['Compare Platform Prices'] = 6
        non_curr['Compare Physical Prices'] = 6
        non_curr['Fast Delivery Importance '] = 6
        non_curr[' Problem No Major Problem'] = 0
        non_curr['Problem Not Applicable'] = 1
        non_curr['Overall Satisfaction'] = 6
        non_curr['Product Quality Satisfaction'] = 6
        non_curr['Delivery Reliability Satisfaction'] = 6
        non_curr['Value Money Satisfaction'] = 6
        non_curr['Kirana Visit Change'] = 7
        non_curr['Supermarket Visit Change'] = 7
        non_curr['Shopping Routine Role'] = 6
        non_curr['Unplanned Purchase'] = 6
        non_curr['New Brand Trial'] = 6
        non_curr['Continue If Discounts Reduced'] = 6
        non_curr['Reason Not Applicable Current User'] = 0

        # Sub-test 1: Non-current user with substantive satisfaction (4 instead of 6)
        viol_sat = dict(non_curr)
        viol_sat['Overall Satisfaction'] = 4  # VIOLATION: Non-current must be 6
        res_sat = audit_survey_dataframe(pd.DataFrame([viol_sat]), enforce_dimensions=False, enforce_full_manifest=False)
        self.assertEqual(res_sat['status'], 'FAILED')
        self.assertTrue(any("QA16-45 Routing Violation in 'Overall Satisfaction'" in err for err in res_sat['blocking_errors']))

        # Sub-test 2: Non-current user with substantive category marked (Fresh Fruit Veg = 1)
        viol_cat = dict(non_curr)
        viol_cat['Category Fresh Fruit Veg'] = 1  # VIOLATION: Non-current cannot purchase categories
        res_cat = audit_survey_dataframe(pd.DataFrame([viol_cat]), enforce_dimensions=False, enforce_full_manifest=False)
        self.assertEqual(res_cat['status'], 'FAILED')
        self.assertTrue(any("QA22 Routing Violation" in err for err in res_cat['blocking_errors']))

        # Sub-test 3: Non-current user with substantive problem marked (Problem Out of Stock = 1)
        viol_prob = dict(non_curr)
        viol_prob['Problem Out of Stock'] = 1  # VIOLATION: Non-current cannot experience service problems
        res_prob = audit_survey_dataframe(pd.DataFrame([viol_prob]), enforce_dimensions=False, enforce_full_manifest=False)
        self.assertEqual(res_prob['status'], 'FAILED')
        self.assertTrue(any("QA36 Routing Violation" in err for err in res_prob['blocking_errors']))

        # Sub-test 4: Current active user with Reason Not Applicable Current User == 0
        viol_curr_flag = dict(self.base_row)
        viol_curr_flag['Reason Not Applicable Current User'] = 0  # VIOLATION: Current user must have flag=1
        res_curr_flag = audit_survey_dataframe(pd.DataFrame([viol_curr_flag]), enforce_dimensions=False, enforce_full_manifest=False)
        self.assertEqual(res_curr_flag['status'], 'FAILED')
        self.assertTrue(any("QA48 Routing Violation" in err for err in res_curr_flag['blocking_errors']))

        # Sub-test 5: Non-current user reporting positive monthly spend (e.g. 3 instead of 1 [₹0])
        viol_spend = dict(non_curr)
        viol_spend['Monthly Spend'] = 3  # VIOLATION: Non-current must report ₹0 monthly spend (Code 1)
        res_spend = audit_survey_dataframe(pd.DataFrame([viol_spend]), enforce_dimensions=False, enforce_full_manifest=False)
        self.assertEqual(res_spend['status'], 'FAILED')
        self.assertTrue(any("QA26 Routing Violation" in err for err in res_spend['blocking_errors']))

        # Sub-test 6: Non-current user reporting active shopping routine role (e.g. 2 instead of 6 ['I do not use quick commerce'])
        viol_routine = dict(non_curr)
        viol_routine['Shopping Routine Role'] = 2  # VIOLATION: Non-current must report Code 6
        res_routine = audit_survey_dataframe(pd.DataFrame([viol_routine]), enforce_dimensions=False, enforce_full_manifest=False)
        self.assertEqual(res_routine['status'], 'FAILED')
        self.assertTrue(any("QA43 Routing Violation" in err for err in res_routine['blocking_errors']))

    def test_qa46_and_qa49_universal_coverage_validation(self):
        """
        Verifies that QA46 (stated future intention, 1-5) and QA49 (improvement, 1-10)
        enforce valid substantive codebook values across all respondents, and fail on invalid codes.
        """
        # Baseline valid row
        valid_df = pd.DataFrame([self.base_row])
        res_valid = audit_survey_dataframe(valid_df, enforce_dimensions=False, enforce_full_manifest=False)
        self.assertNotIn('QA46 Coverage Violation', str(res_valid['blocking_errors']))
        self.assertNotIn('QA49 Coverage Violation', str(res_valid['blocking_errors']))

        # Negative test for QA46: Out-of-bounds code (e.g. 6 or 0)
        bad_qa46 = dict(self.base_row)
        bad_qa46['Next 3 Month Use'] = 6  # Codebook allows 1-5; 6 is invalid
        res_qa46 = audit_survey_dataframe(pd.DataFrame([bad_qa46]), enforce_dimensions=False, enforce_full_manifest=False)
        self.assertEqual(res_qa46['status'], 'FAILED')
        self.assertTrue(any("QA46 Coverage Violation" in err for err in res_qa46['blocking_errors']))

        # Negative test for QA49: Out-of-bounds code (e.g. 11 or 0)
        bad_qa49 = dict(self.base_row)
        bad_qa49['Improvement'] = 11  # Codebook allows 1-10; 11 is invalid
        res_qa49 = audit_survey_dataframe(pd.DataFrame([bad_qa49]), enforce_dimensions=False, enforce_full_manifest=False)
        self.assertEqual(res_qa49['status'], 'FAILED')
        self.assertTrue(any("QA49 Coverage Violation" in err for err in res_qa49['blocking_errors']))

    def test_functional_sheet_argument(self):
        """Verifies that the --sheet argument is properly passed through to read_excel."""
        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
            tmp_path = tmp.name

        try:
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
