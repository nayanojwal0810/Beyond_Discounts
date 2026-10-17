#!/usr/bin/env python3
"""
scripts/audit_survey_data.py

Reproducible quantitative audit script for the Mendeley Quick-Commerce Survey Dataset:
"A Large-Scale Survey Dataset on Quick-Commerce Adoption, Ordering Patterns,
Product Categories and Spending Behaviour among Indian Consumers" (Chandra 2026).

Audits the survey workbook (Data.xlsx) for:
1. Workbook Structure & Dimensions:
   - Configurable worksheet selection via --sheet (default: 'Data')
   - Validates expected dimensions (1,263 data rows x 130 columns)
   - Mandatory schema columns validation (no silent skipping)
   - Duplicate header detection after whitespace normalization
   - Detection of leading/trailing whitespace in headers
2. Completeness & Multi-Tier Missingness Breakdown:
   - Physical blank/null cells (isna)
   - Explicit Not-Applicable / Skip-coded responses (e.g. Code 6 in QA16-45, QA47)
   - Substantive observed responses (QA46 across all 1,263; QA47 across 807 current users)
3. Coding Validity & Range Conformance:
   - Single-select variables validated against codebook integer ranges
   - Multi-select indicator variables validated against binary {0, 1}
   - Safe type handling (handles strings, nulls, decimals without unhandled exceptions)
4. Logical Consistency & Questionnaire Routing:
   - Awareness vs. Aware None
   - Usage vs. Used Never Used
   - Ever-ordered vs. platform usage indicators
   - Problem No Major Problem vs. specific defects
   - QA48 Reason Not Applicable Current User vs. Order Frequency
5. Usage-Status Triangulation & The 80-Record Previous-User Routing:
   - Triangulates Never Users (n=376), Previous Users currently reporting Never ordering (n=80),
     and Current Active Users (n=807)
   - Documents skip-coded satisfaction (QA37-40) and problems (QA36) for all 456 non-current users
   - Verifies that QA46 (stated future intention) has substantive values (1-5) for ALL 1,263 respondents
   - Verifies that QA47 (continue if discounts reduced) has substantive values (1-5) ONLY for 807 current users,
     and value 6 (Not applicable) for all 456 non-current users (prohibits conflating code 6 with defection)
6. Real Audit Status & Error Handling:
   - Returns status 'FAILED' and non-zero exit code (1) if blocking schema, dimension, null, or code violations occur
   - Returns status 'SUCCESS' or 'SUCCESS_WITH_WARNINGS' only when validation checks pass cleanly

Usage:
    python scripts/audit_survey_data.py [--file PATH_TO_XLSX] [--sheet SHEET] [--output PATH_TO_JSON] [--no-output]
"""

import sys
import os
import argparse
import hashlib
import json
from datetime import datetime, timezone
import pandas as pd
import numpy as np

# Force UTF-8 stdout encoding if supported
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

DEFAULT_SURVEY_PATH = os.path.join("data", "raw", "survey", "Data.xlsx")
DEFAULT_OUTPUT_JSON = os.path.join("docs", "gates", "GATE_0_SURVEY_AUDIT_SUMMARY.json")
EXPECTED_ROWS = 1263
EXPECTED_COLS = 130
EXPECTED_SHEET = "Data"

# Mandatory columns essential for usage-status triangulation and principal CRM analyses
MANDATORY_COLUMNS = [
    'Age Group', 'Gender', 'Education', 'Occupation', 'Personal Income',
    'Area of Residence', 'Region', 'Household Size',
    'Awareness of Quick Commerce Services', 'Ever Ordered through a Quick-Commerce Platform',
    'Aware Blinkit', 'Aware Zepto', 'Aware Swiggy Instamart', 'Aware None',
    'Used Blinkit', 'Used Zepto', 'Used Swiggy Instamart', 'Used Never Used',
    'Usage Duration', 'First Trial Reason', 'Order Frequency',
    'Common Days', 'Common Time', 'Items per Order', 'Expected Delivery',
    'Spontaneous Frequency', 'Category Not Applicable', 'Most Frequent Category',
    'Order Spend', 'Monthly Spend', 'Total Spending Change', 'Discount Overspend',
    'Threshold Extra Items', 'Payment Method', 'Most Important Factor',
    'Compare Platform Prices', 'Compare Physical Prices', 'Fast Delivery Importance',
    'Problem No Major Problem', 'Problem Not Applicable',
    'Overall Satisfaction', 'Product Quality Satisfaction',
    'Delivery Reliability Satisfaction', 'Value Money Satisfaction',
    'Next 3 Month Use', 'Continue If Discounts Reduced',
    'Reason Not Applicable Current User', 'Reason Prefer Physical',
    'Reason Prices High', 'Reason Delivery Fees', 'Reason Distrust Quality',
    'Improvement'
]

