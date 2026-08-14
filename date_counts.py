import pandas as pd
from src.normalization import parse_date_series

df = pd.read_csv('/Users/apple/Downloads/12-08-2026_leads.csv')
df['date'] = parse_date_series(df['Order Date']).dt.date
print(df.groupby('date').size())
