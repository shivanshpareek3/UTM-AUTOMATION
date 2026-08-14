import pytest
import pandas as pd
from src.metrics import calculate_metrics

def test_calculate_metrics():
    leads = pd.DataFrame({'email': ['A', 'B']})
    sales = pd.DataFrame({
        'email': ['A'],
        'order_amount': [100.0],
        'registration_fee_applied': [50.0],
        'attributed_spend': [50.0],
        'attribution_source': ['Campaign Match']
    })
    reg_rev = pd.DataFrame({'reg_revenue': [50.0, 50.0]}) # Two registrations
    meta = pd.DataFrame()
    
    metrics = calculate_metrics(leads, sales, reg_rev, meta)
    
    assert metrics['total_leads'] == 2
    assert metrics['total_sales'] == 1
    assert metrics['attributed_sales'] == 1
    assert metrics['backend_revenue'] == 100.0
    assert metrics['total_reg_revenue'] == 100.0
    assert metrics['total_revenue'] == 200.0
    assert metrics['attributed_revenue'] == 150.0 # 100 + 50 from the attributed sale
    assert metrics['attributed_spend'] == 50.0
    assert metrics['profit'] == 100.0 # 150 (attributed) - 50
    assert metrics['roas'] == 3.0 # 150 / 50
    assert metrics['roi_percent'] == 200.0 # 100 / 50 * 100
    assert metrics['cpl'] == 25.0
    assert metrics['cac'] == 50.0
    assert metrics['conversion_rate_percent'] == 50.0

def test_calculate_metrics_zero_spend():
    leads = pd.DataFrame({'email': ['A']})
    sales = pd.DataFrame({
        'email': ['A'],
        'order_amount': [100.0],
        'registration_fee_applied': [0.0],
        'attributed_spend': [0.0],
        'attribution_source': ['Campaign Match']
    })
    reg_rev = pd.DataFrame({'reg_revenue': [0.0]})
    meta = pd.DataFrame()
    
    metrics = calculate_metrics(leads, sales, reg_rev, meta)
    assert metrics['roas'] == 'N/A'
    assert metrics['roi_percent'] == 'N/A'
    assert metrics['cpl'] == 0.0
    assert metrics['cac'] == 'N/A'
    assert metrics['conversion_rate_percent'] == 100.0

def test_profit_calculation_negative():
    leads = pd.DataFrame({'email': ['A']})
    sales = pd.DataFrame({
        'email': ['A'],
        'order_amount': [629930.0],
        'registration_fee_applied': [0.0],
        'attributed_spend': [406647.08],
        'attribution_source': ['Campaign Match']
    })
    reg_rev = pd.DataFrame({'reg_revenue': [0.0]})
    meta = pd.DataFrame()
    
    metrics = calculate_metrics(leads, sales, reg_rev, meta)
    assert metrics['attributed_revenue'] == 629930.0
    assert metrics['attributed_spend'] == 406647.08
    assert round(metrics['profit'], 2) == 223282.92

def test_profit_calculation_positive():
    leads = pd.DataFrame({'email': ['A']})
    sales = pd.DataFrame({
        'email': ['A'],
        'order_amount': [300000.0],
        'registration_fee_applied': [0.0],
        'attributed_spend': [100000.0],
        'attribution_source': ['Campaign Match']
    })
    reg_rev = pd.DataFrame({'reg_revenue': [0.0]})
    meta = pd.DataFrame()
    
    metrics = calculate_metrics(leads, sales, reg_rev, meta)
    assert metrics['attributed_revenue'] == 300000.0
    assert metrics['attributed_spend'] == 100000.0
    assert round(metrics['profit'], 2) == 200000.0

def test_paid_unpaid_metrics():
    settings = {
        'paid_markers': ['paid', 'cpc', 'cpm', 'facebook']
    }
    leads = pd.DataFrame({
        'email': ['A', 'B', 'C'],
        'utm_source': ['facebook', 'organic', 'direct'],
        'utm_medium': ['cpc', 'social', None],
        'has_valid_utm': [True, False, False]
    })
    sales = pd.DataFrame({
        'email': ['A'],
        'order_amount': [100.0],
        'registration_fee_applied': [0.0],
        'attributed_spend': [10.0],
        'attribution_source': ['Campaign Match']
    })
    reg_rev = pd.DataFrame({'reg_revenue': [0.0]})
    meta = pd.DataFrame()
    
    metrics = calculate_metrics(leads, sales, reg_rev, meta, settings)
    assert metrics['total_leads'] == 3
    assert metrics['paid_leads'] == 1
    assert metrics['unpaid_leads'] == 2
    assert round(metrics['paid_funnel_percent'], 2) == 33.33
    assert round(metrics['unpaid_funnel_percent'], 2) == 66.67
    assert metrics['per_sale_value'] == 100.0
