import pandas as pd
from src.normalization import parse_date_series

sales = pd.read_csv('/Users/apple/Downloads/12-08-2026_sales(1).csv')
parsed_dates = parse_date_series(sales['Order Date'])

print(f"Total rows: {len(sales)}")
print(f"NaT dates: {parsed_dates.isna().sum()}")
print("Dates in Aug 5-10:", ((parsed_dates >= '2026-08-05') & (parsed_dates <= '2026-08-10')).sum())
