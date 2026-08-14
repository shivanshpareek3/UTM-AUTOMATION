import pandas as pd
from src.pipeline import run_pipeline
import json

leads = pd.read_csv('/Users/apple/Downloads/12-08-2026_leads.csv')
sales = pd.read_csv('/Users/apple/Downloads/12-08-2026_sales(1).csv')
m1 = pd.read_csv('/Users/apple/Downloads/FML-X-Satyam-2-Campaigns-1-Aug-2026-12-Aug-2026.csv')

with open('config/settings.json', 'r') as f:
    settings = json.load(f)

# Run 2
s2 = settings.copy()
s2['lead_sales_start_date'] = '2026-08-05'
s2['lead_sales_end_date'] = '2026-08-10'

m2_metrics, _, _ = run_pipeline(leads.copy(), sales.copy(), [m1.copy()], s2, 'out2.xlsx')
print("Run 2 Paid with settings.json:", m2_metrics['paid_leads'])

# Remove paid_markers from settings
s3 = settings.copy()
del s3['paid_markers']
m3_metrics, _, _ = run_pipeline(leads.copy(), sales.copy(), [m1.copy()], s3, 'out3.xlsx')
print("Run 2 Paid without paid_markers (Streamlit default):", m3_metrics['paid_leads'])

# Check for any row differences
