import pandas as pd
import datetime
from src.pipeline import run_pipeline

# 1. Realistic Leads
leads_df = pd.DataFrame({
    'Customer Full Name': ['John Doe', 'Jane Smith'],
    'Customer Email Address': ['john@example.com', 'jane@example.com'],
    'Registration Date (IST)': ['2023-10-01', '2023-10-02'],
    'Campaign Source': ['Diwali_Promo', 'Summer_Sale'],
    'Ad Set Name': ['Audience_1', 'Audience_2'],
    'Creative Name': ['Video_1', 'Image_2']
})

# 2. Realistic Sales
sales_df = pd.DataFrame({
    'Buyer Name': ['John Doe'],
    'Buyer Email': ['john@example.com'],
    'Mobile Number': ['9999999999'],
    'Purchase Date': ['2023-10-03'],
    'Final Amount': [4999.0],
    'Payment State': ['Paid']
})

# 3. Realistic Meta
meta_df = pd.DataFrame({
    'Day': ['2023-10-01', '2023-10-02'],
    'Campaign name': ['Diwali_Promo', 'Summer_Sale'],
    'Ad set name': ['Audience_1', 'Audience_2'],
    'Ad name': ['Video_1', 'Image_2'],
    'Amount spent (INR)': [1500.0, 2000.0]
})

# 4. Map them identically to how the UI does it
mapping_dict = {
    'leads': {
        'name': 'Customer Full Name',
        'email': 'Customer Email Address',
        'registration_date': 'Registration Date (IST)',
        'campaign': 'Campaign Source',
        'ad_set': 'Ad Set Name',
        'ad_creative': 'Creative Name'
    },
    'sales': {
        'name': 'Buyer Name',
        'email': 'Buyer Email',
        'phone': 'Mobile Number',
        'sale_date': 'Purchase Date',
        'order_amount': 'Final Amount',
        'payment_status': 'Payment State'
    },
    'meta': [
        {
            'Date': 'Day',
            'campaign': 'Campaign name',
            'ad_set': 'Ad set name',
            'ad_creative': 'Ad name',
            'spend': 'Amount spent (INR)'
        }
    ]
}

# 5. UI Renaming layer
inv_leads = {v: k for k, v in mapping_dict['leads'].items()}
inv_sales = {v: k for k, v in mapping_dict['sales'].items()}
leads_df.rename(columns=inv_leads, inplace=True)
sales_df.rename(columns=inv_sales, inplace=True)

inv_meta = {v: ('Day' if k == 'Date' else k) for k, v in mapping_dict['meta'][0].items()}
meta_df.rename(columns=inv_meta, inplace=True)
meta_dfs = [meta_df]

settings = {
    'cutoff_date': pd.to_datetime('2024-01-01'),
    'funnel_type': 'Paid',
    'paid_funnel_price': 8999.0,
    'fallback_price': 8999.0,
    'meta_start_date': pd.to_datetime('2023-10-01'),
    'meta_end_date': pd.to_datetime('2023-10-31'),
    'ad_start_date': pd.to_datetime('2023-10-01'),
    'ad_end_date': pd.to_datetime('2023-10-31'),
}

print(f"Meta columns before pipeline: {meta_dfs[0].columns.tolist()}")

try:
    metrics, ver_df, xl_path = run_pipeline(leads_df, sales_df, meta_dfs, settings, "realistic_out.xlsx")
    print("SUCCESS!")
    print(metrics)
except Exception as e:
    import traceback
    traceback.print_exc()
