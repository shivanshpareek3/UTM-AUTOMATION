import pandas as pd
from src.ingestion import read_file
from src.inspection import load_aliases, map_columns
from src.normalization import normalize_email, normalize_phone

file_path = '/Users/apple/Downloads/20260829_042031_GlobalJobMasterclass1530328_subscriber.csv'
df = read_file(file_path)
aliases = load_aliases()
df = map_columns(df, aliases)

df['email_norm'] = df['email'].apply(normalize_email)
df['phone_norm'] = df['phone'].apply(normalize_phone) if 'phone' in df.columns else ''

empty_emails = df[df['email_norm'] == '']
print(f"Empty emails: {len(empty_emails)}")

print("Let's look at duplicates:")
dupes_email = df[df.duplicated(subset=['email_norm'], keep=False)].sort_values(by='email_norm')
print(f"Total rows involved in duplicate emails: {len(dupes_email)}")

# Count unique emails vs unique (email, phone) vs unique (name, email, phone)
print(f"Unique email_norm: {df['email_norm'].nunique()}")
print(f"Unique email_norm + phone_norm: {df[['email_norm', 'phone_norm']].drop_duplicates().shape[0]}")
if 'name' in df.columns:
    print(f"Unique name + email_norm + phone_norm: {df[['name', 'email_norm', 'phone_norm']].drop_duplicates().shape[0]}")
