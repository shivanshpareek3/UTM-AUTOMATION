import pandas as pd
from src.ingestion import read_file
from src.inspection import load_aliases, map_columns
from src.normalization import normalize_email, normalize_phone, parse_date_series

file_path = '/Users/apple/Downloads/20260829_042031_GlobalJobMasterclass1530328_subscriber.csv'
df = read_file(file_path)
aliases = load_aliases()
df = map_columns(df, aliases)

df['email'] = df['email'].apply(normalize_email)
df['phone'] = df['phone'].apply(normalize_phone)
df['registration_date'] = parse_date_series(df['registration_date'])

# We want to identify the 10 VALID leads that were dropped by the old logic
df_old = df.drop_duplicates(subset=['email'], keep='first')
df_new = df.drop_duplicates(subset=['email', 'phone'], keep='first')

dropped = df_new[~df_new.index.isin(df_old.index)].copy()

# Filter out the test leads
dropped = dropped[~dropped['email'].isin(['test@gmail.com', 'anurag.foremostleads@gmail.com'])]

print("Diagnostic Table of the 10 Missing Valid Leads:")
print(dropped[['email', 'phone', 'first_name', 'registration_date']].to_markdown())
