import pandas as pd
from src.inspection import load_aliases, map_columns
from src.sales import process_sales

sales = pd.read_csv('/Users/apple/Downloads/12-08-2026_sales(1).csv')
aliases = load_aliases()
sales = map_columns(sales, aliases)

settings = {
    'fallback_price': 8999.0,
    'payment_status_source': 'Actual Payment Status',
}

try:
    process_sales(sales, settings)
except Exception as e:
    import traceback
    traceback.print_exc()

