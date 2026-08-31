import pandas as pd
from src.ingestion import read_file
from src.inspection import load_aliases, map_columns
from src.normalization import normalize_email, normalize_phone

file_path = '/Users/apple/Downloads/20260829_042031_GlobalJobMasterclass1530328_subscriber.csv'
df = read_file(file_path)
aliases = load_aliases()
df = map_columns(df, aliases)

df['email'] = df['email'].apply(normalize_email)
df['phone'] = df['phone'].apply(normalize_phone)

# Deduplicate by email
df_email_only = df.drop_duplicates(subset=['email'])

# Find the ones that have same email but different phone
df_email_phone = df.drop_duplicates(subset=['email', 'phone'])

print(f"By email only: {len(df_email_only)}")
print(f"By email and phone: {len(df_email_phone)}")

# Let's find exactly which ones are kept by email+phone but dropped by email
dropped = df_email_phone[~df_email_phone.index.isin(df_email_only.index)]
print(f"Dropped records: {len(dropped)}")
for idx, row in dropped.iterrows():
    print(f"Email: {row['email']}, Phone: {row['phone']}, Name: {row.get('name', '')}")

# Is it possible that 2 of these are blank phones?
blank_phones = dropped[dropped['phone'] == '']
print(f"Dropped records with blank phone: {len(blank_phones)}")
