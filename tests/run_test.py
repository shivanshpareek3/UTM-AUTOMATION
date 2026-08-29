import pandas as pd
from src.ingestion import read_file
from src.inspection import load_aliases, map_columns
from src.pipeline import run_pipeline

settings = {
    'start_date': '2026-08-15',
    'cutoff_date': '2026-08-21',
    'lead_sales_start_date': '2026-08-15',
    'lead_sales_end_date': '2026-08-21',
    'meta_start_date': '2026-08-15',
    'meta_end_date': '2026-08-21',
    'sale_date_source': 'Actual Sale Date',
    'amount_source': 'Actual Order Amount',
    'payment_status_source': 'Actual Payment Status',
    'paid_markers': ["paid", "cpc", "cpm", "ppc", "paid_social", "paid_search", "google", "facebook", "instagram", "meta", "linkedin", "youtube", "bing", "snapchat", "twitter", "ads", "advertisement"],
    'client_name': 'Golden Client',
    'report_name': 'Golden Recon',
    'fallback_price': 8999.0
}

leads_df = read_file('/Users/apple/Downloads/20260825_071521_GlobalJobMasterclass1530328_subscriber.csv')
sales_df = read_file('/Users/apple/Downloads/22 and 23 Aug sales - Copy of sale (1).csv')
sales_df = sales_df.dropna(how='all')

meta_df1 = read_file('/Users/apple/Downloads/FML-X-ABHISHEK-PAL-Campaigns-15-Aug-2026-21-Aug-2026.csv')
meta_df2 = read_file('/Users/apple/Downloads/A-hishek-Pal---FML-Campaigns-15-Aug-2026-21-Aug-2026.csv')

aliases = load_aliases()
leads_df = map_columns(leads_df, aliases)
sales_df = map_columns(sales_df, aliases)
meta_df1 = map_columns(meta_df1, aliases)
meta_df2 = map_columns(meta_df2, aliases)

metrics, ver_df, path = run_pipeline(leads_df, sales_df, [meta_df1, meta_df2], settings, 'golden_report.xlsx')
print(metrics)
