import pandas as pd
import json
from src.pipeline import run_pipeline

# Mimic the client's uploaded files based on the problem description
sales = pd.DataFrame({
    'email': ['user1@test.com'] * 29 + ['unattributed@test.com'] * 4,
    'order_amount': [8999.0] * 33, 
    'campaign': ['mycampaign'] * 29 + [''] * 4, 
})

# Meta has Campaign Name and spend
meta = pd.DataFrame({
    'Campaign Name': ['mycampaign'],
    'spend': [486068.46],
    'Day': ['2026-08-01']
})

leads = pd.DataFrame({
    'email': ['user1@test.com'],
    'registration_date': ['2026-08-10'],
    'campaign': ['mycampaign'],
    'first_name': ['Test']
})

settings = {
    'report_name': 'Test',
    'client_name': 'Test',
    'lead_start_date': '2026-08-01',
    'lead_end_date': '2026-08-31',
    'ad_start_date': '2026-08-01',
    'ad_end_date': '2026-08-31',
    'cutoff_date': '2026-01-01',
    'funnel_type': 'Paid',
    'fallback_price': 8999.0
}

metrics, _, _ = run_pipeline(leads, sales, [meta], settings, 'test_out.xlsx')

print("\n--- RESULTS ---")
print(f"Total Sales: {metrics['total_sales']}")
print(f"Attributed Sales: {metrics['attributed_sales']}")
print(f"Attributed Spend: {metrics['attributed_spend']}")
print(f"ROAS: {metrics['roas']}")
print(f"ROI: {metrics['roi_percent']}")
print(f"CAC: {metrics['cac']}")
