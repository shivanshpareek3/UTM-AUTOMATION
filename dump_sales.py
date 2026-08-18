import pandas as pd
import sys
import os

sys.path.append(os.path.abspath('.'))
from src.ingestion import read_file
from src.inspection import load_aliases, map_columns
from src.normalization import unify_campaign_name
from src.leads import process_leads
from src.sales import process_sales
from src.attribution import attribute_sales

leads_file = '/Users/apple/Downloads/20260815_053436_GlobalJobMasterclass1530328_subscriber.csv'
sales_file = '/Users/apple/Downloads/15th Aug - Sheet3.csv'

leads_df = read_file(leads_file)
sales_df = read_file(sales_file)
aliases = load_aliases()
leads_mapped = map_columns(leads_df, aliases)
sales_mapped = map_columns(sales_df, aliases)

settings = {
    'cutoff_date': '2026-08-01',
    'fallback_price': 8999.0,
    'currency': 'INR',
    'sale_date_source': 'Lead Registration Date',
    'payment_status_source': 'Treat All Imported Sales as Successful', 
    'amount_source': 'Fallback Price Per Sale'
}
leads_proc = process_leads(leads_mapped, settings)
sales_out = process_sales(sales_mapped, settings)
sales_attr = attribute_sales(sales_out, leads_proc, settings)

sales_attr['camp_norm'] = sales_attr['campaign'].apply(unify_campaign_name) if 'campaign' in sales_attr.columns else ""

print("Sales Distribution by Campaign:")
print(sales_attr['camp_norm'].value_counts())
print("\nUnattributed sales:")
print(sales_attr[sales_attr['match_level'] == 'Unattributed'][['name', 'email', 'phone']])
