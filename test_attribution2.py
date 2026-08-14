import pandas as pd
import os
import sys
sys.path.append(os.path.abspath('.'))
from src.pipeline import run_pipeline
import src.attribution as attr
import src.spend as spend
from src.inspection import load_aliases, map_columns

leads_df = pd.read_csv('/Users/apple/Downloads/12-08-2026_leads.csv')
sales_df = pd.read_csv('/Users/apple/Downloads/12-08-2026_sales(1).csv')
meta_df = pd.read_csv('/Users/apple/Downloads/FML-X-Satyam-2-Campaigns-1-Aug-2026-12-Aug-2026.csv')

leads_df = map_columns(leads_df, load_aliases())
sales_df = map_columns(sales_df, load_aliases())
meta_df = map_columns(meta_df, load_aliases())

sales_attr = attr.attribute_sales(sales_df, leads_df, ['[ignore]'])
sales_alloc, camp_sp, adset_sp, ad_sp = spend.allocate_spend(sales_attr, meta_df, '2026-08-01', '2026-08-12')

print("\nAttributed spend sum:", sales_alloc['attributed_spend'].sum())
print("\nCampaign norms in sales that have match_level != Unattributed:")
print(sales_alloc[sales_alloc['match_level'] != 'Unattributed']['camp_norm'].unique())

print("\nCampaign norms in meta:")
print(camp_sp['camp_norm'].unique() if not camp_sp.empty else "No camp_sp")


print("\nCampaign spend dataframe:")
print(camp_sp)

print("\nAdset summary:")
print(adset_sp)

print("\nSales count by match level:")
print(sales_attr['match_level'].value_counts())

