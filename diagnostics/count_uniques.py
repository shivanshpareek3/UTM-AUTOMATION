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

df['email'] = df['email'].apply(normalize_email)
if 'phone' in df.columns:
    df['phone'] = df['phone'].apply(normalize_phone)

# Print uniques
print(f"Unique emails: {df['email'].nunique()}")
print(f"Unique phones: {df['phone'].nunique()}")
print(f"Unique (email, phone) pairs: {len(df.drop_duplicates(subset=['email', 'phone']))}")

