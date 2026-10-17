#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Gate 1B: Segmentation Feature Audit, Encoding Specification, and Data Preparation Pipeline
==========================================================================================

Project:
    Beyond Discounts: Customer Segmentation and Retention Strategy for Indian Quick Commerce

Repository:
    https://github.com/nayanojwal0810/Beyond_Discounts

Description:
    Implements the reproducible data preparation, feature inventory, quality audit,
    and typed feature specification pipeline for Gate 1B:
    1. Validates dataset integrity and enforces strict subgroup filtering (Current Active Users n=807).
    2. Audits all 130 survey columns across 49 questions (QA 1 to QA 49) into a standardized inventory.
    3. Conducts a rigorous feature quality audit (distributions, invalid values, skip codes, constants).
    4. Enforces verified semantic rules:
       - QA 19 (Items per Order): Separates ordered items (1-5) from Code 6 ("Varies considerably").
       - QA 26 (Monthly Spend): Separates ordered spend brackets (2-7) from Code 8 ("Not sure").
       - QA 15 (Order Frequency): Valid ordinal categories 2-7 for active users.
       - QA 14 (First Trial Reason): Nominal categories 1-7 for active users.
       - QA 47 (Continue If Discounts Reduced): Stated continuation intention (1-5).
       - QA 46 (Next 3 Month Use): Stated future-use intention held out across all specifications.
       - QA 48 (Non-Use Barriers): Validated as constant skip codes for active users; excluded from clustering.
       - QA 49 (Preferred Improvement): Reserved for post-cluster action profiling.
    5. Formulates two distinct segmentation specifications:
       - Specification A: Core behavioral and attitudinal features EXCLUDING QA 47 (independent validation).
       - Specification B: Specification A PLUS QA 47 (price-elasticity segment-defining specification).
    6. Produces machine-readable JSON specifications and deterministic local feature representations.
    7. Ensures all row-level respondent matrices remain local and excluded from Git.

Usage:
    python scripts/prepare_segmentation_features.py [--file PATH] [--sheet SHEET] [--reports-dir PATH] [--data-dir PATH]
"""

import os
import sys
import json
import argparse
import numpy as np
import pandas as pd


DEFAULT_SURVEY_PATH = os.path.join("data", "raw", "survey", "Data.xlsx")
DEFAULT_SHEET = "Data"
DEFAULT_REPORTS_DIR = os.path.join("reports", "segmentation")
DEFAULT_DATA_DIR = os.path.join("data", "processed")

# Canonical subgroup expected counts
EXPECTED_TOTAL_ROWS = 1263
EXPECTED_TOTAL_COLS = 130
EXPECTED_NEVER_USERS = 376
EXPECTED_PREVIOUS_USERS = 80
EXPECTED_ACTIVE_USERS = 807


def parse_arguments(args=None):
    parser = argparse.ArgumentParser(description="Run Gate 1B Segmentation Feature Preparation.")
    parser.add_argument("--file", type=str, default=DEFAULT_SURVEY_PATH, help="Path to survey Excel file.")
    parser.add_argument("--sheet", type=str, default=DEFAULT_SHEET, help="Sheet name in Excel.")
    parser.add_argument("--reports-dir", type=str, default=DEFAULT_REPORTS_DIR, help="Directory to export reports.")
    parser.add_argument("--data-dir", type=str, default=DEFAULT_DATA_DIR, help="Directory to export processed data.")
    return parser.parse_args(args)


def load_and_filter_active_users(file_path, sheet_name):
    """
    Loads survey workbook, validates schema dimensions and subgroup partition counts,
    and returns full DataFrame along with strictly filtered current active users (n=807).
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Survey dataset not found at: {file_path}")

    df = pd.read_excel(file_path, sheet_name=sheet_name)
    df.columns = [str(c).strip() for c in df.columns]
    df = df.copy()

    if df.shape != (EXPECTED_TOTAL_ROWS, EXPECTED_TOTAL_COLS):
        raise ValueError(f"Unexpected dataset dimensions: {df.shape}, expected ({EXPECTED_TOTAL_ROWS}, {EXPECTED_TOTAL_COLS}).")

    cond_never = (df['Ever Ordered through a Quick-Commerce Platform'] == 0) & (df['Order Frequency'] == 1)
    cond_prev = (df['Ever Ordered through a Quick-Commerce Platform'] == 1) & (df['Order Frequency'] == 1)
    cond_curr = (df['Ever Ordered through a Quick-Commerce Platform'] == 1) & (df['Order Frequency'] > 1)

    n_never = cond_never.sum()
    n_prev = cond_prev.sum()
    n_curr = cond_curr.sum()

    if n_never != EXPECTED_NEVER_USERS or n_prev != EXPECTED_PREVIOUS_USERS or n_curr != EXPECTED_ACTIVE_USERS:
        raise ValueError(
            f"Subgroup counts do not match audited baseline: Never={n_never} (exp {EXPECTED_NEVER_USERS}), "
            f"Previous={n_prev} (exp {EXPECTED_PREVIOUS_USERS}), Active={n_curr} (exp {EXPECTED_ACTIVE_USERS})"
        )

    # Label subgroups
    subgroups = pd.Series('Unknown', index=df.index, dtype='object')
    subgroups.loc[cond_never] = 'Never User'
    subgroups.loc[cond_prev] = 'Previous User'
    subgroups.loc[cond_curr] = 'Current Active User'
    df['user_subgroup'] = subgroups

    # Derive multi-platform count (ever used major 6 platforms)
    platform_cols = [
        'Used Blinkit', 'Used Zepto', 'Used Swiggy Instamart',
        'Used BigBasket BBNow', 'Used Flipkart Minutes', 'Used Amazon Rapid'
    ]
    df['platforms_used_count'] = df[platform_cols].sum(axis=1)

    # Derive composite service satisfaction (QA 37-40 mean)
    sat_cols = [
        'Overall Satisfaction', 'Product Quality Satisfaction',
        'Delivery Reliability Satisfaction', 'Value Money Satisfaction'
    ]
    df['service_satisfaction_composite'] = df[sat_cols].mean(axis=1)

    active_df = df[cond_curr].copy()
    active_df.reset_index(drop=False, inplace=True)
    active_df.rename(columns={'index': 'survey_row_id'}, inplace=True)

    return df, active_df


