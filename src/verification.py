import pandas as pd

def run_verification(
    input_sales_count: int,
    excluded_sales_count: int,
    all_sales_df: pd.DataFrame,
    camp_summary: pd.DataFrame,
    adset_summary: pd.DataFrame,
    ad_summary: pd.DataFrame,
    total_windowed_meta_spend: float,
    duplicate_sales_emails: int,
    total_leads_in_window: int,
    funnel_leads_counted: int,
    leads_sheet_reg_revenue: float,
    actual_sale_date_cnt: int = 0,
    derived_sale_date_cnt: int = 0,
    assumed_payment_cnt: int = 0,
    fallback_amount_cnt: int = 0,
    missing_sales_cnt: int = 0,
    standalone_reg_revenue: float = 0.0
) -> pd.DataFrame:
    
    results = []
    
    def add_check(name, expected, actual, diff, explanation, status):
        results.append({
            'Check Name': name,
            'Status': status,
            'Expected': expected,
            'Actual': actual,
            'Difference': diff,
            'Explanation': explanation
        })

    # Check 1: All Sales row count
    c1_expected = input_sales_count - excluded_sales_count
    c1_actual = len(all_sales_df)
    c1_diff = c1_expected - c1_actual
    add_check(
        '1. All Sales row count', c1_expected, c1_actual, c1_diff,
        'Matches valid input sales rows after exclusions',
        'PASS' if c1_diff == 0 else 'FAIL'
    )
    
    # Check 2: Sales totals
    total_sales = len(all_sales_df)
    c_sales = camp_summary['Sales'].sum() if not camp_summary.empty else 0
    a_sales = adset_summary['Sales'].sum() if not adset_summary.empty else 0
    ad_sales = ad_summary['Sales'].sum() if not ad_summary.empty else 0
    
    c2_pass = (total_sales == c_sales == a_sales == ad_sales)
    add_check(
        '2. Summary Sales Match', total_sales, f"C:{c_sales}, AS:{a_sales}, AD:{ad_sales}", 0 if c2_pass else "Mismatch",
        'Campaign/AdSet/Ad Sales totals must equal Total Sales',
        'PASS' if c2_pass else 'FAIL'
    )
    
    # Check 3: Revenue totals
    total_rev = all_sales_df['total_revenue'].sum() if not all_sales_df.empty and 'total_revenue' in all_sales_df.columns else 0.0
    c_rev = camp_summary['Revenue'].sum() if not camp_summary.empty else 0.0
    a_rev = adset_summary['Revenue'].sum() if not adset_summary.empty else 0.0
    ad_rev = ad_summary['Revenue'].sum() if not ad_summary.empty else 0.0
    
    c3_pass = (abs(total_rev - c_rev) < 1.0) and (abs(total_rev - a_rev) < 1.0) and (abs(total_rev - ad_rev) < 1.0)
    add_check(
        '3. Summary Revenue Match', round(total_rev, 2), f"C:{round(c_rev, 2)}, AS:{round(a_rev, 2)}, AD:{round(ad_rev, 2)}", 0 if c3_pass else "Mismatch",
        'Campaign/AdSet/Ad Revenue totals must equal Total Revenue',
        'PASS' if c3_pass else 'FAIL'
    )
    
    # Check 4: Attributed Spend <= Windowed Spend
    total_attr_spend = all_sales_df['attributed_spend'].sum() if not all_sales_df.empty and 'attributed_spend' in all_sales_df.columns else 0.0
    c4_diff = total_windowed_meta_spend - total_attr_spend
    c4_pass = c4_diff >= -0.01 # allow slight float rounding
    add_check(
        '4. Spend Invariant', total_windowed_meta_spend, total_attr_spend, round(c4_diff, 2),
        'Total Attributed Spend <= Total Windowed Meta Spend',
        'PASS' if c4_pass else 'FAIL'
    )
    
    # Check 5: Summary spend totals
    c_s = camp_summary['Spend'].sum() if not camp_summary.empty and 'Spend' in camp_summary.columns else 0.0
    as_s = adset_summary['Spend'].sum() if not adset_summary.empty and 'Spend' in adset_summary.columns else 0.0
    ad_s = ad_summary['Spend'].sum() if not ad_summary.empty and 'Spend' in ad_summary.columns else 0.0
    margin = 0.01
    summary_spend_match = True
    if abs(c_s - total_windowed_meta_spend) > margin:
        summary_spend_match = False
    if as_s > 0 and abs(c_s - as_s) > margin:
        summary_spend_match = False
    if ad_s > 0 and abs(c_s - ad_s) > margin:
        summary_spend_match = False
    add_check(
        '5. Summary Spend Reconcile', round(total_windowed_meta_spend, 2), f"C:{round(c_s, 2)}, AS:{round(as_s, 2)}, AD:{round(ad_s, 2)}", 0 if summary_spend_match else "Mismatch",
        'Summary spend totals reconcile with Total Windowed Meta Spend',
        'PASS' if summary_spend_match else 'FAIL'
    )
    
    # Check 6: Duplicate sales-email
    add_check(
        '6. Duplicate Sales Email', 0, duplicate_sales_emails, duplicate_sales_emails,
        'Report duplicate sales-email count',
        'WARNING' if duplicate_sales_emails > 0 else 'PASS'
    )
    
    # Check 7: Unattributed Count and %
    unattr_count = len(all_sales_df[all_sales_df['attribution_source'] == 'Unattributed']) if not all_sales_df.empty and 'attribution_source' in all_sales_df.columns else 0
    unattr_pct = (unattr_count / total_sales * 100) if total_sales > 0 else 0
    add_check(
        '7. Unattributed Rate', '<10%', f"{unattr_pct:.1f}% ({unattr_count})", f"{max(0, unattr_pct - 10):.1f}%",
        'Warn if > 10%',
        'WARNING' if unattr_pct > 10 else 'PASS'
    )
    
    # Check 8: Leads counted exactly once in funnel summary
    c8_diff = total_leads_in_window - funnel_leads_counted
    add_check(
        '8. Funnel Leads Match', total_leads_in_window, funnel_leads_counted, c8_diff,
        'Every lead counted exactly once in funnel summary',
        'PASS' if c8_diff == 0 else 'FAIL'
    )
    
    # Check 9: Registration fee revenue
    actual_reg_rev = all_sales_df['registration_fee_applied'].sum() if not all_sales_df.empty and 'registration_fee_applied' in all_sales_df.columns else 0.0
    # Add stand-alone reg revenue for non-buyers
    c9_actual = actual_reg_rev + standalone_reg_revenue
    c9_diff = leads_sheet_reg_revenue - c9_actual
    
    add_check(
        '9. Reg Fee Revenue Match', round(leads_sheet_reg_revenue, 2), round(c9_actual, 2), round(c9_diff, 2),
        'Registration fee revenue equals qualifying fees in Leads sheet',
        'PASS' if abs(c9_diff) < 1.0 else 'FAIL'
    )

    # New Data Quality Diagnostic Checks
    add_check(
        '10. Derived Sale Dates', 0, derived_sale_date_cnt, derived_sale_date_cnt,
        'Count of sales using derived dates (Lead Reg/Start Date/Custom)',
        'WARNING' if derived_sale_date_cnt > 0 else 'PASS'
    )
    
    add_check(
        '11. Assumed Payment Status', 0, assumed_payment_cnt, assumed_payment_cnt,
        'Count of sales explicitly assuming successful payment',
        'WARNING' if assumed_payment_cnt > 0 else 'PASS'
    )

    add_check(
        '12. Fallback Order Amounts', 0, fallback_amount_cnt, fallback_amount_cnt,
        'Count of sales using fallback price due to missing order amount',
        'WARNING' if fallback_amount_cnt > 0 else 'PASS'
    )

    explanation_13 = f"{missing_sales_cnt} sales have unresolved sale dates and were not used for date-dependent attribution/spend calculations." if missing_sales_cnt > 0 else 'Count of sales that still lack a valid sale date'
    add_check(
        '13. Unresolved/Missing Sales Dates', 0, missing_sales_cnt, missing_sales_cnt,
        explanation_13,
        'WARNING' if missing_sales_cnt > 0 else 'PASS'
    )
    
    return pd.DataFrame(results)
