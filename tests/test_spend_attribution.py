import pandas as pd
from src.spend import allocate_spend

def test_lead_share_proportional_allocation():
    # A campaign with 100 leads, ₹10,000 spend and 40 paid leads
    # CPL = ₹100
    # Attributed Spend = ₹4,000
    # Unallocated Spend = ₹6,000
    
    # 1. Setup Meta Data
    meta_df = pd.DataFrame({
        'Day': ['2026-08-10'],
        'Campaign name': ['Test Campaign'],
        'Amount spent (INR)': [10000.0]
    })
    
    # 2. Setup Leads Data (100 leads)
    leads_df = pd.DataFrame({
        'campaign': ['Test Campaign'] * 100,
        'ad_set': ['AdSet1'] * 100,
        'ad_creative': ['Ad1'] * 100
    })
    
    # 3. Setup Sales Data (40 sales)
    sales_df = pd.DataFrame({
        'sale_id': range(1, 41),
        'campaign': ['Test Campaign'] * 40,
        'ad_set': ['AdSet1'] * 40,
        'ad_creative': ['Ad1'] * 40,
        'match_level': ['Campaign'] * 40 # valid matches
    })
    
    sales_out, camp_out, adset_out, ad_out = allocate_spend(
        sales_df.copy(), meta_df, leads_df, '2026-08-01', '2026-08-31'
    )
    
    # 4. Assertions
    total_attributed = sales_out['attributed_spend'].sum()
    total_raw = meta_df['Amount spent (INR)'].sum()
    total_unallocated = total_raw - total_attributed
    
    # 100% of spend is attributed since there is at least one sale
    assert abs(total_attributed - 10000.0) < 0.01, f"Expected 10000, got {total_attributed}"
    assert abs(total_unallocated - 0.0) < 0.01, f"Expected 0, got {total_unallocated}"
    
    # Prove that one sale DOES attribute 100% of campaign spend
    sales_df_1 = sales_df.iloc[:1].copy()
    sales_out_1, _, _, _ = allocate_spend(
        sales_df_1, meta_df, leads_df, '2026-08-01', '2026-08-31'
    )
    
    total_attributed_1 = sales_out_1['attributed_spend'].sum()
    assert abs(total_attributed_1 - 10000.0) < 0.01, f"Expected 10000, got {total_attributed_1}"

    
