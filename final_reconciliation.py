import pandas as pd
import sys
import os

sys.path.append(os.path.abspath('.'))
from src.ingestion import read_file
from src.inspection import load_aliases, map_columns
from src.normalization import unify_campaign_name
from src.leads import process_leads
from src.sales import process_sales
from src.attribution import attribute_sales
from src.spend import allocate_spend

leads_file = '/Users/apple/Downloads/20260815_053436_GlobalJobMasterclass1530328_subscriber.csv'
sales_file = '/Users/apple/Downloads/15th Aug - Sheet3.csv'
meta1_file = '/Users/apple/Downloads/FML-X-ABHISHEK-PAL-Campaigns-8-Aug-2026-14-Aug-2026.csv'
meta2_file = '/Users/apple/Downloads/A-hishek-Pal---FML-Campaigns-8-Aug-2026-14-Aug-2026.xlsx'

leads_df = read_file(leads_file)
sales_df = read_file(sales_file)
meta1 = read_file(meta1_file)
meta2 = read_file(meta2_file)
meta_df = pd.concat([meta1, meta2], ignore_index=True)

aliases = load_aliases()
leads_mapped = map_columns(leads_df, aliases)
sales_mapped = map_columns(sales_df, aliases)
meta_mapped = map_columns(meta_df, aliases)

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

sales_alloc, camp_spend, _, _ = allocate_spend(
    sales_attr, meta_mapped, leads_proc, '2026-08-01', '2026-08-20'
)

# Output exact mismatch
meta1_mapped = map_columns(meta1, aliases)
meta2_mapped = map_columns(meta2, aliases)

meta1_mapped['camp_norm'] = meta1_mapped['campaign'].apply(unify_campaign_name)
meta2_mapped['camp_norm'] = meta2_mapped['campaign'].apply(unify_campaign_name)
meta_mapped['camp_norm'] = meta_mapped['campaign'].apply(unify_campaign_name)

m1_spend = meta1_mapped.groupby('camp_norm')['spend'].sum()
m2_spend = meta2_mapped.groupby('camp_norm')['spend'].sum()

print("==================================================")
print("EXACT DISCREPANCY ANALYSIS")
print("==================================================")

sales_counts = sales_attr[sales_attr['match_level'] != 'Unattributed'].groupby(sales_attr['campaign'].apply(unify_campaign_name)).size()

total_attr_spend = 0
total_unalloc_spend = 0

print(f"{'Campaign':<45} | {'File 1 Spend':<15} | {'File 2 Spend':<15} | {'Sales':<5} | {'Attributed Spend':<20}")
print("-" * 110)
for camp in meta_mapped['camp_norm'].unique():
    if not camp: continue
    s1 = m1_spend.get(camp, 0)
    s2 = m2_spend.get(camp, 0)
    sales = sales_counts.get(camp, 0)
    
    if sales > 0:
        attr = s1 + s2
        total_attr_spend += attr
    else:
        attr = 0
        total_unalloc_spend += (s1 + s2)
        
    if s1 > 0 or s2 > 0:
        print(f"{camp:<45} | {s1:<15.2f} | {s2:<15.2f} | {sales:<5} | {attr:<20.2f}")

print("-" * 110)
print(f"Total Attributed Spend: {total_attr_spend:.2f} (Expected: 282120.59)")
print(f"Total Unallocated Spend: {total_unalloc_spend:.2f} (Expected: 173926.96)")