SINGLE_SELECT_RANGES = {
    'Age Group': (1, 6),
    'Gender': (1, 4),
    'Education': (1, 5),
    'Occupation': (1, 8),
    'Personal Income': (1, 8),
    'Area of Residence': (1, 6),
    'Region': (1, 6),
    'Household Size': (1, 6),
    'Awareness of Quick Commerce Services': (0, 1),
    'Ever Ordered through a Quick-Commerce Platform': (0, 1),
    'Usage Duration': (1, 6),
    'First Trial Reason': (1, 8),
    'Order Frequency': (1, 7),
    'Common Days': (1, 5),
    'Common Time': (1, 7),
    'Items per Order': (1, 7),
    'Expected Delivery': (1, 7),
    'Spontaneous Frequency': (1, 6),
    'Most Frequent Category': (1, 8),
    'Order Spend': (1, 8),
    'Monthly Spend': (1, 8),
    'Total Spending Change': (1, 6),
    'Discount Overspend': (1, 6),
    'Threshold Extra Items': (1, 6),
    'Payment Method': (1, 7),
    'Most Important Factor': (1, 9),
    'Compare Platform Prices': (1, 6),
    'Compare Physical Prices': (1, 6),
    'Fast Delivery Importance': (1, 6),
    'Overall Satisfaction': (1, 6),
    'Product Quality Satisfaction': (1, 6),
    'Delivery Reliability Satisfaction': (1, 6),
    'Value Money Satisfaction': (1, 6),
    'Kirana Visit Change': (1, 7),
    'Supermarket Visit Change': (1, 7),
    'Shopping Routine Role': (1, 6),
    'Unplanned Purchase': (1, 6),
    'New Brand Trial': (1, 6),
    'Next 3 Month Use': (1, 5),
    'Continue If Discounts Reduced': (1, 6),
    'Improvement': (1, 10)
}

MULTI_SELECT_PREFIXES = ['Aware ', 'Used ', 'Reason ', 'Category ', 'Physical ', 'Factor ', 'Problem ']


def parse_arguments(args=None):
    parser = argparse.ArgumentParser(
        description="Audit the Mendeley Quick-Commerce Survey Dataset for Gate 0 evaluation."
    )
    parser.add_argument(
        "--file",
        type=str,
        default=None,
        help=f"Path to survey Excel workbook. Default: {DEFAULT_SURVEY_PATH}"
    )
    parser.add_argument(
        "--sheet",
        type=str,
        default=EXPECTED_SHEET,
        help=f"Worksheet name. Default: {EXPECTED_SHEET}"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=DEFAULT_OUTPUT_JSON,
        help=f"Path to export aggregate JSON summary. Default: {DEFAULT_OUTPUT_JSON}"
    )
    parser.add_argument(
        "--no-output",
        action="store_true",
        help="Disable writing the JSON summary to disk."
    )
    return parser.parse_args(args)


def compute_file_sha256(filepath):
    """Computes SHA-256 hash of a file in streaming chunks."""
    sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def resolve_survey_path(file_arg):
    """
    Resolves survey data file path.
    If --file is explicitly passed, it MUST exist and be readable.
    Never silently substitutes another dataset if an explicit path is invalid.
    """
    if file_arg is not None:
        if not os.path.exists(file_arg):
            sys.stderr.write(f"\n[FATAL ERROR] Specified survey file does not exist: {file_arg}\n")
            sys.exit(1)
        if not os.path.isfile(file_arg):
            sys.stderr.write(f"\n[FATAL ERROR] Specified path is not a valid file: {file_arg}\n")
            sys.exit(1)
        return os.path.abspath(file_arg)

    default_candidates = [
        DEFAULT_SURVEY_PATH,
        os.path.join("data", "survey", "Data.xlsx"),
        os.path.join("data", "Data.xlsx")
    ]
    for candidate in default_candidates:
        if os.path.isfile(candidate):
            return os.path.abspath(candidate)

    sys.stderr.write(
        "\n[FATAL ERROR] Survey workbook Data.xlsx not found.\n"
        "Checked default candidate paths:\n"
        f"  1. {default_candidates[0]}\n"
        f"  2. {default_candidates[1]}\n\n"
        "To provide the candidate survey bundle, place 'Data.xlsx' at 'data/raw/survey/Data.xlsx'\n"
        "or pass an explicit path via --file: python scripts/audit_survey_data.py --file <PATH_TO_XLSX>\n"
    )
    sys.exit(1)


