import pandas as pd
import os
import glob

files = glob.glob("/Users/apple/Downloads/*.csv")
for f in files:
    try:
        df = pd.read_csv(f, encoding='utf-8')
        print(f"File: {f} -> {len(df)} rows")
    except Exception:
        try:
            df = pd.read_csv(f, encoding='latin1')
            print(f"File: {f} -> {len(df)} rows (latin1)")
        except Exception as e:
            print(f"Error {f}: {e}")
