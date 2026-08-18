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
    '/Users/apple/Downloads/FML-X-ABHISHEK-PAL-Campaigns-8-Aug-2026-14-Aug-2026.csv',
    '/Users/apple/Downloads/A-hishek-Pal---FML-Campaigns-8-Aug-2026-14-Aug-2026.xlsx'
]

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

# Run the normal pipeline to get the baseline and output excel
metrics, ver_df, xl_path = run_pipeline(leads_df.copy(), sales_df.copy(), [m.copy() for m in meta_dfs], settings, "output/audit.xlsx")

# Run allocate_spend manually for reconciliation table
from src.normalization import unify_campaign_name
aliases = load_aliases()
leads_mapped = map_columns(leads_df, aliases)
sales_mapped = map_columns(sales_df, aliases)

meta_mapped_dfs = [map_columns(m, aliases) for m in meta_dfs]
meta_mapped = pd.concat(meta_mapped_dfs, ignore_index=True)
if not meta_mapped.empty:
    meta_mapped = meta_mapped.drop_duplicates(ignore_index=True)
if 'ad' in meta_mapped.columns:
    meta_mapped = meta_mapped[~meta_mapped['ad'].astype(str).str.lower().str.strip().isin(['all', 'nan', ''])]
    
# Fix Day extraction logic
if 'Reporting starts' in meta_mapped.columns and 'Day' not in meta_mapped.columns:
    meta_mapped['Day'] = meta_mapped['Reporting starts']

from src.leads import process_leads
from src.sales import process_sales
from src.attribution import attribute_sales
from src.spend import allocate_spend

leads_proc = process_leads(leads_mapped, ['[ignore]'])
sales_proc, _ = process_sales(sales_mapped, settings)
sales_attr = attribute_sales(sales_proc, leads_proc, ['[ignore]'])

sales_out, camp_spend_out, adset_spend_out, ad_spend_out = allocate_spend(sales_attr.copy(), meta_mapped.copy(), leads_proc, settings['meta_start_date'], settings['meta_end_date'])

# Build reconciliation
# Apply window filter to leads for correct CPL calculation
try:
    sdt = pd.to_datetime(settings['lead_sales_start_date'])
    edt = pd.to_datetime(settings['lead_sales_end_date'])
    if edt.hour == 0 and edt.minute == 0 and edt.second == 0:
        edt = edt + pd.Timedelta(days=1, microseconds=-1)
    mask = (leads_proc['registration_date'] >= sdt) & (leads_proc['registration_date'] <= edt)
    leads_in_window = leads_proc[mask].copy()
except Exception:
    leads_in_window = leads_proc.copy()

leads_in_window['camp_norm'] = leads_in_window['campaign'].apply(unify_campaign_name) if 'campaign' in leads_in_window.columns else ""
camp_leads = leads_in_window.groupby('camp_norm').size().reset_index(name='Campaign Leads')

sales_out['camp_norm'] = sales_out['campaign'].apply(unify_campaign_name) if 'campaign' in sales_out.columns else ""
camp_paid = sales_out[sales_out['match_level'] != 'Unattributed'].groupby('camp_norm').size().reset_index(name='Paid/Attributed Leads')
camp_attr_spend = sales_out[sales_out['match_level'] != 'Unattributed'].groupby('camp_norm')['attributed_spend'].sum().reset_index(name='Actual Attributed Spend')

recon = pd.merge(camp_spend_out, camp_leads, on='camp_norm', how='left')
recon['Campaign Leads'] = recon['Campaign Leads'].fillna(0)
recon = pd.merge(recon, camp_paid, on='camp_norm', how='left')
recon = pd.merge(recon, camp_attr_spend, on='camp_norm', how='left')

recon = recon.fillna(0)
recon['Campaign CPL'] = recon.apply(lambda r: r['Amount Spent'] / r['Campaign Leads'] if r['Campaign Leads'] > 0 else 0.0, axis=1)
recon['Expected Attributed Spend'] = recon['Campaign CPL'] * recon['Paid/Attributed Leads']
recon['Difference'] = recon['Actual Attributed Spend'] - recon['Expected Attributed Spend']


print("\n==================================================")
print("CAMPAIGN RECONCILIATION")
print("==================================================")
# Print markdown table
print("| Campaign | Campaign Leads | Paid/Attributed Leads | Campaign Spend | Campaign CPL | Expected Attributed Spend | Actual Attributed Spend | Difference |")
print("|---|---:|---:|---:|---:|---:|---:|---:|")
for _, r in recon.iterrows():
    print(f"| {r['camp_norm']} | {int(r['Campaign Leads'])} | {int(r['Paid/Attributed Leads'])} | {r['Amount Spent']:.2f} | {r['Campaign CPL']:.2f} | {r['Expected Attributed Spend']:.2f} | {r['Actual Attributed Spend']:.2f} | {r['Difference']:.2f} |")

print("\n==================================================")
print("TOTALS")
print("==================================================")
print(f"Total Leads: {metrics['total_leads']}")
print(f"Paid Leads: {metrics['paid_leads']}")
print(f"Unpaid Leads: {metrics['unpaid_leads']}")
print(f"Total Sales: {metrics['total_sales']}")
print(f"Attributed Sales: {metrics['attributed_sales']}")
print(f"Unattributed Sales: {metrics['unattributed_sales']}")
print(f"Total Revenue: {metrics['total_revenue']}")
print(f"Attributed Revenue: {metrics['attributed_revenue']}")
print(f"Unattributed Revenue: {metrics['unattributed_revenue']}")
print(f"Raw Meta Spend: {metrics['raw_meta_spend']}")
print(f"Attributed Spend: {metrics['attributed_spend']}")
print(f"Unallocated Spend: {metrics['unallocated_spend']}")
print(f"Profit: {metrics['profit']}")
print(f"ROAS: {metrics['roas']}")
print(f"ROI %: {metrics['roi_percent']}")
print(f"CAC: {metrics['cac']}")
