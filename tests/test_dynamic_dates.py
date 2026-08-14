import pytest
import pandas as pd
import os
from src.pipeline import run_pipeline
from src.ingestion import read_file
from src.inspection import map_columns, load_aliases

# Fixture generator
def generate_mock_data():
    leads = pd.DataFrame({
        'email': [f'lead{i}@test.com' for i in range(1, 11)],
        'registration_date': [f'2026-06-{i:02d}' for i in range(1, 11)],
        'campaign': ['C1'] * 10,
        'ad_set': ['A1'] * 10,
        'ad_creative': ['AD1'] * 10
    })
    
    sales = pd.DataFrame({
        'email': [f'lead{i}@test.com' for i in range(1, 11)],
        'sale_date': [f'2026-06-{i:02d}' for i in range(5, 15)], # shifted +4 days
        'order_amount': [1000.0] * 10,
        'payment_status': ['successful'] * 10
    })
    
    meta = pd.DataFrame({
        'Campaign Name': ['C1'] * 30,
        'Ad Set Name': ['A1'] * 30,
        'Ad Name': ['AD1'] * 30,
        'Amount Spent': [100.0] * 30,
        'Day': [f'2026-06-{i:02d}' for i in range(1, 31)]
    })
    
    return leads, sales, meta

def base_settings():
    return {
        'report_name': 'Test',
        'client_name': 'Test',
        'cutoff_date': '2026-01-01',
        'fallback_price': 999.0,
        'zero_roi_threshold': 5000.0,
        'currency': 'INR',
        'sale_date_source': 'Actual Sale Date',
        'payment_status_source': 'Actual Payment Status',
        'amount_source': 'Actual Order Amount'
    }

def run_scenario(tmp_path, leads, sales, meta, settings):
    out = tmp_path / "report.xlsx"
    metrics, ver_df, xl = run_pipeline(leads, sales, [meta] if isinstance(meta, pd.DataFrame) else meta, settings, str(out))
    return metrics, ver_df

def test_1_7_day_report(tmp_path):
    leads, sales, meta = generate_mock_data()
    settings = base_settings()
    settings.update({
        'lead_sales_start_date': '2026-06-05', 'lead_sales_end_date': '2026-06-11', # 7 days sales
        'meta_start_date': '2026-06-01', 'meta_end_date': '2026-06-07' # 7 days meta
    })
    m, v = run_scenario(tmp_path, leads, sales, meta, settings)
    assert m['total_sales'] == 7 # Sales dates 05..11
    assert m['raw_meta_spend'] == 700.0

def test_2_30_day_report(tmp_path):
    leads, sales, meta = generate_mock_data()
    settings = base_settings()
    settings.update({
        'lead_sales_start_date': '2026-06-01', 'lead_sales_end_date': '2026-06-30',
        'meta_start_date': '2026-06-01', 'meta_end_date': '2026-06-30'
    })
    m, v = run_scenario(tmp_path, leads, sales, meta, settings)
    assert m['total_sales'] == 10
    assert m['raw_meta_spend'] == 3000.0

def test_3_90_day_report(tmp_path):
    leads, sales, meta = generate_mock_data()
    settings = base_settings()
    settings.update({
        'lead_sales_start_date': '2026-05-01', 'lead_sales_end_date': '2026-07-29',
        'meta_start_date': '2026-05-01', 'meta_end_date': '2026-07-29'
    })
    m, v = run_scenario(tmp_path, leads, sales, meta, settings)
    assert m['total_sales'] == 10
    assert m['raw_meta_spend'] == 3000.0

def test_4_monthly_report(tmp_path):
    test_2_30_day_report(tmp_path) # June is 30 days

def test_5_quarterly_report(tmp_path):
    test_3_90_day_report(tmp_path) 

def test_6_yearly_report(tmp_path):
    leads, sales, meta = generate_mock_data()
    settings = base_settings()
    settings.update({
        'lead_sales_start_date': '2026-01-01', 'lead_sales_end_date': '2026-12-31',
        'meta_start_date': '2026-01-01', 'meta_end_date': '2026-12-31'
    })
    m, v = run_scenario(tmp_path, leads, sales, meta, settings)
    assert m['total_sales'] == 10
    assert m['raw_meta_spend'] == 3000.0

def test_7_full_available_data(tmp_path):
    test_6_yearly_report(tmp_path)

def test_8_custom_arbitrary_date_range(tmp_path):
    leads, sales, meta = generate_mock_data()
    settings = base_settings()
    settings.update({
        'lead_sales_start_date': '2026-06-08', 'lead_sales_end_date': '2026-06-09',
        'meta_start_date': '2026-06-01', 'meta_end_date': '2026-06-05'
    })
    m, v = run_scenario(tmp_path, leads, sales, meta, settings)
    assert m['total_sales'] == 2 # 08, 09
    assert m['raw_meta_spend'] == 500.0

