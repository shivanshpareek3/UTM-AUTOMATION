import pandas as pd
from src.ingestion import read_file
from src.inspection import load_aliases, map_columns
from src.normalization import normalize_email

file_path = '/Users/apple/Downloads/20260829_042031_GlobalJobMasterclass1530328_subscriber.csv'
df = read_file(file_path)
aliases = load_aliases()
df = map_columns(df, aliases)

df['email_norm'] = df['email'].apply(normalize_email)
nan_emails = df[df['email_norm'] == 'nan']
print(f"Emails equal to 'nan': {len(nan_emails)}")

if len(nan_emails) > 0:
    print(nan_emails[['email', 'phone', 'name']].head(15))
