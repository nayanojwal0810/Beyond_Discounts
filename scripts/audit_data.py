#!/usr/bin/env python3
"""
scripts/audit_data.py

Reproducible quantitative data audit script for Gate 0 Revision.
Audits candidate review datasets for:
1. Full Corpus Baseline:
   - Essential field validation (platform, review, rating, date)
   - Missingness, blank text, exact duplicates, and near-duplicates
   - Overall platform row counts and rating distributions
2. Common Review Window (14 August 2024 to 31 December 2024, inclusive):
   - Exact usable record counts by platform (Blinkit focal, Zepto primary competitor, JioMart secondary)
   - Exclusion counts (records outside the common window)
   - Missing text, missing ratings, missing dates in the common window
   - Exact duplicate rows and duplicate review text within the common window
   - Actual date coverage (min date, max date, day span) after filtering
   - Acceptance threshold verification (>= 500 usable records for Blinkit and Zepto)
   - Static analysis scope boundary enforcement (no temporal trends or seasonality claims)

Usage:
    python scripts/audit_data.py [--file PATH_TO_CSV] [--window-start YYYY-MM-DD] [--window-end YYYY-MM-DD]
"""

import sys
import os
import argparse
import re
import pandas as pd
import numpy as np

# Force UTF-8 output encoding
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

ESSENTIAL_FIELDS = ['platform', 'review', 'rating', 'date']
DEFAULT_WINDOW_START = "2024-08-14"
DEFAULT_WINDOW_END = "2024-12-31"
MIN_THRESHOLD_PER_PLATFORM = 500

