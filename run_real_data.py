import pandas as pd
import sys
import os

from src.pipeline import run_pipeline
from src.ingestion import read_file

def inspect_and_run(leads_path, sales_path, meta_paths):
    print("Loading data...")
    try:
        leads_df = pd.read_csv(leads_path)
    except UnicodeDecodeError:
        leads_df = pd.read_csv(leads_path, encoding='latin1')
        
    try:
        sales_df = pd.read_csv(sales_path)
    except UnicodeDecodeError:
        sales_df = pd.read_csv(sales_path, encoding='latin1')

    meta_dfs = []
    for m in meta_paths:
        meta_dfs.append(read_file(m))

    print(f"Leads columns: {leads_df.columns.tolist()}")
    print(f"Sales columns: {sales_df.columns.tolist()}")

    # Try to find dates
    lead_dates = []
    if 'registration date' in leads_df.columns:
        # Normalize the string format before converting
        leads_df['registration date'] = leads_df['registration date'].astype(str).str.replace(r'\s*\([A-Z]+\)', '', regex=True)
        lead_dates = pd.to_datetime(leads_df['registration date'], errors='coerce').dropna()
    elif 'created_at' in leads_df.columns:
        leads_df['created_at'] = leads_df['created_at'].astype(str).str.replace(r'\s*\([A-Z]+\)', '', regex=True)
        lead_dates = pd.to_datetime(leads_df['created_at'], errors='coerce').dropna()

    sale_dates = []
    if 'sale date' in sales_df.columns:
        sale_dates = pd.to_datetime(sales_df['sale date'], errors='coerce').dropna()
    elif 'order date' in sales_df.columns:
        sale_dates = pd.to_datetime(sales_df['order date'], errors='coerce').dropna()

    meta_dates = []
    for m_df in meta_dfs:
        if 'Reporting Starts' in m_df.columns:
            meta_dates.extend(pd.to_datetime(m_df['Reporting Starts'], errors='coerce').dropna().tolist())
        elif 'Day' in m_df.columns:
            meta_dates.extend(pd.to_datetime(m_df['Day'], errors='coerce').dropna().tolist())

    print("\n--- Date Ranges ---")
    if len(lead_dates) > 0:
        print(f"Lead date range: {lead_dates.min()} to {lead_dates.max()}")
    else:
        print("Lead date range: None found")
        
    if len(sale_dates) > 0:
        print(f"Sales date availability: {sale_dates.min()} to {sale_dates.max()}")
    else:
        print("Sales date availability: None found")
        
    if len(meta_dates) > 0:
        print(f"Meta spend date range: {min(meta_dates)} to {max(meta_dates)}")
        start_date = min(meta_dates).strftime('%Y-%m-%d')
        end_date = max(meta_dates).strftime('%Y-%m-%d')
    else:
        print("Meta spend date range: None found")
        start_date = '2026-01-01'
        end_date = '2026-12-31'

    # The user asked to use 2026-01-01 to 2026-12-31 for testing, but also "Do NOT hardcode 2024. First inspect their actual date ranges and automatically determine the correct reporting window"
    # Actually, in Phase 10 they said:
    # "Start Date: 2026-01-01, End Date: 2026-12-31, Sale Date Source: Lead Registration Date"
    # I'll use the Meta dates if available to bracket the exact end date, but to encompass all leads, maybe 2026-01-01 to 2026-12-31 is safest based on phase 10.
    
    # I'll use Phase 10 settings:
    settings = {
        'report_name': 'Real Data Test Report',
        'client_name': 'Abhishek Pal',
        'lead_start_date': '2026-01-01',
        'lead_end_date': '2026-12-31',
        'ad_start_date': '2026-01-01',
        'ad_end_date': '2026-12-31',
        'cutoff_date': '2026-08-01',
        'sale_date_source': 'Lead Registration Date',
        'payment_status_source': 'Treat All Imported Sales as Successful',
        'fallback_price': 8999.0,
        'currency': 'INR',
        'zero_roi_threshold': 5000
    }
    
    print(f"\nSelected lead window: {settings['lead_start_date']} to {settings['lead_end_date']}")
    print(f"Sale Date Source: {settings['sale_date_source']}")
    
    output_filepath = 'output/real_data_report.xlsx'
    
    metrics, ver_df, path = run_pipeline(leads_df, sales_df, meta_dfs, settings, output_filepath)
    
    print(f"\nFinal Excel path: {path}")

if __name__ == '__main__':
    leads = sys.argv[1]
    sales = sys.argv[2]
    meta_paths = sys.argv[3:]
    inspect_and_run(leads, sales, meta_paths)