def test_9_start_date_greater_than_end_date(tmp_path):
    leads, sales, meta = generate_mock_data()
    settings = base_settings()
    settings.update({
        'lead_sales_start_date': '2026-06-10', 'lead_sales_end_date': '2026-06-05',
        'meta_start_date': '2026-06-10', 'meta_end_date': '2026-06-05'
    })
    m, v = run_scenario(tmp_path, leads, sales, meta, settings)
    assert m['total_sales'] == 0
    assert m['raw_meta_spend'] == 0.0

def test_10_period_outside_available_data(tmp_path):
    leads, sales, meta = generate_mock_data()
    settings = base_settings()
    settings.update({
        'lead_sales_start_date': '2027-01-01', 'lead_sales_end_date': '2027-12-31',
        'meta_start_date': '2027-01-01', 'meta_end_date': '2027-12-31'
    })
    m, v = run_scenario(tmp_path, leads, sales, meta, settings)
    assert m['total_sales'] == 0
    assert m['raw_meta_spend'] == 0.0

def test_11_partial_meta_coverage(tmp_path):
    leads, sales, meta = generate_mock_data()
    meta = meta.iloc[:5] # Only 5 days
    settings = base_settings()
    settings.update({
        'lead_sales_start_date': '2026-06-01', 'lead_sales_end_date': '2026-06-30',
        'meta_start_date': '2026-06-01', 'meta_end_date': '2026-06-30'
    })
    m, v = run_scenario(tmp_path, leads, sales, meta, settings)
    assert m['total_sales'] == 10
    assert m['raw_meta_spend'] == 500.0 # NOT zeroed, but partial

def test_12_lead_period_different_from_meta_period(tmp_path):
    test_8_custom_arbitrary_date_range(tmp_path)

def test_13_missing_date_values(tmp_path):
    leads, sales, meta = generate_mock_data()
    # Introduce NaT
    sales.loc[0, 'sale_date'] = None
    settings = base_settings()
    settings.update({
        'lead_sales_start_date': '2026-06-01', 'lead_sales_end_date': '2026-06-30',
        'meta_start_date': '2026-06-01', 'meta_end_date': '2026-06-30'
    })
    m, v = run_scenario(tmp_path, leads, sales, meta, settings)
    # The missing date should NOT be dropped because we preserve unresolved dates
    assert m['total_sales'] == 10

def test_14_multiple_meta_files_with_different_date_ranges(tmp_path):
    leads, sales, meta = generate_mock_data()
    meta1 = meta.iloc[:15] # 1 to 15
    meta2 = meta.iloc[15:].copy()
    meta2['Day'] = [f'2026-07-{i:02d}' for i in range(1, 16)] # 15 days in July
    
    settings = base_settings()
    settings.update({
        'lead_sales_start_date': '2026-06-01', 'lead_sales_end_date': '2026-07-31',
        'meta_start_date': '2026-06-01', 'meta_end_date': '2026-07-31'
    })
    m, v = run_scenario(tmp_path, leads, sales, [meta1, meta2], settings)
    assert m['raw_meta_spend'] == 3000.0

@pytest.mark.skipif(not os.path.exists('/Users/apple/Downloads/Lead Sheet Abhishek pal .csv'), reason="Real data not present")
def test_15_completely_different_client_files(tmp_path):
    aliases = load_aliases()
    leads = map_columns(read_file('/Users/apple/Downloads/Lead Sheet Abhishek pal .csv'), aliases)
    sales = map_columns(read_file('/Users/apple/Downloads/Sales .csv'), aliases)
    m1 = map_columns(read_file('/Users/apple/Downloads/Abhishek-Pal-FML-Ad-account-Report.xlsx'), aliases)
    m2 = map_columns(read_file('/Users/apple/Downloads/FML-X-ABHISHEK-PAL-Ad-account-Report.xlsx'), aliases)
    
    settings = base_settings()
    settings.update({
        'lead_sales_start_date': '2026-07-01', 'lead_sales_end_date': '2026-07-31', # Arbitrary custom range for this client
        'meta_start_date': '2026-07-01', 'meta_end_date': '2026-07-31',
        'sale_date_source': 'Lead Registration Date',
        'payment_status_source': 'Treat All Imported Sales as Successful',
        'amount_source': 'Fallback Price Per Sale'
    })
    
    m, v = run_scenario(tmp_path, leads, sales, [m1, m2], settings)
    # We just ensure it doesn't crash and metrics are generated
    assert 'total_sales' in m
    assert 'profit' in m
