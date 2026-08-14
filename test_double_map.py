import pandas as pd
from src.inspection import load_aliases, map_columns

sales = pd.read_csv('/Users/apple/Downloads/12-08-2026_sales(1).csv')
aliases = load_aliases()
print("Original columns:", len(sales.columns))

sales1 = map_columns(sales, aliases)
print("Columns after first map:", len(sales1.columns))
print("order_amount type:", type(sales1['order_amount']))

sales2 = map_columns(sales1, aliases)
print("Columns after second map:", len(sales2.columns))
print("order_amount type:", type(sales2['order_amount']))

