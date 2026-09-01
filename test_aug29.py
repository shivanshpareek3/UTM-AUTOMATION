import pandas as pd
from src.ingestion import read_file
from src.pipeline import run_pipeline

leads_file = '/Users/apple/Downloads/20260829_042031_GlobalJobMasterclass1530328_subscriber.csv'
sales_file = '/Users/apple/Downloads/29th Aug - sale.csv'
meta1_file = '/Users/apple/Downloads/FML-X-Abhishek-Pal-22-28-Aug.csv'
meta2_file = '/Users/apple/Downloads/Abhishek-Pal-X-FML-22-28th-Aug.csv'

leads_df = read_file(leads_file)
sales_df = read_file(sales_file).dropna(how='all')
meta_df1 = read_file(meta1_file)
meta_df2 = read_file(meta2_file)

leads_df.rename(columns={
    'email': 'email', 'created_at': 'registration_date',
    'utm_campaign': 'campaign', 'utm_medium': 'ad_set',
    'utm_source': 'ad_creative', 'first_name': 'name', 'phone': 'phone'
}, inplace=True)
sales_df.rename(columns={'email': 'email', 'name': 'name', 'phone': 'phone'}, inplace=True)
meta_df1.rename(columns={'Campaign name': 'campaign', 'Amount spent (INR)': 'spend', 'Reporting starts': 'Day'}, inplace=True)
meta_df2.rename(columns={'Campaign name': 'campaign', 'Amount spent (INR)': 'spend', 'Reporting starts': 'Day'}, inplace=True)

settings = {
    'start_date': '2026-08-22',
    'cutoff_date': '2026-08-28',
    'lead_sales_start_date': '2026-08-22',
    'lead_sales_end_date': '2026-08-28',
    'meta_start_date': '2026-08-22',
    'meta_end_date': '2026-08-28',
    'sale_date_source': 'Actual Sale Date',
    'amount_source': 'Fallback Price Per Sale',
    'payment_status_source': 'Treat All Imported Sales as Successful',
    'paid_markers': ["paid"], 'client_name': 'Test', 'report_name': 'Test',
    'fallback_price': 8999.0, 'zero_roi_threshold': 5000.0,
    'funnel_type': 'Paid', 'paid_funnel_price': 8999.0
}

m, v, _ = run_pipeline(leads_df, sales_df, [meta_df1, meta_df2], settings, 'test.xlsx')
print(f"Total Leads: {m['total_leads']}")
print(f"Total Sales: {m['total_sales']}")
print(f"Attributed Sales: {m['sales_matched_to_campaign']}")
print(f"Matched to Lead: {m['sales_matched_to_lead']}")
print(f"Spend: {m['raw_meta_spend']}")
