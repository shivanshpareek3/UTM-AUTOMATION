import pandas as pd
import json
from src.pipeline import run_pipeline
from src.ingestion import read_file
from src.inspection import load_aliases, map_columns

def create_baseline():
    aliases = load_aliases()
    leads = map_columns(read_file('/Users/apple/Downloads/Lead Sheet Abhishek pal .csv'), aliases)
    sales = map_columns(read_file('/Users/apple/Downloads/Sales .csv'), aliases)
    m1 = map_columns(read_file('/Users/apple/Downloads/Abhishek-Pal-FML-Ad-account-Report.xlsx'), aliases)
    m2 = map_columns(read_file('/Users/apple/Downloads/FML-X-ABHISHEK-PAL-Ad-account-Report.xlsx'), aliases)
    
    settings = {
        'report_name': 'Baseline Report',
        'client_name': 'Abhishek Pal',
        'lead_start_date': '2026-01-01',
        'lead_end_date': '2026-12-31',
        'ad_start_date': '2026-01-01',
        'ad_end_date': '2026-12-31',
        'cutoff_date': '2026-01-01',
        'sale_date_source': 'Lead Registration Date',
        'payment_status_source': 'Treat All Imported Sales as Successful',
        'amount_source': 'Fallback Price Per Sale',
        'fallback_price': 8999.0,
        'zero_roi_threshold': 5000.0,
        'currency': 'INR'
    }
    
    metrics, ver_df, xl = run_pipeline(leads, sales, [m1, m2], settings, 'output/baseline.xlsx')
    
    print("\n--- BASELINE METRICS ---")
    print(f"Total Sales: {metrics['total_sales']}")
    print(f"Attributed Sales: {metrics['attributed_sales']}")
    print(f"Total Revenue: {metrics['total_revenue']}")
    print(f"Attributed Revenue: {metrics['attributed_revenue']}")
    print(f"Raw Meta Spend: {metrics['raw_meta_spend']}")
    print(f"Attributed Spend: {metrics['attributed_spend']}")
    print(f"Unallocated Spend: {metrics['unallocated_spend']}")
    print(f"Profit: {metrics['profit']}")
    print(f"ROAS: {metrics['roas']}")
    print(f"ROI: {metrics['roi_percent']}")
    print(f"CAC: {metrics['cac']}")
    print("------------------------\n")
    
if __name__ == "__main__":
    create_baseline()
