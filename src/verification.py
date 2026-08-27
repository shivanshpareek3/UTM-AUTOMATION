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
    standalone_reg_revenue: float = 0.0,
    metrics: dict = None
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
    # Campaign summaries only contain ATTRIBUTED sales (unattributed sales have no campaign)
    # So we compare against attributed sales count, not total sales
    total_sales = len(all_sales_df)
    attributed_sales_count = len(all_sales_df[all_sales_df['attribution_source'] != 'Unattributed']) if 'attribution_source' in all_sales_df.columns else total_sales
    unattributed_sales_count = total_sales - attributed_sales_count
    c_sales = camp_summary['Total Sales'].sum() if not camp_summary.empty else 0
    a_sales = adset_summary['Sales'].sum() if not adset_summary.empty else 0
    ad_sales = ad_summary['Sales'].sum() if not ad_summary.empty else 0
    
    c2_pass = (attributed_sales_count == c_sales == a_sales == ad_sales)
    add_check(
        '2. Summary Sales Match', attributed_sales_count, f"C:{c_sales}, AS:{a_sales}, AD:{ad_sales}", 0 if c2_pass else "Mismatch",
        f'Campaign/AdSet/Ad Sales totals must equal Attributed Sales ({attributed_sales_count}). {unattributed_sales_count} unattributed sale(s) correctly excluded from summaries.',
        'PASS' if c2_pass else 'WARNING'
    )
    
    # Check 3: Revenue totals
    # Campaign summaries only show attributed revenue — compare against attributed revenue only
    attributed_sales_df = all_sales_df[all_sales_df['attribution_source'] != 'Unattributed'] if 'attribution_source' in all_sales_df.columns else all_sales_df
    attr_rev = attributed_sales_df['total_revenue'].sum() if not attributed_sales_df.empty and 'total_revenue' in attributed_sales_df.columns else 0.0
    c_rev = camp_summary['Total Revenue'].sum() if not camp_summary.empty else 0.0
    a_rev = adset_summary['Revenue'].sum() if not adset_summary.empty else 0.0
    ad_rev = ad_summary['Revenue'].sum() if not ad_summary.empty else 0.0
    
    c3_pass = (abs(attr_rev - c_rev) < 1.0) and (abs(attr_rev - a_rev) < 1.0) and (abs(attr_rev - ad_rev) < 1.0)
    add_check(
        '3. Summary Revenue Match', round(attr_rev, 2), f"C:{round(c_rev, 2)}, AS:{round(a_rev, 2)}, AD:{round(ad_rev, 2)}", 0 if c3_pass else "Mismatch",
        'Campaign/AdSet/Ad Revenue totals must equal Attributed Revenue (unattributed revenue excluded)',
        'PASS' if c3_pass else 'WARNING'
    )
    
    # Check 4: Spend Invariant
    if metrics:
        attr_sp = metrics.get('attributed_spend', 0.0)
        unalloc_sp = metrics.get('unallocated_spend', 0.0)
        calc_meta = attr_sp + unalloc_sp
        c4_diff = total_windowed_meta_spend - calc_meta
        c4_pass = abs(c4_diff) < 0.05
        add_check(
            '4. Spend Invariant', round(total_windowed_meta_spend, 2), round(calc_meta, 2), round(c4_diff, 2),
            'Attributed Spend + Unallocated Spend must exactly equal Total Windowed Meta Spend',
            'PASS' if c4_pass else 'FAIL'
        )
    else:
        add_check(
            '4. Spend Invariant', total_windowed_meta_spend, "N/A", "N/A",
            'Metrics not provided for invariant check',
            'WARNING'
        )

    # Check 5: Summary spend totals
    c_s = camp_summary['Raw Meta Spend'].sum() if not camp_summary.empty and 'Raw Meta Spend' in camp_summary.columns else 0.0
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
        '7. Unattributed Rate', 10.0, round(unattr_pct, 1), round(max(0, unattr_pct - 10), 1),
        f'Warn if > 10% unattributed. Current: {unattr_pct:.1f}% ({unattr_count} sales)',
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
    
    if metrics:
        # Invariants only — these verify the actual business math
        def safe_float(v):
            if v is None or str(v).strip() == 'N/A':
                return 0.0
            try:
                return float(v)
            except (TypeError, ValueError):
                return 0.0

        rev_inv_diff = abs((safe_float(metrics.get('attributed_revenue')) + safe_float(metrics.get('unattributed_revenue'))) - safe_float(metrics.get('total_revenue')))
        add_check('INV. Revenue Formula', 0.0, round(rev_inv_diff, 4), round(rev_inv_diff, 4), 'Attributed + Unattributed = Total Revenue', 'PASS' if rev_inv_diff < 0.1 else 'FAIL')

        spend_inv_diff = abs((safe_float(metrics.get('attributed_spend')) + safe_float(metrics.get('unallocated_spend'))) - safe_float(metrics.get('raw_meta_spend')))
        add_check('INV. Spend Formula', 0.0, round(spend_inv_diff, 4), round(spend_inv_diff, 4), 'Attributed + Unallocated = Raw Meta Spend', 'PASS' if spend_inv_diff < 0.1 else 'FAIL')

        profit_inv_diff = abs((safe_float(metrics.get('attributed_revenue')) - safe_float(metrics.get('raw_meta_spend'))) - safe_float(metrics.get('profit')))
        add_check('INV. Profit Formula', 0.0, round(profit_inv_diff, 4), round(profit_inv_diff, 4), 'Attributed Revenue - Raw Meta Spend = Profit', 'PASS' if profit_inv_diff < 0.1 else 'FAIL')

    
    # Check: Attribution Disconnect (If we have attributed sales AND meta spend, we expect >0 attributed spend)
    if metrics:
        has_attr_sales = metrics.get('attributed_sales', 0) > 0
        has_meta_spend = metrics.get('raw_meta_spend', 0) > 0
        attr_spend = metrics.get('attributed_spend', 0)
    else:
        has_attr_sales = False
        has_meta_spend = False
        attr_spend = 0
        
    if has_attr_sales and has_meta_spend and attr_spend == 0:
        results.append({
            'Check Name': '14. Spend Attribution Disconnect',
            'Status': 'FAIL',
            'Expected': '> 0',
            'Actual': '0.00',
            'Difference': 'Campaign Mismatch'
        })
    else:
        results.append({
            'Check Name': '14. Spend Attribution Disconnect',
            'Status': 'PASS',
            'Expected': '> 0' if (has_attr_sales and has_meta_spend) else 'N/A',
            'Actual': round(attr_spend, 2) if metrics else 0.00,
            'Difference': 0
        })

    return pd.DataFrame(results)


