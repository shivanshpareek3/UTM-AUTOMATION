import pytest
import pandas as pd
from src.metrics import calculate_metrics

def test_calculate_metrics():
    leads = pd.DataFrame({'email': ['A', 'B'], 'has_valid_utm': [True, False]})
    sales = pd.DataFrame({
        'email': ['A'],
        'attribution_source': ['Leads DB (email)'],
        'campaign': ['C1'],
        'order_amount': [8999.0],
        'total_revenue': [8999.0],
        'attributed_spend': [50.0]
    })
    reg_rev = pd.DataFrame({'reg_revenue': [50.0, 50.0]})
    meta = pd.DataFrame({
        'spend': [50.0],
        'campaign': ['C1'],
        'order_amount': [8999.0]
    })
    
    settings = {'fallback_price': 8999.0}
    metrics = calculate_metrics(leads, sales, reg_rev, meta, settings)
    
    assert metrics['total_leads'] == 2
    assert metrics['total_sales'] == 1
    assert metrics['attributed_sales'] == 1
    assert metrics['backend_revenue'] == 8999.0
    assert metrics['total_reg_revenue'] == 100.0
    assert metrics['total_revenue'] == 8999.0
    assert metrics['attributed_revenue'] == 8999.0
    assert metrics['attributed_spend'] == 50.0
    assert metrics['profit'] == 8999.0 - 50.0
    assert metrics['roas'] == 8999.0 / 50.0
    assert metrics['roi_percent'] == ((8999.0 - 50.0) / 50.0) * 100
    assert metrics['cpl'] == 50.0 / 2
    assert metrics['cac'] == 50.0 / 1
    assert metrics['conversion_rate_percent'] == 50.0

def test_calculate_metrics_zero_spend():
    leads = pd.DataFrame({'email': ['A']})
    sales = pd.DataFrame({
        'email': ['A'],
        'attribution_source': ['Leads DB (email)'],
        'order_amount': [8999.0]
    })
    reg_rev = pd.DataFrame({'reg_revenue': [0.0]})
    meta = pd.DataFrame({
        'spend': [0.0],
        'campaign': ['C1'],
        'order_amount': [8999.0]
    })
    
    settings = {'fallback_price': 8999.0}
    metrics = calculate_metrics(leads, sales, reg_rev, meta, settings)
    assert metrics['roas'] == 'N/A'
    assert metrics['roi_percent'] == 'N/A'
    assert metrics['cpl'] == 0.0
    assert metrics['cac'] == 0.0
    assert metrics['conversion_rate_percent'] == 100.0

def test_profit_calculation_negative():
    leads = pd.DataFrame({'email': ['A']})
    sales = pd.DataFrame({
        'email': ['A'],
        'attribution_source': ['Leads DB (email)'],
        'campaign': ['C1'],
        'order_amount': [8999.0],
        'total_revenue': [8999.0],
        'attributed_spend': [406647.08]
    })
    reg_rev = pd.DataFrame({'reg_revenue': [0.0]})
    meta = pd.DataFrame({
        'spend': [406647.08],
        'campaign': ['C1'],
        'order_amount': [8999.0]
    })
    
    settings = {'fallback_price': 8999.0}
    metrics = calculate_metrics(leads, sales, reg_rev, meta, settings)
    assert metrics['attributed_revenue'] == 8999.0
    assert metrics['attributed_spend'] == 406647.08
    assert round(metrics['profit'], 2) == 8999.0 - 406647.08

def test_profit_calculation_positive():
    leads = pd.DataFrame({'email': ['A']})
    sales = pd.DataFrame({
        'email': ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L'],
        'attribution_source': ['Leads DB (email)'] * 12,
        'campaign': ['C1'] * 12,
        'order_amount': [8999.0] * 12,
        'total_revenue': [8999.0] * 12,
        'attributed_spend': [100000.0 / 12] * 12
    })
    reg_rev = pd.DataFrame({'reg_revenue': [0.0]})
    meta = pd.DataFrame({
        'spend': [100000.0],
        'campaign': ['C1'],
        'order_amount': [8999.0]
    })
    
    settings = {'fallback_price': 8999.0}
    metrics = calculate_metrics(leads, sales, reg_rev, meta, settings)
    assert metrics['attributed_revenue'] == 12 * 8999.0
    assert abs(metrics['attributed_spend'] - 100000.0) < 0.01
    assert round(metrics['profit'], 2) == (12 * 8999.0) - 100000.0

def test_paid_unpaid_metrics():
    settings = {
        'paid_markers': ['paid', 'cpc', 'cpm', 'facebook'],
        'fallback_price': 8999.0
    }
    leads = pd.DataFrame({
        'email': ['A', 'B', 'C'],
        'utm_source': ['facebook', 'organic', 'direct'],
        'utm_medium': ['cpc', 'social', None],
        'has_valid_utm': [True, False, False]
    })
    sales = pd.DataFrame({
        'email': ['A'],
        'attribution_source': ['Leads DB (email)'],
        'order_amount': [8999.0]
    })
    reg_rev = pd.DataFrame({'reg_revenue': [0.0]})
    meta = pd.DataFrame({
        'spend': [10.0],
        'campaign': ['C1'],
        'order_amount': [8999.0]
    })
    
    metrics = calculate_metrics(leads, sales, reg_rev, meta, settings)
    assert metrics['total_leads'] == 3
    assert metrics['paid_leads'] == 1
    assert metrics['unpaid_leads'] == 2
    assert round(metrics['paid_funnel_percent'], 2) == 33.33
    assert round(metrics['unpaid_funnel_percent'], 2) == 66.67
    assert metrics['per_sale_value'] == 8999.0