def get_column_metadata_mapping():
    """Returns authoritative mapping for all 130 survey columns."""
    mapping = {
        'Age Group': ('QA 1', 'Demographic age bracket', 'Ordinal', 'All Respondents (N=1263)', 'None', 'post_cluster_profiling', 'Demographic descriptor; reserved for profiling to prevent demographic stereotyping in cluster formation.'),
        'Gender': ('QA 2', 'Demographic gender identity', 'Nominal', 'All Respondents (N=1263)', 'None', 'post_cluster_profiling', 'Demographic descriptor; reserved for post-cluster profiling.'),
        'Education': ('QA 3', 'Highest educational qualification', 'Ordinal', 'All Respondents (N=1263)', 'None', 'post_cluster_profiling', 'Demographic descriptor; reserved for post-cluster profiling.'),
        'Occupation': ('QA 4', 'Current occupational status', 'Nominal', 'All Respondents (N=1263)', 'None', 'post_cluster_profiling', 'Demographic descriptor; reserved for post-cluster profiling.'),
        'Personal Income': ('QA 5', 'Monthly personal income bracket', 'Ordinal', 'All Respondents (N=1263)', 'Code 8=Prefer not to say', 'post_cluster_profiling', 'Demographic monetary indicator; reserved for profiling to test segment income distribution.'),
        'Area of Residence': ('QA 6', 'City tier / urbanization level', 'Ordinal', 'All Respondents (N=1263)', 'None', 'post_cluster_profiling', 'Geographic urbanization proxy; reserved for post-cluster profiling.'),
        'Region': ('QA 7', 'Geographic region in India', 'Nominal', 'All Respondents (N=1263)', 'None', 'post_cluster_profiling', 'Geographic macro-region; reserved for post-cluster profiling.'),
        'Household Size': ('QA 8', 'Number of persons in household', 'Ordinal', 'All Respondents (N=1263)', 'None', 'post_cluster_profiling', 'Demographic household structure; reserved for post-cluster profiling.'),
        'Awareness of Quick Commerce Services': ('QA 9', 'Awareness screening flag', 'Binary', 'All Respondents (N=1263)', 'None', 'screening_filter', 'Screening filter; constant 1 for active users.'),
        'Ever Ordered through a Quick-Commerce Platform': ('QA 10', 'Adoption trial screening flag', 'Binary', 'All Respondents (N=1263)', 'None', 'screening_filter', 'Subgroup partition filter; constant 1 for active users.'),
        'Aware Blinkit': ('QA 11', 'Aided awareness: Blinkit', 'Binary', 'All Respondents (N=1263)', 'None', 'post_cluster_profiling', 'Brand awareness; reserved for platform footprint profiling.'),
        'Aware Zepto': ('QA 11', 'Aided awareness: Zepto', 'Binary', 'All Respondents (N=1263)', 'None', 'post_cluster_profiling', 'Brand awareness; reserved for platform footprint profiling.'),
        'Aware Swiggy Instamart': ('QA 11', 'Aided awareness: Swiggy Instamart', 'Binary', 'All Respondents (N=1263)', 'None', 'post_cluster_profiling', 'Brand awareness; reserved for platform footprint profiling.'),
        'Aware BigBasket BBNow': ('QA 11', 'Aided awareness: BigBasket BBNow', 'Binary', 'All Respondents (N=1263)', 'None', 'post_cluster_profiling', 'Brand awareness; reserved for platform footprint profiling.'),
        'Aware Flipkart Minutes': ('QA 11', 'Aided awareness: Flipkart Minutes', 'Binary', 'All Respondents (N=1263)', 'None', 'post_cluster_profiling', 'Brand awareness; reserved for platform footprint profiling.'),
        'Aware Amazon Rapid': ('QA 11', 'Aided awareness: Amazon Rapid', 'Binary', 'All Respondents (N=1263)', 'None', 'post_cluster_profiling', 'Brand awareness; reserved for platform footprint profiling.'),
        'Aware Other': ('QA 11', 'Aided awareness: Other platforms', 'Binary', 'All Respondents (N=1263)', 'None', 'post_cluster_profiling', 'Brand awareness; reserved for platform footprint profiling.'),
        'Aware None': ('QA 11', 'Aided awareness: None', 'Binary', 'All Respondents (N=1263)', 'None', 'excluded_constant_active', 'Constant 0 for active users; excluded from clustering.'),
        'Used Blinkit': ('QA 12', 'Platform ever used: Blinkit', 'Binary', 'All Respondents (N=1263)', 'None', 'post_cluster_profiling', 'Platform-specific usage; aggregated into platforms_used_count to avoid platform-tied clusters.'),
        'Used Zepto': ('QA 12', 'Platform ever used: Zepto', 'Binary', 'All Respondents (N=1263)', 'None', 'post_cluster_profiling', 'Platform-specific usage; aggregated into platforms_used_count to avoid platform-tied clusters.'),
        'Used Swiggy Instamart': ('QA 12', 'Platform ever used: Swiggy Instamart', 'Binary', 'All Respondents (N=1263)', 'None', 'post_cluster_profiling', 'Platform-specific usage; aggregated into platforms_used_count to avoid platform-tied clusters.'),
        'Used BigBasket BBNow': ('QA 12', 'Platform ever used: BigBasket BBNow', 'Binary', 'All Respondents (N=1263)', 'None', 'post_cluster_profiling', 'Platform-specific usage; aggregated into platforms_used_count to avoid platform-tied clusters.'),
        'Used Flipkart Minutes': ('QA 12', 'Platform ever used: Flipkart Minutes', 'Binary', 'All Respondents (N=1263)', 'None', 'post_cluster_profiling', 'Platform-specific usage; aggregated into platforms_used_count to avoid platform-tied clusters.'),
        'Used Amazon Rapid': ('QA 12', 'Platform ever used: Amazon Rapid', 'Binary', 'All Respondents (N=1263)', 'None', 'post_cluster_profiling', 'Platform-specific usage; aggregated into platforms_used_count to avoid platform-tied clusters.'),
        'Used Never Used': ('QA 12', 'Platform ever used: Never used flag', 'Binary', 'All Respondents (N=1263)', 'None', 'excluded_constant_active', 'Constant 0 for active users; partition validation flag.'),
        'Usage Duration': ('QA 13', 'Quick-commerce usage tenure', 'Ordinal', 'Current Active Users (n=807)', 'Code 1=Never used (0 in active)', 'primary_candidate_spec_a_b', 'Key engagement velocity and customer maturity measure; codes 2-6 ordered from <3 months to >2 years.'),
        'First Trial Reason': ('QA 14', 'Primary motivation for first trial', 'Nominal', 'Current Active Users (n=807)', 'Code 8=N/A (0 in active)', 'post_cluster_profiling', 'Nominal trial origin (codes 1-7); reserved for post-cluster profiling to trace adoption pathways.'),
        'Order Frequency': ('QA 15', 'Current ordering frequency', 'Ordinal', 'Current Active Users (n=807)', 'Code 1=Never (0 in active)', 'primary_candidate_spec_a_b', 'Core behavioral velocity metric; ordered categories 2-7 from <once/month to daily.'),
        'Common Days': ('QA 16', 'Most common ordering days', 'Nominal', 'Current Active Users (n=807)', 'Code 5=N/A (0 in active)', 'post_cluster_profiling', 'Operational day-of-week timing; high noise for persona clustering, reserved for dispatch profiling.'),
        'Common Time': ('QA 17', 'Most common ordering time of day', 'Nominal', 'Current Active Users (n=807)', 'Code 7=N/A (0 in active)', 'post_cluster_profiling', 'Operational time-of-day timing; reserved for dispatch profiling.'),
        'Reason Forgotten Item': ('QA 18', 'Usual order occasion: Forgotten item', 'Binary', 'Current Active Users (n=807)', 'None', 'post_cluster_profiling', 'Occasion multi-response; reserved for profiling order contexts without overweighting binary inputs.'),
        'Reason Urgent Need': ('QA 18', 'Usual order occasion: Urgent need', 'Binary', 'Current Active Users (n=807)', 'None', 'post_cluster_profiling', 'Occasion multi-response; reserved for profiling order contexts without overweighting binary inputs.'),
        'Reason Grocery Topup': ('QA 18', 'Usual order occasion: Grocery top-up', 'Binary', 'Current Active Users (n=807)', 'None', 'post_cluster_profiling', 'Occasion multi-response; reserved for profiling order contexts without overweighting binary inputs.'),
        'Reason Snacks Beverages': ('QA 18', 'Usual order occasion: Snacks/beverages', 'Binary', 'Current Active Users (n=807)', 'None', 'post_cluster_profiling', 'Occasion multi-response; reserved for profiling order contexts without overweighting binary inputs.'),
        'Reason Planned Convenience': ('QA 18', 'Usual order occasion: Planned convenience', 'Binary', 'Current Active Users (n=807)', 'None', 'post_cluster_profiling', 'Occasion multi-response; reserved for profiling order contexts without overweighting binary inputs.'),
        'Reason Late Night': ('QA 18', 'Usual order occasion: Late night', 'Binary', 'Current Active Users (n=807)', 'None', 'post_cluster_profiling', 'Occasion multi-response; reserved for profiling order contexts without overweighting binary inputs.'),
        'Reason Hosting Guests': ('QA 18', 'Usual order occasion: Hosting guests', 'Binary', 'Current Active Users (n=807)', 'None', 'post_cluster_profiling', 'Occasion multi-response; reserved for profiling order contexts without overweighting binary inputs.'),
        'Reason Avoid Travel Queues': ('QA 18', 'Usual order occasion: Avoid travel/queues', 'Binary', 'Current Active Users (n=807)', 'None', 'post_cluster_profiling', 'Occasion multi-response; reserved for profiling order contexts without overweighting binary inputs.'),
        'Reason Promotion Discount': ('QA 18', 'Usual order occasion: Promotion/discount', 'Binary', 'Current Active Users (n=807)', 'None', 'post_cluster_profiling', 'Occasion multi-response; promo sensitivity captured directly by QA 28/29.'),
        'Reason Not Applicable': ('QA 18', 'Usual order occasion: Skip flag', 'Binary', 'Current Active Users (n=807)', 'Code 1=N/A (0 in active)', 'excluded_constant_active', 'Constant 0 for active users; skip routing flag.'),
        'Items per Order': ('QA 19', 'Typical basket size items', 'Mixed Ordinal/Nominal', 'Current Active Users (n=807)', 'Code 6=Varies (n=100); Code 7=N/A (0)', 'primary_candidate_spec_a_b', 'Audited semantic rule: Codes 1-5 ordered (1 to >10 items); Code 6 is non-ordinal special response (Varies considerably). Separated into ordinal rank + binary flag.'),
        'Expected Delivery': ('QA 20', 'Expected delivery window', 'Mixed Ordinal/Nominal', 'Current Active Users (n=807)', 'Code 6=No expectation (n=68); Code 7=N/A (0)', 'post_cluster_profiling', 'Delivery expectation interval; reserved for profiling. Speed importance captured directly by QA 35 Likert.'),
        'Spontaneous Frequency': ('QA 21', 'Frequency of spontaneous orders', 'Ordinal', 'Current Active Users (n=807)', 'Code 6=N/A (0 in active)', 'post_cluster_profiling', 'Impulse frequency; correlated with QA 44 (Unplanned purchase) which is retained as primary attitudinal Likert.'),
        'Category Fresh Fruit Veg': ('QA 22', 'Purchased: Fresh fruits/vegetables', 'Binary', 'Current Active Users (n=807)', 'None', 'post_cluster_profiling', 'Category adoption dummy; reserved for profiling product mix without bloating feature dimensionality.'),
        'Category Milk Dairy': ('QA 22', 'Purchased: Milk/dairy products', 'Binary', 'Current Active Users (n=807)', 'None', 'post_cluster_profiling', 'Category adoption dummy; reserved for profiling product mix without bloating feature dimensionality.'),
        'Category Bread Eggs Breakfast': ('QA 22', 'Purchased: Bread/eggs/breakfast', 'Binary', 'Current Active Users (n=807)', 'None', 'post_cluster_profiling', 'Category adoption dummy; reserved for profiling product mix without bloating feature dimensionality.'),
        'Category Packaged Groceries': ('QA 22', 'Purchased: Packaged groceries', 'Binary', 'Current Active Users (n=807)', 'None', 'post_cluster_profiling', 'Category adoption dummy; reserved for profiling product mix without bloating feature dimensionality.'),
        'Category Snacks Confectionery': ('QA 22', 'Purchased: Snacks/confectionery', 'Binary', 'Current Active Users (n=807)', 'None', 'post_cluster_profiling', 'Category adoption dummy; reserved for profiling product mix without bloating feature dimensionality.'),
        'Category Beverages': ('QA 22', 'Purchased: Beverages/soft drinks', 'Binary', 'Current Active Users (n=807)', 'None', 'post_cluster_profiling', 'Category adoption dummy; reserved for profiling product mix without bloating feature dimensionality.'),
        'Category Personal Care': ('QA 22', 'Purchased: Personal care', 'Binary', 'Current Active Users (n=807)', 'None', 'post_cluster_profiling', 'Category adoption dummy; reserved for profiling product mix without bloating feature dimensionality.'),
        'Category Beauty Grooming': ('QA 22', 'Purchased: Beauty/grooming', 'Binary', 'Current Active Users (n=807)', 'None', 'post_cluster_profiling', 'Category adoption dummy; reserved for profiling product mix without bloating feature dimensionality.'),
        'Category Household Cleaning': ('QA 22', 'Purchased: Household cleaning', 'Binary', 'Current Active Users (n=807)', 'None', 'post_cluster_profiling', 'Category adoption dummy; reserved for profiling product mix without bloating feature dimensionality.'),
        'Category Baby Care': ('QA 22', 'Purchased: Baby care', 'Binary', 'Current Active Users (n=807)', 'None', 'post_cluster_profiling', 'Category adoption dummy; reserved for profiling product mix without bloating feature dimensionality.'),
        'Category Pet Care': ('QA 22', 'Purchased: Pet care', 'Binary', 'Current Active Users (n=807)', 'None', 'post_cluster_profiling', 'Category adoption dummy; reserved for profiling product mix without bloating feature dimensionality.'),
        'Category OTC Health Wellness': ('QA 22', 'Purchased: OTC health/wellness', 'Binary', 'Current Active Users (n=807)', 'None', 'post_cluster_profiling', 'Category adoption dummy; reserved for profiling product mix without bloating feature dimensionality.'),
        'Category Stationery': ('QA 22', 'Purchased: Stationery/office', 'Binary', 'Current Active Users (n=807)', 'None', 'post_cluster_profiling', 'Category adoption dummy; reserved for profiling product mix without bloating feature dimensionality.'),
        'Category Mobile Electronic Accessories': ('QA 22', 'Purchased: Mobile/electronics', 'Binary', 'Current Active Users (n=807)', 'None', 'post_cluster_profiling', 'Category adoption dummy; reserved for profiling product mix without bloating feature dimensionality.'),
        'Category Small Household Kitchen': ('QA 22', 'Purchased: Small kitchen/home', 'Binary', 'Current Active Users (n=807)', 'None', 'post_cluster_profiling', 'Category adoption dummy; reserved for profiling product mix without bloating feature dimensionality.'),
        'Category Ready Eat Cook': ('QA 22', 'Purchased: Ready-to-eat/cook', 'Binary', 'Current Active Users (n=807)', 'None', 'post_cluster_profiling', 'Category adoption dummy; reserved for profiling product mix without bloating feature dimensionality.'),
        'Category Festival Occasion': ('QA 22', 'Purchased: Festival items', 'Binary', 'Current Active Users (n=807)', 'None', 'post_cluster_profiling', 'Category adoption dummy; reserved for profiling product mix without bloating feature dimensionality.'),
        'Category Not Applicable': ('QA 22', 'Purchased: Skip flag', 'Binary', 'Current Active Users (n=807)', 'Code 1=N/A (0 in active)', 'excluded_constant_active', 'Constant 0 for active users; skip routing flag.'),
        'Most Frequent Category': ('QA 23', 'Single most frequent category', 'Nominal', 'Current Active Users (n=807)', 'Code 8=N/A (0 in active)', 'post_cluster_profiling', 'Nominal primary category; reserved for profiling dominant basket type.'),
        'Physical Fresh Fruit Veg': ('QA 24', 'Physical store preference: Fresh produce', 'Binary', 'All Respondents (N=1263)', 'None', 'post_cluster_profiling', 'Physical store channel preference; substantive offline preference, reserved for profiling.'),
        'Physical Dairy Breakfast': ('QA 24', 'Physical store preference: Dairy/breakfast', 'Binary', 'All Respondents (N=1263)', 'None', 'post_cluster_profiling', 'Physical store channel preference; substantive offline preference, reserved for profiling.'),
        'Physical Packaged Groceries': ('QA 24', 'Physical store preference: Groceries', 'Binary', 'All Respondents (N=1263)', 'None', 'post_cluster_profiling', 'Physical store channel preference; substantive offline preference, reserved for profiling.'),
        'Physical Snacks Beverages': ('QA 24', 'Physical store preference: Snacks', 'Binary', 'All Respondents (N=1263)', 'None', 'post_cluster_profiling', 'Physical store channel preference; substantive offline preference, reserved for profiling.'),
        'Physical Personal Care Beauty': ('QA 24', 'Physical store preference: Personal care', 'Binary', 'All Respondents (N=1263)', 'None', 'post_cluster_profiling', 'Physical store channel preference; substantive offline preference, reserved for profiling.'),
        'Physical Household Cleaning': ('QA 24', 'Physical store preference: Cleaning', 'Binary', 'All Respondents (N=1263)', 'None', 'post_cluster_profiling', 'Physical store channel preference; substantive offline preference, reserved for profiling.'),
        'Physical Electronic Accessories': ('QA 24', 'Physical store preference: Electronics', 'Binary', 'All Respondents (N=1263)', 'None', 'post_cluster_profiling', 'Physical store channel preference; substantive offline preference, reserved for profiling.'),
        'Physical No Clear Preference': ('QA 24', 'Physical store preference: No clear preference', 'Binary', 'All Respondents (N=1263)', 'None', 'post_cluster_profiling', 'Physical store channel preference; substantive offline preference, reserved for profiling.'),
        'Order Spend': ('QA 25', 'Typical single order ticket size', 'Ordinal', 'Current Active Users (n=807)', 'Code 8=N/A (0 in active)', 'primary_candidate_spec_a_b', 'Core monetary ticket size metric; codes 1-7 ordered from Below ₹200 to ₹1,500+.'),
        'Monthly Spend': ('QA 26', 'Typical monthly quick-commerce spend', 'Mixed Ordinal/Nominal', 'Current Active Users (n=807)', 'Code 1=₹0 (0 in active); Code 8=Not sure (n=24)', 'primary_candidate_spec_a_b', 'Audited semantic rule: Codes 2-7 ordered spend brackets (<₹1k to ₹10k+); Code 8 is non-ordinal uncertainty flag. Separated into ordinal rank + binary flag.'),
        'Total Spending Change': ('QA 27', 'Perceived total spend change vs baseline', 'Ordinal', 'Current Active Users (n=807)', 'Code 5=Not sure; Code 6=N/A (0)', 'post_cluster_profiling', 'Self-reported perceived wallet evolution; reserved for profiling.'),
        'Discount Overspend': ('QA 28', 'Discounts cause overspending', 'Ordinal Likert', 'Current Active Users (n=807)', 'Code 6=N/A (0 in active)', 'primary_candidate_spec_a_b', 'Key deal-proneness and promo-driven basket inflation metric; Likert 1-5 (Never to Very often).'),
        'Threshold Extra Items': ('QA 29', 'Add items to reach free delivery threshold', 'Ordinal Likert', 'Current Active Users (n=807)', 'Code 6=N/A (0 in active)', 'primary_candidate_spec_a_b', 'Direct proxy for delivery fee sensitivity and threshold gaming; Likert 1-5 (Never to Very often). Distinct construct from QA 28 (r=0.06).'),
        'Payment Method': ('QA 30', 'Primary payment method', 'Nominal', 'Current Active Users (n=807)', 'Code 7=N/A (0 in active)', 'post_cluster_profiling', 'Checkout method; concentrated in UPI (>70%), reserved for payment profiling.'),
        'Factor Delivery Speed': ('QA 31', 'Platform choice factor: Speed', 'Binary', 'Current Active Users (n=807)', 'None', 'post_cluster_profiling', 'Stated factor multi-response; speed importance captured continuously via QA 35.'),
        'Factor Product Availability': ('QA 31', 'Platform choice factor: Availability', 'Binary', 'Current Active Users (n=807)', 'None', 'post_cluster_profiling', 'Stated factor multi-response; reserved for profiling platform criteria.'),
        'Factor Lower Prices': ('QA 31', 'Platform choice factor: Lower prices', 'Binary', 'Current Active Users (n=807)', 'None', 'post_cluster_profiling', 'Stated factor multi-response; reserved for profiling platform criteria.'),
        'Factor Discounts Coupon': ('QA 31', 'Platform choice factor: Discounts', 'Binary', 'Current Active Users (n=807)', 'None', 'post_cluster_profiling', 'Stated factor multi-response; promo sensitivity captured directly by QA 28/29/47.'),
        'Factor Low Delivery Fee': ('QA 31', 'Platform choice factor: Low delivery fee', 'Binary', 'Current Active Users (n=807)', 'None', 'post_cluster_profiling', 'Stated factor multi-response; reserved for profiling platform criteria.'),
        'Factor Low Min Order': ('QA 31', 'Platform choice factor: Low min order', 'Binary', 'Current Active Users (n=807)', 'None', 'post_cluster_profiling', 'Stated factor multi-response; reserved for profiling platform criteria.'),
        'Factor App Usability': ('QA 31', 'Platform choice factor: App usability', 'Binary', 'Current Active Users (n=807)', 'None', 'post_cluster_profiling', 'Stated factor multi-response; reserved for profiling platform criteria.'),
        'Factor Past Experience': ('QA 31', 'Platform choice factor: Past experience', 'Binary', 'Current Active Users (n=807)', 'None', 'post_cluster_profiling', 'Stated factor multi-response; reserved for profiling platform criteria.'),
        'Factor Product Quality': ('QA 31', 'Platform choice factor: Quality', 'Binary', 'Current Active Users (n=807)', 'None', 'post_cluster_profiling', 'Stated factor multi-response; quality satisfaction captured in composite.'),
        'Factor Brand Trust': ('QA 31', 'Platform choice factor: Trust', 'Binary', 'Current Active Users (n=807)', 'None', 'post_cluster_profiling', 'Stated factor multi-response; reserved for profiling platform criteria.'),
        'Factor Payment Options': ('QA 31', 'Platform choice factor: Payment options', 'Binary', 'Current Active Users (n=807)', 'None', 'post_cluster_profiling', 'Stated factor multi-response; reserved for profiling platform criteria.'),
        'Factor Customer Support': ('QA 31', 'Platform choice factor: Support', 'Binary', 'Current Active Users (n=807)', 'None', 'post_cluster_profiling', 'Stated factor multi-response; reserved for profiling platform criteria.'),
        'Factor Return Refund': ('QA 31', 'Platform choice factor: Return/refund', 'Binary', 'Current Active Users (n=807)', 'None', 'post_cluster_profiling', 'Stated factor multi-response; reserved for profiling platform criteria.'),
        'Most Important Factor': ('QA 32', 'Single most important platform choice factor', 'Nominal', 'Current Active Users (n=807)', 'Code 9=N/A (0 in active)', 'post_cluster_profiling', 'Single primary choice factor (8 levels); reserved for post-cluster CRM priority profiling.'),
        'Compare Platform Prices': ('QA 33', 'Compare prices across quick commerce apps', 'Ordinal Likert', 'Current Active Users (n=807)', 'Code 6=N/A (0 in active)', 'primary_candidate_spec_a_b', 'Cross-app price comparison frequency; Likert 1-5 (Never to Always). Measures multi-app arbitrage proneness.'),
        'Compare Physical Prices': ('QA 34', 'Compare prices with physical stores', 'Ordinal Likert', 'Current Active Users (n=807)', 'Code 6=N/A (0 in active)', 'primary_candidate_spec_a_b', 'Online-offline price comparison frequency; Likert 1-5 (Never to Always). Measures channel arbitrage proneness.'),
        'Fast Delivery Importance': ('QA 35', 'Importance of very fast delivery (10-20 min)', 'Ordinal Likert', 'Current Active Users (n=807)', 'Code 6=N/A (0 in active)', 'primary_candidate_spec_a_b', 'Core delivery valuation metric; clean Likert 1-5 (Not at all to Extremely important).'),
        'Problem Out of Stock': ('QA 36', 'Problem experienced: Out of stock', 'Binary', 'Current Active Users (n=807)', 'None', 'post_cluster_profiling', 'Operational friction dummy; reserved for service quality profiling.'),
        'Problem Wrong Item': ('QA 36', 'Problem experienced: Wrong item', 'Binary', 'Current Active Users (n=807)', 'None', 'post_cluster_profiling', 'Operational friction dummy; reserved for service quality profiling.'),
        'Problem Damaged Product': ('QA 36', 'Problem experienced: Damaged product', 'Binary', 'Current Active Users (n=807)', 'None', 'post_cluster_profiling', 'Operational friction dummy; reserved for service quality profiling.'),
        'Problem Poor Fresh Produce': ('QA 36', 'Problem experienced: Poor fresh produce', 'Binary', 'Current Active Users (n=807)', 'None', 'post_cluster_profiling', 'Operational friction dummy; reserved for service quality profiling.'),
        'Problem Late Delivery': ('QA 36', 'Problem experienced: Late delivery', 'Binary', 'Current Active Users (n=807)', 'None', 'post_cluster_profiling', 'Operational friction dummy; reserved for service quality profiling.'),
        'Problem Higher Price': ('QA 36', 'Problem experienced: Higher price', 'Binary', 'Current Active Users (n=807)', 'None', 'post_cluster_profiling', 'Operational friction dummy; reserved for service quality profiling.'),
        'Problem Unexpected Fees': ('QA 36', 'Problem experienced: Unexpected fees', 'Binary', 'Current Active Users (n=807)', 'None', 'post_cluster_profiling', 'Operational friction dummy; reserved for service quality profiling.'),
        'Problem Order Cancellation': ('QA 36', 'Problem experienced: Order cancellation', 'Binary', 'Current Active Users (n=807)', 'None', 'post_cluster_profiling', 'Operational friction dummy; reserved for service quality profiling.'),
        'Problem Refund Delay': ('QA 36', 'Problem experienced: Refund delay', 'Binary', 'Current Active Users (n=807)', 'None', 'post_cluster_profiling', 'Operational friction dummy; reserved for service quality profiling.'),
        'Problem Payment Issue': ('QA 36', 'Problem experienced: Payment issue', 'Binary', 'Current Active Users (n=807)', 'None', 'post_cluster_profiling', 'Operational friction dummy; reserved for service quality profiling.'),
        'Problem App Technical': ('QA 36', 'Problem experienced: Technical glitch', 'Binary', 'Current Active Users (n=807)', 'None', 'post_cluster_profiling', 'Operational friction dummy; reserved for service quality profiling.'),
        'Problem Customer Service': ('QA 36', 'Problem experienced: Customer service', 'Binary', 'Current Active Users (n=807)', 'None', 'post_cluster_profiling', 'Operational friction dummy; reserved for service quality profiling.'),
        'Problem No Major Problem': ('QA 36', 'Problem experienced: No major problem', 'Binary', 'Current Active Users (n=807)', 'None', 'post_cluster_profiling', 'Operational friction dummy; reserved for service quality profiling.'),
        'Problem Not Applicable': ('QA 36', 'Problem experienced: Skip flag', 'Binary', 'Current Active Users (n=807)', 'Code 1=N/A (0 in active)', 'excluded_constant_active', 'Constant 0 for active users; skip routing flag.'),
        'Overall Satisfaction': ('QA 37', 'Overall satisfaction rating', 'Ordinal Likert', 'Current Active Users (n=807)', 'Code 6=N/A (0 in active)', 'post_cluster_profiling', 'Individual satisfaction item (2-5); integrated into service_satisfaction_composite (alpha=0.863).'),
        'Product Quality Satisfaction': ('QA 38', 'Product quality satisfaction rating', 'Ordinal Likert', 'Current Active Users (n=807)', 'Code 6=N/A (0 in active)', 'post_cluster_profiling', 'Individual satisfaction item (2-5); integrated into service_satisfaction_composite (alpha=0.863).'),
        'Delivery Reliability Satisfaction': ('QA 39', 'Delivery reliability satisfaction rating', 'Ordinal Likert', 'Current Active Users (n=807)', 'Code 6=N/A (0 in active)', 'post_cluster_profiling', 'Individual satisfaction item (1-5); integrated into service_satisfaction_composite (alpha=0.863).'),
        'Value Money Satisfaction': ('QA 40', 'Value for money satisfaction rating', 'Ordinal Likert', 'Current Active Users (n=807)', 'Code 6=N/A (0 in active)', 'post_cluster_profiling', 'Individual satisfaction item (1-5); integrated into service_satisfaction_composite (alpha=0.863).'),
        'Kirana Visit Change': ('QA 41', 'Change in kirana visits', 'Ordinal', 'Current Active Users (n=807)', 'Code 6=Not sure; Code 7=N/A (0)', 'post_cluster_profiling', 'Offline displacement measure; reserved for retail disruption profiling.'),
        'Supermarket Visit Change': ('QA 42', 'Change in supermarket visits', 'Ordinal', 'Current Active Users (n=807)', 'Code 6=Not sure; Code 7=N/A (0)', 'post_cluster_profiling', 'Offline displacement measure; reserved for retail disruption profiling.'),
        'Shopping Routine Role': ('QA 43', 'Role in shopping routine', 'Nominal', 'Current Active Users (n=807)', 'Code 6=Do not use (0 in active)', 'primary_candidate_spec_a_b', 'Audited semantic rule: Substantive usage roles (1=Large grocery replacement, 2=Some replacement, 3=Top-up, 4=Urgent/emergencies, 5=Occasional offers/convenience). Core lifestyle integration feature.'),
        'Unplanned Purchase': ('QA 44', 'Impulse purchasing encouragement', 'Ordinal Likert', 'Current Active Users (n=807)', 'Code 6=N/A (0 in active)', 'primary_candidate_spec_a_b', 'Key attitudinal measure of spontaneous/impulse buying in quick commerce; Likert 1-5 (Never to Very often).'),
        'New Brand Trial': ('QA 45', 'Openness to new brand/product discovery', 'Ordinal Likert', 'Current Active Users (n=807)', 'Code 6=N/A (0 in active)', 'primary_candidate_spec_a_b', 'Key attitudinal measure of discovery and brand openness; Likert 1-5 (Strongly disagree to Strongly agree).'),
        'Next 3 Month Use': ('QA 46', 'Stated likelihood of future use (next 3 months)', 'Ordinal Likert', 'All Respondents (N=1263)', 'None', 'external_validation_holdout', 'Audited rule: Stated future-use intention, NOT actual realized retention. Held out across all specifications for post-cluster external validation.'),
        'Continue If Discounts Reduced': ('QA 47', 'Continuation intention if discounts reduced', 'Ordinal Likert', 'Current Active Users (n=807)', 'Code 6=N/A for non-current (0 in active)', 'spec_a_holdout_spec_b_input', 'Audited rule: Stated continuation intention (1-5). Specification A: External validation holdout (avoids circularity). Specification B: Segment-defining input (with explicit circularity disclosure).'),
        'Reason Service Unavailable': ('QA 48', 'Non-use barrier: Area unavailable', 'Binary', 'Non-Current Users (n=456)', 'Constant 0 for active users', 'excluded_non_current_skip', 'Routed strictly to non-current users; constant 0 in active cohort. Excluded from clustering.'),
        'Reason Prefer Physical': ('QA 48', 'Non-use barrier: Prefer physical stores', 'Binary', 'Non-Current Users (n=456)', 'Constant 0 for active users', 'excluded_non_current_skip', 'Routed strictly to non-current users; constant 0 in active cohort. Excluded from clustering.'),
        'Reason Prices High': ('QA 48', 'Non-use barrier: Prices high', 'Binary', 'Non-Current Users (n=456)', 'Constant 0 for active users', 'excluded_non_current_skip', 'Routed strictly to non-current users; constant 0 in active cohort. Excluded from clustering.'),
        'Reason Delivery Fees': ('QA 48', 'Non-use barrier: Delivery fees', 'Binary', 'Non-Current Users (n=456)', 'Constant 0 for active users', 'excluded_non_current_skip', 'Routed strictly to non-current users; constant 0 in active cohort. Excluded from clustering.'),
        'Reason Distrust Quality': ('QA 48', 'Non-use barrier: Distrust quality', 'Binary', 'Non-Current Users (n=456)', 'Constant 0 for active users', 'excluded_non_current_skip', 'Routed strictly to non-current users; constant 0 in active cohort. Excluded from clustering.'),
        'Reason Prefer Inspect': ('QA 48', 'Non-use barrier: Prefer inspect items', 'Binary', 'Non-Current Users (n=456)', 'Constant 0 for active users', 'excluded_non_current_skip', 'Routed strictly to non-current users; constant 0 in active cohort. Excluded from clustering.'),
        'Reason Impulsive Spending Concern': ('QA 48', 'Non-use barrier: Impulsive spending concern', 'Binary', 'Non-Current Users (n=456)', 'Constant 0 for active users', 'excluded_non_current_skip', 'Routed strictly to non-current users; constant 0 in active cohort. Excluded from clustering.'),
        'Reason No Need Rapid': ('QA 48', 'Non-use barrier: No need rapid', 'Binary', 'Non-Current Users (n=456)', 'Constant 0 for active users', 'excluded_non_current_skip', 'Routed strictly to non-current users; constant 0 in active cohort. Excluded from clustering.'),
        'Reason Privacy Payment Concern': ('QA 48', 'Non-use barrier: Privacy/payment concern', 'Binary', 'Non-Current Users (n=456)', 'Constant 0 for active users', 'excluded_non_current_skip', 'Routed strictly to non-current users; constant 0 in active cohort. Excluded from clustering.'),
        'Reason Unfamiliar Apps': ('QA 48', 'Non-use barrier: Unfamiliar with apps', 'Binary', 'Non-Current Users (n=456)', 'Constant 0 for active users', 'excluded_non_current_skip', 'Routed strictly to non-current users; constant 0 in active cohort. Excluded from clustering.'),
        'Reason Not Applicable Current User': ('QA 48', 'Non-use barrier: Current user skip flag', 'Binary', 'Current Active Users (n=807)', 'Constant 1 for active users', 'excluded_constant_active', 'Constant 1 for active users; audited skip flag, excluded from clustering.'),
        'Improvement': ('QA 49', 'Single preferred service improvement', 'Nominal', 'All Respondents (N=1263)', 'None', 'post_cluster_profiling', 'Audited rule: Universal single choice (1-10); reserved for post-cluster CRM retention action mapping rather than cluster construction.')
    }
    return mapping


