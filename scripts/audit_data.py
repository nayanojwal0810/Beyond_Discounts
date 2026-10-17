#!/usr/bin/env python3
"""
scripts/audit_data.py

Reproducible quantitative data audit script for Gate 0 Remediation.
Audits candidate quick-commerce review datasets for:
1. Full Corpus Baseline:
   - Essential field presence (platform, review, rating, date)
   - Missingness, blank text, unparseable dates, and invalid ratings (non-integer / out of 1-5 range)
   - Disaggregated counts to prevent double-counting missing vs blank vs unparseable values
   - Safe platform normalization and detection of unknown/unclassified platforms
   - Exact duplicate rows vs. duplicate review text
   - Baseline platform row counts and date spans
2. Common Review Window (default: 14 August 2024 to 31 December 2024, inclusive):
   - Strict inclusive boundary enforcement (start_date <= review_date <= end_date)
   - Validation against inverted windows (start_date > end_date)
   - Source row counts vs. fully usable row counts in the window
   - Detailed accounting of exclusions (out-of-window vs in-window quality exclusions)
   - Platform rating distributions (counts, percentages, means)
   - Evaluation of feasibility thresholds (>= 500 usable records for Blinkit and Zepto)
   - Enforcement of static scope boundary (no temporal trend or seasonality claims)
   - Generation of machine-readable aggregate audit summary JSON (no raw reviews or PII)

Usage:
    python scripts/audit_data.py [--file PATH_TO_CSV] [--window-start YYYY-MM-DD] [--window-end YYYY-MM-DD] [--output PATH_TO_JSON]
"""

import sys
import os
import argparse
import hashlib
import json
from datetime import datetime, timezone
import pandas as pd
import numpy as np

# Force UTF-8 output encoding if supported
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

ESSENTIAL_FIELDS = ['platform', 'review', 'rating', 'date']
DEFAULT_WINDOW_START = "2024-08-14"
DEFAULT_WINDOW_END = "2024-12-31"
DEFAULT_MIN_THRESHOLD = 500
RECOGNIZED_PLATFORMS = {'blinkit', 'zepto', 'jiomart'}
DEFAULT_OUTPUT_JSON = os.path.join("docs", "gates", "GATE_0_AUDIT_SUMMARY.json")

