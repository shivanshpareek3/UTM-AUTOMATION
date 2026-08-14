import pandas as pd
from src.normalization import parse_date_series

df = pd.read_csv('/Users/apple/Downloads/12-08-2026_leads.csv')
dates = parse_date_series(df['Order Date'])
nan_count = dates.isna().sum()
print("NaN dates:", nan_count)