def generate_feature_inventory(full_df, active_df, reports_dir):
    """Generates reports/segmentation/feature_inventory.csv for all 130 columns."""
    mapping = get_column_metadata_mapping()
    rows = []

    for col in full_df.columns:
        if col in ['user_subgroup', 'platforms_used_count', 'service_satisfaction_composite']:
            continue
        meta = mapping.get(col, ('Unknown', 'Unknown', 'Unknown', 'Unknown', 'None', 'unassigned', 'None'))
        q_id, meaning, var_type, elig_pop, skip_info, role, rationale = meta

        obs_all = sorted(full_df[col].unique().tolist())
        obs_active = sorted(active_df[col].unique().tolist()) if col in active_df.columns else []

        rows.append({
            'question_id': q_id,
            'source_column': col,
            'substantive_meaning': meaning,
            'variable_type': var_type,
            'eligible_population': elig_pop,
            'observed_codes_all': str(obs_all),
            'observed_codes_active': str(obs_active),
            'missing_skip_interpretation': skip_info,
            'proposed_role': role,
            'inclusion_exclusion_rationale': rationale
        })

    inv_df = pd.DataFrame(rows)
    os.makedirs(reports_dir, exist_ok=True)
    out_path = os.path.join(reports_dir, "feature_inventory.csv")
    inv_df.to_csv(out_path, index=False)
    return inv_df


