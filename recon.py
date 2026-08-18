import pandas as pd
import sys
import os

sys.path.append(os.path.abspath('.'))

from src.ingestion import read_file
from src.inspection import load_aliases, map_columns
from src.pipeline import run_pipeline

leads_file = '/Users/apple/Downloads/20260815_053436_GlobalJobMasterclass1530328_subscriber.csv'
sales_file = '/Users/apple/Downloads/15th Aug - Sheet3.csv'
meta_files = [
    '/Users/apple/Downloads/FML-X-ABHISHEK-PAL-Campaigns-8-Aug-2026-14-Aug-2026.csv'
]

leads_df = read_file(leads_file)
sales_df = read_file(sales_file)
meta_dfs = [read_file(f) for f in meta_files]

settings = {
    'report_name': 'Reconciliation Test',
    'client_name': 'Abhishek Pal',
    'cutoff_date': '2026-08-01',
    'fallback_price': 8999.0,
    'zero_roi_threshold': 5000.0,
    'currency': 'INR',
    'sale_date_source': 'Actual Sale Date',
    'payment_status_source': 'Treat All Imported Sales as Successful', 
    'amount_source': 'Actual Order Amount' if 'order_amount' in sales_df.columns else 'Fallback Price Per Sale',
    'report_type': 'Custom',
    'lead_sales_start_date': "2026-08-01", 'lead_sales_end_date': "2026-08-20",
    'meta_start_date': "2026-08-01", 'meta_end_date': "2026-08-20"
}

metrics, ver_df, xl_path = run_pipeline(leads_df.copy(), sales_df.copy(), [m.copy() for m in meta_dfs], settings, "output/recon_test.xlsx")

# Output the markdown table
sales_df_mapped = map_columns(sales_df, load_aliases())
from src.leads import process_leads
from src.sales import process_sales
from src.attribution import attribute_sales

leads_mapped = map_columns(leads_df, load_aliases())
leads_proc = process_leads(leads_mapped, ['[ignore]'])
sales_proc, _ = process_sales(sales_df_mapped, settings)

sales_attr = attribute_sales(sales_proc, leads_proc, ['[ignore]'])

md = "| Sale ID | Email | Phone | Match Level | Attribution Source | Campaign | Ad Set | Creative |\n"
md += "|---|---|---|---|---|---|---|---|\n"

for idx, row in sales_attr.iterrows():
    md += f"| {row.get('sale_id','')} | {row.get('email','')} | {row.get('phone','')} | {row.get('match_level','')} | {row.get('attribution_source','')} | {row.get('campaign','')} | {row.get('ad_set','')} | {row.get('ad_creative','')} |\n"

with open("/Users/apple/.gemini/antigravity-ide/brain/a00d7520-454b-47a8-82f3-9b5835288fe3/reconciliation_table.md", "w") as f:
    f.write(md)

print("Attributed:", len(sales_attr[sales_attr['attribution_source'] != 'Unattributed']))
print("Unattributed:", len(sales_attr[sales_attr['attribution_source'] == 'Unattributed']))
print("Total:", len(sales_attr))

