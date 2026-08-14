import pandas as pd
import json

from src.ingestion import read_file
from src.pipeline import run_pipeline

def run_streamlit_sim():
    leads_path = '/Users/apple/Downloads/12-08-2026_leads.csv'
    sales_path = '/Users/apple/Downloads/12-08-2026_sales(1).csv'
    meta_paths = [
        '/Users/apple/Downloads/FML-X-Satyam-2-Campaigns-1-Aug-2026-12-Aug-2026.csv',
        '/Users/apple/Downloads/SSA-X-SATYAM-KHANDELWAL-Campaigns-1-Aug-2026-12-Aug-2026.csv'
    ]

    # Load exactly like Streamlit
    leads_df = read_file(leads_path)
    sales_df = read_file(sales_path)
    meta_dfs = [read_file(p) for p in meta_paths]
    
    with open('config/settings.json', 'r') as f:
        settings = json.load(f)
        
    # Run 1: Aug 1 - 12
    s1 = settings.copy()
    s1['lead_sales_start_date'] = '2026-08-01'
    s1['lead_sales_end_date'] = '2026-08-12'
    s1['meta_start_date'] = '2026-08-01'
    s1['meta_end_date'] = '2026-08-12'
    
    m1, _, _ = run_pipeline(leads_df.copy(), sales_df.copy(), [m.copy() for m in meta_dfs], s1, 'dummy1.xlsx')
    print("Run 1 Paid Leads:", m1['paid_leads'])
    
    # Run 2: Aug 5 - 10
    s2 = settings.copy()
    s2['lead_sales_start_date'] = '2026-08-05'
    s2['lead_sales_end_date'] = '2026-08-10'
    s2['meta_start_date'] = '2026-08-05'
    s2['meta_end_date'] = '2026-08-10'
    
    m2, _, _ = run_pipeline(leads_df.copy(), sales_df.copy(), [m.copy() for m in meta_dfs], s2, 'dummy2.xlsx')
    print("Run 2 Paid Leads:", m2['paid_leads'])
    print("Run 2 Total Leads:", m2['total_leads'])

if __name__ == '__main__':
    run_streamlit_sim()
