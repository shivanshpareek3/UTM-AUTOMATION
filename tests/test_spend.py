import pytest
import pandas as pd
from src.spend import allocate_spend

def test_allocate_spend_lead_share():
    sales = pd.DataFrame()
    leads = pd.DataFrame({
        'campaign': ['C1', 'C1', 'C2'],
        'ad_set': ['A1', 'A1', 'A2'],
        'ad_creative': ['AD1', 'AD2', 'AD3']
    })
    meta = pd.DataFrame({
        'Campaign Name': ['C1', 'C2'],
        'Amount Spent': [100.0, 50.0],
        'Day': ['2024-01-01', '2024-01-01']
    })
    sales_df, camp_spend, adset_spend, ad_spend, placement_spend = allocate_spend(sales, meta, leads, '2024-01-01', '2024-01-01')
    
    # C1 has 2 leads, C2 has 1 lead
    assert camp_spend[camp_spend['camp_norm'] == 'c1']['Amount Spent'].iloc[0] == 100.0
    assert camp_spend[camp_spend['camp_norm'] == 'c2']['Amount Spent'].iloc[0] == 50.0
    
    # Ad level share: C1->A1->AD1 has 1 lead (50% of C1 leads)
    c1_ad1 = ad_spend[(ad_spend['camp_norm'] == 'c1') & (ad_spend['ad_norm'] == 'ad1')]
    assert c1_ad1['Amount Spent'].iloc[0] == 50.0
    
    c1_ad2 = ad_spend[(ad_spend['camp_norm'] == 'c1') & (ad_spend['ad_norm'] == 'ad2')]
    assert c1_ad2['Amount Spent'].iloc[0] == 50.0

def test_allocate_spend_no_leads():
    sales = pd.DataFrame()
    leads = pd.DataFrame()
    meta = pd.DataFrame({
        'Campaign Name': ['C1'],
        'Amount Spent': [100.0],
        'Day': ['2024-01-01']
    })
    sales_df, camp_spend, adset_spend, ad_spend, placement_spend = allocate_spend(sales, meta, leads, '2024-01-01', '2024-01-01')
    
    assert camp_spend[camp_spend['camp_norm'] == 'c1']['Amount Spent'].iloc[0] == 100.0
    # Adset and Ad should have 0 spend because there are no leads to calculate share
    assert len(adset_spend) == 0

def test_allocate_spend_zero_spend():
    sales = pd.DataFrame()
    leads = pd.DataFrame({
        'campaign': ['C1'],
        'ad_set': ['A1'],
        'ad_creative': ['AD1']
    })
    meta = pd.DataFrame({
        'Campaign Name': ['C1'],
        'Amount Spent': [0.0],
        'Day': ['2024-01-01']
    })
    sales_df, camp_spend, adset_spend, ad_spend, placement_spend = allocate_spend(sales, meta, leads, '2024-01-01', '2024-01-01')
    
    assert camp_spend[camp_spend['camp_norm'] == 'c1']['Amount Spent'].iloc[0] == 0.0
    assert ad_spend[ad_spend['camp_norm'] == 'c1']['Amount Spent'].iloc[0] == 0.0
