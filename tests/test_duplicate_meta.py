import pytest
import pandas as pd
from src.pipeline import run_pipeline

def test_duplicate_meta_rows_dropped():
    leads = pd.DataFrame()
    sales = pd.DataFrame()
    
    # Exact duplicate files
    meta1 = pd.DataFrame({
        'Day': ['2026-08-05'],
        'spend': [50.0],
        'campaign': ['ads']
    })
    meta2 = pd.DataFrame({
        'Day': ['2026-08-05'],
        'spend': [50.0],
        'campaign': ['ads']
    })

    settings = {
        'cutoff_date': '2026-08-01',
        'lead_sales_start_date': '2026-08-01',
        'lead_sales_end_date': '2026-08-10',
        'meta_start_date': '2026-08-01',
        'meta_end_date': '2026-08-10',
    }

    metrics, _, _ = run_pipeline(leads.copy(), sales.copy(), [meta1.copy(), meta2.copy()], settings, 'dummy.xlsx')
    
    # It should drop perfectly duplicate rows, resulting in 50 spend, not 100
    assert metrics['raw_meta_spend'] == 50.0

def test_overlapping_but_different_meta_rows_kept():
    leads = pd.DataFrame()
    sales = pd.DataFrame()
    
    # Different campaigns on the same day
    meta1 = pd.DataFrame({
        'Day': ['2026-08-05'],
        'spend': [50.0],
        'campaign': ['ads1']
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
    
    # It should keep both because they are distinct
    assert metrics['raw_meta_spend'] == 150.0
