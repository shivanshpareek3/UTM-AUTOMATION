import pandas as pd
import json
import sys
import os

sys.path.append(os.path.abspath('.'))
from src.ingestion import read_file
from src.inspection import load_aliases, map_columns
from src.normalization import unify_campaign_name
from src.leads import process_leads
from src.sales import process_sales
from src.attribution import attribute_sales

leads_file = '/Users/apple/Downloads/20260815_053436_GlobalJobMasterclass1530328_subscriber.csv'
sales_file = '/Users/apple/Downloads/15th Aug - Sheet3.csv'
meta1_file = '/Users/apple/Downloads/FML-X-ABHISHEK-PAL-Campaigns-8-Aug-2026-14-Aug-2026.csv'
meta2_file = '/Users/apple/Downloads/A-hishek-Pal---FML-Campaigns-8-Aug-2026-14-Aug-2026.xlsx'

leads_df = read_file(leads_file)
sales_df = read_file(sales_file)
meta1 = read_file(meta1_file)
meta2 = read_file(meta2_file)

aliases = load_aliases()
leads_mapped = map_columns(leads_df, aliases)
sales_mapped = map_columns(sales_df, aliases)

settings = {
    'cutoff_date': '2026-08-01',
    'fallback_price': 8999.0,
    'currency': 'INR',
    'sale_date_source': 'Lead Registration Date',
    'payment_status_source': 'Treat All Imported Sales as Successful', 
    'amount_source': 'Fallback Price Per Sale'
}
leads_proc = process_leads(leads_mapped, settings)
sales_out, unresolved = process_sales(sales_mapped, settings)
sales_attr = attribute_sales(sales_out, leads_proc, settings)

sales_attr['camp_norm'] = sales_attr['campaign'].apply(unify_campaign_name) if 'campaign' in sales_attr.columns else ""

print("Sales Distribution by Campaign (Our extraction):")
print(sales_attr['camp_norm'].value_counts())

# Now let's try to map without unify_campaign_name, or check exact strings
print("\nExact Campaign Strings in Sales:")
print(sales_attr['campaign'].value_counts())

meta1['camp_norm'] = meta1.get('Campaign name', pd.Series(dtype=str)).apply(unify_campaign_name)
meta1_spend = meta1.groupby('camp_norm')['Amount spent (INR)'].sum().reset_index()

# Check what happens if we only use one meta file
print("\nMeta 1 Spend by Campaign:")
for _, r in meta1_spend.sort_values('Amount spent (INR)', ascending=False).head(10).iterrows():
    if r['camp_norm'] != '':
        print(f"{r['camp_norm']}: {r['Amount spent (INR)']}")

# Check what happens if we only use Meta 2
# Note: Meta2 is Abhishek Pal - FML Ad account Report
if 'Campaign name' in meta2.columns:
    meta2['camp_norm'] = meta2['Campaign name'].apply(unify_campaign_name)
    col = 'Amount spent (INR)' if 'Amount spent (INR)' in meta2.columns else 'Amount Spent'
    meta2_spend = meta2.groupby('camp_norm')[col].sum().reset_index()
    print("\nMeta 2 Spend by Campaign:")
    for _, r in meta2_spend.sort_values(col, ascending=False).head(10).iterrows():
        if r['camp_norm'] != '':
            print(f"{r['camp_norm']}: {r[col]}")
