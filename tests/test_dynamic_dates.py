import pandas as pd
import pytest
from src.normalization import parse_date_series, parse_date_range
from src.pipeline import run_pipeline

def test_meta_date_range():
    # Test A - Meta date range overlapping
    s = pd.Series(["2026-08-01 - 2026-08-23"])
    df = parse_date_range(s)
    
    start_dt = pd.to_datetime("2026-08-01")
    end_dt = pd.to_datetime("2026-08-23")
    
    assert df.iloc[0]['start_date'] == start_dt
    assert df.iloc[0]['end_date'] == end_dt
    
    # Check overlap logic explicitly
    # Requested window: 2026-08-15 to 2026-08-21
    m_sdt = pd.to_datetime("2026-08-15")
    m_edt = pd.to_datetime("2026-08-21")
    
    overlap = (df.iloc[0]['start_date'] <= m_edt) and (df.iloc[0]['end_date'] >= m_sdt)
    assert overlap is True
    
    # Test B - Meta outside range
    s_out = pd.Series(["2026-08-01 - 2026-08-10"])
    df_out = parse_date_range(s_out)
    overlap_out = (df_out.iloc[0]['start_date'] <= m_edt) and (df_out.iloc[0]['end_date'] >= m_sdt)
    assert overlap_out is False

def test_sales_timezone_parsing():
    # Test D - Sales filtering with Indian Standard Time
    s = pd.Series([
        "24/08/2026 10:35 am (Indian Standard Time)",
        "25-08-2026 11:00 am (IST)",
        "2026-08-26 12:00:00 (EST)",
        "Invalid Date (IST)"
    ])
    
    parsed = parse_date_series(s)
    
    assert parsed.iloc[0].year == 2026
    assert parsed.iloc[0].month == 8
    assert parsed.iloc[0].day == 24
    assert parsed.iloc[0].hour == 10
    
    assert parsed.iloc[1].day == 25
    assert parsed.iloc[2].day == 26
    assert pd.isna(parsed.iloc[3])

def test_no_silent_zero():
    # Test E - No silent zero if parsing fails in pipeline
    leads_df = pd.DataFrame({'email': ['test@test.com'], 'registration_date': ['2026-08-16']})
    sales_df = pd.DataFrame({'email': ['test@test.com'], 'sale_date': ['2026-08-17'], 'payment_status': ['paid'], 'order_amount': [1000]})
    
    meta_df = pd.DataFrame({
        'campaign': ['camp1'],
        'spend': [1000],
        'Day': ['Invalid Date Format Completely']
    })
    
    settings = {
        'report_name': 'Test',
        'client_name': 'Test',
        'cutoff_date': '2026-01-01',
        'fallback_price': 8999.0,
        'zero_roi_threshold': 5000.0,
        'currency': 'INR',
        'sale_date_source': 'Actual Sale Date',
        'payment_status_source': 'Actual Payment Status',
        'amount_source': 'Actual Order Amount',
        'meta_start_date': '2026-08-15',
        'meta_end_date': '2026-08-21',
        'lead_start_date': '2026-08-15',
        'lead_end_date': '2026-08-21',
        'lead_sales_start_date': '2026-08-15',
        'lead_sales_end_date': '2026-08-21'
    }
    
    with pytest.raises(ValueError, match="Could not parse any dates from Meta 'Day' column"):
        run_pipeline(leads_df, sales_df, [meta_df], settings, "test.xlsx")

def test_lead_filtering():
    # Test C - Lead filtering
    leads_df = pd.DataFrame({
        'email': ['in1@test.com', 'in2@test.com', 'out1@test.com'],
        'registration_date': ['2026-08-16', '2026-08-20', '2026-08-10']
    })
    sales_df = pd.DataFrame(columns=['email', 'sale_date', 'payment_status', 'order_amount'])
    meta_df = pd.DataFrame(columns=['campaign', 'spend', 'Day'])
    
    settings = {
        'report_name': 'Test',
        'client_name': 'Test',
        'cutoff_date': '2026-01-01',
        'fallback_price': 8999.0,
        'zero_roi_threshold': 5000.0,
        'currency': 'INR',
        'sale_date_source': 'Actual Sale Date',
        'payment_status_source': 'Actual Payment Status',
        'amount_source': 'Actual Order Amount',
        'meta_start_date': '2026-08-15',
        'meta_end_date': '2026-08-21',
        'lead_start_date': '2026-08-15',
        'lead_end_date': '2026-08-21',
        'lead_sales_start_date': '2026-08-15',
        'lead_sales_end_date': '2026-08-21'
    }
    
    metrics, _, _ = run_pipeline(leads_df, sales_df, [], settings, "test.xlsx")
    
    # Total leads should be 2 because 1 is outside the window
    assert metrics['total_leads'] == 2
