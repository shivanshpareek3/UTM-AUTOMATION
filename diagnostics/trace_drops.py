import pandas as pd
from src.ingestion import read_file
from src.inspection import load_aliases, map_columns
from src.leads import process_leads
import json
from src.normalization import normalize_email, normalize_phone

file_path = '/Users/apple/Downloads/20260829_042031_GlobalJobMasterclass1530328_subscriber.csv'
df = read_file(file_path)

print(f"Raw rows: {len(df)}")
aliases = load_aliases()
df = map_columns(df, aliases)

if not df.empty and 'email' in df.columns:
    df = df[~df['email'].astype(str).str.lower().str.strip().isin(['email', 'email address', 'customer email'])]
print(f"After removing header rows: {len(df)}")

df['email'] = df['email'].apply(normalize_email)
df['phone'] = df['phone'].apply(normalize_phone) if 'phone' in df.columns else ''

print(f"Unique emails: {df['email'].nunique()}")
print(f"Unique (email, phone): {df[['email', 'phone']].drop_duplicates().shape[0]}")

from src.normalization import parse_date_series
df['registration_date_parsed'] = parse_date_series(df['registration_date'])
print(f"Rows with valid dates: {df['registration_date_parsed'].notna().sum()}")

# Maybe date filtering drops 10 rows?
settings = {
    'lead_start_date': '2026-08-01',
    'lead_end_date': '2026-08-31'
}

sdt = pd.to_datetime(settings.get('lead_start_date'))
edt = pd.to_datetime(settings.get('lead_end_date'))
if edt.hour == 0 and edt.minute == 0 and edt.second == 0:
    edt = edt + pd.Timedelta(days=1, microseconds=-1)

mask = df['registration_date_parsed'].isna() | ((df['registration_date_parsed'] >= sdt) & (df['registration_date_parsed'] <= edt))
print(f"Rows inside date window: {mask.sum()}")
