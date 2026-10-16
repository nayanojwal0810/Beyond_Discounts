#!/usr/bin/env python3
"""
scripts/audit_data.py

Reproducible quantitative data audit script for Gate 0.
Audits candidate review datasets for:
- Essential field validation (platform, review, rating, date)
- Missingness, blank text, exact duplicates, and near-duplicates
- Platform representation and row counts (raw vs usable)
- Date parsing, temporal coverage, and platform-level date alignment
- Rating and sentiment distributions
- Text length metrics (character and word count distributions)
- Project feasibility threshold checks (Target vs Minimum thresholds)

Usage:
    python scripts/audit_data.py [--file PATH_TO_CSV]
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

def parse_arguments():
    parser = argparse.ArgumentParser(description="Audit quick-commerce review dataset for Gate 0.")
    parser.add_argument(
        "--file",
        type=str,
        default=None,
        help="Path to CSV dataset to audit. If omitted, checks standard local paths or Candidate A cache."
    )
    return parser.parse_args()

def find_dataset(file_arg):
    if file_arg and os.path.exists(file_arg):
        return file_arg
    
    # Check standard project paths
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

def run_audit(file_path):
    print("=" * 80)
    print("GATE 0 QUANTITATIVE DATASET AUDIT")
    print(f"Target File: {file_path}")
    print(f"File Size: {os.path.getsize(file_path):,} bytes")
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

    # 2. Missingness Audit
    print("\n" + "-" * 40)
    print("1. FIELD COMPLETENESS & MISSINGNESS")
    print("-" * 40)
    for col in df.columns:
        n_missing = df[col].isna().sum()
        pct_missing = (n_missing / len(df)) * 100
        print(f"  - {col:<12}: {n_missing:>5} missing ({pct_missing:>5.2f}%)")

    # 3. Blank / Whitespace Text
    blank_mask = df['review'].apply(lambda x: len(str(x).strip()) == 0 or str(x).lower() == 'nan')
    n_blank = blank_mask.sum()
    pct_blank = (n_blank / len(df)) * 100
    print(f"  - Blank/Whitespace Text: {n_blank} ({pct_blank:.2f}%)")

    # 4. Duplication Analysis
    print("\n" + "-" * 40)
    print("2. DUPLICATION ANALYSIS")
    print("-" * 40)
    exact_all = df.duplicated().sum()
    exact_text_plat = df.duplicated(subset=['platform', 'review']).sum()
    exact_text_only = df.duplicated(subset=['review']).sum()

    df['norm_review'] = df['review'].apply(normalize_text_for_dedup)
    near_dupes = df.duplicated(subset=['platform', 'norm_review']).sum()

    print(f"  - Exact Duplicate Rows (all columns)   : {exact_all:>5} ({exact_all/len(df)*100:>5.2f}%)")
    print(f"  - Exact Duplicate Review Text (platform): {exact_text_plat:>5} ({exact_text_plat/len(df)*100:>5.2f}%)")
    print(f"  - Exact Duplicate Review Text (cross)   : {exact_text_only:>5} ({exact_text_only/len(df)*100:>5.2f}%)")
    print(f"  - Near-Duplicate Review Text (platform) : {near_dupes:>5} ({near_dupes/len(df)*100:>5.2f}%)")

    # 5. Platform Breakdown & Usability
    print("\n" + "-" * 40)
    print("3. PLATFORM USABILITY & ROW COUNTS")
    print("-" * 40)
    usable_mask = (~df['review'].isna()) & (~blank_mask)
    platforms = df['platform'].str.lower().unique()

    platform_summary = []
    for p in platforms:
        p_total = (df['platform'].str.lower() == p).sum()
        p_usable = ((df['platform'].str.lower() == p) & usable_mask).sum()
        p_unique_text = df[df['platform'].str.lower() == p]['review'].nunique()
        platform_summary.append({
            'platform': p,
            'total': p_total,
            'usable': p_usable,
            'unique_text': p_unique_text
        })
        print(f"  - {p:<12}: Total={p_total:>5}, Usable={p_usable:>5}, Unique Text={p_unique_text:>5}")

    # 6. Temporal Coverage & Date Parsing
    print("\n" + "-" * 40)
    print("4. TEMPORAL COVERAGE & DATE ALIGNMENT")
    print("-" * 40)
    df['parsed_date'] = pd.to_datetime(df['date'], format='%d %B %Y', errors='coerce')
    if df['parsed_date'].isna().all():
        df['parsed_date'] = pd.to_datetime(df['date'], errors='coerce')

    n_bad_date = df['parsed_date'].isna().sum()
    print(f"  - Unparseable Dates: {n_bad_date} ({n_bad_date/len(df)*100:.2f}%)")

    for p in platforms:
        sub = df[df['platform'].str.lower() == p]
        d_min = sub['parsed_date'].min()
        d_max = sub['parsed_date'].max()
        if pd.notna(d_min) and pd.notna(d_max):
            span_days = (d_max - d_min).days
            span_months = span_days / 30.4375
            print(f"  - {p:<12}: {d_min.strftime('%Y-%m-%d')} to {d_max.strftime('%Y-%m-%d')} ({span_days:>4} days, ~{span_months:>4.1f} months)")
        else:
            print(f"  - {p:<12}: Date parsing failed or no dates available.")

    # 7. Rating Distribution
    print("\n" + "-" * 40)
    print("5. RATING DISTRIBUTION BY PLATFORM")
    print("-" * 40)
    for p in platforms:
        sub = df[df['platform'].str.lower() == p]
        counts = sub['rating'].value_counts().sort_index().to_dict()
        mean_val = sub['rating'].mean()
        pcts = {k: f"{(v/len(sub))*100:.1f}%" for k, v in counts.items()}
        print(f"  - {p:<12} (Mean={mean_val:.2f}): {counts} | {pcts}")

    overall_counts = df['rating'].value_counts().sort_index().to_dict()
    overall_pcts = {k: f"{(v/len(df))*100:.1f}%" for k, v in overall_counts.items()}
    print(f"  - OVERALL      (Mean={df['rating'].mean():.2f}): {overall_counts} | {overall_pcts}")

    # 8. Text Length Distribution
    print("\n" + "-" * 40)
    print("6. TEXT LENGTH DISTRIBUTION (WORDS & CHARACTERS)")
    print("-" * 40)
    df['char_count'] = df['review'].astype(str).str.len()
    df['word_count'] = df['review'].astype(str).str.split().str.len()

    for p in platforms:
        sub = df[df['platform'].str.lower() == p]
        print(f"  - {p:<12}: Words [Min={sub['word_count'].min()}, Median={sub['word_count'].median():.0f}, Mean={sub['word_count'].mean():.1f}, Max={sub['word_count'].max()}] | "
              f"Chars [Min={sub['char_count'].min()}, Median={sub['char_count'].median():.0f}, Mean={sub['char_count'].mean():.1f}, Max={sub['char_count'].max()}]")

    # 9. Feasibility Threshold Check
    print("\n" + "=" * 80)
    print("FEASIBILITY THRESHOLD EVALUATION")
    print("=" * 80)
    total_usable = usable_mask.sum()
    print(f"Total Usable Records: {total_usable:,}")
    print("Target Threshold  : >= 3,000 total, >= 1,000 per platform, >= 12 months coverage")
    print("Minimum Threshold : >= 1,500 total, >=   500 per platform, >=  6 months coverage")
    print("Required Platforms: Blinkit, Zepto, Swiggy Instamart")
    print("-" * 80)

    # Check overall count
    pass_total_target = total_usable >= 3000
    pass_total_min = total_usable >= 1500
    print(f"Total Count Check    : Target [ {'PASS' if pass_total_target else 'FAIL'} ] | Minimum [ {'PASS' if pass_total_min else 'FAIL'} ]")

    # Check platforms
    req_platforms = {'blinkit', 'zepto', 'swiggy instamart'}
    present_platforms = set(p.lower() for p in platforms)
    missing_platforms = req_platforms - present_platforms
    extra_platforms = present_platforms - req_platforms

    print(f"Platform Scope Check : Present={sorted(list(present_platforms))}")
    if missing_platforms:
        print(f"                       MISSING REQUIRED PLATFORMS: {sorted(list(missing_platforms))}")
    if extra_platforms:
        print(f"                       UNEXPECTED EXTRA PLATFORMS: {sorted(list(extra_platforms))}")

    # Check temporal threshold
    sub_b = df[df['platform'].str.lower() == 'blinkit']
    sub_z = df[df['platform'].str.lower() == 'zepto']
    b_days = (sub_b['parsed_date'].max() - sub_b['parsed_date'].min()).days if len(sub_b) else 0
    z_days = (sub_z['parsed_date'].max() - sub_z['parsed_date'].min()).days if len(sub_z) else 0

    pass_temporal_min = (b_days >= 180) and (z_days >= 180)
    print(f"Temporal Check (>=180d): Blinkit={b_days}d ({'PASS' if b_days>=180 else 'FAIL'}), Zepto={z_days}d ({'z_days' if z_days>=180 else 'FAIL'})")

    print("\n" + "=" * 80)
    if not missing_platforms and pass_total_target and pass_temporal_min:
        print("OVERALL GATE 0 DATA STATUS: PASS")
    elif pass_total_min and (missing_platforms or not pass_temporal_min):
        print("OVERALL GATE 0 DATA STATUS: CONDITIONAL PASS (Requires Scope/Platform Resolution)")
    else:
        print("OVERALL GATE 0 DATA STATUS: FAIL")
    print("=" * 80)

def main():
    args = parse_arguments()
    data_path = find_dataset(args.file)
    if not data_path:
        print("\n[ERROR] No candidate dataset found to audit.")
        print("Please provide a dataset path using --file PATH_TO_CSV.")
        sys.exit(1)
    run_audit(data_path)

if __name__ == "__main__":
    main()
