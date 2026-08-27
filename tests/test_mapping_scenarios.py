import pandas as pd
from src.pipeline import run_pipeline

def test_mapping_scenarios():
    settings = {
        'start_date': '2026-08-01',
        'cutoff_date': '2026-08-31',
        'meta_start_date': '2026-08-01',
        'meta_end_date': '2026-08-31',
        'lead_sales_start_date': '2026-08-01',
        'lead_sales_end_date': '2026-08-31',
        'fallback_price': 8999.0
    }
    
    leads_df = pd.DataFrame({'email': ['test@test.com'], 'campaign': ['camp1']})
    sales_df = pd.DataFrame({'email': ['test@test.com'], 'order_amount': [100.0], 'campaign': ['camp1']})
    
    meta_a = pd.DataFrame({'campaign': ['camp1'], 'spend': [100.0]})
    metrics_a, _, _ = run_pipeline(leads_df, sales_df, [meta_a], settings, 'output_a.xlsx')
    
    meta_b = pd.DataFrame({'campaign': ['camp1'], 'spend': [100.0]})
    metrics_b, _, _ = run_pipeline(leads_df, sales_df, [meta_b], settings, 'output_b.xlsx')
    
    meta_c = pd.DataFrame({'campaign': ['camp1'], 'spend': [100.0]})
    metrics_c, _, _ = run_pipeline(leads_df, sales_df, [meta_c], settings, 'output_c.xlsx')
    
    meta_d = pd.DataFrame({'campaign': ['camp1'], 'spend': [100.0], 'Amount Spent': ['Not a number']})
    metrics_d, _, _ = run_pipeline(leads_df, sales_df, [meta_d], settings, 'output_d.xlsx')
    
    for metrics in [metrics_a, metrics_b, metrics_c, metrics_d]:
        assert metrics['raw_meta_spend'] == 100.0
        assert metrics['attributed_spend'] == 100.0
        assert metrics['profit'] == 8899.0

