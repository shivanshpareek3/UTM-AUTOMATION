import pandas as pd
import glob
import os

files = glob.glob("/Users/apple/Downloads/*.csv") + glob.glob("/Users/apple/Desktop/UTM automation/*.csv") + glob.glob("/Users/apple/Desktop/UTM automation/*.xlsx")
for f in files:
    try:
        if f.endswith('.csv'):
            df = pd.read_csv(f, on_bad_lines='skip', encoding='utf-8')
        else:
            df = pd.read_excel(f)
        
        # Check lengths
        l1 = len(df)
        l2 = len(df.dropna(how='all'))
        
        if l1 == 3605 or l2 == 3605 or l1 == 3595 or l2 == 3595:
            print(f"MATCH: {f} | Rows: {l1} | Non-empty: {l2}")
        elif abs(l1 - 3605) < 100 or abs(l2 - 3605) < 100:
            print(f"CLOSE: {f} | Rows: {l1} | Non-empty: {l2}")
    except Exception:
        pass
