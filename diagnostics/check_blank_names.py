import pandas as pd
from src.ingestion import read_file

file_path = '/Users/apple/Downloads/20260829_042031_GlobalJobMasterclass1530328_subscriber.csv'
df = read_file(file_path)

if 'name' in df.columns or 'Name' in df.columns:
    name_col = 'name' if 'name' in df.columns else 'Name'
    blank_names = df[df[name_col].isna() | (df[name_col].astype(str).str.strip() == '')]
    print(f"Blank names: {len(blank_names)}")
else:
    # check for first_name / last_name or similar
    print("Columns:", df.columns.tolist())
    blank_names = df[df['name'].isna() | (df['name'].astype(str).str.strip() == '')]
    print(f"Blank names (lowercase): {len(blank_names)}")
