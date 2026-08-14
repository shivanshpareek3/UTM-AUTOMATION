import pandas as pd
from src.pipeline import run_pipeline
from src.ingestion import read_file

print("Loading data...")
leads_df = read_file('/Users/apple/Downloads/Lead Sheet Abhishek pal .csv')
sales_df = read_file('/Users/apple/Downloads/Sales .csv')
m1 = read_file('/Users/apple/Downloads/Abhishek-Pal-FML-Ad-account-Report.xlsx')
m2 = read_file('/Users/apple/Downloads/FML-X-ABHISHEK-PAL-Ad-account-Report.xlsx')

settings = {
    'report_name': 'Window Test Report',
    'client_name': 'Abhishek Pal',
    'lead_start_date': '2026-01-01',
    'lead_end_date': '2026-12-31',
    'ad_start_date': '2026-08-01',
    'ad_end_date': '2026-08-07',
    'cutoff_date': '2026-08-01',
    'sale_date_source': 'Lead Registration Date',
    'payment_status_source': 'Treat All Imported Sales as Successful',
    'amount_source': 'Fallback Price Per Sale',
    'fallback_price': 8999.0,
    'currency': 'INR',
    'zero_roi_threshold': 5000
}

output_path = 'output/window_test_report.xlsx'
metrics, ver_df, path = run_pipeline(leads_df, sales_df, [m1, m2], settings, output_path)

print(f"Excel Path: {path}")

xl = pd.ExcelFile(path)
settings_df = xl.parse('1. ⚙ Settings & Run Log')
for index, row in settings_df.iterrows():
    if row.iloc[0] in ['Lead Tracking Start Date', 'Lead Tracking End Date', 'Ads Tracking Start Date', 'Ads Tracking End Date']:
        print(f"{row.iloc[0]}: {row.iloc[1]}")
