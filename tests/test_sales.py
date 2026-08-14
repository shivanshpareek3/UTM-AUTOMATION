import pytest
import pandas as pd
from src.sales import process_sales

def test_process_sales_fallback_price():
    df = pd.DataFrame({
        'email': ['test@test.com'],
        'sale_date': ['2024-01-01']
    })
    
    settings = {'fallback_price': 999.0, 'payment_status_source': 'Actual Payment Status'}
    valid, excluded = process_sales(df, settings)
    assert len(valid) == 1
    assert valid.iloc[0]['order_amount'] == 999.0
    assert valid.iloc[0]['amount_source'] == 'fallback_price'
    assert len(excluded) == 0

def test_process_sales_filtering():
    df = pd.DataFrame({
        'email': ['valid@test.com', 'failed@test.com', 'refunded@test.com', 'pending@test.com'],
        'payment_status': ['successful', 'failed', 'refunded', 'pending']
    })
    
    settings = {'fallback_price': 999.0, 'payment_status_source': 'Actual Payment Status'}
    valid, excluded = process_sales(df, settings)
    assert len(valid) == 1
    assert valid.iloc[0]['email'] == 'valid@test.com'
    assert len(excluded) == 3

def test_process_sales_assume_successful():
    df = pd.DataFrame({
        'email': ['missing@test.com', 'failed@test.com'],
        'payment_status': [None, 'failed']
    })
    
    settings = {'fallback_price': 999.0, 'payment_status_source': 'Treat All Imported Sales as Successful'}
    valid, excluded = process_sales(df, settings)
    assert len(valid) == 2
    assert len(excluded) == 0
    assert 'assumed_successful' in valid['payment_status_source'].values
    
def test_process_sales_exclude_missing():
    df = pd.DataFrame({
        'email': ['valid@test.com', 'missing@test.com'],
        'payment_status': ['successful', None]
    })
    
    settings = {'fallback_price': 999.0, 'payment_status_source': 'Exclude Sales Without Payment Status'}
    valid, excluded = process_sales(df, settings)
    assert len(valid) == 1
    assert valid.iloc[0]['email'] == 'valid@test.com'
    assert len(excluded) == 1
    assert excluded.iloc[0]['email'] == 'missing@test.com'
