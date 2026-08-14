import pandas as pd
from src.pipeline import run_pipeline
from src.inspection import load_aliases, map_columns

def is_paid_calc(leads_df, paid_markers):
    count = 0
    for idx, row in leads_df.iterrows():
        for col in ['utm_medium', 'utm_source', 'campaign', 'source']:
            if col in row and pd.notna(row[col]):
                val = str(row[col]).lower()
                if any(m in val for m in paid_markers):
                    count += 1
                    break
    return count

leads_df_raw = pd.read_csv('/Users/apple/Downloads/12-08-2026_leads.csv')
sales_df_raw = pd.read_csv('/Users/apple/Downloads/12-08-2026_sales(1).csv')
m1 = pd.read_csv('/Users/apple/Downloads/FML-X-Satyam-2-Campaigns-1-Aug-2026-12-Aug-2026.csv')
m2 = pd.read_csv('/Users/apple/Downloads/SSA-X-SATYAM-KHANDELWAL-Campaigns-1-Aug-2026-12-Aug-2026.csv')

settings = {
    'cutoff_date': '2026-08-01',
    'fallback_price': 8999.0,
    'zero_roi_threshold': 5000.0,
    'sale_date_source': 'Actual Sale Date',
    'payment_status_source': 'Actual Payment Status',
    'amount_source': 'Actual Order Amount',
    'custom_sale_date': None
}

# Run 1
s1 = settings.copy()
s1['lead_sales_start_date'] = '2026-08-01'
s1['lead_sales_end_date'] = '2026-08-12'
s1['meta_start_date'] = '2026-08-01'
s1['meta_end_date'] = '2026-08-12'

m1_metrics, _, _ = run_pipeline(leads_df_raw.copy(), sales_df_raw.copy(), [m1.copy(), m2.copy()], s1, 'out1.xlsx')
print("Run 1 Paid:", m1_metrics['paid_leads'])

# Run 2
s2 = settings.copy()
s2['lead_sales_start_date'] = '2026-08-05'
s2['lead_sales_end_date'] = '2026-08-10'
s2['meta_start_date'] = '2026-08-05'
s2['meta_end_date'] = '2026-08-10'

m2_metrics, _, _ = run_pipeline(leads_df_raw.copy(), sales_df_raw.copy(), [m1.copy(), m2.copy()], s2, 'out2.xlsx')
print("Run 2 Paid:", m2_metrics['paid_leads'])