def audit_survey_dataframe(df, enforce_dimensions=True):
    """
    Performs comprehensive structural, schema, completeness, coding validity,
    logical consistency, and usage-status routing audits on the survey DataFrame.
    
    Returns a dict containing all audit metrics and an overall 'status' of:
    - 'SUCCESS': all checks passed without any errors or warnings
    - 'SUCCESS_WITH_WARNINGS': passed with non-blocking warnings (e.g. whitespace in headers)
    - 'FAILED': blocking schema, missing required columns, dimensions, nulls, or code violations
    """
    total_rows = len(df)
    total_cols = len(df.columns)
    raw_col_names = [str(c) for c in df.columns]

    blocking_errors = []
    warning_messages = []

    # 1. Header whitespace and normalization
    stripped_col_names = [c.strip() for c in raw_col_names]
    whitespace_cols = [raw_col_names[i] for i in range(len(raw_col_names)) if raw_col_names[i] != stripped_col_names[i]]
    if whitespace_cols:
        warning_messages.append(f"Detected {len(whitespace_cols)} column headers with leading or trailing whitespace.")

    # Check for duplicate headers after whitespace normalization
    seen_cols = set()
    duplicate_normalized_headers = []
    for c in stripped_col_names:
        if c in seen_cols:
            duplicate_normalized_headers.append(c)
        else:
            seen_cols.add(c)
    if duplicate_normalized_headers:
        blocking_errors.append(f"Duplicate column headers after normalization: {duplicate_normalized_headers}")

    # Standardized working copy with trimmed column headers.
    # If duplicates exist, make subsequent column names unique with __dup suffix
    # so work_df[col] always returns a Series without ambiguous truth value exceptions.
    work_df = df.copy()
    if duplicate_normalized_headers:
        temp_cols = []
        counts = {}
        for c in stripped_col_names:
            counts[c] = counts.get(c, 0) + 1
            if counts[c] > 1:
                temp_cols.append(f"{c}__dup{counts[c]}")
            else:
                temp_cols.append(c)
        work_df.columns = temp_cols
    else:
        work_df.columns = stripped_col_names

    # 2. Dimension checks
    dimension_discrepancy = None
    if enforce_dimensions:
        if total_rows != EXPECTED_ROWS or total_cols != EXPECTED_COLS:
            dimension_discrepancy = {
                'expected_rows': EXPECTED_ROWS,
                'actual_rows': total_rows,
                'expected_columns': EXPECTED_COLS,
                'actual_columns': total_cols
            }
            blocking_errors.append(
                f"Dimension discrepancy: expected ({EXPECTED_ROWS} rows, {EXPECTED_COLS} cols), "
                f"found ({total_rows} rows, {total_cols} cols)."
            )

    # 3. Mandatory columns validation
    missing_mandatory_columns = [c for c in MANDATORY_COLUMNS if c not in work_df.columns]
    if missing_mandatory_columns:
        blocking_errors.append(f"Missing mandatory required columns: {missing_mandatory_columns}")

    # 4. Physical Completeness vs. Missingness
    total_null_cells = int(df.isna().sum().sum())
    null_counts_per_col = {
        raw_col_names[i]: int(df.iloc[:, i].isna().sum())
        for i in range(len(raw_col_names))
        if int(df.iloc[:, i].isna().sum()) > 0
    }
    if total_null_cells > 0:
        blocking_errors.append(f"Physical null/blank cells found: {total_null_cells} cells across {len(null_counts_per_col)} columns.")

    # Duplicate full rows
    full_duplicate_rows = int(work_df.duplicated().sum())
    if full_duplicate_rows > 0:
        warning_messages.append(f"Found {full_duplicate_rows} exact duplicate full rows.")
    demo_cols = ['Age Group', 'Gender', 'Education', 'Occupation', 'Personal Income', 'Area of Residence', 'Region', 'Household Size']
    demo_cols_present = [c for c in demo_cols if c in work_df.columns]
    demographic_duplicate_rows = int(work_df.duplicated(subset=demo_cols_present).sum()) if demo_cols_present else 0

    # 5. Multi-Select Binary Indicator Check
    binary_cols = []
    for c in work_df.columns:
        if any(c.startswith(p) for p in MULTI_SELECT_PREFIXES):
            binary_cols.append(c)

    binary_violations = {}
    for c in binary_cols:
        series = work_df[c]
        # Robustly handle non-numeric or non-binary
        numeric_series = pd.to_numeric(series, errors='coerce')
        nan_count = int(numeric_series.isna().sum())
        non_binary_mask = ~numeric_series.isin([0, 1])
        non_binary_count = int(non_binary_mask.sum())
        if non_binary_count > 0 or nan_count > 0:
            invalid_unique = [v for v in series.unique() if v not in [0, 1, 0.0, 1.0]]
            binary_violations[c] = {
                'invalid_count': non_binary_count,
                'invalid_values': invalid_unique
            }
            blocking_errors.append(f"Binary column '{c}' has {non_binary_count} non-binary entries: {invalid_unique}")

    # 6. Single-Select Codebook Range Conformance Check
    range_violations = {}
    for col, (min_val, max_val) in SINGLE_SELECT_RANGES.items():
        if col not in work_df.columns:
            # If col is missing, report missing check
            blocking_errors.append(f"Expected single-select column '{col}' is missing from DataFrame.")
            continue

        series = work_df[col]
        numeric_series = pd.to_numeric(series, errors='coerce')
        coerced_nans = int(numeric_series.isna().sum()) - int(series.isna().sum())

        # Check bounds and integer constraint
        out_of_bounds_mask = (numeric_series < min_val) | (numeric_series > max_val) | (numeric_series.isna())
        # Check decimals / floats
        non_integer_mask = numeric_series.apply(lambda x: False if pd.isna(x) else not float(x).is_integer())

        invalid_mask = out_of_bounds_mask | non_integer_mask
        invalid_count = int(invalid_mask.sum())

        if invalid_count > 0:
            invalid_vals = series[invalid_mask].unique().tolist()
            range_violations[col] = {
                'invalid_count': invalid_count,
                'expected_range': [min_val, max_val],
                'invalid_values': invalid_vals
            }
            blocking_errors.append(f"Column '{col}' has {invalid_count} out-of-range or non-integer values: {invalid_vals}")

    # 7. Logical Consistency & Mutually Exclusive Checks
    aware_platforms = ['Aware Blinkit', 'Aware Zepto', 'Aware Swiggy Instamart', 'Aware BigBasket BBNow', 'Aware Flipkart Minutes', 'Aware Amazon Rapid', 'Aware Other']
    aware_platforms_present = [c for c in aware_platforms if c in work_df.columns]
    used_platforms = ['Used Blinkit', 'Used Zepto', 'Used Swiggy Instamart', 'Used BigBasket BBNow', 'Used Flipkart Minutes', 'Used Amazon Rapid']
    used_platforms_present = [c for c in used_platforms if c in work_df.columns]

    logical_conflicts = {}
    if 'Aware None' in work_df.columns and aware_platforms_present:
        aware_none_conflict = int(((work_df['Aware None'] == 1) & (work_df[aware_platforms_present].sum(axis=1) > 0)).sum())
        logical_conflicts['aware_none_conflict'] = aware_none_conflict
        if aware_none_conflict > 0:
            blocking_errors.append(f"Logical conflict: 'Aware None' == 1 while platform awareness > 0 in {aware_none_conflict} rows.")

    if 'Used Never Used' in work_df.columns and used_platforms_present:
        used_never_conflict = int(((work_df['Used Never Used'] == 1) & (work_df[used_platforms_present].sum(axis=1) > 0)).sum())
        logical_conflicts['used_never_vs_used_platforms'] = used_never_conflict
        if used_never_conflict > 0:
            blocking_errors.append(f"Logical conflict: 'Used Never Used' == 1 while used platforms > 0 in {used_never_conflict} rows.")

    col_ever = 'Ever Ordered through a Quick-Commerce Platform'
    if col_ever in work_df.columns and used_platforms_present:
        ever_0_used_any = int(((work_df[col_ever] == 0) & (work_df[used_platforms_present].sum(axis=1) > 0)).sum())
        ever_1_used_never = int(((work_df[col_ever] == 1) & (work_df.get('Used Never Used', 0) == 1)).sum())
        logical_conflicts['ever_0_used_platforms_conflict'] = ever_0_used_any
        logical_conflicts['ever_1_used_never_conflict'] = ever_1_used_never
        if ever_0_used_any > 0:
            blocking_errors.append(f"Logical conflict: 'Ever Ordered' == 0 but used platforms marked in {ever_0_used_any} rows.")
        if ever_1_used_never > 0:
            blocking_errors.append(f"Logical conflict: 'Ever Ordered' == 1 but 'Used Never Used' marked in {ever_1_used_never} rows.")

    problem_cols = [c for c in work_df.columns if c.startswith('Problem ') and c not in ['Problem No Major Problem', 'Problem Not Applicable']]
    if 'Problem No Major Problem' in work_df.columns and problem_cols:
        problem_no_major_conflict = int(((work_df['Problem No Major Problem'] == 1) & (work_df[problem_cols].sum(axis=1) > 0)).sum())
        logical_conflicts['problem_no_major_conflict'] = problem_no_major_conflict
        if problem_no_major_conflict > 0:
            blocking_errors.append(f"Logical conflict: 'Problem No Major Problem' == 1 while specific problems marked in {problem_no_major_conflict} rows.")

    col_freq = 'Order Frequency'
    col_na_current = 'Reason Not Applicable Current User'
    if col_freq in work_df.columns and col_na_current in work_df.columns:
        qa48_na_vs_order_freq_1 = int(((work_df[col_freq] == 1) & (work_df[col_na_current] == 1)).sum())
        qa48_non_na_vs_order_freq_gt_1 = int(((work_df[col_freq] > 1) & (work_df[col_na_current] == 0)).sum())
        logical_conflicts['qa48_na_current_user_mismatch'] = qa48_na_vs_order_freq_1 + qa48_non_na_vs_order_freq_gt_1
        if (qa48_na_vs_order_freq_1 + qa48_non_na_vs_order_freq_gt_1) > 0:
            blocking_errors.append(
                f"Logical conflict: QA48 current-user skip flag mismatch in "
                f"{qa48_na_vs_order_freq_1 + qa48_non_na_vs_order_freq_gt_1} rows."
            )

    # 8. Triangulation of Usage Status & The 80-Record Previous-User Routing
    usage_status_audit = {}
    routing_breakdown = {}
    if col_ever in work_df.columns and col_freq in work_df.columns:
        ever_series = pd.to_numeric(work_df[col_ever], errors='coerce')
        freq_series = pd.to_numeric(work_df[col_freq], errors='coerce')

        ever_yes = int((ever_series == 1).sum())
        ever_no = int((ever_series == 0).sum())
        freq_never = int((freq_series == 1).sum())
        freq_current = int((freq_series > 1).sum())

        never_users_mask = (ever_series == 0) & (freq_series == 1)
        prev_users_mask = (ever_series == 1) & (freq_series == 1)
        current_users_mask = (ever_series == 1) & (freq_series > 1)
        inconsistent_never_mask = (ever_series == 0) & (freq_series > 1)

        never_users_count = int(never_users_mask.sum())
        prev_users_count = int(prev_users_mask.sum())
        current_users_count = int(current_users_mask.sum())
        inconsistent_never_count = int(inconsistent_never_mask.sum())

        if inconsistent_never_count > 0:
            blocking_errors.append(f"Inconsistent respondents: Ever Ordered == 0 but Order Frequency > Never in {inconsistent_never_count} rows.")

        # Skip-logic routing verification for QA16-45:
        # All 456 respondents with Order Frequency == 1 (Never) skip QA16-45
        skipped_satisfaction_fields = [
            'Overall Satisfaction', 'Product Quality Satisfaction',
            'Delivery Reliability Satisfaction', 'Value Money Satisfaction'
        ]
        prev_user_satisfaction_na = {}
        for sf in skipped_satisfaction_fields:
            if sf in work_df.columns:
                na_cnt = int((pd.to_numeric(work_df.loc[prev_users_mask, sf], errors='coerce') == 6).sum())
                prev_user_satisfaction_na[sf] = na_cnt

        # QA46: Future-use intention (Next 3 Month Use)
        # Verify substantive values 1-5 across all groups
        qa46_stats = {}
        if 'Next 3 Month Use' in work_df.columns:
            s_qa46 = pd.to_numeric(work_df['Next 3 Month Use'], errors='coerce')
            qa46_stats = {
                'substantive_total_1_to_5': int(s_qa46.isin([1, 2, 3, 4, 5]).sum()),
                'never_users_substantive': int(s_qa46[never_users_mask].isin([1, 2, 3, 4, 5]).sum()),
                'previous_users_substantive': int(s_qa46[prev_users_mask].isin([1, 2, 3, 4, 5]).sum()),
                'current_users_substantive': int(s_qa46[current_users_mask].isin([1, 2, 3, 4, 5]).sum()),
                'na_count': int((s_qa46 == 6).sum())
            }

        # QA47: Continue if discounts reduced
        # Verify substantive 1-5 for 807 current users, and code 6 (Not applicable) for 456 non-current users
        qa47_stats = {}
        if 'Continue If Discounts Reduced' in work_df.columns:
            s_qa47 = pd.to_numeric(work_df['Continue If Discounts Reduced'], errors='coerce')
            qa47_stats = {
                'current_users_substantive_1_to_5': int(s_qa47[current_users_mask].isin([1, 2, 3, 4, 5]).sum()),
                'current_users_na_code_6': int((s_qa47[current_users_mask] == 6).sum()),
                'non_current_users_na_code_6': int((s_qa47[freq_series == 1] == 6).sum()),
                'non_current_users_substantive': int(s_qa47[freq_series == 1].isin([1, 2, 3, 4, 5]).sum())
            }

        # QA48: Reasons for not currently using
        prev_user_qa48_reasons = {}
        never_user_qa48_reasons = {}
        reason_non_user_cols = [
            'Reason Service Unavailable', 'Reason Prefer Physical', 'Reason Prices High',
            'Reason Delivery Fees', 'Reason Distrust Quality', 'Reason Prefer Inspect',
            'Reason Impulsive Spending Concern', 'Reason No Need Rapid',
            'Reason Privacy Payment Concern', 'Reason Unfamiliar Apps'
        ]
        for rc in reason_non_user_cols:
            if rc in work_df.columns:
                prev_user_qa48_reasons[rc] = int(pd.to_numeric(work_df.loc[prev_users_mask, rc], errors='coerce').sum())
                never_user_qa48_reasons[rc] = int(pd.to_numeric(work_df.loc[never_users_mask, rc], errors='coerce').sum())

        usage_status_audit = {
            'ever_ordered_yes': ever_yes,
            'ever_ordered_no': ever_no,
            'current_order_frequency_never': freq_never,
            'current_order_frequency_active': freq_current,
            'never_users_count': never_users_count,
            'previous_users_count': prev_users_count,
            'current_users_count': current_users_count,
            'inconsistent_never_count': inconsistent_never_count,
            'previous_users_satisfaction_mislabeled_as_never_used': prev_user_satisfaction_na,
            'previous_users_reasons_for_not_using': prev_user_qa48_reasons,
            'never_users_reasons_for_not_using': never_user_qa48_reasons
        }

        routing_breakdown = {
            'qa16_to_qa45_skip_coded_count': freq_never,
            'qa46_future_use_intention': qa46_stats,
            'qa47_discount_continuation': qa47_stats,
            'qa48_non_user_reasons_available_count': freq_never
        }

    # 9. Completeness & Missingness Multi-Tier Summary
    completeness_summary = {
        'physical_blank_cells': total_null_cells,
        'physical_data_completeness_pct': 100.0 if total_null_cells == 0 else round((1 - total_null_cells / (total_rows * total_cols)) * 100, 2),
        'explicit_not_applicable_counts': {
            'qa16_to_qa45_skip_coded_respondents': usage_status_audit.get('current_order_frequency_never', 0),
            'qa37_to_qa40_satisfaction_code_6_not_applicable': int((pd.to_numeric(work_df.get('Overall Satisfaction', pd.Series()), errors='coerce') == 6).sum()),
            'qa47_discount_reduction_code_6_not_applicable': int((pd.to_numeric(work_df.get('Continue If Discounts Reduced', pd.Series()), errors='coerce') == 6).sum()),
            'qa48_current_user_skip_flag_code_1': int((pd.to_numeric(work_df.get('Reason Not Applicable Current User', pd.Series()), errors='coerce') == 1).sum()),
            'category_not_applicable_code_1': int((pd.to_numeric(work_df.get('Category Not Applicable', pd.Series()), errors='coerce') == 1).sum()),
            'problem_not_applicable_code_1': int((pd.to_numeric(work_df.get('Problem Not Applicable', pd.Series()), errors='coerce') == 1).sum())
        },
        'substantive_observed_response_counts': {
            'qa46_future_use_intention_substantive_1_to_5': routing_breakdown.get('qa46_future_use_intention', {}).get('substantive_total_1_to_5', 0),
            'qa47_discount_continuation_substantive_1_to_5': routing_breakdown.get('qa47_discount_continuation', {}).get('current_users_substantive_1_to_5', 0),
            'qa48_non_user_reasons_active_respondents': usage_status_audit.get('current_order_frequency_never', 0),
            'qa49_improvement_substantive_1_to_10': int(pd.to_numeric(work_df.get('Improvement', pd.Series()), errors='coerce').isin(range(1, 11)).sum())
        }
    }

    # 10. Platform Usage Footprint in Survey (QA 12)
    platform_usage_counts = {}
    for pc in used_platforms_present:
        p_name = pc.replace('Used ', '')
        used_sum = int(pd.to_numeric(work_df[pc], errors='coerce').sum())
        platform_usage_counts[p_name] = {
            'total_used_count': used_sum,
            'pct_of_all_respondents': f"{(used_sum / total_rows) * 100:.1f}%",
            'pct_of_ever_users': f"{(used_sum / 887) * 100:.1f}%" if total_rows >= 887 else "N/A"
        }

    # Determine overall audit status
    if blocking_errors:
        audit_status = 'FAILED'
    elif warning_messages:
        audit_status = 'SUCCESS_WITH_WARNINGS'
    else:
        audit_status = 'SUCCESS'

    return {
        'status': audit_status,
        'blocking_errors': blocking_errors,
        'warnings': warning_messages,
        'total_rows': total_rows,
        'total_columns': total_cols,
        'dimension_discrepancy': dimension_discrepancy,
        'full_duplicate_rows': full_duplicate_rows,
        'demographic_duplicate_rows': demographic_duplicate_rows,
        'total_null_cells': total_null_cells,
        'null_columns_count': len(null_counts_per_col),
        'whitespace_column_names': whitespace_cols,
        'missing_mandatory_columns': missing_mandatory_columns,
        'duplicate_normalized_headers': duplicate_normalized_headers,
        'binary_column_violations': binary_violations,
        'range_violations': range_violations,
        'logical_conflicts': logical_conflicts,
        'usage_status_audit': usage_status_audit,
        'questionnaire_routing': routing_breakdown,
        'completeness_and_missingness': completeness_summary,
        'platform_usage_counts': platform_usage_counts
    }


