import pytest
import pandas as pd
from src.spend import allocate_spend

def test_allocate_spend_lead_share():
    # Golden methodology directly uses Meta spend natively without lead-based proportional attribution
    sales = pd.DataFrame()
    leads = pd.DataFrame()
    meta = pd.DataFrame({
        'Campaign Name': ['C1', 'C2'],
        'Ad Set Name': ['A1', 'A2'],
        'Ad Name': ['AD1', 'AD3'],
        'spend': [100.0, 50.0],
        'Day': ['2024-01-01', '2024-01-01']
    })
    sales_df, camp_spend, adset_spend, ad_spend, placement_spend = allocate_spend(sales, meta, leads, '2024-01-01', '2024-01-01')
    
    assert camp_spend[camp_spend['camp_norm'] == 'c1']['spend'].iloc[0] == 100.0
    assert camp_spend[camp_spend['camp_norm'] == 'c2']['spend'].iloc[0] == 50.0
    
    # Ad level natively passes through
    c1_ad1 = ad_spend[(ad_spend['camp_norm'] == 'c1') & (ad_spend['ad_norm'] == 'ad1')]
    assert c1_ad1['spend'].iloc[0] == 100.0

def test_allocate_spend_no_leads():
    sales = pd.DataFrame()
    leads = pd.DataFrame()
    meta = pd.DataFrame({
        'Campaign Name': ['C1'],
        'spend': [100.0],
        'Day': ['2024-01-01']
    })
    sales_df, camp_spend, adset_spend, ad_spend, placement_spend = allocate_spend(sales, meta, leads, '2024-01-01', '2024-01-01')
    
    assert camp_spend[camp_spend['camp_norm'] == 'c1']['spend'].iloc[0] == 100.0

def test_allocate_spend_zero_spend():
    sales = pd.DataFrame()
    leads = pd.DataFrame()
    meta = pd.DataFrame({
        'Campaign Name': ['C1'],
        'Ad Set Name': ['A1'],
        'Ad Name': ['AD1'],
        'spend': [0.0],
        'Day': ['2024-01-01']
    })
    sales_df, camp_spend, adset_spend, ad_spend, placement_spend = allocate_spend(sales, meta, leads, '2024-01-01', '2024-01-01')
    
    assert camp_spend[camp_spend['camp_norm'] == 'c1']['spend'].iloc[0] == 0.0
    assert ad_spend[ad_spend['camp_norm'] == 'c1']['spend'].iloc[0] == 0.0
