#!/usr/bin/env python3
"""
tests/test_audit_data.py

Unit and integration tests for scripts/audit_data.py.
Verifies data schema validation, missing/blank text disaggregation,
rating range validation, platform normalization, inclusive date window boundaries,
duplicate row vs. duplicate text distinctions, and non-zero exit on invalid inputs.

All test fixtures in this file are explicitly synthetic unit-test fixtures.
They are NOT business data and must never be conflated with the actual review corpus.
"""

import os
import sys
import unittest
from datetime import date
import pandas as pd
import numpy as np

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from scripts.audit_data import (
    audit_dataframe,
    validate_date_window,
    resolve_dataset_path,
    compute_file_sha256,
    ESSENTIAL_FIELDS
)


class TestAuditData(unittest.TestCase):
    """Test suite reproducing identified risks and validating audit_data.py behavior."""

    def test_schema_validation_missing_columns(self):
        """Verifies that missing essential columns are caught and report schema failure."""
        incomplete_df = pd.DataFrame({
            'platform': ['blinkit'],
            'review': ['Great delivery'],
            # 'rating' is missing
            'date': ['15 August 2024']
        })
        start_date = date(2024, 8, 14)
        end_date = date(2024, 12, 31)

        result = audit_dataframe(incomplete_df, start_date, end_date)
        self.assertEqual(result['status'], 'FAILED_SCHEMA')
        self.assertIn('rating', result['missing_columns'])

    def test_schema_validation_all_columns_present(self):
        """Verifies that complete schema passes schema check."""
        df = pd.DataFrame({
            'platform': ['blinkit'],
            'review': ['Fast delivery'],
            'rating': [5],
            'date': ['15 August 2024']
        })
        start_date = date(2024, 8, 14)
        end_date = date(2024, 12, 31)

        result = audit_dataframe(df, start_date, end_date)
        self.assertEqual(result['status'], 'SUCCESS')

    def test_nonexistent_explicit_path_fails(self):
        """Verifies that an explicitly supplied nonexistent file path fails non-zero without silent fallback."""
        with self.assertRaises(SystemExit) as cm:
            resolve_dataset_path("nonexistent_candidate_file_xyz_123.csv")
        self.assertEqual(cm.exception.code, 1)

    def test_null_and_blank_text_disaggregation(self):
        """
        Verifies that null text and blank whitespace text are counted separately
        and never double-counted.
        """
        synthetic_df = pd.DataFrame({
            'platform': ['blinkit', 'blinkit', 'blinkit'],
            'review': [
                'Valid review text here',  # valid
                None,                      # missing null
                '   \t  \n  '              # blank whitespace
            ],
            'rating': [5, 4, 3],
            'date': ['15 August 2024', '15 August 2024', '15 August 2024']
        })
        start_date = date(2024, 8, 14)
        end_date = date(2024, 12, 31)

        result = audit_dataframe(synthetic_df, start_date, end_date, min_threshold_per_platform=1)
        fh = result['full_dataset_summary']['field_health']['review']

        self.assertEqual(fh['missing_null'], 1, "Expected exactly 1 missing null text")
        self.assertEqual(fh['blank_whitespace'], 1, "Expected exactly 1 blank whitespace text")
        self.assertEqual(fh['valid'], 1, "Expected exactly 1 valid text")
        self.assertEqual(
            fh['missing_null'] + fh['blank_whitespace'] + fh['valid'],
            len(synthetic_df),
            "Disaggregated text counts must sum exactly to total rows (no double counting)"
        )

    def test_invalid_ratings_and_unknown_platforms(self):
        """
        Verifies that invalid ratings (out of range 1-5, non-integer, non-numeric)
        and unknown/unclassified platforms are correctly identified.
        """
        synthetic_df = pd.DataFrame({
            'platform': [
                'blinkit',        # valid
                'Zepto',          # valid (case-insensitive normalization)
                'JIOMART',        # valid (case-insensitive normalization)
                'amazon_fresh',   # unknown platform
                'blinkit',        # valid platform, but invalid rating below
                'blinkit',        # valid platform, but float rating
                'blinkit',        # valid platform, but non-numeric rating
                'blinkit'         # valid platform, but missing rating
            ],
            'review': ['Good service'] * 8,
            'rating': [
                1,                # valid
                3,                # valid
                5,                # valid
                4,                # valid rating, unknown platform
                0,                # invalid: below 1
                3.5,              # invalid: non-integer float
                'not_a_number',   # invalid: non-numeric string
                None              # missing: null
            ],
            'date': ['20 August 2024'] * 8
        })
        start_date = date(2024, 8, 14)
        end_date = date(2024, 12, 31)

        result = audit_dataframe(synthetic_df, start_date, end_date, min_threshold_per_platform=1)

        # Check platform health
        pf_health = result['full_dataset_summary']['field_health']['platform']
        self.assertEqual(pf_health['unknown_unclassified'], 1)
        self.assertEqual(pf_health['recognized'], 7)

        # Check rating health
        r_health = result['full_dataset_summary']['field_health']['rating']
        self.assertEqual(r_health['valid'], 4, "Ratings 1, 3, 5, 4 should be valid")
        self.assertEqual(r_health['invalid_not_integer_1_to_5'], 3, "Ratings 0, 3.5, 'not_a_number' should be invalid")
        self.assertEqual(r_health['missing_null'], 1, "None rating should be missing null")
        self.assertEqual(
            r_health['valid'] + r_health['invalid_not_integer_1_to_5'] + r_health['missing_null'],
            len(synthetic_df),
            "Rating categories must sum to total records without double counting"
        )

    def test_malformed_and_unparseable_dates(self):
        """Verifies that malformed date strings and null dates are detected without crashing."""
        synthetic_df = pd.DataFrame({
            'platform': ['blinkit', 'blinkit', 'blinkit', 'blinkit'],
            'review': ['Review 1', 'Review 2', 'Review 3', 'Review 4'],
            'rating': [4, 4, 4, 4],
            'date': [
                '15 August 2024',       # valid text format
                '2024-09-01',           # valid ISO format
                '99-99-9999-invalid',   # unparseable string
                None                    # missing null
            ]
        })
        start_date = date(2024, 8, 14)
        end_date = date(2024, 12, 31)

        result = audit_dataframe(synthetic_df, start_date, end_date, min_threshold_per_platform=1)
        d_health = result['full_dataset_summary']['field_health']['date']

        self.assertEqual(d_health['valid'], 2)
        self.assertEqual(d_health['unparseable'], 1)
        self.assertEqual(d_health['missing_null'], 1)
        self.assertEqual(
            d_health['valid'] + d_health['unparseable'] + d_health['missing_null'],
            len(synthetic_df)
        )

    def test_window_boundary_behavior(self):
        """
        Verifies inclusive date window boundary behavior:
        - Exactly before start: excluded as out-of-window
        - Exactly on start date: included as in-window
        - Inside window: included as in-window
        - Exactly on end date: included as in-window
        - Exactly after end date: excluded as out-of-window
        """
        synthetic_df = pd.DataFrame({
            'platform': ['blinkit'] * 5,
            'review': ['Review ' + str(i) for i in range(5)],
            'rating': [5] * 5,
            'date': [
                '13 August 2024',   # Day before window (should be excluded)
                '14 August 2024',   # On window start boundary (must be included)
                '15 October 2024',  # In middle of window (must be included)
                '31 December 2024', # On window end boundary (must be included)
                '01 January 2025'   # Day after window (should be excluded)
            ]
        })
        start_date = date(2024, 8, 14)
        end_date = date(2024, 12, 31)

        result = audit_dataframe(synthetic_df, start_date, end_date, min_threshold_per_platform=1)
        win = result['common_window_summary']

        self.assertEqual(win['total_window_source_rows'], 3, "Rows on 14 Aug, 15 Oct, and 31 Dec must be in window")
        self.assertEqual(win['total_out_of_window_exclusions'], 2, "Rows on 13 Aug and 01 Jan must be excluded")
        self.assertEqual(win['total_usable_rows'], 3)

        b_metric = win['platform_metrics']['blinkit']
        self.assertEqual(b_metric['min_date'], '2024-08-14')
        self.assertEqual(b_metric['max_date'], '2024-12-31')
        self.assertEqual(b_metric['out_of_window_exclusions'], 2)

    def test_duplicate_rows_vs_duplicate_review_text(self):
        """
        Verifies separate reporting of exact duplicate rows (all columns identical)
        versus duplicate review text (same text, different dates or ratings).
        """
        synthetic_df = pd.DataFrame({
            'platform': ['blinkit', 'blinkit', 'blinkit', 'blinkit'],
            'review': [
                'Delivery was super fast',  # Original review A
                'Delivery was super fast',  # Exact duplicate row of A
                'Delivery was super fast',  # Same text as A, but different rating/date
                'Different unique review'   # Distinct review B
            ],
            'rating': [5, 5, 1, 4],
            'date': ['15 August 2024', '15 August 2024', '20 August 2024', '25 August 2024']
        })
        start_date = date(2024, 8, 14)
        end_date = date(2024, 12, 31)

        result = audit_dataframe(synthetic_df, start_date, end_date, min_threshold_per_platform=1)
        full = result['full_dataset_summary']

        self.assertEqual(full['exact_duplicate_rows'], 1, "Only row index 1 is an exact duplicate row of row 0")
        self.assertEqual(full['duplicate_review_texts'], 2, "Row indices 1 and 2 repeat review text of row 0")

    def test_synthetic_fixture_counts_and_proportions(self):
        """
        Verifies counts and proportions using a tiny, explicitly synthetic 10-row unit-test fixture.
        Demonstrates that rating distributions and threshold evaluations calculate correctly.
        """
        synthetic_df = pd.DataFrame({
            'platform': ['blinkit', 'blinkit', 'blinkit', 'blinkit', 'blinkit',
                         'zepto', 'zepto', 'zepto', 'zepto', 'zepto'],
            'review': ['Review ' + str(i) for i in range(10)],
            'rating': [1, 1, 2, 4, 5, 1, 1, 1, 3, 5],
            'date': ['20 August 2024'] * 10
        })
        start_date = date(2024, 8, 14)
        end_date = date(2024, 12, 31)

        result = audit_dataframe(synthetic_df, start_date, end_date, min_threshold_per_platform=5)
        eval_sec = result['feasibility_evaluation']

        self.assertEqual(eval_sec['blinkit_usable_count'], 5)
        self.assertTrue(eval_sec['blinkit_meets_threshold'])
        self.assertEqual(eval_sec['zepto_usable_count'], 5)
        self.assertTrue(eval_sec['zepto_meets_threshold'])

        # Check Blinkit rating distribution: two 1s (40.0%), one 2 (20.0%), one 4 (20.0%), one 5 (20.0%)
        b_dist = result['common_window_summary']['platform_metrics']['blinkit']
        self.assertEqual(b_dist['rating_distribution_counts']['1'], 2)
        self.assertEqual(b_dist['rating_distribution_percentages']['1'], '40.0%')
        self.assertAlmostEqual(b_dist['mean_rating'], 2.60, places=2)

    def test_invalid_and_inverted_date_windows(self):
        """Verifies that inverted date windows and malformed window strings produce SystemExit(1)."""
        # Inverted window (start > end)
        with self.assertRaises(SystemExit) as cm:
            validate_date_window("2024-12-31", "2024-08-14")
        self.assertEqual(cm.exception.code, 1)

        # Malformed start date
        with self.assertRaises(SystemExit) as cm:
            validate_date_window("not-a-date", "2024-12-31")
        self.assertEqual(cm.exception.code, 1)

        # Malformed end date
        with self.assertRaises(SystemExit) as cm:
            validate_date_window("2024-08-14", "31-12-2024")
        self.assertEqual(cm.exception.code, 1)


if __name__ == '__main__':
    unittest.main()