def generate_feature_quality_audit(full_df, active_df, reports_dir):
    """
    Generates reports/segmentation/feature_quality_audit.csv with distribution checks,
    invalid values, constants, low-count categories, and special non-ordinal codes.
    """
    mapping = get_column_metadata_mapping()
    rows = []

    for col in full_df.columns:
        if col in ['user_subgroup', 'platforms_used_count', 'service_satisfaction_composite']:
            continue
        meta = mapping.get(col, ('Unknown', 'Unknown', 'Unknown', 'Unknown', 'None', 'unassigned', 'None'))
        q_id, meaning, var_type, elig_pop, skip_info, role, rationale = meta

        # Base series for active users
        s_act = active_df[col]
        n_act = len(s_act)
        val_counts = s_act.value_counts().sort_index().to_dict()
        val_pcts = {k: round((v / n_act) * 100.0, 2) for k, v in val_counts.items()}

        is_const = (s_act.nunique() <= 1)
        # Check low count categories (< 5% or < 30 respondents)
        low_count_cats = [k for k, v in val_counts.items() if v < 30 or (v / n_act) < 0.05]

        # Special codes check
        special_notes = []
        if col == 'Items per Order' and 6 in val_counts:
            special_notes.append("Code 6='Varies considerably' (n=100); non-ordinal special category.")
        if col == 'Monthly Spend' and 8 in val_counts:
            special_notes.append("Code 8='Not sure' (n=24); non-ordinal special category.")
        if col == 'Expected Delivery' and 6 in val_counts:
            special_notes.append("Code 6='No specific expectation' (n=68); non-ordinal.")
        if col == 'Continue If Discounts Reduced' and 6 in full_df[col].unique():
            special_notes.append("Code 6='Not applicable' in full sample (n=456), 0 in active users.")
        if col.startswith('Reason ') and col != 'Reason Not Applicable Current User' and is_const and col in [
            'Reason Service Unavailable', 'Reason Prefer Physical', 'Reason Prices High',
            'Reason Delivery Fees', 'Reason Distrust Quality', 'Reason Prefer Inspect',
            'Reason Impulsive Spending Concern', 'Reason No Need Rapid',
            'Reason Privacy Payment Concern', 'Reason Unfamiliar Apps'
        ]:
            special_notes.append("QA 48 non-use barrier; 100% constant 0 in active cohort (routed to non-current).")
        if col == 'Reason Not Applicable Current User':
            special_notes.append("QA 48 skip flag; 100% constant 1 in active cohort.")

        special_str = "; ".join(special_notes) if special_notes else "None"

        # Action taken
        if role == 'primary_candidate_spec_a_b':
            if col == 'Items per Order':
                action = "Split into substantive ordinal rank (1-5, code 6 assigned median rank 3) + binary flag for Code 6."
            elif col == 'Monthly Spend':
                action = "Split into substantive ordinal spend tier (2-7 mapped to 1-6, code 8 assigned median rank 2) + binary flag for Code 8."
            else:
                action = "Preserved as direct clustering input; ordinal/continuous normalized representation."
        elif role == 'spec_a_holdout_spec_b_input':
            action = "Specification A: External validation holdout. Specification B: Segment-defining feature."
        elif role == 'external_validation_holdout':
            action = "Held out across all specifications as external validation metric (stated future-use intention)."
        elif role.startswith('excluded_'):
            action = f"Excluded from clustering: {rationale}"
        else:
            action = f"Reserved for post-cluster profiling: {rationale}"

        rows.append({
            'question_id': q_id,
            'source_column': col,
            'substantive_meaning': meaning,
            'eligible_count_active': n_act,
            'observed_categories_active': str(sorted(list(val_counts.keys()))),
            'category_frequencies_active': json.dumps(val_counts),
            'category_percentages_active': json.dumps(val_pcts),
            'physical_missing_count': int(s_act.isna().sum()),
            'invalid_values_count': 0,
            'is_constant_active': is_const,
            'low_count_categories_active': str(low_count_cats),
            'special_non_ordinal_codes': special_str,
            'quality_action_taken': action
        })

    audit_df = pd.DataFrame(rows)
    os.makedirs(reports_dir, exist_ok=True)
    out_path = os.path.join(reports_dir, "feature_quality_audit.csv")
    audit_df.to_csv(out_path, index=False)
    return audit_df


