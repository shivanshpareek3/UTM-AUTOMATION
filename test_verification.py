import pandas as pd
import json
import os
import sys
sys.path.append(os.path.abspath('.'))
from src.pipeline import run_pipeline

leads_df = pd.read_csv('/Users/apple/Downloads/12-08-2026_leads.csv')
sales_df = pd.read_csv('/Users/apple/Downloads/12-08-2026_sales(1).csv')
meta_df = pd.read_csv('/Users/apple/Downloads/FML-X-Satyam-2-Campaigns-1-Aug-2026-12-Aug-2026.csv')

settings = {
    'report_name': 'Test',
    'client_name': 'Satyam',
    'report_type': 'Custom',
    'lead_start_date': '2026-08-01',
    'lead_end_date': '2026-08-12',
    'ad_start_date': '2026-08-01',
    'ad_end_date': '2026-08-12',
    'cutoff_date': '2026-08-01',
    'currency': '₹',
    'amount_source': 'Actual Order Amount'
}

metrics, ver_df, xl_path = run_pipeline(leads_df, sales_df, [meta_df], settings, 'output/test.xlsx')

print("\n--- METRICS EXTRACT ---")
print(json.dumps({k: v for k, v in metrics.items() if isinstance(v, (int, float, str))}, indent=2))
