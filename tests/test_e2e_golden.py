import pandas as pd
import pytest
from src.pipeline import run_pipeline

def test_e2e_golden_methodology():
    # 1. Mock Leads Data
    leads_df = pd.DataFrame([
        {'email': 'test1@example.com', 'registration_date': '2024-01-01', 'campaign': 'C1', 'ad_set': 'A1', 'ad_creative': 'Ad1', 'name': 'Test 1', 'registration_fee': 99},
        {'email': 'test2@example.com', 'registration_date': '2024-01-02', 'campaign': 'C2', 'ad_set': 'A2', 'ad_creative': 'Ad2', 'name': 'Test 2', 'registration_fee': 0},
        {'email': 'test3@example.com', 'registration_date': '2024-01-03', 'campaign': 'C1', 'ad_set': 'A1', 'ad_creative': 'Ad1', 'name': 'Test 3', 'registration_fee': 99}
    ])
    
    # 2. Mock Sales Data
    sales_df = pd.DataFrame([
        {'email': 'test1@example.com', 'name': 'Test 1', 'phone': '1234567890', 'sale_date': '2024-01-05', 'order_amount': 5000, 'payment_status': 'paid'},
        {'email': 'test4@example.com', 'name': 'Test 4', 'phone': '0987654321', 'sale_date': '2024-01-06', 'order_amount': 3000, 'payment_status': 'paid'} # Unattributed
    ])
    
    # 3. Mock Meta Spend with DIFFERENT raw column name manually mapped to 'spend'
    # Simulating UI mapping: The raw column was "Amount spent (INR)", but UI passes it as canonical 'spend'
    meta_df_mapped = pd.DataFrame([
        {'Day': '2024-01-01', 'campaign': 'C1', 'ad_set': 'A1', 'ad': 'Ad1', 'spend': 1000},
        {'Day': '2024-01-02', 'campaign': 'C2', 'ad_set': 'A2', 'ad': 'Ad2', 'spend': 2000},
        {'Day': '2024-01-03', 'campaign': 'C3', 'ad_set': 'A3', 'ad': 'Ad3', 'spend': 500} # Unallocated
    ])
    
    settings = {
        'report_name': 'Test',
        'client_name': 'Test Client',
        'cutoff_date': '2024-01-01',
        'funnel_type': 'Paid',
        'fallback_price': 8999.0,
        'paid_funnel_price': 8999.0,
        'zero_roi_threshold': 5000.0,
        'currency': 'INR',
        'sale_date_source': 'Actual Sale Date',
        'payment_status_source': 'Actual Payment Status',
        'amount_source': 'Actual Order Amount',
        'lead_sales_start_date': '2024-01-01',
        'lead_sales_end_date': '2024-01-10',
        'meta_start_date': '2024-01-01',
        'meta_end_date': '2024-01-10',
        'lead_start_date': '2024-01-01',
        'lead_end_date': '2024-01-10',
        'ad_start_date': '2024-01-01',
        'ad_end_date': '2024-01-10'
    }
    
    # 6. Run Golden Methodology
    metrics, ver_df, xl_path = run_pipeline(leads_df, sales_df, [meta_df_mapped], settings, 'output/test_e2e.xlsx')
    
    # 7. Verifies Raw Meta Spend
    assert metrics['raw_meta_spend'] == 3500.0
    
    # 8. Verifies Attributed Spend
    # Sales: test1@example.com is from C1. C1 spent 1000. So 1000 is attributed.
    assert metrics['attributed_spend'] == 1000.0
    
    # 9. Verifies Unallocated Spend (3500 - 1000 = 2500)
    assert metrics['unallocated_spend'] == 2500.0
    
    # 10. Verifies Revenue
    # Backend Revenue = 5000 + 3000 = 8000
    # Reg Revenue = 99 (test1) + 99 (test3) = 198
    # Total = 8198
    assert metrics['backend_revenue'] == 8000.0
    assert metrics['total_reg_revenue'] == 198.0
    assert metrics['total_revenue'] == 8198.0
    
    # Attributed Revenue = test1 (5000 backend + 99 reg) = 5099
    assert metrics['attributed_revenue'] == 5099.0
    
    # 11. Verifies Profit (Attributed Rev - Attributed Spend = 5099 - 1000 = 4099)
    assert metrics['profit'] == 4099.0
    
    # 12. Verifies ROAS (Attributed Rev / Attributed Spend = 5099 / 1000 = 5.099)
    assert round(metrics['roas'], 2) == 5.10
    
    # 13. Verifies ROI (Profit / Attributed Spend = 4099 / 1000 = 409.9%)
    assert round(metrics['roi_percent'], 1) == 409.9
    
    # 14. Verifies CAC (Attributed Spend / Attributed Sales = 1000 / 1 = 1000)
    assert metrics['cac'] == 1000.0
    
    # Golden methodology does not crash with KeyError!
    
def test_missing_spend_raises_error():
    # 15. Verifies KeyError when spend is missing
    leads_df = pd.DataFrame()
    sales_df = pd.DataFrame()
    meta_df_bad = pd.DataFrame([
        {'Day': '2024-01-01', 'campaign': 'C1', 'ad_set': 'A1', 'ad': 'Ad1', 'Amount spent (INR)': 1000}
    ])
    
    settings = {}
    
    with pytest.raises(KeyError, match="'spend' column is MISSING"):
        run_pipeline(leads_df, sales_df, [meta_df_bad], settings, 'output/test_e2e_bad.xlsx')

if __name__ == "__main__":
    test_e2e_golden_methodology()
    test_missing_spend_raises_error()
    print("All E2E Golden Methodology tests passed!")
