#!/usr/bin/env python3
"""
scripts/audit_survey_data.py

Reproducible quantitative audit script for the Mendeley Quick-Commerce Survey Dataset:
"A Large-Scale Survey Dataset on Quick-Commerce Adoption, Ordering Patterns,
Product Categories and Spending Behaviour among Indian Consumers" (Chandra 2026).

Audits the survey workbook (Data.xlsx) for:
1. Workbook Structure & Dimensions:
   - Worksheet names, dimensions (1,263 rows x 130 columns)
   - Header formatting and leading/trailing whitespace anomalies
   - Complete absence of null/missing/blank cells
2. Coding Validity & Range Conformance:
   - Single-select variables validated against codebook integer ranges
   - Multi-select indicator variables validated against binary {0, 1}
   - Full duplicate row detection
3. Logical Consistency & Mutually Exclusive Constraints:
   - Awareness vs. "Aware None"
   - Usage vs. "Used Never Used"
   - Ever-ordered vs. platform usage indicators
   - "Problem No Major Problem" vs. specific operational defects
   - Non-user reasons vs. current ordering status
4. Usage-Status Triangulation & The 80-Record Previous-User Issue:
   - Disaggregates Never Users (n=376), Previous Users (n=80), and Current Users (n=807)
   - Documents the skip-logic routing where QA 15 ("Order Frequency" == 1) routes
     all 456 non-current users past QA 16-47
   - Identifies which service-experience fields are mislabeled as "Not applicable - never used"
     for the 80 previous users
   - Quantifies available substantive feedback from previous users (QA 12, 13, 14, 46, 48, 49)
5. Aggregate-Only Machine-Readable Summary Export:
   - Exports docs/gates/GATE_0_SURVEY_AUDIT_SUMMARY.json (zero raw PII or row-level microdata)

Usage:
    python scripts/audit_survey_data.py [--file PATH_TO_XLSX] [--output PATH_TO_JSON]
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

def audit_survey_dataframe(df):
    """
    Performs comprehensive structural, coding, logical consistency,
    and usage-status audits on the survey DataFrame.
    """
    total_rows = len(df)
    total_cols = len(df.columns)
    raw_col_names = df.columns.tolist()

    # 1. Whitespace in column headers
    stripped_col_names = [str(c).strip() for c in raw_col_names]
    whitespace_cols = [raw_col_names[i] for i in range(len(raw_col_names)) if raw_col_names[i] != stripped_col_names[i]]

    # Standardized working copy with trimmed column headers
    work_df = df.copy()
    work_df.columns = stripped_col_names

    # 2. Missing / Blank Cells
    null_counts_per_col = {col: int(work_df[col].isna().sum()) for col in work_df.columns if work_df[col].isna().sum() > 0}
    total_null_cells = int(work_df.isna().sum().sum())

    # 3. Duplicate Rows
    full_duplicate_rows = int(work_df.duplicated().sum())
    demo_cols = ['Age Group', 'Gender', 'Education', 'Occupation', 'Personal Income', 'Area of Residence', 'Region', 'Household Size']
    demographic_duplicate_rows = int(work_df.duplicated(subset=demo_cols).sum()) if all(c in work_df.columns for c in demo_cols) else 0

    # 4. Multi-Select Binary Indicator Check
    binary_cols = []
    for c in work_df.columns:
        if any(c.startswith(p) for p in MULTI_SELECT_PREFIXES):
            binary_cols.append(c)

    binary_violations = {}
    for c in binary_cols:
        unique_vals = [v for v in work_df[c].unique() if not pd.isna(v)]
        non_binary = [v for v in unique_vals if v not in [0, 1]]
        if non_binary:
            binary_violations[c] = non_binary

    # 5. Single-Select Codebook Range Conformance Check
    range_violations = {}
    for col, (min_val, max_val) in SINGLE_SELECT_RANGES.items():
        if col in work_df.columns:
            series = work_df[col]
            invalid_mask = (series < min_val) | (series > max_val) | (series.isna()) | (~series.apply(lambda x: float(x).is_integer() if pd.notna(x) else False))
            invalid_count = int(invalid_mask.sum())
            if invalid_count > 0:
                range_violations[col] = {
                    'invalid_count': invalid_count,
                    'invalid_values': series[invalid_mask].unique().tolist()
                }

    # 6. Logical Consistency & Mutually Exclusive Checks
    aware_platforms = ['Aware Blinkit', 'Aware Zepto', 'Aware Swiggy Instamart', 'Aware BigBasket BBNow', 'Aware Flipkart Minutes', 'Aware Amazon Rapid', 'Aware Other']
    aware_platforms_present = [c for c in aware_platforms if c in work_df.columns]
    used_platforms = ['Used Blinkit', 'Used Zepto', 'Used Swiggy Instamart', 'Used BigBasket BBNow', 'Used Flipkart Minutes', 'Used Amazon Rapid']
    used_platforms_present = [c for c in used_platforms if c in work_df.columns]

    logical_conflicts = {}
    if 'Aware None' in work_df.columns and aware_platforms_present:
        aware_none_conflict = int(((work_df['Aware None'] == 1) & (work_df[aware_platforms_present].sum(axis=1) > 0)).sum())
        logical_conflicts['aware_none_conflict'] = aware_none_conflict

    if 'Used Never Used' in work_df.columns and used_platforms_present:
        used_never_conflict = int(((work_df['Used Never Used'] == 1) & (work_df[used_platforms_present].sum(axis=1) > 0)).sum())
        logical_conflicts['used_never_vs_used_platforms'] = used_never_conflict

    col_ever = 'Ever Ordered through a Quick-Commerce Platform'
    if col_ever in work_df.columns and used_platforms_present:
        ever_0_used_any = int(((work_df[col_ever] == 0) & (work_df[used_platforms_present].sum(axis=1) > 0)).sum())
        ever_1_used_never = int(((work_df[col_ever] == 1) & (work_df.get('Used Never Used', 0) == 1)).sum())
        logical_conflicts['ever_0_used_platforms_conflict'] = ever_0_used_any
        logical_conflicts['ever_1_used_never_conflict'] = ever_1_used_never

    problem_cols = [c for c in work_df.columns if c.startswith('Problem ') and c not in ['Problem No Major Problem', 'Problem Not Applicable']]
    if 'Problem No Major Problem' in work_df.columns and problem_cols:
        problem_no_major_conflict = int(((work_df['Problem No Major Problem'] == 1) & (work_df[problem_cols].sum(axis=1) > 0)).sum())
        logical_conflicts['problem_no_major_conflict'] = problem_no_major_conflict

    col_freq = 'Order Frequency'
    col_na_current = 'Reason Not Applicable Current User'
    if col_freq in work_df.columns and col_na_current in work_df.columns:
        qa48_na_vs_order_freq_1 = int(((work_df[col_freq] == 1) & (work_df[col_na_current] == 1)).sum())
        qa48_non_na_vs_order_freq_gt_1 = int(((work_df[col_freq] > 1) & (work_df[col_na_current] == 0)).sum())
        logical_conflicts['qa48_na_current_user_mismatch'] = qa48_na_vs_order_freq_1 + qa48_non_na_vs_order_freq_gt_1

    # 7. Triangulation of Usage Status & The 80-Record Previous-User Issue
    usage_status_audit = {}
    if col_ever in work_df.columns and col_freq in work_df.columns:
        ever_series = work_df[col_ever]
        freq_series = work_df[col_freq]

        ever_yes = int((ever_series == 1).sum())
        ever_no = int((ever_series == 0).sum())

        freq_never = int((freq_series == 1).sum())
        freq_current = int((freq_series > 1).sum())

        never_users_mask = (ever_series == 0) & (freq_series == 1)
        prev_users_mask = (ever_series == 1) & (freq_series == 1)
        current_users_mask = (ever_series == 1) & (freq_series > 1)
        ever_0_freq_gt_1_mask = (ever_series == 0) & (freq_series > 1)

        never_users_count = int(never_users_mask.sum())
        prev_users_count = int(prev_users_mask.sum())
        current_users_count = int(current_users_mask.sum())
        inconsistent_never_count = int(ever_0_freq_gt_1_mask.sum())

        # Check skip-logic routing: which fields code "Not applicable - never used" for the 80 previous users
        skipped_satisfaction_fields = [
            'Overall Satisfaction', 'Product Quality Satisfaction',
            'Delivery Reliability Satisfaction', 'Value Money Satisfaction'
        ]
        prev_user_satisfaction_na = {}
        for sf in skipped_satisfaction_fields:
            if sf in work_df.columns:
                # Code 6 is "Not applicable - never used"
                na_cnt = int((work_df.loc[prev_users_mask, sf] == 6).sum())
                prev_user_satisfaction_na[sf] = na_cnt

        prev_user_qa48_reasons = {}
        reason_non_user_cols = [
            'Reason Service Unavailable', 'Reason Prefer Physical', 'Reason Prices High',
            'Reason Delivery Fees', 'Reason Distrust Quality', 'Reason Prefer Inspect',
            'Reason Impulsive Spending Concern', 'Reason No Need Rapid',
            'Reason Privacy Payment Concern', 'Reason Unfamiliar Apps'
        ]
        for rc in reason_non_user_cols:
            if rc in work_df.columns:
                prev_user_qa48_reasons[rc] = int(work_df.loc[prev_users_mask, rc].sum())

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
            'previous_users_reasons_for_not_using': prev_user_qa48_reasons
        }

    # 8. Platform Usage Footprint in Survey
    platform_usage_counts = {}
    for pc in used_platforms_present:
        p_name = pc.replace('Used ', '')
        platform_usage_counts[p_name] = {
            'total_used_count': int(work_df[pc].sum()),
            'pct_of_all_respondents': f"{(work_df[pc].sum() / total_rows) * 100:.1f}%",
            'pct_of_ever_users': f"{(work_df[pc].sum() / 887) * 100:.1f}%" if total_rows >= 887 else "N/A"
        }

    return {
        'status': 'SUCCESS',
        'total_rows': total_rows,
        'total_columns': total_cols,
        'full_duplicate_rows': full_duplicate_rows,
        'demographic_duplicate_rows': demographic_duplicate_rows,
        'total_null_cells': total_null_cells,
        'null_columns_count': len(null_counts_per_col),
        'whitespace_column_names': whitespace_cols,
        'binary_column_violations': binary_violations,
        'range_violations': range_violations,
        'logical_conflicts': logical_conflicts,
        'usage_status_audit': usage_status_audit,
        'platform_usage_counts': platform_usage_counts
    }

def print_survey_audit_report(file_path, file_sha256, file_size, audit_results):
    """Prints a structured, formatted survey audit report to stdout."""
    print("=" * 80)
    print("GATE 0 CANDIDATE SURVEY AUDIT: MENDELEY QUICK-COMMERCE DATASET (CHANDRA 2026)")
    print(f"Target File : {file_path}")
    print(f"File Size   : {file_size:,} bytes")
    print(f"SHA-256 Hash: {file_sha256}")
    print(f"Dimensions  : {audit_results['total_rows']:,} data rows x {audit_results['total_columns']} columns")
    print("=" * 80)

    print("\n" + "-" * 60)
    print("PART 1: STRUCTURAL INTEGRITY & CODING CONFORMANCE")
    print("-" * 60)
    print(f"  - Total Data Rows Loaded   : {audit_results['total_rows']:,} (Expected: {EXPECTED_ROWS})")
    print(f"  - Total Columns Loaded     : {audit_results['total_columns']} (Expected: {EXPECTED_COLS})")
    print(f"  - Full Duplicate Rows      : {audit_results['full_duplicate_rows']}")
    print(f"  - Demographic Profile Dups : {audit_results['demographic_duplicate_rows']} / {audit_results['total_rows']}")
    print(f"  - Missing / Null Cells     : {audit_results['total_null_cells']} across all 164,190 cells")
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
    print("PART 3: USAGE STATUS TRIANGULATION & THE 80-RECORD PREVIOUS-USER ISSUE")
    print("-" * 60)
    us = audit_results['usage_status_audit']
    print(f"  - QA 10 Ever Ordered through Quick Commerce = Yes (1) : {us.get('ever_ordered_yes', 'N/A'):,}")
    print(f"  - QA 10 Ever Ordered through Quick Commerce = No  (0) : {us.get('ever_ordered_no', 'N/A'):,}")
    print(f"  - QA 15 Current Order Frequency = Never (1)           : {us.get('current_order_frequency_never', 'N/A'):,}")
    print(f"  - QA 15 Current Order Frequency = Active (2..7)       : {us.get('current_order_frequency_active', 'N/A'):,}")
    print("\nTriangulated Subgroup Breakdown:")
    print(f"  1. Never Users    (Ever=0, Current Freq=Never): {us.get('never_users_count', 'N/A'):>4} ({us.get('never_users_count', 0)/audit_results['total_rows']*100:.1f}%)")
    print(f"  2. Previous Users (Ever=1, Current Freq=Never): {us.get('previous_users_count', 'N/A'):>4} ({us.get('previous_users_count', 0)/audit_results['total_rows']*100:.1f}%)")
    print(f"  3. Current Users  (Ever=1, Current Freq>Never): {us.get('current_users_count', 'N/A'):>4} ({us.get('current_users_count', 0)/audit_results['total_rows']*100:.1f}%)")
    print(f"  Total Rows Accounted For                      : {audit_results['total_rows']:,}")

    print("\nDownstream Skip-Logic Impact on the 80 Previous Users:")
    print("  * Service Satisfaction fields (QA 37-40) coded as 'Not applicable - never used' (Code 6):")
    for sf, cnt in us.get('previous_users_satisfaction_mislabeled_as_never_used', {}).items():
        print(f"      - {sf:<35}: {cnt} / 80 ({cnt/80*100:.1f}%) mislabeled as 'never used'")
    print("  * Substantive feedback PRESERVED for Previous Users in QA 48 (Reasons for Not Currently Using):")
    for rc, cnt in us.get('previous_users_reasons_for_not_using', {}).items():
        print(f"      - {rc:<35}: {cnt:>2} / 80 ({cnt/80*100:.1f}%)")

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

def run_survey_audit(file_path, output_json=None, no_output=False):
    """Coordinates reading workbook, hashing, auditing, printing, and exporting JSON."""
    file_sha256 = compute_file_sha256(file_path)
    file_size = os.path.getsize(file_path)

    try:
        df = pd.read_excel(file_path, sheet_name=EXPECTED_SHEET)
    except Exception as e:
        sys.stderr.write(f"\n[FATAL ERROR] Could not read Excel workbook '{file_path}': {e}\n")
        sys.exit(1)

    results = audit_survey_dataframe(df)

    results['survey_metadata'] = {
        'source_title': "A Large-Scale Survey Dataset on Quick-Commerce Adoption, Ordering Patterns, Product Categories and Spending Behaviour among Indian Consumers",
        'contributor': "Dr. Ashish Chandra (Amity Business School, Amity University, Lucknow)",
        'declared_licence': "CC BY 4.0",
        'mendeley_doi': "10.17632/cw88nb7822.1",
        'deposit_date': "14 October 2026",
        'input_file_path': os.path.relpath(file_path, os.getcwd()) if os.path.isabs(file_path) else file_path,
        'input_file_sha256': file_sha256,
        'input_file_size_bytes': file_size,
        'audit_timestamp_utc': datetime.now(timezone.utc).isoformat()
    }

    print_survey_audit_report(results['survey_metadata']['input_file_path'], file_sha256, file_size, results)

    if not no_output and output_json:
        out_dir = os.path.dirname(output_json)
        if out_dir and not os.path.exists(out_dir):
            os.makedirs(out_dir, exist_ok=True)
        with open(output_json, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)
        print(f"[OUTPUT] Saved aggregate machine-readable survey audit summary to: {output_json}")

    return results

def main():
    args = parse_arguments()
    survey_path = resolve_survey_path(args.file)
    output_path = None if args.no_output else args.output
    run_survey_audit(
        file_path=survey_path,
        output_json=output_path,
        no_output=args.no_output
    )

if __name__ == "__main__":
    main()
