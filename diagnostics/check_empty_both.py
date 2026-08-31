import pandas as pd
from src.ingestion import read_file

df = read_file('/Users/apple/Downloads/20260829_042031_GlobalJobMasterclass1530328_subscriber.csv')
blank_email = df['email'].isna() | (df['email'].astype(str).str.strip() == '')
blank_phone = df['phone'].isna() | (df['phone'].astype(str).str.strip() == '')

both_blank = df[blank_email & blank_phone]
print(f"Both blank: {len(both_blank)}")

df_clean = df[~(blank_email & blank_phone)]
print(f"Clean: {len(df_clean)}")

df_clean2 = df[~blank_email]
print(f"Email only clean: {len(df_clean2)}")
