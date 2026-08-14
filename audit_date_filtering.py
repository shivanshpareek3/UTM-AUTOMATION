import pandas as pd
import datetime
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__))))
from src.ingestion import read_file
from src.inspection import load_aliases, map_columns
from src.pipeline import run_pipeline

print("--- FINAL DATE-FILTERING AUDIT ---\n")

leads_file = '/Users/apple/Downloads/12-08-2026_leads.csv'
sales_file = '/Users/apple/Downloads/12-08-2026_sales(1).csv'

leads_raw = read_file(leads_file)
sales_raw = read_file(sales_file)

print(f"1. Exact column names detected in Satyam Lead file:\n{list(leads_raw.columns)}\n")
print(f"2. Exact column names detected in Satyam Sales file:\n{list(sales_raw.columns)}\n")

aliases = load_aliases()
leads_mapped = map_columns(leads_raw, aliases)
sales_mapped = map_columns(sales_raw, aliases)

print("--- After Mapping ---")
print(f"Lead mapped columns: {list(leads_mapped.columns)}")
print(f"Sales mapped columns: {list(sales_mapped.columns)}\n")

print("3. Which column is being used as the Sales date source.")
print("It defaults to 'Actual Sale Date' in Streamlit, which looks for 'sale_date'.\n")

print("4. Whether Sales actually contain usable dates:")
if 'sale_date' in sales_mapped.columns:
    print(sales_mapped['sale_date'].head())
    s_dates = pd.to_datetime(sales_mapped['sale_date'], errors='coerce').dropna()
    print(f"Usable sale dates count: {len(s_dates)} out of {len(sales_mapped)} rows")
else:
    print("NO 'sale_date' column found after mapping.")

print("\n5. Whether Leads actually contain usable registration dates:")
if 'registration_date' in leads_mapped.columns:
    print(leads_mapped['registration_date'].head())
    l_dates = pd.to_datetime(leads_mapped['registration_date'], errors='coerce').dropna()
    print(f"Usable lead dates count: {len(l_dates)} out of {len(leads_mapped)} rows")
else:
    print("NO 'registration_date' column found after mapping.")
print("")

meta_files = [
    '/Users/apple/Downloads/FML-X-Satyam-2-Campaigns-1-Aug-2026-12-Aug-2026.csv',
    '/Users/apple/Downloads/SSA-X-SATYAM-KHANDELWAL-Campaigns-1-Aug-2026-12-Aug-2026.csv'
]
meta_dfs = [read_file(f) for f in meta_files]
meta_df = pd.concat(meta_dfs, ignore_index=True)
meta_df = map_columns(meta_df, aliases)

base_settings = {
    'report_name': 'Audit',
    'client_name': 'Satyam',
    'cutoff_date': '2026-08-01',
    'fallback_price': 8999.0,
    'zero_roi_threshold': 5000.0,
    'currency': 'INR',
    'sale_date_source': 'Actual Sale Date', 
    'payment_status_source': 'Treat All Imported Sales as Successful',
    'amount_source': 'Actual Order Amount' if 'order_amount' in sales_mapped.columns else 'Fallback Price Per Sale',
    'report_type': 'Custom'
}

def run_test(start, end, label):
    print(f"--- Testing Period: {label} ({start} -> {end}) ---")
    settings = base_settings.copy()
    settings.update({
        'lead_sales_start_date': start, 'lead_sales_end_date': end,
        'meta_start_date': start, 'meta_end_date': end
    })
    
    print(f"Sales BEFORE pipeline: {len(sales_mapped)}")
    metrics, _, _ = run_pipeline(leads_mapped.copy(), sales_mapped.copy(), [meta_df.copy()], settings, f"output/audit_{label}.xlsx")
    print(f"Sales AFTER pipeline (total_sales metrics): {metrics['total_sales']}")
    print(f"Attributed Sales: {metrics['attributed_sales']}\n")

print("7. Show the number of Sales BEFORE date filtering and AFTER date filtering for each of these periods:")
run_test("2026-08-01", "2026-08-12", "A_1_12")
run_test("2026-08-05", "2026-08-10", "B_5_10")
run_test("2020-01-01", "2029-12-31", "C_Full")

print("10. Testing completely outside available data: 2025-01-01 -> 2025-01-31")
run_test("2025-01-01", "2025-01-31", "D_Outside")

# 11. Test a period where only part of the available data should be included
print("11. To test partial data inclusion, I will mock a dataset with sales dates from 2026-08-01 to 2026-08-10, and filter 2026-08-05 to 2026-08-10.")
mock_sales = sales_mapped.copy()
mock_sales['sale_date'] = pd.date_range(start='2026-08-01', periods=len(mock_sales), freq='D') # 41 days
settings = base_settings.copy()
settings.update({
    'lead_sales_start_date': '2026-08-05', 'lead_sales_end_date': '2026-08-10',
    'meta_start_date': '2026-08-05', 'meta_end_date': '2026-08-10'
})
metrics_mock, _, _ = run_pipeline(leads_mapped.copy(), mock_sales, [meta_df.copy()], settings, f"output/audit_partial.xlsx")
print(f"Sales BEFORE pipeline: {len(mock_sales)}")
print(f"Sales AFTER pipeline with specific partial dates: {metrics_mock['total_sales']}")

