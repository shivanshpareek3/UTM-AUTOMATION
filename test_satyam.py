import pandas as pd
from src.inspection import load_aliases, map_columns

sales = pd.read_csv('/Users/apple/Downloads/12-08-2026_sales(1).csv')
aliases = load_aliases()
sales = map_columns(sales, aliases)

print("order_amount columns right after map_columns:")
print(sales.columns[sales.columns == 'order_amount'])

from src.pipeline import run_pipeline
meta = pd.read_csv('/Users/apple/Downloads/FML-X-Satyam-2-Campaigns-1-Aug-2026-12-Aug-2026.csv')
leads = pd.read_csv('/Users/apple/Downloads/12-08-2026_leads.csv')
meta = map_columns(meta, aliases)
leads = map_columns(leads, aliases)

print("order_amount columns after mapping others:")
print(sales.columns[sales.columns == 'order_amount'])

