import pandas as pd
from src.normalization import parse_date_series

sales = pd.read_csv('/Users/apple/Downloads/12-08-2026_sales(1).csv')
parsed_dates = parse_date_series(sales['Order Date'])
mask = (parsed_dates >= '2026-08-05') & (parsed_dates <= '2026-08-10')
print("Dates in Aug 5-10:")
print(parsed_dates[mask])