def parse_arguments(args=None):
    parser = argparse.ArgumentParser(
        description="Audit quick-commerce review dataset for Gate 0 Feasibility."
    )
    parser.add_argument(
        "--file",
        type=str,
        default=None,
        help="Path to candidate CSV dataset. If omitted, checks standard repository-relative paths."
    )
    parser.add_argument(
        "--window-start",
        type=str,
        default=DEFAULT_WINDOW_START,
        help=f"Common window start date (inclusive, YYYY-MM-DD). Default: {DEFAULT_WINDOW_START}"
    )
    parser.add_argument(
        "--window-end",
        type=str,
        default=DEFAULT_WINDOW_END,
        help=f"Common window end date (inclusive, YYYY-MM-DD). Default: {DEFAULT_WINDOW_END}"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=DEFAULT_OUTPUT_JSON,
        help=f"Path to export aggregate-only JSON summary. Default: {DEFAULT_OUTPUT_JSON}"
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

def resolve_dataset_path(file_arg):
    """
    Resolves data file path.
    If --file is explicitly passed, it MUST exist and be readable.
    Never silently substitutes another dataset if an explicit path is invalid.
    If --file is omitted, checks documented repository-relative paths only.
    """
    if file_arg is not None:
        if not os.path.exists(file_arg):
            sys.stderr.write(f"\n[FATAL ERROR] Specified data file does not exist: {file_arg}\n")
            sys.exit(1)
        if not os.path.isfile(file_arg):
            sys.stderr.write(f"\n[FATAL ERROR] Specified path is not a valid file: {file_arg}\n")
            sys.exit(1)
        return os.path.abspath(file_arg)

    # Documented repository-relative default candidate paths
    default_candidates = [
        os.path.join("data", "raw", "reviews.csv"),
        os.path.join("data", "reviews.csv"),
    ]
    for candidate in default_candidates:
        if os.path.isfile(candidate):
            return os.path.abspath(candidate)

    sys.stderr.write(
        "\n[FATAL ERROR] Candidate review dataset not found.\n"
        "Checked repository-relative default paths:\n"
        f"  1. {default_candidates[0]}\n"
        f"  2. {default_candidates[1]}\n\n"
        "To provide the candidate dataset, place the source CSV at 'data/raw/reviews.csv'\n"
        "or pass an explicit path via --file: python scripts/audit_data.py --file <PATH_TO_CSV>\n"
    )
    sys.exit(1)

def validate_date_window(start_str, end_str):
    """
    Validates date window format and ensures window is not inverted.
    Boundary convention is inclusive of both start and end dates.
    """
    try:
        start_date = pd.to_datetime(start_str, format="%Y-%m-%d").date()
    except Exception as e:
        sys.stderr.write(f"\n[FATAL ERROR] Invalid window-start date '{start_str}' (expected YYYY-MM-DD): {e}\n")
        sys.exit(1)

    try:
        end_date = pd.to_datetime(end_str, format="%Y-%m-%d").date()
    except Exception as e:
        sys.stderr.write(f"\n[FATAL ERROR] Invalid window-end date '{end_str}' (expected YYYY-MM-DD): {e}\n")
        sys.exit(1)

    if start_date > end_date:
        sys.stderr.write(
            f"\n[FATAL ERROR] Inverted date window: start date ({start_str}) is after end date ({end_str}).\n"
        )
        sys.exit(1)

    return start_date, end_date

def audit_dataframe(df, start_date, end_date, min_threshold_per_platform=DEFAULT_MIN_THRESHOLD):
    """
    Core quantitative audit function operating on a DataFrame.
    Validates essential columns, disaggregates missing/blank/invalid values,
    normalizes platforms, enforces inclusive window boundaries,
    and calculates usable rows versus exclusions.
    """
    total_raw_rows = len(df)
    columns_found = list(df.columns)

    # 1. Essential Columns Check
    missing_columns = [col for col in ESSENTIAL_FIELDS if col not in df.columns]
    if missing_columns:
        return {
            'status': 'FAILED_SCHEMA',
            'error': f"Essential fields missing from dataset: {missing_columns}. Required: {ESSENTIAL_FIELDS}",
            'total_raw_rows': total_raw_rows,
            'columns_found': columns_found,
            'missing_columns': missing_columns
        }

    # Working copy to prevent mutating caller's DataFrame
    work_df = df.copy()

    # 2. Text Validation: Mutually exclusive missing vs blank/whitespace
    is_text_null = work_df['review'].isna()
    is_text_blank = ~is_text_null & work_df['review'].astype(str).str.strip().eq('')
    is_text_valid = ~is_text_null & ~is_text_blank

    # 3. Rating Validation: Mutually exclusive missing vs invalid (non-integer or out of 1-5)
    # Convert rating values safely
    raw_rating_str = work_df['rating'].astype(str).str.strip()
    is_rating_null = work_df['rating'].isna() | raw_rating_str.isin(['', 'nan', 'null', 'none'])
    
    numeric_ratings = pd.to_numeric(work_df['rating'], errors='coerce')
    is_numeric = numeric_ratings.notna()
    is_integer = is_numeric & numeric_ratings.apply(lambda x: float(x).is_integer() if pd.notna(x) else False)
    is_in_range = is_integer & (numeric_ratings >= 1) & (numeric_ratings <= 5)
    
    is_rating_valid = ~is_rating_null & is_in_range
    is_rating_invalid = ~is_rating_null & ~is_rating_valid

    # Store parsed integer rating where valid
    work_df['clean_rating'] = np.where(is_rating_valid, numeric_ratings.astype(float), np.nan)

    # 4. Date Validation: Mutually exclusive missing vs unparseable
    raw_date_str = work_df['date'].astype(str).str.strip()
    is_date_null = work_df['date'].isna() | raw_date_str.isin(['', 'nan', 'null', 'none'])

    # Parse dates: try explicit format '%d %B %Y' first, fallback for any remaining non-null dates
    parsed_date = pd.to_datetime(work_df['date'], format='%d %B %Y', errors='coerce')
    failed_mask = parsed_date.isna() & ~is_date_null
    if failed_mask.any():
        fallback_parsed = pd.to_datetime(work_df.loc[failed_mask, 'date'], errors='coerce')
        parsed_date = parsed_date.combine_first(fallback_parsed)

    is_date_unparseable = ~is_date_null & parsed_date.isna()
    is_date_valid = parsed_date.notna()
    work_df['parsed_date'] = parsed_date
    work_df['parsed_day'] = parsed_date.dt.date

    # 5. Platform Normalization & Classification
    raw_platform_str = work_df['platform'].astype(str).str.strip()
    is_platform_null = work_df['platform'].isna() | raw_platform_str.isin(['', 'nan', 'null', 'none'])
    norm_platform = raw_platform_str.str.lower()
    norm_platform = np.where(is_platform_null, 'unknown', norm_platform)
    work_df['norm_platform'] = norm_platform

    is_platform_recognized = pd.Series(norm_platform, index=work_df.index).isin(RECOGNIZED_PLATFORMS)
    is_platform_unknown = ~is_platform_recognized

    # 6. Duplication Statistics (Full Dataset)
    exact_duplicate_rows = int(work_df[ESSENTIAL_FIELDS].duplicated().sum())
    duplicate_review_texts = int(work_df.duplicated(subset=['review']).sum())

    # Full Dataset Baseline Counts
    full_dataset_summary = {
        'total_rows': total_raw_rows,
        'columns': columns_found,
        'exact_duplicate_rows': exact_duplicate_rows,
        'duplicate_review_texts': duplicate_review_texts,
        'field_health': {
            'review': {
                'missing_null': int(is_text_null.sum()),
                'blank_whitespace': int(is_text_blank.sum()),
                'valid': int(is_text_valid.sum())
            },
            'rating': {
                'missing_null': int(is_rating_null.sum()),
                'invalid_not_integer_1_to_5': int(is_rating_invalid.sum()),
                'valid': int(is_rating_valid.sum())
            },
            'date': {
                'missing_null': int(is_date_null.sum()),
                'unparseable': int(is_date_unparseable.sum()),
                'valid': int(is_date_valid.sum())
            },
            'platform': {
                'missing_null': int(is_platform_null.sum()),
                'unknown_unclassified': int(is_platform_unknown.sum()),
                'recognized': int(is_platform_recognized.sum())
            }
        },
        'platform_raw_counts': work_df['norm_platform'].value_counts().to_dict()
    }

    # 7. Common Window Filtering & Usable Row Accounting
    # Inclusive window boundary condition: start_date <= date <= end_date
    in_window_mask = is_date_valid & (work_df['parsed_day'] >= start_date) & (work_df['parsed_day'] <= end_date)
    out_of_window_mask = is_date_valid & ~in_window_mask

    # Usable definition:
    # 1. Date is valid and falls inside inclusive window
    # 2. Review text is non-null and non-blank
    # 3. Rating is valid integer 1..5
    # 4. Platform is recognized (blinkit, zepto, jiomart)
    row_usable_mask = in_window_mask & is_text_valid & is_rating_valid & is_platform_recognized

    df_window = work_df[in_window_mask].copy()
    total_window_source_rows = len(df_window)
    total_out_of_window_exclusions = int(out_of_window_mask.sum())
    total_unparseable_date_exclusions = int(is_date_unparseable.sum() + is_date_null.sum())
    total_usable_rows = int(row_usable_mask.sum())

    # Platform-specific metrics
    platform_metrics = {}
    target_platforms = ['blinkit', 'zepto', 'jiomart']
    
    # Also check if any unknown platforms exist in window
    unknown_in_window = df_window[~df_window['norm_platform'].isin(RECOGNIZED_PLATFORMS)]
    unknown_in_window_count = len(unknown_in_window)

    for p in target_platforms:
        p_raw = work_df[work_df['norm_platform'] == p]
        p_win = df_window[df_window['norm_platform'] == p]
        p_usable = work_df[row_usable_mask & (work_df['norm_platform'] == p)]

        # Specific exclusions for this platform
        p_out_of_window = len(p_raw[is_date_valid.loc[p_raw.index] & ~in_window_mask.loc[p_raw.index]])
        p_in_win_missing_text = int(is_text_null.loc[p_win.index].sum())
        p_in_win_blank_text = int(is_text_blank.loc[p_win.index].sum())
        p_in_win_missing_rating = int(is_rating_null.loc[p_win.index].sum())
        p_in_win_invalid_rating = int(is_rating_invalid.loc[p_win.index].sum())
        p_in_win_exact_dupes = int(p_win[ESSENTIAL_FIELDS].duplicated().sum())
        p_in_win_dupe_text = int(p_win.duplicated(subset=['review']).sum())

        # Dates coverage within usable records
        if len(p_usable) > 0:
            min_date = p_usable['parsed_day'].min()
            max_date = p_usable['parsed_day'].max()
            coverage_days = (max_date - min_date).days + 1  # Calendar days covered
            day_span = (max_date - min_date).days
            min_date_str = min_date.strftime('%Y-%m-%d')
            max_date_str = max_date.strftime('%Y-%m-%d')
        else:
            min_date_str = "N/A"
            max_date_str = "N/A"
            coverage_days = 0
            day_span = 0

        # Rating distribution across usable records
        if len(p_usable) > 0:
            rating_counts_raw = p_usable['clean_rating'].astype(int).value_counts().to_dict()
            rating_distribution = {str(r): int(rating_counts_raw.get(r, 0)) for r in range(1, 6)}
            rating_percentages = {
                str(r): f"{(rating_distribution[str(r)] / len(p_usable)) * 100:.1f}%"
                for r in range(1, 6)
            }
            mean_rating = round(float(p_usable['clean_rating'].mean()), 2)
        else:
            rating_distribution = {str(r): 0 for r in range(1, 6)}
            rating_percentages = {str(r): "0.0%" for r in range(1, 6)}
            mean_rating = 0.0

        meets_thresh = len(p_usable) >= min_threshold_per_platform

        platform_metrics[p] = {
            'role': 'Focal Company' if p == 'blinkit' else ('Primary Competitor' if p == 'zepto' else 'Secondary Context'),
            'raw_total_rows': len(p_raw),
            'window_source_rows': len(p_win),
            'out_of_window_exclusions': p_out_of_window,
            'in_window_invalid_or_missing': len(p_win) - len(p_usable),
            'usable_rows': len(p_usable),
            'missing_text_null': p_in_win_missing_text,
            'blank_text_whitespace': p_in_win_blank_text,
            'missing_rating_null': p_in_win_missing_rating,
            'invalid_rating_not_1_to_5': p_in_win_invalid_rating,
            'exact_duplicate_rows': p_in_win_exact_dupes,
            'duplicate_review_text': p_in_win_dupe_text,
            'min_date': min_date_str,
            'max_date': max_date_str,
            'calendar_days_covered': coverage_days,
            'day_span': day_span,
            'rating_distribution_counts': rating_distribution,
            'rating_distribution_percentages': rating_percentages,
            'mean_rating': mean_rating,
            'threshold_requirement': min_threshold_per_platform,
            'meets_threshold': meets_thresh
        }

    blinkit_pass = platform_metrics['blinkit']['meets_threshold']
    zepto_pass = platform_metrics['zepto']['meets_threshold']
    jiomart_pass = platform_metrics['jiomart']['meets_threshold']
    total_window_pass = total_usable_rows >= 1500

    overall_pass = blinkit_pass and zepto_pass

    return {
        'status': 'SUCCESS',
        'window_start': start_date.strftime('%Y-%m-%d'),
        'window_end': end_date.strftime('%Y-%m-%d'),
        'boundary_convention': 'inclusive (start_date <= review_date <= end_date)',
        'usable_definition': (
            "A record is usable iff it falls within the inclusive date window, "
            "has recognized platform ('blinkit', 'zepto', 'jiomart'), "
            "contains non-null non-whitespace review text, "
            "has an integer rating in range 1..5, and has a valid parseable date."
        ),
        'full_dataset_summary': full_dataset_summary,
        'common_window_summary': {
            'total_window_source_rows': total_window_source_rows,
            'total_out_of_window_exclusions': total_out_of_window_exclusions,
            'total_unparseable_date_exclusions': total_unparseable_date_exclusions,
            'total_usable_rows': total_usable_rows,
            'unknown_platform_rows_in_window': unknown_in_window_count,
            'platform_metrics': platform_metrics
        },
        'feasibility_evaluation': {
            'blinkit_usable_count': platform_metrics['blinkit']['usable_rows'],
            'blinkit_threshold': min_threshold_per_platform,
            'blinkit_meets_threshold': blinkit_pass,
            'zepto_usable_count': platform_metrics['zepto']['usable_rows'],
            'zepto_threshold': min_threshold_per_platform,
            'zepto_meets_threshold': zepto_pass,
            'jiomart_usable_count': platform_metrics['jiomart']['usable_rows'],
            'jiomart_threshold': min_threshold_per_platform,
            'jiomart_meets_threshold': jiomart_pass,
            'total_usable_count': total_usable_rows,
            'total_usable_threshold': 1500,
            'total_meets_threshold': total_window_pass,
            'overall_status': 'PASS_UNDER_AUTHORIZED_CONDITIONAL_SCOPE' if overall_pass else 'FAIL_INSUFFICIENT_VOLUME',
            'statistical_caveat': (
                "Record-count thresholds verify qualitative failure-theme feasibility. "
                "They do NOT establish statistical power or population representativeness."
            ),
            'scope_enforcement': (
                "STATIC complaint-theme and expressed-switching analysis ONLY. "
                "Temporal trend modeling and seasonality claims are strictly prohibited."
            )
        }
    }

def print_audit_report(file_path, file_sha256, file_size, audit_results):
    """Prints a structured, formatted quantitative audit report to stdout."""
    print("=" * 80)
    print("GATE 0 REMEDIATION: QUANTITATIVE DATASET AUDIT & EVIDENCE VERIFICATION")
    print(f"Target File : {file_path}")
    print(f"File Size   : {file_size:,} bytes")
    print(f"SHA-256 Hash: {file_sha256}")
    print(f"Scope Window: {audit_results['window_start']} to {audit_results['window_end']} (inclusive)")
    print(f"Boundary    : {audit_results['boundary_convention']}")
    print("=" * 80)

    full = audit_results['full_dataset_summary']
    print(f"\nTotal Records Loaded: {full['total_rows']:,}")
    print(f"Columns Found ({len(full['columns'])}): {full['columns']}")
    print("[PASS] All essential fields ('platform', 'review', 'rating', 'date') are present.")

    print("\n" + "-" * 60)
    print("PART 1: FULL DATASET BASELINE HEALTH (DISAGGREGATED COUNTS)")
    print("-" * 60)
    fh = full['field_health']
    print(f"  - Review Text: {fh['review']['missing_null']} missing null, {fh['review']['blank_whitespace']} blank whitespace ({fh['review']['valid']} valid)")
    print(f"  - Rating     : {fh['rating']['missing_null']} missing null, {fh['rating']['invalid_not_integer_1_to_5']} invalid not 1-5 ({fh['rating']['valid']} valid)")
    print(f"  - Date       : {fh['date']['missing_null']} missing null, {fh['date']['unparseable']} unparseable ({fh['date']['valid']} valid)")
    print(f"  - Platform   : {fh['platform']['missing_null']} missing null, {fh['platform']['unknown_unclassified']} unknown ({fh['platform']['recognized']} recognized)")
    print(f"  - Exact Duplicate Rows : {full['exact_duplicate_rows']} ({full['exact_duplicate_rows']/full['total_rows']*100:.2f}%)")
    print(f"  - Duplicate Review Text: {full['duplicate_review_texts']} ({full['duplicate_review_texts']/full['total_rows']*100:.2f}%)")
    print("\nFull Dataset Platform Breakdown:")
    for p, cnt in full['platform_raw_counts'].items():
        print(f"  - {p:<10}: {cnt:>5} rows")

    print("\n" + "-" * 60)
    print(f"PART 2: COMMON REVIEW WINDOW ({audit_results['window_start']} to {audit_results['window_end']}, inclusive)")
    print("-" * 60)
    win = audit_results['common_window_summary']
    print(f"Total Source Rows in Window   : {win['total_window_source_rows']:,}")
    print(f"Out-of-Window Excluded Rows   : {win['total_out_of_window_exclusions']:,}")
    print(f"Unparseable Date Excluded Rows: {win['total_unparseable_date_exclusions']:,}")
    print(f"Total Usable Records in Window: {win['total_usable_rows']:,}")

    pm = win['platform_metrics']
    for p in ['blinkit', 'zepto', 'jiomart']:
        m = pm[p]
        print(f"\n[{p.upper()}] — {m['role']}")
        print(f"  - Full Dataset Raw Rows        : {m['raw_total_rows']:,}")
        print(f"  - Common Window Source Rows    : {m['window_source_rows']:,}")
        print(f"  - Excluded (Out of Window)     : {m['out_of_window_exclusions']:,}")
        print(f"  - In-Window Quality Exclusions : {m['in_window_invalid_or_missing']:,}")
        print(f"  - Fully Usable Records         : {m['usable_rows']:,}")
        print(f"  - Missing Text (Null)          : {m['missing_text_null']}")
        print(f"  - Blank Text (Whitespace)      : {m['blank_text_whitespace']}")
        print(f"  - Missing Ratings              : {m['missing_rating_null']}")
        print(f"  - Invalid Ratings (Not 1..5)   : {m['invalid_rating_not_1_to_5']}")
        print(f"  - Exact Duplicate Rows         : {m['exact_duplicate_rows']}")
        print(f"  - Duplicate Review Text        : {m['duplicate_review_text']}")
        print(f"  - Actual Date Coverage         : {m['min_date']} to {m['max_date']} ({m['calendar_days_covered']} calendar days, {m['day_span']} day span)")
        print(f"  - Threshold Check (>= {m['threshold_requirement']})    : {'[PASS]' if m['meets_threshold'] else '[FAIL]'}")

    print("\n" + "-" * 60)
    print("RATING DISTRIBUTIONS IN COMMON WINDOW (USABLE RECORDS)")
    print("-" * 60)
    for p in ['blinkit', 'zepto', 'jiomart']:
        m = pm[p]
        print(f"  - {p:<10} (Mean={m['mean_rating']:.2f}): Counts {m['rating_distribution_counts']} | Pcts {m['rating_distribution_percentages']}")

    eval_sec = audit_results['feasibility_evaluation']
    print("\n" + "=" * 80)
    print("GATE 0 FEASIBILITY THRESHOLD EVALUATION")
    print("=" * 80)
    print(f"1. Focal Company (Blinkit) Usable Records (>= 500)    : {eval_sec['blinkit_usable_count']:,} [{'PASS' if eval_sec['blinkit_meets_threshold'] else 'FAIL'}]")
    print(f"2. Primary Competitor (Zepto) Usable Records (>= 500)  : {eval_sec['zepto_usable_count']:,} [{'PASS' if eval_sec['zepto_meets_threshold'] else 'FAIL'}]")
    print(f"3. Secondary Context (JioMart) Usable Records (>= 500) : {eval_sec['jiomart_usable_count']:,} [{'PASS' if eval_sec['jiomart_meets_threshold'] else 'FAIL'}]")
    print(f"4. Total Common-Window Usable Volume (>= 1,500)        : {eval_sec['total_usable_count']:,} [{'PASS' if eval_sec['total_meets_threshold'] else 'FAIL'}]")
    print("\n[METHODOLOGICAL CAVEATS]")
    print(f"  - {eval_sec['statistical_caveat']}")
    print(f"  - {eval_sec['scope_enforcement']}")
    print("-" * 80)
    print(f"OVERALL FEASIBILITY AUDIT STATUS: {eval_sec['overall_status']}")
    print("=" * 80)

def run_audit(file_path, window_start_str, window_end_str, output_json=None, no_output=False):
    """Coordinates reading data, computing hash, auditing, printing, and saving JSON."""
    file_sha256 = compute_file_sha256(file_path)
    file_size = os.path.getsize(file_path)

    start_date, end_date = validate_date_window(window_start_str, window_end_str)

    try:
        df = pd.read_csv(file_path)
    except Exception as e:
        sys.stderr.write(f"\n[FATAL ERROR] Could not read CSV file '{file_path}': {e}\n")
        sys.exit(1)

    results = audit_dataframe(df, start_date, end_date)
    if results.get('status') == 'FAILED_SCHEMA':
        sys.stderr.write(f"\n[FATAL ERROR] {results['error']}\n")
        sys.exit(1)

    # Attach file metadata
    results['input_file_path'] = os.path.relpath(file_path, os.getcwd()) if os.path.isabs(file_path) else file_path
    results['input_file_sha256'] = file_sha256
    results['input_file_size_bytes'] = file_size
    results['audit_timestamp_utc'] = datetime.now(timezone.utc).isoformat()

    print_audit_report(results['input_file_path'], file_sha256, file_size, results)

    if not no_output and output_json:
        out_dir = os.path.dirname(output_json)
        if out_dir and not os.path.exists(out_dir):
            os.makedirs(out_dir, exist_ok=True)
        with open(output_json, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)
        print(f"\n[OUTPUT] Saved aggregate machine-readable audit summary to: {output_json}")

    return results

def main():
    args = parse_arguments()
    data_path = resolve_dataset_path(args.file)
    output_path = None if args.no_output else args.output
    run_audit(
        file_path=data_path,
        window_start_str=args.window_start,
        window_end_str=args.window_end,
        output_json=output_path,
        no_output=args.no_output
    )

if __name__ == "__main__":
    main()
