import pandas as pd
import json

from src.ingestion import read_file
from src.pipeline import run_pipeline
from src.inspection import load_aliases, map_columns
from src.metrics import calculate_metrics
from src.normalization import parse_date_series

def run_audit():
    leads_path = '/Users/apple/Downloads/12-08-2026_leads.csv'
    leads_df_raw = read_file(leads_path)
    
    with open('config/settings.json', 'r') as f:
        settings = json.load(f)
        
    settings['lead_sales_start_date'] = '2026-08-05'
    settings['lead_sales_end_date'] = '2026-08-10'
    
    # Do exactly what pipeline.py does for filtering
    aliases = load_aliases()
    leads_df = map_columns(leads_df_raw.copy(), aliases)
    
    if 'registration_date' in leads_df.columns:
        leads_df['registration_date'] = parse_date_series(leads_df['registration_date'])
        
    sdt = pd.to_datetime('2026-08-05')
    edt = pd.to_datetime('2026-08-10') + pd.Timedelta(days=1, microseconds=-1)
    
    mask = leads_df['registration_date'].isna() | ((leads_df['registration_date'] >= sdt) & (leads_df['registration_date'] <= edt))
    leads_in_window = leads_df[mask].copy()
    
    print(f"Total Leads in window: {len(leads_in_window)}")
    
    paid_markers = settings.get('paid_markers', [
        "paid", "cpc", "cpm", "ppc", "paid_social", "paid_search",
        "google", "facebook", "instagram", "meta", "linkedin",
        "youtube", "bing", "snapchat", "twitter", "ads", "advertisement"
    ])
    
    def is_paid(row):
        for col in ['utm_medium', 'utm_source', 'campaign', 'source']:
            if col in row and pd.notna(row[col]):
                val = str(row[col]).lower()
                if any(marker in val for marker in paid_markers):
                    return True
        return False

    leads_in_window['is_paid'] = leads_in_window.apply(is_paid, axis=1)
    paid_count = leads_in_window['is_paid'].sum()
    unpaid_count = len(leads_in_window) - paid_count
    
    print(f"Paid Leads: {paid_count}")
    print(f"Unpaid Leads: {unpaid_count}")
    
    # We want to know which row is classified differently between run 1 and run 2, but wait, both runs use the same logic?
    # Let's save the IDs of paid leads.
    paid_emails = leads_in_window[leads_in_window['is_paid']]['email'].tolist()
    
    with open('paid_emails.json', 'w') as f:
        json.dump(paid_emails, f)

if __name__ == '__main__':
    run_audit()
