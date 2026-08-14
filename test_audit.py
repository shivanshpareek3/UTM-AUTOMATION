import pandas as pd
from src.pipeline import run_pipeline

leads_df = pd.read_csv('/Users/apple/Downloads/12-08-2026_leads.csv')
sales_df = pd.read_csv('/Users/apple/Downloads/12-08-2026_sales(1).csv')
meta_df = pd.read_csv('/Users/apple/Downloads/FML-X-Satyam-2-Campaigns-1-Aug-2026-12-Aug-2026.csv')

settings = {
    'report_name': 'Test',
    'client_name': 'Satyam',
    'report_type': 'Custom',
    'lead_start_date': '2026-08-01',
    'lead_end_date': '2026-08-12',
    'ad_start_date': '2026-08-01',
    'ad_end_date': '2026-08-12',
    'cutoff_date': '2026-08-01',
    'currency': '₹',
    'amount_source': 'Actual Order Amount'
}

metrics, ver_df, xl_path = run_pipeline(leads_df, sales_df, [meta_df], settings, 'output/audit.xlsx')

all_sales = pd.read_excel('output/audit.xlsx', sheet_name='2. 📋 All Sales (Attributed)')

print("\n--- AUDIT TABLE ---")
print(f"{'Order ID'.ljust(25)} | {'Raw Rev'.ljust(8)} | {'Parsed'.ljust(8)} | {'Attr'.ljust(5)} | {'Match Level'.ljust(15)} | {'Attr Rev'.ljust(8)}")
print("-" * 80)

for i, row in all_sales.iterrows():
    email = row.get('email')
    parsed_amount = row.get('order_amount', 0)
    attr_source = row.get('attribution_source')
    match_level = row.get('match_level')
    
    orig_row = sales_df[sales_df['email'].str.lower().str.strip() == email.lower().strip()]
    if not orig_row.empty:
        raw_amt = orig_row.iloc[0].get('Amount Received (Sub)', 'N/A')
        order_id = str(orig_row.iloc[0].get('Order Id', 'N/A'))
    else:
        raw_amt = 'N/A'
        order_id = 'N/A'
        
    is_attr = attr_source != 'Unattributed'
    attr_revenue = parsed_amount if is_attr else 0
    
    # We truncate Order ID if it's too long
    order_id_print = order_id[:23] + '..' if len(order_id) > 25 else order_id.ljust(25)
    
    print(f"{order_id_print} | {str(raw_amt).ljust(8)} | {str(parsed_amount).ljust(8)} | {str(is_attr).ljust(5)} | {str(match_level).ljust(15)} | {str(attr_revenue).ljust(8)}")

