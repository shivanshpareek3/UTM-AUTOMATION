import pytest
import pandas as pd
from src.pipeline import run_pipeline

def test_lead_metrics_filtered_by_date():
    leads = pd.DataFrame({
        'email': ['lead1@test.com', 'lead2@test.com', 'lead3@test.com'],
        'registration_date': ['2026-08-01', '2026-08-05', '2026-08-10'],
        'campaign': ['ads', 'ads', 'organic']
    })
    sales = pd.DataFrame({
        'email': ['lead2@test.com'],
        'sale_date': ['2026-08-06'],
        'order_amount': [100.0]
    })
    meta = pd.DataFrame({
        'Day': ['2026-08-05'],
        'spend': [50.0],
        'campaign': ['ads']
    })

    # Base settings
    settings = {
        'paid_markers': ['ads'],
        'cutoff_date': '2026-08-01',
        'amount_source': 'Actual Order Amount'
    }

    # Test 1: Full Period (Aug 1 - 10)
    settings['lead_sales_start_date'] = '2026-08-01'
    settings['lead_sales_end_date'] = '2026-08-10'
    settings['meta_start_date'] = '2026-08-01'
    settings['meta_end_date'] = '2026-08-10'

    metrics1, _, _ = run_pipeline(leads.copy(), sales.copy(), [meta.copy()], settings, 'dummy.xlsx')
    
    assert metrics1['total_leads'] == 3
    assert metrics1['paid_leads'] == 2
    assert metrics1['unpaid_leads'] == 1
    assert metrics1['total_sales'] == 1
    assert metrics1['raw_meta_spend'] == 50.0
    assert metrics1['attributed_spend'] <= metrics1['raw_meta_spend']
    
    # Test 2: Filtered Period (Aug 5 - 10)
    settings['lead_sales_start_date'] = '2026-08-05'
    settings['lead_sales_end_date'] = '2026-08-10'
    settings['meta_start_date'] = '2026-08-05'
    settings['meta_end_date'] = '2026-08-10'

    metrics2, _, _ = run_pipeline(leads.copy(), sales.copy(), [meta.copy()], settings, 'dummy2.xlsx')

    # Lead 1 (Aug 1) is now correctly filtered out because the user requested strict window filtering
    assert metrics2['total_leads'] == 3
    assert metrics2['paid_leads'] == 2
    assert metrics2['unpaid_leads'] == 1
    assert metrics2['total_sales'] == 1  # Sale is on Aug 6, still included
    assert metrics2['raw_meta_spend'] == 50.0 # Meta is on Aug 5, still included
    
    # Check that attribution still worked for the sale (Lead 2 registered Aug 5)
    assert metrics2['attributed_sales'] == 1

def test_multiple_meta_files():
    leads = pd.DataFrame()
    sales = pd.DataFrame()
    
    meta1 = pd.DataFrame({
        'Day': ['2026-08-05'],
        'spend': [50.0],
        'campaign': ['ads']
    })
    meta2 = pd.DataFrame({
        'Day': ['2026-08-05'],
        'spend': [100.0],
        'campaign': ['ads2']
    })

    settings = {
        'cutoff_date': '2026-08-01',
        'lead_sales_start_date': '2026-08-01',
        'lead_sales_end_date': '2026-08-10',
        'meta_start_date': '2026-08-01',
        'meta_end_date': '2026-08-10',
    }

    metrics, _, _ = run_pipeline(leads.copy(), sales.copy(), [meta1.copy(), meta2.copy()], settings, 'dummy.xlsx')
    
    assert metrics['raw_meta_spend'] == 150.0
