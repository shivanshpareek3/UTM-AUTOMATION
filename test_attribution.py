import pandas as pd
import os
import sys
sys.path.append(os.path.abspath('.'))
from src.pipeline import run_pipeline

leads_df = pd.read_csv('/Users/apple/Downloads/12-08-2026_leads.csv')
sales_df = pd.read_csv('/Users/apple/Downloads/12-08-2026_sales(1).csv')
meta_df = pd.read_csv('/Users/apple/Downloads/FML-X-Satyam-2-Campaigns-1-Aug-2026-12-Aug-2026.csv')

settings = {
    'report_name': 'Test',
    'cutoff_date': '2024-01-01',
    'fallback_price': 8999.0,
    'zero_roi_threshold': 5000.0,
    'currency': 'INR',
    'sale_date_source': 'Actual Sale Date',
    'payment_status_source': 'Actual Payment Status',
    'amount_source': 'Actual Order Amount',
    'custom_sale_date': None,
    'report_type': 'Custom',
    'lead_sales_start_date': '2026-08-01',
    'lead_sales_end_date': '2026-08-12',
    'meta_start_date': '2026-08-01',
    'meta_end_date': '2026-08-12',
    'lead_start_date': '2026-08-01',
    'lead_end_date': '2026-08-12',
    'ad_start_date': '2026-08-01',
    'ad_end_date': '2026-08-12'
}

_, ver_df, _ = run_pipeline(leads_df, sales_df, [meta_df], settings, 'test_attr.xlsx')

import sqlite3
# Load the data directly to see what happened
from src.inspection import load_aliases, map_columns
leads_df = map_columns(leads_df, load_aliases())
sales_df = map_columns(sales_df, load_aliases())
meta_df = map_columns(meta_df, load_aliases())

print("Leads campaigns:")
print(leads_df['campaign'].dropna().unique())
print("\nMeta campaigns:")
print(meta_df['campaign'].dropna().unique())

import src.attribution as attr
import src.spend as spend

sales_attr = attr.attribute_sales(sales_df, leads_df, ['[ignore]'])
print("\nMatch levels:")
print(sales_attr['match_level'].value_counts())

sales_alloc, camp_sp, adset_sp, ad_sp = spend.allocate_spend(sales_attr, meta_df, '2026-08-01', '2026-08-12')
print("\nAttributed spend sum:", sales_alloc['attributed_spend'].sum())
print("\nMeta spend sum:", meta_df['Amount Spent'].sum())

print("\nCampaign norms in sales:")
print(sales_alloc['camp_norm'].dropna().unique())

print("\nCampaign norms in meta:")
print(meta_df['campaign'].apply(lambda x: spend.unify_campaign_name(x)).unique())

