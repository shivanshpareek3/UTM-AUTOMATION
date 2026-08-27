import pytest
import pandas as pd
import os
from src.pipeline import run_pipeline

@pytest.mark.skipif(not os.path.exists('/Users/apple/Downloads/20260825_071521_GlobalJobMasterclass1530328_subscriber.csv'), reason="Golden data not present")
def test_golden_methodology_verified(tmp_path):
    from src.ingestion import read_file
    
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

    from src.inspection import load_aliases, map_columns
    aliases = load_aliases()
    leads_df = map_columns(leads_df, aliases)
    sales_df = map_columns(sales_df, aliases)
    meta_df1 = map_columns(meta_df1, aliases)
    meta_df2 = map_columns(meta_df2, aliases)


    out = tmp_path / "golden_report.xlsx"
    metrics, ver_df, path = run_pipeline(leads_df, sales_df, [meta_df1, meta_df2], settings, str(out))

    # Assert exact Golden Methodology metrics
    assert abs(metrics['raw_meta_spend'] - 445696.06) < 0.01
    assert metrics['total_leads'] == 3295.0
    assert metrics['total_sales'] == 49.0
    assert metrics['attributed_sales'] == 45.0
    assert metrics['unattributed_sales'] == 4.0
    assert metrics['attributed_revenue'] == 404955.0
    assert abs(metrics['cpl'] - 131.96795144157815) < 0.001
    assert abs(metrics['attributed_spend'] - 434834.4) < 0.1
    assert abs(metrics['cac'] - 9662.986666666668) < 0.001
    assert abs(metrics['roas'] - 0.9312855652634657) < 0.001
