import pandas as pd
from src.pipeline import run_pipeline

leads_df = pd.DataFrame({
    'email': ['test@example.com'],
    'registration_date': ['2023-01-01'],
    'campaign': ['camp1'],
    'ad_set': ['adset1'],
    'ad_creative': ['ad1']
})

sales_df = pd.DataFrame({
    'email': ['test@example.com'],
    'sale_date': ['2023-01-02'],
    'order_amount': [100.0]
})

meta_df = pd.DataFrame({
    'Date': ['2023-01-01'],
    'campaign': ['camp1'],
    'ad_set': ['adset1'],
    'ad_creative': ['ad1'],
    'Amount Spent': [10.0]
})

mapping_dict = {
    'meta': [
        {'campaign': 'campaign', 'spend': 'Amount Spent', 'Date': 'Date'}
    ]
}

inv_meta = {v: ('Day' if k == 'Date' else k) for k, v in mapping_dict['meta'][0].items()}
meta_df.rename(columns=inv_meta, inplace=True)
meta_dfs = [meta_df]

settings = {
    'cutoff_date': pd.to_datetime('2024-01-01'),
    'funnel_type': 'Paid',
    'paid_funnel_price': 100.0,
    'fallback_price': 100.0,
    'meta_start_date': pd.to_datetime('2023-01-01'),
    'meta_end_date': pd.to_datetime('2023-01-01'),
    'ad_start_date': pd.to_datetime('2023-01-01'),
    'ad_end_date': pd.to_datetime('2023-01-01'),
}

try:
    metrics, ver_df, xl_path = run_pipeline(leads_df, sales_df, meta_dfs, settings, "test_out.xlsx")
    print("SUCCESS")
except Exception as e:
    import traceback
    traceback.print_exc()

