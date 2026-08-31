import pandas as pd
from src.ingestion import read_file
from src.inspection import load_aliases, map_columns
from src.normalization import normalize_email, normalize_phone

file_path = '/Users/apple/Downloads/20260815_053436_GlobalJobMasterclass1530328_subscriber.csv'
df = read_file(file_path)

print(f"Raw rows: {len(df)}")

aliases = load_aliases()
df = map_columns(df, aliases)

df['email_norm'] = df['email'].apply(normalize_email)
if 'phone' in df.columns:
    df['phone_norm'] = df['phone'].apply(normalize_phone)
else:
    df['phone_norm'] = ''

print(f"Unique emails: {df['email_norm'].nunique()}")
print(f"Unique (email, phone): {df[['email_norm', 'phone_norm']].drop_duplicates().shape[0]}")
