import pandas as pd
import json
from src.inspection import load_aliases, map_columns
from src.normalization import parse_date_series

leads_raw = pd.read_csv('/Users/apple/Downloads/12-08-2026_leads.csv')
leads_df = map_columns(leads_raw, load_aliases())
leads_df['registration_date'] = parse_date_series(leads_df['registration_date'])

sdt = pd.to_datetime('2026-08-05')
edt = pd.to_datetime('2026-08-10') + pd.Timedelta(days=1, microseconds=-1)
mask = leads_df['registration_date'].isna() | ((leads_df['registration_date'] >= sdt) & (leads_df['registration_date'] <= edt))
leads = leads_df[mask].copy()

paid_markers = ["paid", "cpc", "cpm", "ppc", "paid_social", "paid_search",
                "google", "facebook", "instagram", "meta", "linkedin",
                "youtube", "bing", "snapchat", "twitter", "ads", "advertisement"]

def is_paid(row):
    for col in ['utm_medium', 'utm_source', 'campaign', 'source']:
        if col in row and pd.notna(row[col]):
            val = str(row[col]).lower()
            if any(marker in val for marker in paid_markers):
                return True
    return False

leads['is_paid'] = leads.apply(is_paid, axis=1)

# Now, apply ASTYPE(STR) to simulate Arrow fixes
leads_arrow = leads_df[mask].copy()
for col in leads_arrow.columns:
    leads_arrow[col] = leads_arrow[col].astype(str)

leads_arrow['is_paid'] = leads_arrow.apply(is_paid, axis=1)

diff = leads[leads['is_paid'] != leads_arrow['is_paid']]
print("Differences found due to astype(str):", len(diff))
if len(diff) > 0:
    for _, r in diff.iterrows():
        print(r['email'], r['utm_medium'], r['utm_source'], r['campaign'], r['source'])
