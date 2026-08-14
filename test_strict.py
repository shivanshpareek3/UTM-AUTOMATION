import pandas as pd
import json
import sys
import os

sys.path.append(os.path.abspath('.'))
from src.inspection import map_columns

leads_df = pd.read_csv('/Users/apple/Downloads/12-08-2026_leads.csv')
with open('config/aliases.json', 'r') as f:
    aliases = json.load(f)

leads_df = map_columns(leads_df, aliases)

strict_leads = ['email', 'registration_date', 'campaign', 'ad_set', 'ad_creative']
missing = [c for c in strict_leads if c not in leads_df.columns]
print("Missing strict leads:", missing)

sales_df = pd.read_csv('/Users/apple/Downloads/12-08-2026_sales(1).csv')
sales_df = map_columns(sales_df, aliases)
strict_sales = ['email']
missing_sales = [c for c in strict_sales if c not in sales_df.columns]
print("Missing strict sales:", missing_sales)

meta_df = pd.read_csv('/Users/apple/Downloads/FML-X-Satyam-2-Campaigns-1-Aug-2026-12-Aug-2026.csv')
meta_df = map_columns(meta_df, aliases)
strict_meta = ['campaign', 'ad_set', 'ad', 'spend', 'Day']
missing_meta = [c for c in strict_meta if c not in meta_df.columns]
print("Missing strict meta:", missing_meta)
