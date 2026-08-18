import pandas as pd
import sys
import os

sys.path.append(os.path.abspath('.'))
from src.ingestion import read_file

meta = pd.read_csv('/Users/apple/Downloads/FML-X-ABHISHEK-PAL-Campaigns-8-Aug-2026-14-Aug-2026.csv')
print("Meta campaigns:")
if 'Campaign name' in meta.columns:
    print(meta['Campaign name'].unique())

meta2 = pd.read_excel('/Users/apple/Downloads/FML-X-ABHISHEK-PAL-Ad-account-Report.xlsx')
print("\nMeta2 campaigns:")
if 'Campaign name' in meta2.columns:
    print(meta2['Campaign name'].unique())
    
meta3 = pd.read_excel('/Users/apple/Downloads/Abhishek-Pal-FML-Ad-account-Report.xlsx')
print("\nMeta3 campaigns:")
if 'Campaign name' in meta3.columns:
    print(meta3['Campaign name'].unique())

leads = pd.read_csv('/Users/apple/Downloads/20260815_053436_GlobalJobMasterclass1530328_subscriber.csv')
for col in leads.columns:
    if leads[col].astype(str).str.contains('cbo <> r1', case=False).any():
        print(f"Found 'cbo <> r1' in column: {col}")
        print(leads[leads[col].astype(str).str.contains('cbo <> r1', case=False)][col].unique())

