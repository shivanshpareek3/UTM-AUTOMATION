import pandas as pd
from src.pipeline import run_pipeline
from src.inspection import load_aliases, map_columns
from src.ingestion import read_file
import json

# Load file just like Streamlit's file_uploader + read_stream
leads_raw = pd.read_csv('/Users/apple/Downloads/12-08-2026_leads.csv')
sales_raw = pd.read_csv('/Users/apple/Downloads/12-08-2026_sales(1).csv')
m1_raw = pd.read_csv('/Users/apple/Downloads/FML-X-Satyam-2-Campaigns-1-Aug-2026-12-Aug-2026.csv')

# st.session_state equivalents
st_leads_df = leads_raw.copy()
st_sales_df = sales_raw.copy()

# Phase 2 UI mappings
leads_df_ui = map_columns(st_leads_df, load_aliases())

# Settings for Streamlit
settings = {
    'report_name': 'Antigravity Default',
    'client_name': 'Antigravity Default',
    'cutoff_date': '2024-01-01',
    'fallback_price': 8999.0,
    'zero_roi_threshold': 5000.0,
    'currency': 'INR',
    'sale_date_source': 'Actual Sale Date',
    'payment_status_source': 'Actual Payment Status',
    'amount_source': 'Actual Order Amount',
    'custom_sale_date': None
}

# Run 1
s1 = settings.copy()
s1['lead_sales_start_date'] = '2026-08-01'
s1['lead_sales_end_date'] = '2026-08-12'
s1['meta_start_date'] = '2026-08-01'
s1['meta_end_date'] = '2026-08-12'

leads_file = st_leads_df.copy()
m1_metrics, _, _ = run_pipeline(leads_file, st_sales_df.copy(), [m1_raw.copy()], s1, 'out1.xlsx')
print("Run 1 Total:", m1_metrics['total_leads'])
print("Run 1 Paid:", m1_metrics['paid_leads'])

# Run 2
s2 = settings.copy()
s2['lead_sales_start_date'] = '2026-08-05'
s2['lead_sales_end_date'] = '2026-08-10'
s2['meta_start_date'] = '2026-08-05'
s2['meta_end_date'] = '2026-08-10'

leads_file2 = st_leads_df.copy()
m2_metrics, _, _ = run_pipeline(leads_file2, st_sales_df.copy(), [m1_raw.copy()], s2, 'out2.xlsx')
print("Run 2 Total:", m2_metrics['total_leads'])
print("Run 2 Paid:", m2_metrics['paid_leads'])

