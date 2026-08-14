import pandas as pd
import numpy as np

file_path = 'output/real_data_report.xlsx'
xl = pd.ExcelFile(file_path)
print("Sheets:", xl.sheet_names)

print("\n--- 1. Settings & Run Log ---")
settings_df = xl.parse('1. ⚙ Settings & Run Log')
for index, row in settings_df.iterrows():
    print(f"{row.iloc[0]}: {row.iloc[1]}")

print("\n--- 12. Verification ---")
ver_df = xl.parse('12. ✅ Verification')
for index, row in ver_df.iterrows():
    print(f"{row.iloc[0]}: {row.iloc[1]}")

print("\n--- Checking for NaNs or Infinities in Verification ---")
has_nan = False
for index, row in ver_df.iterrows():
    val = row.iloc[1]
    if isinstance(val, float):
        if pd.isna(val) or np.isinf(val):
            print(f"ERROR: {row.iloc[0]} has invalid value {val}")
            has_nan = True
if not has_nan:
    print("No NaNs or Infinity found in Verification values.")
