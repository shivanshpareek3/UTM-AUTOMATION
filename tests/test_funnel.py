import pytest
import pandas as pd
from src.funnel import apply_funnel_logic, aggregate_registration_revenue

def test_apply_funnel_logic():
    sales = pd.DataFrame({
        'email': ['new@test.com', 'old@test.com'],
        'order_amount': [100.0, 200.0]
    })
    leads = pd.DataFrame({
        'email': ['new@test.com', 'old@test.com'],
        'registration_date': [pd.to_datetime('2024-02-01'), pd.to_datetime('2023-12-01')],
        'webinar_type': ['paid', 'free'],
        'registration_fee': [50.0, 0.0]
    })
    
    cutoff = '2024-01-01'
    df = apply_funnel_logic(sales, leads, cutoff)
    
    assert df[df['email'] == 'new@test.com']['new_old_lead'].iloc[0] == 'New'
    assert df[df['email'] == 'old@test.com']['new_old_lead'].iloc[0] == 'Old'
    
    assert df[df['email'] == 'new@test.com']['total_revenue'].iloc[0] == 150.0
    assert df[df['email'] == 'old@test.com']['total_revenue'].iloc[0] == 200.0

def test_aggregate_registration_revenue():
    leads = pd.DataFrame({
        'email': ['A', 'B', 'C'],
        'registration_date': [pd.to_datetime('2024-01-10'), pd.to_datetime('2024-01-15'), pd.to_datetime('2024-02-01')],
        'webinar_type': ['paid', 'free', 'paid'],
        'registration_fee': [50.0, 0.0, 50.0]
    })
    
    # Window ends Jan 31, C should be excluded
    df = aggregate_registration_revenue(leads, '2024-01-01', '2024-01-31', [])
    assert len(df) == 1
    assert df.iloc[0]['email'] == 'A'
    assert df.iloc[0]['reg_revenue'] == 50.0
