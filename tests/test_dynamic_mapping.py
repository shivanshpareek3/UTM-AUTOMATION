import pandas as pd
import pytest
from src.pipeline import run_pipeline
from src.inspection import suggest_mapping, load_aliases

def test_suggest_mapping():
    aliases = load_aliases()
    
    # Dataset A
    cols_a = ['Campaign', 'Ad Set', 'Ad Name', 'Email', 'Phone']
    assert suggest_mapping('email', cols_a, aliases) == 'Email'
    assert suggest_mapping('campaign', cols_a, aliases) == 'Campaign'
    assert suggest_mapping('phone', cols_a, aliases) == 'Phone'
    
    # Dataset B
    cols_b = ['Campaign Name', 'Adset Name', 'Creative Name', 'Email Address', 'Mobile Number']
    assert suggest_mapping('email', cols_b, aliases) == 'Email Address'
    assert suggest_mapping('campaign', cols_b, aliases) == 'Campaign Name'
    
    # Dataset C
    cols_c = ['campaign_name', 'ad_set_name', 'ad_creative', 'email_address', 'phone_number']
    assert suggest_mapping('email', cols_c, aliases) == 'email_address'
    assert suggest_mapping('phone', cols_c, aliases) == 'phone_number'

def build_leads_a():
    return pd.DataFrame({
        'Campaign': ['Camp1', 'Camp2'],
        'Ad Set': ['Adset1', 'Adset2'],
        'Ad Name': ['Ad1', 'Ad2'],
        'Email': ['test1@example.com', 'test2@example.com'],
        'Phone': ['1234567890', '0987654321'],
        'Registration Date': ['2024-01-01', '2024-01-02']
    })

def build_sales_a():
    return pd.DataFrame({
        'Email': ['test1@example.com'],
        'Sale Date': ['2024-01-05'],
        'Payment Status': ['Paid'],
        'Order Amount': [1000]
    })

def build_meta_a():
    return pd.DataFrame({
        'Campaign': ['Camp1', 'Camp2'],
        'Amount Spent': [100, 200],
        'Day': ['2024-01-01', '2024-01-02'],
        'Ad Set': ['Adset1', 'Adset2'],
        'Ad Name': ['Ad1', 'Ad2']
    })

def build_leads_c():
    return pd.DataFrame({
        'campaign_name': ['Camp1', 'Camp2'],
        'ad_set_name': ['Adset1', 'Adset2'],
        'ad_creative': ['Ad1', 'Ad2'],
        'email_address': ['test1@example.com', 'test2@example.com'],
        'phone_number': ['1234567890', '0987654321'],
        'registration_date': ['2024-01-01', '2024-01-02']
    })
    
def test_pipeline_with_different_schemas(tmp_path):
    settings = {
        'report_name': 'Test',
        'client_name': 'Test',
        'cutoff_date': '2024-01-01',
        'fallback_price': 8999.0,
        'zero_roi_threshold': 5000.0,
        'currency': 'INR',
        'sale_date_source': 'Actual Sale Date',
        'payment_status_source': 'Actual Payment Status',
        'amount_source': 'Actual Order Amount',
        'meta_start_date': '2024-01-01',
        'meta_end_date': '2024-01-31',
        'lead_start_date': '2024-01-01',
        'lead_end_date': '2024-01-31'
    }
    
    # Run A schema
    leads_a = build_leads_a()
    sales_a = build_sales_a()
    meta_a = build_meta_a()
    
    # Explicit mapping
    leads_a = leads_a.rename(columns={'Email': 'email', 'Phone': 'phone', 'Registration Date': 'registration_date', 'Campaign': 'campaign', 'Ad Set': 'ad_set', 'Ad Name': 'ad_creative'})
    sales_a = sales_a.rename(columns={'Email': 'email', 'Sale Date': 'sale_date', 'Payment Status': 'payment_status', 'Order Amount': 'order_amount'})
    meta_a = meta_a.rename(columns={'Campaign': 'campaign', 'Amount Spent': 'spend', 'Day': 'Day', 'Ad Set': 'ad_set', 'Ad Name': 'ad'})
    
    metrics_a, _, _ = run_pipeline(leads_a, sales_a, [meta_a], settings, str(tmp_path / "out_a.xlsx"))
    
    # Run C schema
    leads_c = build_leads_c()
    leads_c = leads_c.rename(columns={'email_address': 'email', 'phone_number': 'phone', 'campaign_name': 'campaign', 'ad_set_name': 'ad_set', 'ad_creative': 'ad_creative'})
    
    metrics_c, _, _ = run_pipeline(leads_c, sales_a, [meta_a], settings, str(tmp_path / "out_c.xlsx"))
    
    assert metrics_a['total_leads'] == metrics_c['total_leads']
    assert metrics_a['total_sales'] == metrics_c['total_sales']
    
def test_missing_optional_column(tmp_path):
    leads = build_leads_a()
    leads = leads.rename(columns={'Email': 'email', 'Registration Date': 'registration_date', 'Campaign': 'campaign'})
    # ad_set is missing entirely
    leads = leads.drop(columns=['Ad Set', 'Ad Name', 'Phone'])
    
    sales = build_sales_a().rename(columns={'Email': 'email', 'Sale Date': 'sale_date', 'Order Amount': 'order_amount'})
    meta = build_meta_a().rename(columns={'Campaign': 'campaign', 'Amount Spent': 'spend', 'Day': 'Day'})
    
    settings = {
        'cutoff_date': '2024-01-01',
        'meta_start_date': '2024-01-01',
        'meta_end_date': '2024-01-31',
        'lead_start_date': '2024-01-01',
        'lead_end_date': '2024-01-31'
    }
    metrics, _, _ = run_pipeline(leads, sales, [meta], settings, str(tmp_path / "out.xlsx"))
    assert metrics['total_leads'] == 2

