import pytest
import pandas as pd
from src.attribution import attribute_sales

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
    assert attr.iloc[0]['campaign'] == 'Unattributed'

from src.normalization import normalize_phone, normalize_email

def test_regression_phone_dot_zero():
    # phone number with .0 suffix
    assert normalize_phone("7981582658.0") == "7981582658"
    assert normalize_phone(7981582658.0) == "7981582658"

def test_regression_phone_numeric_vs_string():
    # phone number stored as numeric in one file and string in another
    assert normalize_phone(9712867122) == normalize_phone("9712867122")
    assert normalize_phone("9712867122") == "9712867122"

def test_regression_email_whitespace_case():
    # email case/whitespace normalization
    assert normalize_email(" TEST@test.com ") == "test@test.com"
    assert normalize_email("t e s t@test.com") == "test@test.com"

def test_regression_valid_lead_remains_attributable():
    # valid matched lead with valid UTM must remain attributable
    sales = pd.DataFrame({
        'sale_id': [1],
        'email': ['test@test.com'],
        'phone': [9891326996]
    })
    leads = pd.DataFrame({
        'email': ['test@test.com'],
        'phone': ["9891326996.0"],
        'campaign': ['Foremost Leads <> 01/07 <> ABO'],
        'ad_set': ['Adset1'],
        'ad_creative': ['Ad1'],
        'has_valid_utm': [True]
    })
    sentinels = ['fb']
    attr = attribute_sales(sales, leads, sentinels)
    assert attr.iloc[0]['attribution_source'] == 'Leads DB (email)'
    assert attr.iloc[0]['campaign'] == 'Foremost Leads <> 01/07 <> ABO'

def test_regression_genuinely_unmatched_sale():
    # genuinely unmatched sale must remain unattributed
    sales = pd.DataFrame({
        'sale_id': [1],
        'email': ['unmatched@test.com'],
        'phone': [1234567890]
    })
    leads = pd.DataFrame({
        'email': ['test@test.com'],
        'phone': ["9891326996"],
        'campaign': ['Foremost Leads <> 01/07 <> ABO'],
        'ad_set': ['Adset1'],
        'ad_creative': ['Ad1'],
        'has_valid_utm': [True]
    })
    sentinels = ['fb']
    attr = attribute_sales(sales, leads, sentinels)
    assert attr.iloc[0]['attribution_source'] == 'Unattributed'

