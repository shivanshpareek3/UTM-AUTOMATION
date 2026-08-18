import pandas as pd
import sys
import os

sys.path.append(os.path.abspath('.'))
from src.ingestion import read_file
from src.inspection import load_aliases, map_columns
from src.normalization import unify_campaign_name

meta_files = [
    '/Users/apple/Downloads/Abhishek-Pal-FML-Ad-account-Report.xlsx',
    '/Users/apple/Downloads/FML-X-ABHISHEK-PAL-Ad-account-Report.xlsx',
    '/Users/apple/Downloads/FML-X-ABHISHEK-PAL-Campaigns-8-Aug-2026-14-Aug-2026.csv',
    '/Users/apple/Downloads/A-hishek-Pal---FML-Campaigns-8-Aug-2026-14-Aug-2026.xlsx'
]

dfs = []
for f in meta_files:
    try:
        df = read_file(f)
        df['source_file'] = os.path.basename(f)
        dfs.append(df)
    except Exception as e:
        print(f"Error reading {f}: {e}")

aliases = load_aliases()

mapped_dfs = []
for df in dfs:
    mapped = map_columns(df, aliases)
    mapped_dfs.append(mapped)
    
if not mapped_dfs:
    print("No valid meta files")
    sys.exit(0)

# Concatenate all
meta_df = pd.concat(mapped_dfs, ignore_index=True)

# Apply duplicate protection
if not meta_df.empty:
    meta_df = meta_df.drop_duplicates(ignore_index=True)

# Standard pipeline filtering
if 'ad' in meta_df.columns:
    meta_df = meta_df[~meta_df['ad'].astype(str).str.lower().str.strip().isin(['all', 'nan', ''])]
    
meta_df['Day'] = pd.to_datetime(meta_df.get('Day', meta_df.get('Reporting starts', pd.Series(dtype=str))), errors='coerce')

# Apply date filter (Aug 1 - Aug 20)
sdt = pd.to_datetime('2026-08-01')
edt = pd.to_datetime('2026-08-20')
window_meta = meta_df[(meta_df['Day'] >= sdt) & (meta_df['Day'] <= edt)].copy()

# Rename spend
if 'Amount spent (INR)' in window_meta.columns:
    window_meta = window_meta.rename(columns={'Amount spent (INR)': 'Amount Spent'})
elif 'spend' in window_meta.columns and 'Amount Spent' not in window_meta.columns:
    window_meta = window_meta.rename(columns={'spend': 'Amount Spent'})

window_meta['camp_norm'] = window_meta.get('campaign', window_meta.get('Campaign name', window_meta.get('Campaign Name', pd.Series(dtype=str)))).apply(unify_campaign_name)
valid_meta = window_meta[window_meta['camp_norm'] != ''].copy()

# File level reconciliation
print("\nFILE LEVEL RECONCILIATION")
total_valid_spend = 0.0
for f in meta_files:
    fname = os.path.basename(f)
    file_df = valid_meta[valid_meta['source_file'] == fname]
    raw_spend = file_df['Amount Spent'].sum() if 'Amount Spent' in file_df.columns else 0.0
    print(f"File: {fname}")
    print(f"  Rows included: {len(file_df)}")
    print(f"  Spend: {raw_spend:.2f}")
    total_valid_spend += raw_spend

print("-" * 50)
print(f"TOTAL INCLUDED RAW META SPEND: {total_valid_spend:.2f}")

# Also let's try combinations
from itertools import combinations
for i in range(1, len(meta_files) + 1):
    for combo in combinations(meta_files, i):
        combo_dfs = [df for df in mapped_dfs if df['source_file'].iloc[0] in [os.path.basename(x) for x in combo]]
        c_df = pd.concat(combo_dfs, ignore_index=True)
        c_df = c_df.drop_duplicates(ignore_index=True)
        if 'ad' in c_df.columns:
            c_df = c_df[~c_df['ad'].astype(str).str.lower().str.strip().isin(['all', 'nan', ''])]
        c_df['Day'] = pd.to_datetime(c_df.get('Day', c_df.get('Reporting starts', pd.Series(dtype=str))), errors='coerce')
        c_df = c_df[(c_df['Day'] >= sdt) & (c_df['Day'] <= edt)].copy()
        if 'Amount spent (INR)' in c_df.columns:
            c_df = c_df.rename(columns={'Amount spent (INR)': 'Amount Spent'})
        elif 'spend' in c_df.columns and 'Amount Spent' not in c_df.columns:
            c_df = c_df.rename(columns={'spend': 'Amount Spent'})
        c_df['camp_norm'] = c_df.get('campaign', c_df.get('Campaign name', c_df.get('Campaign Name', pd.Series(dtype=str)))).apply(unify_campaign_name)
        c_df = c_df[c_df['camp_norm'] != '']
        spend = c_df['Amount Spent'].sum() if 'Amount Spent' in c_df.columns else 0.0
        
        if abs(spend - 456047.55) < 10.0:
            print("\n!!! FOUND EXACT MATCHING COMBINATION !!!")
            print([os.path.basename(x) for x in combo])
            print(f"Spend: {spend:.2f}")
