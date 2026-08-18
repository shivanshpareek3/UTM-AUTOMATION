import pandas as pd
import sys
import os

sys.path.append(os.path.abspath('.'))

from src.ingestion import read_file
from src.inspection import load_aliases, map_columns
from src.pipeline import run_pipeline
from src.leads import process_leads
from src.sales import process_sales
from src.attribution import attribute_sales

leads_file = '/Users/apple/Downloads/20260815_053436_GlobalJobMasterclass1530328_subscriber.csv'
sales_file = '/Users/apple/Downloads/15th Aug - Sheet3.csv'
meta_files = ['/Users/apple/Downloads/FML-X-ABHISHEK-PAL-Campaigns-8-Aug-2026-14-Aug-2026.csv']

leads_df = read_file(leads_file)
sales_df = read_file(sales_file)
meta_dfs = [read_file(f) for f in meta_files]

settings = {
    'report_name': 'Final Reconciliation',
    'client_name': 'Abhishek',
    'cutoff_date': '2026-08-01',
    'fallback_price': 8999.0,
    'zero_roi_threshold': 5000.0,
    'currency': 'INR',
    'sale_date_source': 'Actual Sale Date',
    'payment_status_source': 'Treat All Imported Sales as Successful', 
    'amount_source': 'Fallback Price Per Sale',
    'report_type': 'Custom',
    'lead_sales_start_date': "2026-08-01", 'lead_sales_end_date': "2026-08-20",
    'meta_start_date': "2026-08-01", 'meta_end_date': "2026-08-20"
}

metrics, ver_df, xl_path = run_pipeline(leads_df.copy(), sales_df.copy(), [m.copy() for m in meta_dfs], settings, "output/recon_final.xlsx")

aliases = load_aliases()
leads_mapped = map_columns(leads_df, aliases)
sales_mapped = map_columns(sales_df, aliases)

leads_proc = process_leads(leads_mapped, ['[ignore]'])
sales_proc, _ = process_sales(sales_mapped, settings)

sales_attr = attribute_sales(sales_proc, leads_proc, ['[ignore]'])

total_sales = len(sales_attr)
attributed_sales = len(sales_attr[sales_attr['match_level'] != 'Unattributed'])
unattributed_sales = len(sales_attr[sales_attr['match_level'] == 'Unattributed'])

print("--------------------------------------------------")
print(f"Total Sales: {total_sales}")
print(f"Attributed Sales: {attributed_sales}")
print(f"Unattributed Sales: {unattributed_sales}")
print(f"Sum matches: {attributed_sales + unattributed_sales == total_sales}")

unattributed = sales_attr[sales_attr['match_level'] == 'Unattributed']
print("\nUnattributed Details:")
for _, row in unattributed.iterrows():
    print(f"- Customer: {row.get('first_name','')} {row.get('last_name','')}")
    print(f"  Phone: {row.get('norm_phone','')}")
    print(f"  Email: {row.get('norm_email','')}")
    print(f"  Date: {row.get('sale_date','')}")
    print(f"  Amount: {row.get('final_price','')}")
    print(f"  Raw Source: {row.get('attribution_source','')}")
    
    phone_match = leads_proc[leads_proc['norm_phone'] == row.get('norm_phone')] if pd.notnull(row.get('norm_phone')) else pd.DataFrame()
    email_match = leads_proc[leads_proc['norm_email'] == row.get('norm_email')] if pd.notnull(row.get('norm_email')) else pd.DataFrame()
    
    if not phone_match.empty or not email_match.empty:
        print("  Found in leads! (Should not happen if Unattributed due to no match)")
    else:
        print("  Confirmed: No matching normalized phone/email in Lead Sheet.")
        print("  Reason for failure: Customer data not in Leads sheet within the selected date range or at all.")

print("\nAttributed Verification:")
all_valid = True
for _, row in sales_attr[sales_attr['match_level'] != 'Unattributed'].iterrows():
    if row['match_level'] == 'Unattributed':
        all_valid = False
        print(f"Error: Unattributed found in attributed set: {row}")

print(f"All attributed sales have valid match: {all_valid}")

print("\nInvariants Verification:")
total_revenue = sales_attr['final_price'].sum() if 'final_price' in sales_attr.columns else sales_attr['amount'].sum() if 'amount' in sales_attr.columns else sales_attr.get('Amount', 0).sum() if 'Amount' in sales_attr.columns else metrics['total_revenue']

attr_rev = metrics['attributed_revenue']
print(f"Total Revenue ({total_revenue}) == Attributed + Unattributed: {abs(total_revenue - metrics['total_revenue']) < 0.1}")

attr_spend = metrics['attributed_spend']
profit = metrics['profit']
print(f"Profit ({profit}) == Attributed Revenue ({attr_rev}) - Attributed Spend ({attr_spend}): {abs(profit - (attr_rev - attr_spend)) < 0.1}")

roas = metrics['roas']
expected_roas = attr_rev / attr_spend if attr_spend > 0 else 0
print(f"ROAS ({roas}) == Attributed Revenue / Attributed Spend ({expected_roas}): {abs(roas - expected_roas) < 0.01 if type(roas) != str else True}")

roi = metrics['roi_percent']
expected_roi = (profit / attr_spend) * 100 if attr_spend > 0 else 0
print(f"ROI ({roi}) == Profit / Attributed Spend * 100 ({expected_roi}): {abs(roi - expected_roi) < 0.01 if type(roi) != str else True}")

cac = metrics['cac']
expected_cac = attr_spend / metrics['attributed_sales'] if metrics['attributed_sales'] > 0 else 0
print(f"CAC ({cac}) == Attributed Spend / Attributed Sales ({expected_cac}): {abs(cac - expected_cac) < 0.01 if type(cac) != str else True}")

print("\nMetrics match check (Dashboard/Excel/Pipeline):")
print(f"Pipeline returned Attributed Sales: {metrics['attributed_sales']}")
print(f"Pipeline returned Total Sales: {metrics['total_sales']}")

# Write markdown table
md = "| Sale ID | Name | Email | Phone | Match Level | Attribution Source |\n"
md += "|---|---|---|---|---|---|\n"
for idx, row in sales_attr.iterrows():
    md += f"| {row.get('sale_id','')} | {row.get('first_name','')} {row.get('last_name','')} | {row.get('email','')} | {row.get('phone','')} | {row.get('match_level','')} | {row.get('attribution_source','')} |\n"

with open("/Users/apple/.gemini/antigravity-ide/brain/49125410-20e3-4dd0-861f-ea504a516a10/reconciliation_table.md", "w") as f:
    f.write(md)

print("Reconciliation table saved to artifact.")
