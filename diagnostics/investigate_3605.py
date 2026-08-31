import pandas as pd
from src.ingestion import read_file
from src.inspection import load_aliases, map_columns
from src.leads import process_leads
import json

with open('config/sentinels.json', 'r') as f:
    sentinels = json.load(f)

file_path = '/Users/apple/Downloads/20260829_042031_GlobalJobMasterclass1530328_subscriber.csv'
leads_df = read_file(file_path)

print(f"Raw leads loaded: {len(leads_df)}")

aliases = load_aliases()
leads_df = map_columns(leads_df, aliases)

if not leads_df.empty and 'email' in leads_df.columns:
    leads_df = leads_df[~leads_df['email'].astype(str).str.lower().str.strip().isin(['email', 'email address', 'customer email'])]
    print(f"After removing header rows: {len(leads_df)}")

df_proc = process_leads(leads_df, sentinels)
print(f"After process_leads: {len(df_proc)}")

# The user expects 3605 raw leads. Let's see if 3693 - some blanks = 3605.
blanks = leads_df[leads_df['email'].isna() | (leads_df['email'].astype(str).str.strip() == '')]
print(f"Blank emails: {len(blanks)}")

leads_no_blanks = leads_df.dropna(subset=['email'])
print(f"Leads with non-blank email: {len(leads_no_blanks)}")