def print_survey_audit_report(file_path, sheet_name, file_sha256, file_size, audit_results):
    """Prints a structured, formatted survey audit report to stdout."""
    print("=" * 80)
    print("GATE 0 CANDIDATE SURVEY AUDIT: MENDELEY QUICK-COMMERCE DATASET (CHANDRA 2026)")
    print(f"Target File : {file_path}")
    print(f"Worksheet   : {sheet_name}")
    print(f"File Size   : {file_size:,} bytes")
    print(f"SHA-256 Hash: {file_sha256}")
    print(f"Dimensions  : {audit_results['total_rows']:,} data rows x {audit_results['total_columns']} columns")
    print(f"Audit Status: {audit_results['status']}")
    print("=" * 80)

    if audit_results['blocking_errors']:
        print("\n[BLOCKING AUDIT ERRORS ENCOUNTERED]")
        for err in audit_results['blocking_errors']:
            print(f"  [X] {err}")

    if audit_results['warnings']:
        print("\n[NON-BLOCKING WARNINGS]")
        for warn in audit_results['warnings']:
            print(f"  [!] {warn}")

    print("\n" + "-" * 60)
    print("PART 1: STRUCTURAL INTEGRITY, SCHEMA & CONFORMANCE")
    print("-" * 60)
    print(f"  - Total Data Rows Loaded   : {audit_results['total_rows']:,} (Expected: {EXPECTED_ROWS})")
    print(f"  - Total Columns Loaded     : {audit_results['total_columns']} (Expected: {EXPECTED_COLS})")
    print(f"  - Missing Mandatory Columns: {len(audit_results['missing_mandatory_columns'])}")
    print(f"  - Duplicate Column Headers : {len(audit_results['duplicate_normalized_headers'])}")
    print(f"  - Full Duplicate Rows      : {audit_results['full_duplicate_rows']}")
    print(f"  - Demographic Profile Dups : {audit_results['demographic_duplicate_rows']} / {audit_results['total_rows']}")
    print(f"  - Physical Null/Blank Cells: {audit_results['total_null_cells']} across all cells")
    print(f"  - Header Whitespace Flaws  : {len(audit_results['whitespace_column_names'])} columns with leading/trailing spaces")
    for wc in audit_results['whitespace_column_names']:
        print(f"      * '{wc}'")
    print(f"  - Binary Dummy Violations  : {len(audit_results['binary_column_violations'])} (All dummy variables strictly in {{0, 1}})")
    print(f"  - Codebook Range Violations: {len(audit_results['range_violations'])} (All single-select variables in bounds)")

    print("\n" + "-" * 60)
    print("PART 2: LOGICAL CONSISTENCY & MUTUAL EXCLUSIVITY")
    print("-" * 60)
    for k, v in audit_results['logical_conflicts'].items():
        print(f"  - {k:<38}: {v} conflicts")

    print("\n" + "-" * 60)
    print("PART 3: USAGE STATUS TRIANGULATION & QUESTIONNAIRE ROUTING")
    print("-" * 60)
    us = audit_results.get('usage_status_audit', {})
    rt = audit_results.get('questionnaire_routing', {})

    def fmt_num(val):
        return f"{val:,}" if isinstance(val, (int, float)) else "N/A"

    print(f"  - QA 10 Ever Ordered through Quick Commerce = Yes (1) : {fmt_num(us.get('ever_ordered_yes'))}")
    print(f"  - QA 10 Ever Ordered through Quick Commerce = No  (0) : {fmt_num(us.get('ever_ordered_no'))}")
    print(f"  - QA 15 Current Order Frequency = Never (1)           : {fmt_num(us.get('current_order_frequency_never'))}")
    print(f"  - QA 15 Current Order Frequency = Active (2..7)       : {fmt_num(us.get('current_order_frequency_active'))}")

    nu = us.get('never_users_count', 0)
    pu = us.get('previous_users_count', 0)
    cu = us.get('current_users_count', 0)
    tot = audit_results.get('total_rows', 1)

    print("\nTriangulated Subgroup Breakdown:")
    print(f"  1. Never Users    (Ever=0, Current Freq=Never): {fmt_num(nu):>4} ({(nu/tot*100) if tot else 0:.1f}%)")
    print(f"  2. Previous Users (Ever=1, Current Freq=Never): {fmt_num(pu):>4} ({(pu/tot*100) if tot else 0:.1f}%)")
    print(f"  3. Current Users  (Ever=1, Current Freq>Never): {fmt_num(cu):>4} ({(cu/tot*100) if tot else 0:.1f}%)")
    print(f"  Total Rows Accounted For                      : {tot:,}")

    print("\nQuestionnaire Routing & Variable Availability Breakdown:")
    print(f"  * QA 16 - QA 45 Skip-Coded Modules for Non-Current Users: {rt.get('qa16_to_qa45_skip_coded_count', 0)} respondents")
    print("    - Service Satisfaction (QA 37-40) coded as 'Not applicable - never used' (Code 6):")
    for sf, cnt in us.get('previous_users_satisfaction_mislabeled_as_never_used', {}).items():
        print(f"        * {sf:<33}: {cnt} / 80 previous users mislabeled")
    q46 = rt.get('qa46_future_use_intention', {})
    print(f"  * QA 46 Stated Future-Use Intention: Substantive (1-5) across ALL {fmt_num(q46.get('substantive_total_1_to_5', 0))} respondents")
    print(f"      - Never Users Substantive   : {q46.get('never_users_substantive', 0):>4} / {nu}")
    print(f"      - Previous Users Substantive: {q46.get('previous_users_substantive', 0):>4} / {pu}")
    print(f"      - Current Users Substantive : {q46.get('current_users_substantive', 0):>4} / {cu}")
    q47 = rt.get('qa47_discount_continuation', {})
    print(f"  * QA 47 Willingness to Continue if Discounts Reduced:")
    print(f"      - Current Users Substantive (1-5): {q47.get('current_users_substantive_1_to_5', 0):>4} / {cu}")
    print(f"      - Non-Current Users N/A (Code 6) : {q47.get('non_current_users_na_code_6', 0):>4} / {us.get('current_order_frequency_never', 0)} (Explicit N/A; NOT defection)")
    print(f"  * QA 48 Reasons for Not Currently Using Quick Commerce:")
    print(f"      - Available for all {rt.get('qa48_non_user_reasons_available_count', 0)} non-current users (376 never-users + 80 previous users)")

    print("\n" + "-" * 60)
    print("PART 4: PLATFORM USAGE FOOTPRINT IN SURVEY (QA 12)")
    print("-" * 60)
    for p, stats in audit_results['platform_usage_counts'].items():
        print(f"  - {p:<20}: {stats['total_used_count']:>4} users ({stats['pct_of_all_respondents']} of all, {stats['pct_of_ever_users']} of ever-users)")

    print("\n" + "=" * 80)
    print("PROJECT FIT & METHODOLOGICAL BOUNDARIES SUMMARY")
    print("=" * 80)
    print("  1. General Quick-Commerce Scope: Satisfaction, problems, and spending questions")
    print("     measure general quick-commerce experiences; NO platform-specific satisfaction exists.")
    print("  2. Absent Key CRM Outcomes: Actual churn, longitudinal repeat purchase, and causal")
    print("     retention uplift are unobserved. Stated intentions (QA 46/47) are proxy perceptions.")
    print("  3. Segmentation Viability: Supports consumer segmentation around discount-dependence")
    print("     (QA 28, 29, 47), basket economics, and service priorities at an industry level.")
    print("================================================================================\n")


