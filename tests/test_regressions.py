import pytest
import pandas as pd
from src.pipeline import run_pipeline

def test_sales_zero_spend_summary_reconciliation(tmp_path):
    # Campaign with sales but ZERO spend
    leads = pd.DataFrame({
        'email': ['test@test.com'],
        'registration_date': ['2026-06-01'],
        'campaign': ['CampZeroSpend'],
        'ad_set': ['AdSet1'],
        'ad_creative': ['Ad1']
    })
    
    sales = pd.DataFrame({
        'email': ['test@test.com'],
        'sale_date': ['2026-06-05'],
        'order_amount': [5000.0],
        'payment_status': ['successful']
    })
    
    # Empty meta spend
    meta = pd.DataFrame(columns=['Campaign Name', 'Ad Set Name', 'Ad Name', 'Amount Spent', 'Day'])
    
    settings = {
        'lead_start_date': '2026-01-01', 'ad_start_date': '2026-01-01',
        'lead_end_date': '2026-12-31', 'ad_end_date': '2026-12-31',
        'cutoff_date': '2026-01-01',
        'fallback_price': 999.0
    }
    
    out = tmp_path / "report.xlsx"
    metrics, ver_df, xl = run_pipeline(leads, sales, [meta], settings, str(out))
    
    camp_summary = pd.read_excel(xl, sheet_name="3. 📢 Campaign Summary")
    
    assert len(camp_summary) == 1
    assert camp_summary.iloc[0]['Node Name'] == 'campzerospend'
    assert camp_summary.iloc[0]['Spend'] == 0.0
    assert camp_summary.iloc[0]['Sales'] == 1
    assert camp_summary.iloc[0]['Revenue'] == 5000.0
    assert camp_summary.iloc[0]['Profit'] == 5000.0

def test_unresolved_sale_dates_exclusion(tmp_path):
    # Sale with no matching lead and deriving date from lead
    leads = pd.DataFrame({
        'email': ['other@test.com'],
        'registration_date': ['2026-06-01']
    })
    
    sales = pd.DataFrame({
        'email': ['unresolved@test.com'],
        'order_amount': [5000.0],
        'payment_status': ['successful']
    })
    
    meta = pd.DataFrame()
    
    settings = {
        'lead_start_date': '2026-01-01', 'ad_start_date': '2026-01-01',
        'lead_end_date': '2026-12-31', 'ad_end_date': '2026-12-31',
        'cutoff_date': '2026-01-01',
        'sale_date_source': 'Lead Registration Date',
        'fallback_price': 999.0
    }
    
    out = tmp_path / "report_unresolved.xlsx"
    metrics, ver_df, xl = run_pipeline(leads, sales, [meta], settings, str(out))
    
    all_sales = pd.read_excel(xl, sheet_name="2. 📋 All Sales (Attributed)")
    excluded = pd.read_excel(xl, sheet_name="13. 🚫 Excluded Sales")
    
    assert len(all_sales) == 1
    assert metrics['total_sales'] == 1
    
    assert len(excluded) == 0
    
    check_13 = ver_df[ver_df['Check Name'] == '13. Unresolved/Missing Sales Dates']
    assert not check_13.empty
    assert check_13.iloc[0]['Status'] == 'WARNING'

import os
@pytest.mark.skipif(not os.path.exists('/Users/apple/Downloads/Lead Sheet Abhishek pal .csv'), reason="Real data not present")
def test_real_data_profitability_metrics(tmp_path):
    from src.ingestion import read_file
    from src.inspection import map_columns
    import json
    
    with open('config/aliases.json', 'r') as f:
        aliases = json.load(f)
        
    leads = read_file('/Users/apple/Downloads/Lead Sheet Abhishek pal .csv')
    sales = read_file('/Users/apple/Downloads/Sales .csv')
    m1 = read_file('/Users/apple/Downloads/Abhishek-Pal-FML-Ad-account-Report.xlsx')
    m2 = read_file('/Users/apple/Downloads/FML-X-ABHISHEK-PAL-Ad-account-Report.xlsx')
    
    settings = {
        'lead_start_date': '2026-01-01', 'ad_start_date': '2026-01-01',
        'lead_end_date': '2026-12-31', 'ad_end_date': '2026-12-31',
        'cutoff_date': '2026-01-01',
        'sale_date_source': 'Lead Registration Date',
        'payment_status_source': 'Treat All Imported Sales as Successful',
        'amount_source': 'Fallback Price Per Sale',
        'fallback_price': 8999.0
    }
    
    out = tmp_path / "real_report.xlsx"
    metrics, ver_df, xl = run_pipeline(leads, sales, [m1, m2], settings, str(out))
    
    assert abs(metrics['total_revenue'] - 629930.0) < 0.01
    assert abs(metrics['attributed_revenue'] - 602933.0) < 0.01
    assert abs(metrics['attributed_spend'] - 229802.21) < 0.05
    assert abs(metrics['profit'] - 373130.79) < 0.05
    assert abs(metrics['roas'] - 2.62) < 0.05
    assert abs(metrics['cac'] - 3429.88) < 0.05

@pytest.mark.skipif(not os.path.exists('/Users/apple/Downloads/20260815_053436_GlobalJobMasterclass1530328_subscriber.csv'), reason="Golden data not present")
def test_golden_methodology(tmp_path):
    from src.ingestion import read_file
    
    leads = read_file('/Users/apple/Downloads/20260815_053436_GlobalJobMasterclass1530328_subscriber.csv')
    sales = read_file('/Users/apple/Downloads/15th Aug - Sheet3.csv')
    m1 = read_file('/Users/apple/Downloads/FML-X-ABHISHEK-PAL-Campaigns-8-Aug-2026-14-Aug-2026.csv')
    m2 = read_file('/Users/apple/Downloads/A-hishek-Pal---FML-Campaigns-8-Aug-2026-14-Aug-2026.xlsx')
    
    settings = {
        'lead_start_date': '2026-01-01', 'ad_start_date': '2026-01-01',
        'lead_end_date': '2026-12-31', 'ad_end_date': '2026-12-31',
        'cutoff_date': '2026-01-01',
        'sale_date_source': 'Lead Registration Date',
        'payment_status_source': 'Treat All Imported Sales as Successful',
        'amount_source': 'Fallback Price Per Sale',
        'fallback_price': 8999.0
    }
    
    out = tmp_path / "golden_report.xlsx"
    metrics, ver_df, xl = run_pipeline(leads, sales, [m1, m2], settings, str(out))
    
    assert metrics['total_sales'] == 52
    assert metrics['attributed_sales'] == 49
    assert metrics['total_sales'] - metrics['attributed_sales'] == 3
    
    assert abs(metrics['raw_meta_spend'] - 456047.55) < 0.01
    assert abs(metrics['attributed_spend'] - 282120.59) < 0.01
    assert abs(metrics['unallocated_spend'] - 173926.96) < 0.01
    
    assert abs(metrics['profit'] - 158830.41) < 0.01
    assert abs(metrics['roas'] - 1.56) < 0.01
    assert abs(metrics['roi_percent'] - 56.30) < 0.01
    assert abs(metrics['cac'] - 5757.56) < 0.01