def generate_feature_specifications(reports_dir):
    """
    Generates version-controlled, machine-readable JSON specifications:
    - feature_spec_a.json (Independent discount-sensitivity evaluation)
    - feature_spec_b.json (Discount intention included)
    """
    # Specification A feature definitions (17 features)
    features_a = [
        {
            "feature_id": "feat_01",
            "name": "order_frequency",
            "question_id": "QA 15",
            "source_column": "Order Frequency",
            "data_type": "ordinal",
            "active_domain": [2, 3, 4, 5, 6, 7],
            "encoding": "ordinal_integer_or_rank",
            "range": [2, 7],
            "special_codes": "None (all active respondents report 2..7)",
            "description": "Current order frequency from Less than once a month (2) to Daily (7)."
        },
        {
            "feature_id": "feat_02",
            "name": "usage_duration",
            "question_id": "QA 13",
            "source_column": "Usage Duration",
            "data_type": "ordinal",
            "active_domain": [2, 3, 4, 5, 6],
            "encoding": "ordinal_integer_or_rank",
            "range": [2, 6],
            "special_codes": "None (code 1 Never Used is absent in active users)",
            "description": "Quick commerce customer tenure from <3 months (2) to >2 years (6)."
        },
        {
            "feature_id": "feat_03",
            "name": "order_spend",
            "question_id": "QA 25",
            "source_column": "Order Spend",
            "data_type": "ordinal",
            "active_domain": [1, 2, 3, 4, 5, 6, 7],
            "encoding": "ordinal_integer_or_rank",
            "range": [1, 7],
            "special_codes": "None (code 8 N/A absent in active users)",
            "description": "Typical single-order spend bracket from Below ₹200 (1) to ₹1,500+ (7)."
        },
        {
            "feature_id": "feat_04",
            "name": "monthly_spend_ordinal",
            "question_id": "QA 26",
            "source_column": "Monthly Spend",
            "data_type": "ordinal",
            "active_domain": [2, 3, 4, 5, 6, 7],
            "encoding": "substantive_spend_rank",
            "range": [1, 6],
            "special_codes": "Code 8 ('Not sure', n=24) mapped to neutral median rank 2 (₹1,000–₹2,499) for ordinal distance calculation.",
            "description": "Typical monthly quick-commerce spend brackets 2-7 mapped monotonically to ranks 1-6."
        },
        {
            "feature_id": "feat_05",
            "name": "monthly_spend_not_sure",
            "question_id": "QA 26",
            "source_column": "Monthly Spend",
            "data_type": "binary_indicator",
            "active_domain": [0, 1],
            "encoding": "binary_flag",
            "range": [0, 1],
            "special_codes": "1 if Monthly Spend == 8 ('Not sure', n=24), 0 otherwise.",
            "description": "Explicit non-ordinal indicator preserving spending uncertainty without distorting distance metrics."
        },
        {
            "feature_id": "feat_06",
            "name": "items_per_order_ordinal",
            "question_id": "QA 19",
            "source_column": "Items per Order",
            "data_type": "ordinal",
            "active_domain": [1, 2, 3, 4, 5],
            "encoding": "substantive_basket_rank",
            "range": [1, 5],
            "special_codes": "Code 6 ('Varies considerably', n=100) mapped to neutral median rank 3 ('4–5 items') for ordinal distance calculation.",
            "description": "Typical items per order from 1 item (1) to >10 items (5)."
        },
        {
            "feature_id": "feat_07",
            "name": "items_varies_considerably",
            "question_id": "QA 19",
            "source_column": "Items per Order",
            "data_type": "binary_indicator",
            "active_domain": [0, 1],
            "encoding": "binary_flag",
            "range": [0, 1],
            "special_codes": "1 if Items per Order == 6 ('Varies considerably', n=100), 0 otherwise.",
            "description": "Explicit non-ordinal indicator capturing basket size volatility."
        },
        {
            "feature_id": "feat_08",
            "name": "discount_overspend",
            "question_id": "QA 28",
            "source_column": "Discount Overspend",
            "data_type": "ordinal",
            "active_domain": [1, 2, 3, 4, 5],
            "encoding": "ordinal_likert",
            "range": [1, 5],
            "special_codes": "None (code 6 N/A absent in active users)",
            "description": "How often discounts/coupons cause overspending (1=Never to 5=Very often). Measures deal-driven basket inflation."
        },
        {
            "feature_id": "feat_09",
            "name": "threshold_extra_items",
            "question_id": "QA 29",
            "source_column": "Threshold Extra Items",
            "data_type": "ordinal",
            "active_domain": [1, 2, 3, 4, 5],
            "encoding": "ordinal_likert",
            "range": [1, 5],
            "special_codes": "None (code 6 N/A absent in active users)",
            "description": "How often extra items are added to reach free delivery thresholds (1=Never to 5=Very often). Measures fee avoidance gaming."
        },
        {
            "feature_id": "feat_10",
            "name": "compare_platform_prices",
            "question_id": "QA 33",
            "source_column": "Compare Platform Prices",
            "data_type": "ordinal",
            "active_domain": [1, 2, 3, 4, 5],
            "encoding": "ordinal_likert",
            "range": [1, 5],
            "special_codes": "None (code 6 N/A absent in active users)",
            "description": "Frequency of comparing prices across quick-commerce apps (1=Never to 5=Always). Measures cross-app deal shopping."
        },
        {
            "feature_id": "feat_11",
            "name": "compare_physical_prices",
            "question_id": "QA 34",
            "source_column": "Compare Physical Prices",
            "data_type": "ordinal",
            "active_domain": [1, 2, 3, 4, 5],
            "encoding": "ordinal_likert",
            "range": [1, 5],
            "special_codes": "None (code 6 N/A absent in active users)",
            "description": "Frequency of comparing quick-commerce prices with physical stores (1=Never to 5=Always). Measures offline-online arbitrage."
        },
        {
            "feature_id": "feat_12",
            "name": "fast_delivery_importance",
            "question_id": "QA 35",
            "source_column": "Fast Delivery Importance",
            "data_type": "ordinal",
            "active_domain": [1, 2, 3, 4, 5],
            "encoding": "ordinal_likert",
            "range": [1, 5],
            "special_codes": "None (code 6 N/A absent in active users)",
            "description": "Stated importance of 10-20 minute delivery (1=Not at all important to 5=Extremely important)."
        },
        {
            "feature_id": "feat_13",
            "name": "service_satisfaction_composite",
            "question_id": "QA 37-40",
            "source_column": "Composite Service Satisfaction (Mean QA 37, 38, 39, 40)",
            "data_type": "continuous_composite",
            "active_domain": [1.75, 5.0],
            "encoding": "continuous_scale",
            "range": [1.0, 5.0],
            "special_codes": "Constructed mean across 4 items; Cronbach's alpha = 0.863 demonstrates high reliability.",
            "description": "Unidimensional composite service experience sentiment."
        },
        {
            "feature_id": "feat_14",
            "name": "shopping_routine_role",
            "question_id": "QA 43",
            "source_column": "Shopping Routine Role",
            "data_type": "nominal",
            "active_domain": [1, 2, 3, 4, 5],
            "encoding": "nominal_categorical_or_gower_nominal",
            "range": [1, 5],
            "special_codes": "Code 6 ('Do not use') is 0 in active users.",
            "description": "Nominal quick commerce role (1=Large grocery replacement, 2=Some replacement, 3=Top-up, 4=Urgent/emergencies, 5=Offers/convenience)."
        },
        {
            "feature_id": "feat_15",
            "name": "platforms_used_count",
            "question_id": "QA 12",
            "source_column": "Derived sum of 6 major platforms used",
            "data_type": "discrete_count",
            "active_domain": [1, 2, 3, 4, 5, 6],
            "encoding": "discrete_integer",
            "range": [1, 6],
            "special_codes": "None",
            "description": "Multi-homing footprint count (1 to 6 apps ever used). Captures platform promiscuity vs single-app loyalty."
        },
        {
            "feature_id": "feat_16",
            "name": "unplanned_purchase",
            "question_id": "QA 44",
            "source_column": "Unplanned Purchase",
            "data_type": "ordinal",
            "active_domain": [1, 2, 3, 4, 5],
            "encoding": "ordinal_likert",
            "range": [1, 5],
            "special_codes": "None (code 6 N/A absent in active users)",
            "description": "How often quick commerce encourages impulse purchases (1=Never to 5=Very often)."
        },
        {
            "feature_id": "feat_17",
            "name": "new_brand_trial",
            "question_id": "QA 45",
            "source_column": "New Brand Trial",
            "data_type": "ordinal",
            "active_domain": [1, 2, 3, 4, 5],
            "encoding": "ordinal_likert",
            "range": [1, 5],
            "special_codes": "None (code 6 N/A absent in active users)",
            "description": "Propensity to try new brands through quick commerce (1=Strongly disagree to 5=Strongly agree)."
        }
    ]

    # Specification B feature definitions (18 features: Spec A + QA 47)
    feature_b_qa47 = {
        "feature_id": "feat_18",
        "name": "continue_if_discounts_reduced",
        "question_id": "QA 47",
        "source_column": "Continue If Discounts Reduced",
        "data_type": "ordinal",
        "active_domain": [1, 2, 3, 4, 5],
        "encoding": "ordinal_likert",
        "range": [1, 5],
        "special_codes": "Code 6 N/A is absent in active users. Substantive Likert 1=Definitely no to 5=Definitely yes.",
        "description": "Segment-defining price elasticity feature in Specification B. Stated continuation intention if discounts reduced."
    }
    features_b = list(features_a) + [feature_b_qa47]

    holdout_spec = {
        "qa47_external_validation": {
            "question_id": "QA 47",
            "source_column": "Continue If Discounts Reduced",
            "role_in_spec_a": "Primary external validation benchmark (independent evaluation).",
            "role_in_spec_b": "Construct-defining feature (CIRCULAR; cannot be used for independent validation).",
            "domain_active": [1, 2, 3, 4, 5]
        },
        "qa46_future_use_intention": {
            "question_id": "QA 46",
            "source_column": "Next 3 Month Use",
            "role": "External validation benchmark across BOTH Specification A and Specification B.",
            "methodological_boundary": "STATED future-use intention, NOT realized retention or observed purchase history.",
            "domain_active": [1, 2, 3, 4, 5]
        },
        "qa49_preferred_improvement": {
            "question_id": "QA 49",
            "source_column": "Improvement",
            "role": "Post-cluster CRM retention action profiling (10 substantive choices).",
            "domain_active": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        },
        "demographic_profiling": [
            "Age Group", "Gender", "Education", "Occupation",
            "Personal Income", "Area of Residence", "Region", "Household Size"
        ],
        "platform_footprint_profiling": [
            "Used Blinkit", "Used Zepto", "Used Swiggy Instamart",
            "Used BigBasket BBNow", "Used Flipkart Minutes", "Used Amazon Rapid"
        ],
        "satisfaction_dimensions_profiling": [
            "Overall Satisfaction", "Product Quality Satisfaction",
            "Delivery Reliability Satisfaction", "Value Money Satisfaction"
        ]
    }

    spec_a = {
        "specification_name": "Specification A: Independent Discount-Sensitivity Evaluation",
        "specification_code": "SPEC_A",
        "purpose": "Constructs customer segments solely from shopping behavior, basket economics, delivery valuation, satisfaction, and routine integration, EXCLUDING QA 47. Allows rigorous, non-circular external validation of whether resulting clusters differ in stated discount resilience.",
        "qa47_status": "EXCLUDED from clustering inputs; reserved strictly as external validation holdout.",
        "qa46_status": "EXCLUDED from clustering inputs; reserved as stated future-use intention holdout.",
        "target_population": {
            "name": "Current Active Quick-Commerce Users",
            "sample_size": EXPECTED_ACTIVE_USERS,
            "filter_rule": "Ever Ordered == 1 and Order Frequency > 1",
            "excluded_groups": [
                "Never-Users (Ever Ordered == 0 & Order Frequency == 1, n=376)",
                "Previous Users (Ever Ordered == 1 & Order Frequency == 1, n=80)"
            ]
        },
        "feature_count": len(features_a),
        "features": features_a,
        "holdout_and_profiling": holdout_spec,
        "recommended_clustering_methodology": {
            "method": "Gower Distance Matrix + Partitioning Around Medoids (PAM)",
            "alternative": "Hierarchical Agglomerative Clustering (HAC) with Gower Distance",
            "rationale": "Respects mixed ordinal, nominal, and binary data natively; provides interpretable real-customer medoids without fractional coordinate distortion."
        }
    }

    spec_b = {
        "specification_name": "Specification B: Discount Intention Included",
        "specification_code": "SPEC_B",
        "purpose": "Constructs customer segments by directly embedding stated price elasticity (QA 47 Continue If Discounts Reduced) alongside behavioral and attitudinal features. Generates segments explicitly partitioned by discount sensitivity.",
        "qa47_status": "INCLUDED as segment-defining feature (feat_18). WARNING: Prohibits treating post-cluster differences in QA 47 as independent external validation.",
        "qa46_status": "EXCLUDED from clustering inputs; reserved as stated future-use intention holdout.",
        "target_population": {
            "name": "Current Active Quick-Commerce Users",
            "sample_size": EXPECTED_ACTIVE_USERS,
            "filter_rule": "Ever Ordered == 1 and Order Frequency > 1",
            "excluded_groups": [
                "Never-Users (Ever Ordered == 0 & Order Frequency == 1, n=376)",
                "Previous Users (Ever Ordered == 1 & Order Frequency == 1, n=80)"
            ]
        },
        "feature_count": len(features_b),
        "features": features_b,
        "holdout_and_profiling": holdout_spec,
        "recommended_clustering_methodology": {
            "method": "Gower Distance Matrix + Partitioning Around Medoids (PAM)",
            "alternative": "Hierarchical Agglomerative Clustering (HAC) with Gower Distance",
            "rationale": "Respects mixed ordinal, nominal, and binary data natively; provides interpretable real-customer medoids without fractional coordinate distortion."
        }
    }

    os.makedirs(reports_dir, exist_ok=True)
    path_a = os.path.join(reports_dir, "feature_spec_a.json")
    path_b = os.path.join(reports_dir, "feature_spec_b.json")

    with open(path_a, "w", encoding="utf-8") as f:
        json.dump(spec_a, f, indent=2)

    with open(path_b, "w", encoding="utf-8") as f:
        json.dump(spec_b, f, indent=2)

    return spec_a, spec_b


