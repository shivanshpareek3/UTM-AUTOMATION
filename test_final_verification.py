import pandas as pd
import os
import sys

sys.path.append(os.path.abspath('.'))
from src.pipeline import run_pipeline

leads_df = pd.read_csv('/Users/apple/Downloads/12-08-2026_leads.csv')
sales_df = pd.read_csv('/Users/apple/Downloads/12-08-2026_sales(1).csv')
meta_df = pd.read_csv('/Users/apple/Downloads/FML-X-Satyam-2-Campaigns-1-Aug-2026-12-Aug-2026.csv')

def run_test(ls_start, ls_end, m_start, m_end, filename):
    settings = {
        'report_name': 'Final UI Test',
        'cutoff_date': '2024-01-01',
        'fallback_price': 8999.0,
        'zero_roi_threshold': 5000.0,
        'currency': 'INR',
        'sale_date_source': 'Actual Sale Date',
        'payment_status_source': 'Actual Payment Status',
        'amount_source': 'Actual Order Amount',
        'custom_sale_date': None,
        'report_type': 'Custom',
        'lead_sales_start_date': ls_start,
        'lead_sales_end_date': ls_end,
        'meta_start_date': m_start,
        'meta_end_date': m_end,
        'lead_start_date': ls_start,
        'lead_end_date': ls_end,
        'ad_start_date': m_start,
        'ad_end_date': m_end
    }
    
    metrics, ver_df, xl_path = run_pipeline(leads_df, sales_df, [meta_df], settings, filename)
    return metrics, xl_path

print("REPORT 1 (LS: 08-01 -> 08-12 | Meta: 08-01 -> 08-07)")
m1, p1 = run_test('2026-08-01', '2026-08-12', '2026-08-01', '2026-08-07', 'output/report1.xlsx')
print(f"Metrics 1: {m1}")
print(f"Generated: {p1}")
print("-" * 50)
print("REPORT 2 (LS: 08-05 -> 08-10 | Meta: 08-05 -> 08-10)")
m2, p2 = run_test('2026-08-05', '2026-08-10', '2026-08-05', '2026-08-10', 'output/report2.xlsx')
print(f"Metrics 2: {m2}")
print(f"Generated: {p2}")
