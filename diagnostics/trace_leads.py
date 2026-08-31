import pandas as pd
from src.ingestion import read_file
from src.inspection import load_aliases, map_columns
from src.leads import process_leads

file_path = '/Users/apple/Downloads/20260829_042031_GlobalJobMasterclass1530328_subscriber.csv'
df = read_file(file_path)
print(f"Raw rows: {len(df)}")

aliases = load_aliases()
mapped = map_columns(df, aliases)
print(f"Mapped rows: {len(mapped)}")

settings = {
    'cutoff_date': '2020-01-01',
    'lead_start_date': '2020-01-01',
    'lead_end_date': '2030-01-01'
}

# Instead of process_leads directly, let's step through process_leads step by step
# to see where the numbers drop.
df_clean = mapped.dropna(subset=['email', 'phone'], how='all').copy()
print(f"After dropping missing email/phone: {len(df_clean)}")

if 'email' in df_clean.columns:
    df_clean['email'] = df_clean['email'].astype(str).str.strip().str.lower()
if 'phone' in df_clean.columns:
    df_clean['phone'] = df_clean['phone'].astype(str).str.strip().str.replace(r'\D+', '', regex=True)

# Deduplication
df_dedup = df_clean.copy()
if 'email' in df_dedup.columns and 'phone' in df_dedup.columns:
    df_dedup = df_dedup.drop_duplicates(subset=['email', 'phone'])
elif 'email' in df_dedup.columns:
    df_dedup = df_dedup.drop_duplicates(subset=['email'])
elif 'phone' in df_dedup.columns:
    df_dedup = df_dedup.drop_duplicates(subset=['phone'])

print(f"After deduplication: {len(df_dedup)}")

# Actually, let's just see how many rows process_leads returns
processed = process_leads(mapped, settings)
print(f"Processed leads: {len(processed)}")
