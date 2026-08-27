import pytest
import pandas as pd
from src.inspection import map_columns, check_missing_columns

def test_map_columns():
    df = pd.DataFrame({
        'Email Address': ['a@b.com'],
        'Campaign Name': ['C1'],
        'spend': [100]
    })
    
    aliases = {
        'email': ['email address', 'e-mail'],
        'campaign': ['campaign name', 'utm_source'],
        'spend': ['amount spent', 'spend']
    }
    
    mapped_df = map_columns(df, aliases)
    
    assert 'email' in mapped_df.columns
    assert 'campaign' in mapped_df.columns
    assert 'spend' in mapped_df.columns
    assert 'Email Address' not in mapped_df.columns

def test_check_missing_columns():
    df = pd.DataFrame({'a': [1], 'b': [2]})
    missing = check_missing_columns(df, ['a', 'c', 'd'])
    assert missing == ['c', 'd']

def test_map_columns_ambiguity():
    # Simulate a Leads DataFrame with 'Order Date'
    leads_df = pd.DataFrame({
        'name': ['John'],
        'email': ['j@test.com'],
        'phone': ['123'],
        'Order Date': ['2026-08-11']
    })
    
    aliases = {
        'registration_date': ['registration date', 'order date'],
        'sale_date': ['sale date', 'order date']
    }
    
    mapped_leads = map_columns(leads_df, aliases)
    
    # Prove that 'Order Date' mapped to registration_date (and sale_date safely)
    assert 'registration_date' in mapped_leads.columns
    assert 'sale_date' in mapped_leads.columns
    assert mapped_leads['registration_date'].iloc[0] == '2026-08-11'
    
    # Simulate a Sales DataFrame with 'Order Date'
    sales_df = pd.DataFrame({
        'email': ['j@test.com'],
        'Order Date': ['2026-08-15']
    })
    
    mapped_sales = map_columns(sales_df, aliases)
    assert 'sale_date' in mapped_sales.columns
    assert 'registration_date' in mapped_sales.columns
    assert mapped_sales['sale_date'].iloc[0] == '2026-08-15'