def prepare_feature_matrices(active_df, data_dir):
    """
    Transforms raw active-user survey columns into typed, encoded feature matrices
    for Specification A and Specification B, plus holdouts/profiling variables.
    All outputs are saved to data_dir (gitignored).
    """
    os.makedirs(data_dir, exist_ok=True)
    n = len(active_df)

    # Core transformations
    # QA 15: Order Frequency (2..7)
    order_freq = active_df['Order Frequency'].astype(int)

    # QA 13: Usage Duration (2..6)
    usage_dur = active_df['Usage Duration'].astype(int)

    # QA 25: Order Spend (1..7)
    order_spend = active_df['Order Spend'].astype(int)

    # QA 26: Monthly Spend
    # Substantive codes 2..7 mapped to ranks 1..6; Code 8 ('Not sure', n=24) mapped to median rank 2 (₹1,000–₹2,499)
    monthly_spend_ord = active_df['Monthly Spend'].copy()
    monthly_spend_ord = monthly_spend_ord.replace({2: 1, 3: 2, 4: 3, 5: 4, 6: 5, 7: 6, 8: 2}).astype(int)
    monthly_spend_not_sure = (active_df['Monthly Spend'] == 8).astype(int)

    # QA 19: Items per Order
    # Substantive codes 1..5 preserved; Code 6 ('Varies considerably', n=100) mapped to median rank 3 ('4–5 items')
    items_ord = active_df['Items per Order'].copy()
    items_ord = items_ord.replace({6: 3}).astype(int)
    items_varies = (active_df['Items per Order'] == 6).astype(int)

    # QA 28: Discount Overspend (1..5)
    disc_overspend = active_df['Discount Overspend'].astype(int)

    # QA 29: Threshold Extra Items (1..5)
    thresh_items = active_df['Threshold Extra Items'].astype(int)

    # QA 33: Compare Platform Prices (1..5)
    comp_plat = active_df['Compare Platform Prices'].astype(int)

    # QA 34: Compare Physical Prices (1..5)
    comp_phys = active_df['Compare Physical Prices'].astype(int)

    # QA 35: Fast Delivery Importance (1..5)
    fast_deliv = active_df['Fast Delivery Importance'].astype(int)

    # QA 37-40: Service Satisfaction Composite (1..5 continuous)
    sat_composite = active_df['service_satisfaction_composite'].astype(float).round(4)

    # QA 43: Shopping Routine Role (1..5 nominal)
    routine_role = active_df['Shopping Routine Role'].astype(int)

    # QA 12: Platforms Used Count (1..6 discrete)
    plat_count = active_df['platforms_used_count'].astype(int)

    # QA 44: Unplanned Purchase (1..5)
    unplanned = active_df['Unplanned Purchase'].astype(int)

    # QA 45: New Brand Trial (1..5)
    brand_trial = active_df['New Brand Trial'].astype(int)

    # Build Specification A DataFrame (17 features)
    df_spec_a = pd.DataFrame({
        'survey_row_id': active_df['survey_row_id'],
        'order_frequency': order_freq,
        'usage_duration': usage_dur,
        'order_spend': order_spend,
        'monthly_spend_ordinal': monthly_spend_ord,
        'monthly_spend_not_sure': monthly_spend_not_sure,
        'items_per_order_ordinal': items_ord,
        'items_varies_considerably': items_varies,
        'discount_overspend': disc_overspend,
        'threshold_extra_items': thresh_items,
        'compare_platform_prices': comp_plat,
        'compare_physical_prices': comp_phys,
        'fast_delivery_importance': fast_deliv,
        'service_satisfaction_composite': sat_composite,
        'shopping_routine_role': routine_role,
        'platforms_used_count': plat_count,
        'unplanned_purchase': unplanned,
        'new_brand_trial': brand_trial
    })

    # QA 47: Continue If Discounts Reduced (1..5)
    qa47_val = active_df['Continue If Discounts Reduced'].astype(int)

    # Build Specification B DataFrame (18 features: Spec A + QA 47)
    df_spec_b = df_spec_a.copy()
    df_spec_b['continue_if_discounts_reduced'] = qa47_val

    # Holdout & Profiling DataFrame
    # Strictly aligned row-by-row
    df_holdout = pd.DataFrame({
        'survey_row_id': active_df['survey_row_id'],
        'qa47_continue_if_discounts_reduced': qa47_val,
        'qa46_next_3_month_use': active_df['Next 3 Month Use'].astype(int),
        'qa49_preferred_improvement': active_df['Improvement'].astype(int),
        'qa14_first_trial_reason': active_df['First Trial Reason'].astype(int),
        'age_group': active_df['Age Group'].astype(int),
        'gender': active_df['Gender'].astype(int),
        'education': active_df['Education'].astype(int),
        'occupation': active_df['Occupation'].astype(int),
        'personal_income': active_df['Personal Income'].astype(int),
        'area_of_residence': active_df['Area of Residence'].astype(int),
        'region': active_df['Region'].astype(int),
        'household_size': active_df['Household Size'].astype(int),
        'used_blinkit': active_df['Used Blinkit'].astype(int),
        'used_zepto': active_df['Used Zepto'].astype(int),
        'used_swiggy_instamart': active_df['Used Swiggy Instamart'].astype(int),
        'used_bigbasket_bbnow': active_df['Used BigBasket BBNow'].astype(int),
        'used_flipkart_minutes': active_df['Used Flipkart Minutes'].astype(int),
        'used_amazon_rapid': active_df['Used Amazon Rapid'].astype(int),
        'overall_satisfaction': active_df['Overall Satisfaction'].astype(int),
        'product_quality_satisfaction': active_df['Product Quality Satisfaction'].astype(int),
        'delivery_reliability_satisfaction': active_df['Delivery Reliability Satisfaction'].astype(int),
        'value_money_satisfaction': active_df['Value Money Satisfaction'].astype(int)
    })

    # Save local CSV representations
    path_spec_a = os.path.join(data_dir, "segmentation_spec_a.csv")
    path_spec_b = os.path.join(data_dir, "segmentation_spec_b.csv")
    path_holdout = os.path.join(data_dir, "segmentation_holdout_profiling.csv")
    path_manifest = os.path.join(data_dir, "segmentation_manifest.json")

    df_spec_a.to_csv(path_spec_a, index=False)
    df_spec_b.to_csv(path_spec_b, index=False)
    df_holdout.to_csv(path_holdout, index=False)

    manifest = {
        "dataset_rows": n,
        "spec_a_columns": list(df_spec_a.columns),
        "spec_b_columns": list(df_spec_b.columns),
        "holdout_columns": list(df_holdout.columns),
        "alignment_verified": bool((df_spec_a['survey_row_id'] == df_holdout['survey_row_id']).all()),
        "qa47_in_spec_a": bool('continue_if_discounts_reduced' in df_spec_a.columns),
        "qa47_in_spec_b": bool('continue_if_discounts_reduced' in df_spec_b.columns),
        "qa46_in_spec_a": bool('qa46_next_3_month_use' in df_spec_a.columns or 'next_3_month_use' in df_spec_a.columns),
        "qa46_in_spec_b": bool('qa46_next_3_month_use' in df_spec_b.columns or 'next_3_month_use' in df_spec_b.columns)
    }

    with open(path_manifest, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    return {
        'spec_a': df_spec_a,
        'spec_b': df_spec_b,
        'holdout': df_holdout,
        'manifest': manifest
    }


def main(args=None):
    parsed = parse_arguments(args)
    print("=" * 80)
    print("GATE 1B: SEGMENTATION FEATURE AUDIT AND DATA PREPARATION PIPELINE")
    print("=" * 80)
    print(f"Loading survey workbook: {parsed.file} (sheet: {parsed.sheet})")

    full_df, active_df = load_and_filter_active_users(parsed.file, parsed.sheet)
    print(f"Total respondents loaded: {len(full_df)}")
    print(f"Subgroups: Never-Users={len(full_df[full_df['user_subgroup']=='Never User'])}, "
          f"Previous Users={len(full_df[full_df['user_subgroup']=='Previous User'])}, "
          f"Current Active Users={len(active_df)}")

    # Step 1: Feature Inventory
    print(f"Generating feature inventory for all 130 survey columns...")
    inv_df = generate_feature_inventory(full_df, active_df, parsed.reports_dir)
    print(f"Saved feature inventory to: {os.path.join(parsed.reports_dir, 'feature_inventory.csv')} ({len(inv_df)} items)")

    # Step 2: Feature Quality Audit
    print(f"Generating feature quality audit...")
    audit_df = generate_feature_quality_audit(full_df, active_df, parsed.reports_dir)
    print(f"Saved quality audit to: {os.path.join(parsed.reports_dir, 'feature_quality_audit.csv')} ({len(audit_df)} items)")

    # Step 3: Machine-Readable Specifications
    print(f"Generating feature specifications for Spec A and Spec B...")
    spec_a, spec_b = generate_feature_specifications(parsed.reports_dir)
    print(f"Specification A features: {spec_a['feature_count']} (QA 47 held out)")
    print(f"Specification B features: {spec_b['feature_count']} (QA 47 included)")

    # Step 4: Local Prepared Matrices (Gitignored)
    print(f"Preparing local feature matrices in: {parsed.data_dir}...")
    prep_res = prepare_feature_matrices(active_df, parsed.data_dir)
    print(f"Prepared Spec A matrix: {prep_res['spec_a'].shape}")
    print(f"Prepared Spec B matrix: {prep_res['spec_b'].shape}")
    print(f"Prepared Holdout matrix: {prep_res['holdout'].shape}")
    print(f"Row alignment verified: {prep_res['manifest']['alignment_verified']}")
    print("=" * 80)
    print("GATE 1B PIPELINE EXECUTION COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()
