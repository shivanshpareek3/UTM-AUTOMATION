import pandas as pd
import sys

def audit_excel(filepath):
    xls = pd.ExcelFile(filepath)
    
    print("A. Workbook path:", filepath)
    print("B. Sheet count/order:")
    for i, sheet in enumerate(xls.sheet_names):
        print(f"  {i+1}. {sheet}")
        
    print("\n--- Sales Reconciliation ---")
    sales_df = pd.read_excel(xls, sheet_name="2. 📋 All Sales (Attributed)")
    excluded_df = pd.read_excel(xls, sheet_name="13. 🚫 Excluded Sales")
    
    print(f"Included Sales: {len(sales_df)}")
    print(f"Excluded Sales: {len(excluded_df)}")
    print(f"Raw Sales: {len(sales_df) + len(excluded_df)}")
    
    unresolved_sales = len(sales_df[sales_df['sale_date_source'] == 'unresolved']) if 'sale_date_source' in sales_df.columns else 0
    print(f"Unresolved Sale Dates: {unresolved_sales}")
    
    unattributed_sales = len(sales_df[sales_df['attribution_source'] == 'Unattributed']) if 'attribution_source' in sales_df.columns else 0
    attributed_sales = len(sales_df) - unattributed_sales
    print(f"Attributed Sales: {attributed_sales}")
    print(f"Unattributed Sales: {unattributed_sales}")
    
    print("\n--- Column Checks in All Sales ---")
    cols = ['attribution_source', 'match_level', 'campaign', 'ad_set', 'ad_creative', 'sale_date_source', 'payment_status_source', 'amount_source', 'data_quality_warning']
    missing_cols = [c for c in cols if c not in sales_df.columns]
    print(f"Missing columns: {missing_cols}")
    if not missing_cols:
        for c in cols:
            print(f"{c} missing values: {sales_df[c].isna().sum()}")
    
    print("\n--- Old/New Reconciliation ---")
    if 'new_old_lead' in sales_df.columns:
        print(sales_df['new_old_lead'].value_counts())
    else:
        print("Missing new_old_lead column")
        
    print("\n--- Revenue & Spend Reconciliation ---")
    camp_sum = pd.read_excel(xls, sheet_name="3. 📢 Campaign Summary")
    adset_sum = pd.read_excel(xls, sheet_name="4. 🎯 Ad Set Summary")
    ad_sum = pd.read_excel(xls, sheet_name="5. 🎨 Ad Creative Summary")
    
    c_sales = camp_sum['Sales'].sum() if 'Sales' in camp_sum.columns else 0
    a_sales = adset_sum['Sales'].sum() if 'Sales' in adset_sum.columns else 0
    ad_sales = ad_sum['Sales'].sum() if 'Sales' in ad_sum.columns else 0
    
    c_rev = camp_sum['Revenue'].sum() if 'Revenue' in camp_sum.columns else 0
    a_rev = adset_sum['Revenue'].sum() if 'Revenue' in adset_sum.columns else 0
    ad_rev = ad_sum['Revenue'].sum() if 'Revenue' in ad_sum.columns else 0
    
    c_spend = camp_sum['Spend'].sum() if 'Spend' in camp_sum.columns else 0
    
    raw_rev = sales_df['order_amount'].sum() if 'order_amount' in sales_df.columns else 0
    final_rev = sales_df['total_revenue'].sum() if 'total_revenue' in sales_df.columns else 0
    # Add standalone if not in total_revenue? Actually total_revenue in All Sales only includes backend buyers.
    # Total Final Revenue = Campaign Summary Revenue.
    
    attr_spend = sales_df['attributed_spend'].sum() if 'attributed_spend' in sales_df.columns else 0
    
    print(f"Raw Revenue (order_amount): {raw_rev}")
    print(f"Final Revenue in All Sales: {final_rev}")
    print(f"Campaign Summary Revenue: {c_rev}")
    print(f"Ad Set Summary Revenue: {a_rev}")
    print(f"Ad Creative Summary Revenue: {ad_rev}")
    
    print(f"Attributed Spend in All Sales: {attr_spend}")
    print(f"Campaign Summary Spend: {c_spend}")
    
    print(f"Campaign Sales: {c_sales}")
    print(f"Ad Set Sales: {a_sales}")
    print(f"Ad Creative Sales: {ad_sales}")
    
    print("\n--- Zero Spend Campaigns ---")
    if 'Spend' in camp_sum.columns:
        zero_spend_c = camp_sum[camp_sum['Spend'] == 0]
        print(f"Zero Spend Campaigns: {len(zero_spend_c)}")
        if len(zero_spend_c) > 0:
            print("Examples:")
            print(zero_spend_c[['Node Name', 'Sales', 'Revenue', 'Spend', 'ROAS']].head())
            
    print("\n--- Formatting Check ---")
    print(f"ROAS values in Campaign Summary (head 5): {camp_sum['ROAS'].head().tolist()}")
    if (camp_sum['ROAS'] == 'N/A').any():
        print("Found 'N/A' in ROAS - formatting OK")
        
    print("\n--- Verification Sheet ---")
    ver_df = pd.read_excel(xls, sheet_name="12. ✅ Verification")
    for _, row in ver_df.iterrows():
        print(f"[{row['Status']}] {row['Check Name']} | Expected: {row['Expected']} | Actual: {row['Actual']} | Diff: {row['Difference']} | {row['Explanation']}")

if __name__ == '__main__':
    audit_excel('output/real_data_report.xlsx')