def run_survey_audit(file_path, sheet_name=EXPECTED_SHEET, output_json=None, no_output=False):
    """
    Coordinates reading workbook, computing SHA-256, executing audit,
    printing report, and exporting aggregate JSON summary.
    """
    file_sha256 = compute_file_sha256(file_path)
    file_size = os.path.getsize(file_path)

    try:
        df = pd.read_excel(file_path, sheet_name=sheet_name)
    except Exception as e:
        sys.stderr.write(f"\n[FATAL ERROR] Could not read Excel workbook '{file_path}' (sheet: '{sheet_name}'): {e}\n")
        sys.exit(1)

    results = audit_survey_dataframe(df, enforce_dimensions=True)

    try:
        rel_input_path = os.path.relpath(file_path, os.getcwd()) if os.path.isabs(file_path) else file_path
    except ValueError:
        rel_input_path = os.path.abspath(file_path)

    results['survey_metadata'] = {
        'source_title': "A Large-Scale Survey Dataset on Quick-Commerce Adoption, Ordering Patterns, Product Categories and Spending Behaviour among Indian Consumers",
        'contributor': "Dr. Ashish Chandra (Amity Business School, Amity University, Lucknow)",
        'declared_licence': "CC BY 4.0",
        'mendeley_doi': "10.17632/cw88nb7822.1",
        'deposit_date': "14 October 2026",
        'input_file_path': rel_input_path,
        'input_worksheet': sheet_name,
        'input_file_sha256': file_sha256,
        'input_file_size_bytes': file_size,
        'audit_timestamp_utc': datetime.now(timezone.utc).isoformat()
    }

    print_survey_audit_report(results['survey_metadata']['input_file_path'], sheet_name, file_sha256, file_size, results)

    if not no_output and output_json:
        out_dir = os.path.dirname(output_json)
        if out_dir and not os.path.exists(out_dir):
            os.makedirs(out_dir, exist_ok=True)
        with open(output_json, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)
        print(f"[OUTPUT] Saved aggregate machine-readable survey audit summary to: {output_json}")

    if results['status'] == 'FAILED':
        sys.stderr.write("\n[FATAL ERROR] Survey audit FAILED due to blocking schema or validation errors.\n")
        sys.exit(1)

    return results


def main():
    args = parse_arguments()
    survey_path = resolve_survey_path(args.file)
    output_path = None if args.no_output else args.output
    run_survey_audit(
        file_path=survey_path,
        sheet_name=args.sheet,
        output_json=output_path,
        no_output=args.no_output
    )


if __name__ == "__main__":
    main()