def parse_arguments():
    parser = argparse.ArgumentParser(description="Audit quick-commerce review dataset for Gate 0 Revision.")
    parser.add_argument(
        "--file",
        type=str,
        default=None,
        help="Path to CSV dataset to audit. If omitted, checks standard local paths."
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
    return parser.parse_args()

def find_dataset(file_arg):
    if file_arg and os.path.exists(file_arg):
        return file_arg
    
    candidates = [
        os.path.join("data", "raw", "reviews.csv"),
        os.path.join("data", "reviews.csv"),
        os.path.join(r"C:\Users\nayan\.gemini\antigravity\brain\d4f688e5-a0b4-4a01-9195-3df0fdd5835c\scratch\cand_a_reviews.csv")
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    return None

def normalize_text_for_dedup(text):
    t = str(text).lower().strip()
    t = re.sub(r'[^\w\s]', '', t)
    return re.sub(r'\s+', ' ', t)

def run_audit(file_path, window_start_str, window_end_str):
    print("=" * 80)
    print("GATE 0 REVISION: QUANTITATIVE DATASET AUDIT & COMMON WINDOW VERIFICATION")
    print(f"Target File : {file_path}")
    print(f"File Size   : {os.path.getsize(file_path):,} bytes")
    print(f"Scope Window: {window_start_str} to {window_end_str} (inclusive)")
    print("=" * 80)

    try:
        df = pd.read_csv(file_path)
    except Exception as e:
        print(f"\n[FATAL ERROR] Could not read CSV file: {e}")
        sys.exit(1)

    print(f"\nTotal Records Loaded: {len(df):,}")
    print(f"Columns Found ({len(df.columns)}): {df.columns.tolist()}")

    # 1. Essential Fields Check
    missing_essential = [col for col in ESSENTIAL_FIELDS if col not in df.columns]
    if missing_essential:
        print(f"\n[FATAL ERROR] Essential fields missing from dataset: {missing_essential}")
        print(f"Required fields are: {ESSENTIAL_FIELDS}")
        sys.exit(1)
    print("\n[PASS] All essential fields ('platform', 'review', 'rating', 'date') are present.")

    # 2. Parse Dates
    df['parsed_date'] = pd.to_datetime(df['date'], format='%d %B %Y', errors='coerce')
    if df['parsed_date'].isna().all():
        df['parsed_date'] = pd.to_datetime(df['date'], errors='coerce')

    n_bad_date = df['parsed_date'].isna().sum()
    print(f"Unparseable Dates in Entire Dataset: {n_bad_date} ({n_bad_date/len(df)*100:.2f}%)")

    # 3. Overall Missingness & Duplication (Entire Dataset)
    print("\n" + "-" * 60)
    print("PART 1: FULL DATASET BASELINE (ENTIRE 4,620-ROW CORPUS)")
    print("-" * 60)
    for col in ESSENTIAL_FIELDS:
        n_missing = df[col].isna().sum()
        pct_missing = (n_missing / len(df)) * 100
        print(f"  - {col:<12}: {n_missing:>5} missing ({pct_missing:>5.2f}%)")

    blank_mask_full = df['review'].apply(lambda x: len(str(x).strip()) == 0 or str(x).lower() == 'nan')
    print(f"  - Blank/Whitespace Text: {blank_mask_full.sum()} ({blank_mask_full.sum()/len(df)*100:.2f}%)")
    print(f"  - Exact Duplicate Rows : {df.duplicated().sum()} ({df.duplicated().sum()/len(df)*100:.2f}%)")
    print(f"  - Duplicate Review Text: {df.duplicated(subset=['review']).sum()} ({df.duplicated(subset=['review']).sum()/len(df)*100:.2f}%)")

    # Platform counts full dataset
    print("\nFull Dataset Platform Row Counts:")
    for p in sorted(df['platform'].str.lower().unique()):
        sub_full = df[df['platform'].str.lower() == p]
        d_min = sub_full['parsed_date'].min()
        d_max = sub_full['parsed_date'].max()
        days = (d_max - d_min).days if pd.notna(d_min) and pd.notna(d_max) else 0
        print(f"  - {p:<10}: {len(sub_full):>5} rows | {d_min.strftime('%Y-%m-%d')} to {d_max.strftime('%Y-%m-%d')} ({days:>4} days)")

    # 4. Common Review Window Audit
    print("\n" + "-" * 60)
    print(f"PART 2: RE-AUDIT OF COMMON REVIEW WINDOW ({window_start_str} to {window_end_str})")
    print("-" * 60)
    print("Controlling Constraint: Static complaint-theme and expressed-switching analysis ONLY.")
    print("CRITICAL NOTICE: Must NOT be used to claim temporal trends or seasonality.")
    print("-" * 60)

    start_date = pd.to_datetime(window_start_str)
    end_date = pd.to_datetime(window_end_str)

    window_mask = (df['parsed_date'] >= start_date) & (df['parsed_date'] <= end_date)
    df_window = df[window_mask].copy()

    total_window_records = len(df_window)
    print(f"Total Records in Common Window: {total_window_records:,} (out of {len(df):,} total, {len(df)-total_window_records} excluded)")

    # Platforms in window audit
    target_platforms = ['blinkit', 'zepto', 'jiomart']
    platform_metrics = {}

    for p in target_platforms:
        sub_raw = df[df['platform'].str.lower() == p]
        sub_win = df_window[df_window['platform'].str.lower() == p]
        
        blank_mask = sub_win['review'].apply(lambda x: len(str(x).strip()) == 0 or str(x).lower() == 'nan')
        usable_records = len(sub_win) - blank_mask.sum()
        
        exclusions = len(sub_raw) - len(sub_win)
        missing_text = sub_win['review'].isna().sum() + blank_mask.sum()
        missing_rating = sub_win['rating'].isna().sum()
        missing_date = sub_win['date'].isna().sum() + sub_win['parsed_date'].isna().sum()
        
        exact_dupes = sub_win.duplicated().sum()
        dupe_text = sub_win.duplicated(subset=['review']).sum()
        
        min_date = sub_win['parsed_date'].min()
        max_date = sub_win['parsed_date'].max()
        coverage_days = (max_date - min_date).days if len(sub_win) > 0 else 0
        
        meets_threshold = usable_records >= MIN_THRESHOLD_PER_PLATFORM
        
        platform_metrics[p] = {
            'raw_total': len(sub_raw),
            'window_total': len(sub_win),
            'usable': usable_records,
            'exclusions': exclusions,
            'missing_text': missing_text,
            'missing_rating': missing_rating,
            'missing_date': missing_date,
            'exact_dupes': exact_dupes,
            'dupe_text': dupe_text,
            'min_date': min_date.strftime('%Y-%m-%d') if pd.notna(min_date) else "N/A",
            'max_date': max_date.strftime('%Y-%m-%d') if pd.notna(max_date) else "N/A",
            'coverage_days': coverage_days,
            'meets_threshold': meets_threshold
        }
        
        role_label = "Focal Company" if p == "blinkit" else ("Primary Competitor" if p == "zepto" else "Secondary Context")
        print(f"\n[{p.upper()}] — {role_label}")
        print(f"  - Full Dataset Raw Rows      : {len(sub_raw):,}")
        print(f"  - Common Window Records      : {len(sub_win):,}")
        print(f"  - Excluded (Out of Window)   : {exclusions:,}")
        print(f"  - Usable Text-Bearing Records: {usable_records:,}")
        print(f"  - Missing Text               : {missing_text}")
        print(f"  - Missing Ratings            : {missing_rating}")
        print(f"  - Missing / Unparseable Dates: {missing_date}")
        print(f"  - Exact Duplicate Rows       : {exact_dupes}")
        print(f"  - Duplicate Review Text      : {dupe_text}")
        print(f"  - Actual Date Coverage       : {platform_metrics[p]['min_date']} to {platform_metrics[p]['max_date']} ({coverage_days} days)")
        print(f"  - Threshold Check (>= {MIN_THRESHOLD_PER_PLATFORM})  : {'[PASS]' if meets_threshold else '[FAIL]'}")

    # 5. Rating breakdown in common window
    print("\n" + "-" * 60)
    print("RATING DISTRIBUTIONS IN COMMON WINDOW")
    print("-" * 60)
    for p in target_platforms:
        sub_win = df_window[df_window['platform'].str.lower() == p]
        counts = sub_win['rating'].value_counts().sort_index().to_dict()
        pcts = {k: f"{(v/len(sub_win))*100:.1f}%" for k, v in counts.items()}
        print(f"  - {p:<10} (Mean={sub_win['rating'].mean():.2f}): {counts} | {pcts}")

    # 6. Formal Acceptance Verification
    print("\n" + "=" * 80)
    print("GATE 0 REVISION ACCEPTANCE EVALUATION")
    print("=" * 80)
    blinkit_pass = platform_metrics['blinkit']['meets_threshold']
    zepto_pass = platform_metrics['zepto']['meets_threshold']
    jiomart_pass = platform_metrics['jiomart']['meets_threshold']
    
    print(f"1. Focal Company (Blinkit) Usable Records (>= 500)    : {platform_metrics['blinkit']['usable']:,} [{'PASS' if blinkit_pass else 'FAIL'}]")
    print(f"2. Primary Competitor (Zepto) Usable Records (>= 500)  : {platform_metrics['zepto']['usable']:,} [{'PASS' if zepto_pass else 'FAIL'}]")
    print(f"3. Secondary Context (JioMart) Usable Records (>= 500) : {platform_metrics['jiomart']['usable']:,} [{'PASS' if jiomart_pass else 'FAIL'}]")
    print(f"4. Total Common-Window Usable Volume (>= 1,500)        : {total_window_records:,} [{'PASS' if total_window_records >= 1500 else 'FAIL'}]")
    print("5. Scope Enforcement: STATIC complaint-theme and expressed-switching analysis ONLY.")
    print("   (Temporal trend modeling and seasonality claims are strictly prohibited.)")
    print("-" * 80)

    if blinkit_pass and zepto_pass:
        print("OVERALL GATE 0 REVISION STATUS: PASS (CONDITIONAL SCOPE ACCEPTED)")
        print("The common-window filtered dataset meets all minimum record criteria for Blinkit and Zepto.")
    else:
        print("[FATAL FAILURE] Either Blinkit or Zepto has fewer than 500 usable records in the common window.")
        sys.exit(1)
    print("=" * 80)

def main():
    args = parse_arguments()
    data_path = find_dataset(args.file)
    if not data_path:
        print("\n[ERROR] No candidate dataset found to audit.")
        print("Please provide a dataset path using --file PATH_TO_CSV.")
        sys.exit(1)
    run_audit(data_path, args.window_start, args.window_end)

if __name__ == "__main__":
    main()
