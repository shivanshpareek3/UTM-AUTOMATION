import pytest
import pandas as pd
from src.attribution import attribute_sales

def test_attribute_sales_priority_1():
    sales = pd.DataFrame({
        'sale_id': [1],
        'email': ['test@test.com'],
        'campaign': ['S1'],
        'ad_set': ['M1'],
        'ad_creative': ['C1']
    })
    leads = pd.DataFrame() # Empty leads
    sentinels = ['fb']
    
    attr = attribute_sales(sales, leads, sentinels)
    assert len(attr) == 1
    assert attr.iloc[0]['campaign'] == 'S1'
    assert attr.iloc[0]['ad_set'] == 'M1'
    assert attr.iloc[0]['ad_creative'] == 'C1'
    assert attr.iloc[0]['match_level'] == 'Ad Level'
    assert attr.iloc[0]['attribution_source'] == 'Sales Sheet UTM'

def test_attribute_sales_priority_2_email():
    sales = pd.DataFrame({
        'sale_id': [1],
        'email': ['test@test.com']
    })
    leads = pd.DataFrame({
        'email': ['test@test.com'],
        'campaign': ['S2'],
        'ad_set': ['M2'],
        'ad_creative': ['C2'],
        'has_valid_utm': [True]
    })
    sentinels = ['fb']
    
    attr = attribute_sales(sales, leads, sentinels)
    assert attr.iloc[0]['campaign'] == 'S2'
    assert attr.iloc[0]['ad_set'] == 'M2'
    assert attr.iloc[0]['ad_creative'] == 'C2'
    assert attr.iloc[0]['attribution_source'] == 'Leads DB (email)'

def test_attribute_sales_unattributed():
    sales = pd.DataFrame({
        'sale_id': [1],
        'email': ['missing@test.com']
    })
    leads = pd.DataFrame({
        'email': ['test@test.com'],
        'utm_source': ['S2'],
        'utm_medium': ['M2'],
        'utm_content': ['C2'],
        'has_valid_utm': [True]
    })
    sentinels = ['fb']
    
    attr = attribute_sales(sales, leads, sentinels)
    assert attr.iloc[0]['attribution_source'] == 'Unattributed'
    assert attr.iloc[0]['match_level'] == 'Unattributed'
    assert pd.isna(attr.iloc[0]['campaign'])
