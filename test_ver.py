import pandas as pd
import json
import os
import sys

sys.path.append(os.path.abspath('.'))
from src.pipeline import run_pipeline
from src.inspection import load_aliases

leads_df = pd.read_csv('/Users/apple/Downloads/12-08-2026_leads.csv')
sales_df = pd.read_csv('/Users/apple/Downloads/12-08-2026_sales(1).csv')
meta_df = pd.read_csv('/Users/apple/Downloads/FML-X-Satyam-2-Campaigns-1-Aug-2026-12-Aug-2026.csv')

settings = {
    'report_name': 'test',
    'cutoff_date': '2024-01-01',
    'fallback_price': 8999.0,
    'zero_roi_threshold': 5000.0,
    'currency': 'INR',
    'sale_date_source': 'Actual Sale Date',
    'payment_status_source': 'Actual Payment Status',
    'amount_source': 'Actual Order Amount',
    'custom_sale_date': None,
    'report_type': 'Custom',
    'lead_sales_start_date': '2026-08-01',
    'lead_sales_end_date': '2026-08-12',
    'meta_start_date': '2026-08-01',
    'meta_end_date': '2026-08-12'
}

metrics, ver_df, _ = run_pipeline(leads_df, sales_df, [meta_df], settings, 'test.xlsx')
print(ver_df)
