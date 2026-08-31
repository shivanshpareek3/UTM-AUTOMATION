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

# Drop header rows if any
if not df.empty and 'email' in df.columns:
    df = df[~df['email'].astype(str).str.lower().str.strip().isin(['email', 'email address', 'customer email'])]

print(f"Start: {len(df)}")

# 1. Exact duplicate rows
df = df.drop_duplicates()
print(f"After exact duplicates: {len(df)}")

# 2. Duplicate emails (ignore blank)
blank_emails = df[df['email'] == '']
non_blank_emails = df[df['email'] != '']
non_blank_emails = non_blank_emails.drop_duplicates(subset=['email'])
df = pd.concat([non_blank_emails, blank_emails])
print(f"After duplicate emails: {len(df)}")

# 3. Duplicate phones (ignore blank)
blank_phones = df[df['phone'] == '']
non_blank_phones = df[df['phone'] != '']
non_blank_phones = non_blank_phones.drop_duplicates(subset=['phone'])
df = pd.concat([non_blank_phones, blank_phones])
print(f"After duplicate phones: {len(df)}")

