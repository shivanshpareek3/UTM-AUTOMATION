import pandas as pd
from src.normalization import parse_date_series
leads = pd.read_csv('/Users/apple/Downloads/12-08-2026_leads.csv')
leads['registration_date'] = parse_date_series(leads['Order Date'])
min_dt = leads['registration_date'].min()
max_dt = leads['registration_date'].max()
total_rows = len(leads)

print(f"Min Date: {min_dt}")
print(f"Max Date: {max_dt}")
print(f"Total rows before filter: {total_rows}")

m1 = (leads['registration_date'] >= '2026-08-01') & (leads['registration_date'] <= '2026-08-12 23:59:59')
# wait, ls_edt is '2026-08-12 00:00:00' because pd.to_datetime('2026-08-12')
print("Aug 1-12 rows:", m1.sum())

m2 = (leads['registration_date'] >= '2026-08-05') & (leads['registration_date'] <= '2026-08-10 23:59:59')
print("Aug 5-10 rows:", m2.sum())

