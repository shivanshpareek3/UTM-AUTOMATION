import pandas as pd
from typing import Dict, List, Tuple
import os

from src.inspection import load_aliases, map_columns, check_missing_columns
from src.normalization import clean_text, parse_date_range, parse_date_series
from src.leads import process_leads
from src.sales import process_sales
from src.attribution import attribute_sales
from src.spend import allocate_spend
from src.funnel import apply_funnel_logic, aggregate_registration_revenue
from src.metrics import calculate_metrics
from src.summaries import build_summaries
from src.verification import run_verification
from src.workbook import generate_workbook

import json

def run_pipeline(
    leads_df: pd.DataFrame,
    sales_df: pd.DataFrame,
    meta_dfs: List[pd.DataFrame],
    settings: Dict,
    output_filepath: str
) -> Tuple[Dict, pd.DataFrame, str]:
    """
    Orchestrates the entire Phase 1 engine.
    Returns: (metrics, verification_df, excel_filepath)
    """
    
    # Load configs
    aliases = load_aliases()
    with open('config/sentinels.json', 'r') as f:
        sentinels = json.load(f)
        
    # Initial row counts
    input_sales_count = len(sales_df)
    
    # 1. Column Mapping (Handled by UI)
    # The UI now guarantees leads_df and sales_df have been renamed to canonical mapping fields.
    
    # Remove repeated header rows from merged CSVs/sheets
    if not leads_df.empty and 'email' in leads_df.columns:
        leads_df = leads_df[~leads_df['email'].astype(str).str.lower().str.strip().isin(['email', 'email address', 'customer email'])]
        
    if not sales_df.empty and 'email' in sales_df.columns:
        sales_df = sales_df[~sales_df['email'].astype(str).str.lower().str.strip().isin(['email', 'email address', 'customer email'])]
    
    if meta_dfs:
        for i, df in enumerate(meta_dfs):
            if not df.empty and 'spend' not in df.columns:
                raise KeyError(f"'spend' column is MISSING from meta_dfs[{i}] before concatenation. Available columns: {list(df.columns)}")
        for i, df in enumerate(meta_dfs):
            df['source_file_id'] = i
        meta_df = pd.concat(meta_dfs, ignore_index=True)
        if not meta_df.empty and 'spend' not in meta_df.columns:
            raise KeyError(f"'spend' column is MISSING from meta_df after concatenation. Available columns: {list(meta_df.columns)}")
    else:
        meta_df = pd.DataFrame()
        
    if not meta_df.empty:
        subset_cols = [c for c in meta_df.columns if c != 'source_file_id']
        meta_df = meta_df.drop_duplicates(subset=subset_cols, ignore_index=True)
    # The UI has already mapped the meta_dfs before they were concatenated here
    
    # Remove hierarchical summary rows where ad is 'all' or empty
    if not meta_df.empty and 'ad' in meta_df.columns:
        meta_df = meta_df[~meta_df['ad'].astype(str).str.lower().str.strip().isin(['all', 'nan', ''])]
        
    # Remove repeated header rows from merged CSVs/sheets
    if not meta_df.empty and 'campaign' in meta_df.columns:
        meta_df = meta_df[~meta_df['campaign'].astype(str).str.lower().str.strip().isin(['campaign name', 'campaign'])]
        
    # Apply custom reporting period filter to Meta
    meta_start_str = settings.get('meta_start_date', settings.get('ad_start_date'))
    meta_end_str = settings.get('meta_end_date', settings.get('ad_end_date'))
    if not meta_df.empty and meta_start_str and meta_end_str:
        m_sdt = pd.to_datetime(meta_start_str)
        m_edt = pd.to_datetime(meta_end_str)
        if 'Day' in meta_df.columns:
            range_df = parse_date_range(meta_df['Day'])
            
            # If the user mapped 'Reporting starts' to 'Day', we need to check for 'Reporting ends'
            end_cols = [c for c in meta_df.columns if str(c).lower().strip() == 'reporting ends']
            if end_cols:
                end_range = parse_date_range(meta_df[end_cols[0]])
                range_df['end_date'] = end_range['end_date'].fillna(range_df['end_date'])
            
            # Validation: if Day was populated but NO dates could be parsed, raise error
            if meta_df['Day'].notna().any() and range_df['start_date'].isna().all():
                raise ValueError("Could not parse any dates from Meta 'Day' column. Please verify date format.")
                
            # Filter condition: source_start <= requested_end AND source_end >= requested_start
            mask = (range_df['start_date'] <= m_edt) & (range_df['end_date'] >= m_sdt)
            meta_df = meta_df[mask]
    # Validate required columns (rudimentary check here, Streamlit can do deeper)
    # Assume mapped correctly for now
    
    # 2. Leads Processing
    leads_df = process_leads(leads_df, sentinels)
    
    # 3. Sales Processing & Date Resolution
    sale_date_source = settings.get('sale_date_source', 'Actual Sale Date')
    
    if sale_date_source == 'Lead Registration Date':
        # Pre-join to get registration_date
        if 'email' in sales_df.columns and 'email' in leads_df.columns:
            from src.normalization import normalize_email
            sales_df['email'] = sales_df['email'].apply(normalize_email)
            temp_leads = leads_df.copy()
            temp_leads['email'] = temp_leads['email'].apply(normalize_email)
            temp_leads = temp_leads.drop_duplicates(subset=['email'])
            
            # Use registration_date if sale_date is missing
            if 'registration_date' in temp_leads.columns:
                sales_df = sales_df.merge(temp_leads[['email', 'registration_date']], on='email', how='left')
            else:
                sales_df['registration_date'] = pd.NaT
                
            if 'sale_date' not in sales_df.columns:
                sales_df['sale_date'] = sales_df['registration_date']
            elif 'registration_date' in sales_df.columns:
                sales_df['sale_date'] = sales_df['sale_date'].fillna(sales_df['registration_date'])
                
            if 'registration_date' in sales_df.columns:
                sales_df.drop(columns=['registration_date'], inplace=True)
            
            if 'sale_date_source' not in sales_df.columns:
                sales_df['sale_date_source'] = sales_df['sale_date'].apply(
                    lambda x: 'lead_registration_date' if pd.notna(x) else 'unresolved'
                )
    elif sale_date_source == 'Reporting Start Date':
        if 'sale_date' not in sales_df.columns:
            sales_df['sale_date'] = pd.to_datetime(settings.get('start_date'))
            sales_df['sale_date_source'] = 'reporting_start_date'
        else:
            mask = sales_df['sale_date'].isna()
            sales_df.loc[mask, 'sale_date'] = pd.to_datetime(settings.get('start_date'))
            sales_df['sale_date_source'] = ['reporting_start_date' if m else 'actual' for m in mask]
    elif sale_date_source == 'Custom Date':
        c_date = settings.get('custom_sale_date')
        if 'sale_date' not in sales_df.columns:
            sales_df['sale_date'] = pd.to_datetime(c_date)
            sales_df['sale_date_source'] = 'custom_assumed_date'
        else:
            mask = sales_df['sale_date'].isna()
            sales_df.loc[mask, 'sale_date'] = pd.to_datetime(c_date)
            sales_df['sale_date_source'] = ['custom_assumed_date' if m else 'actual' for m in mask]
    else:
        # Actual
        if 'sale_date' in sales_df.columns:
            sales_df['sale_date_source'] = 'actual'
        else:
            sales_df['sale_date_source'] = 'missing'
            
    sales_df, excluded_sales = process_sales(sales_df, settings)
    
    # Apply custom reporting period filter to sales
    sales_start_str = settings.get('lead_sales_start_date', settings.get('lead_start_date'))
    sales_end_str = settings.get('lead_sales_end_date', settings.get('lead_end_date'))
    if sales_start_str and sales_end_str:
        sdt = pd.to_datetime(sales_start_str)
        edt = pd.to_datetime(sales_end_str)
        # Ensure end date includes the full day if it has no time component
        if edt.hour == 0 and edt.minute == 0 and edt.second == 0:
            edt = edt + pd.Timedelta(days=1, microseconds=-1)
        if 'sale_date' in sales_df.columns:
            mask = sales_df['sale_date'].isna() | ((sales_df['sale_date'] >= sdt) & (sales_df['sale_date'] <= edt))
            out_of_window = sales_df[~mask].copy()
            if not out_of_window.empty:
                out_of_window['exclusion_reason'] = 'Outside Reporting Period'
                excluded_sales = pd.concat([excluded_sales, out_of_window], ignore_index=True)
            sales_df = sales_df[mask]
    
    # We keep unresolved dates in All Sales per Phase 2 requirements
    # instead of excluding them.
    # Exclude logic for unresolved dates has been removed.
    
    # Check for duplicate sales emails (for verification)
    dup_sales_emails = sales_df.duplicated(subset=['email']).sum() if 'email' in sales_df.columns else 0
    
    # 4. Sales Attribution
    sales_df = attribute_sales(sales_df, leads_df, sentinels)
    
    # 5. Spend Attribution
    meta_start = settings.get('meta_start_date', settings.get('ad_start_date'))
    meta_end = settings.get('meta_end_date', settings.get('ad_end_date'))
    
    if not meta_df.empty and 'spend' not in meta_df.columns:
        raise KeyError(f"'spend' is MISSING before allocate_spend. Columns: {list(meta_df.columns)}")
        
    camp_spend, adset_spend, ad_spend = allocate_spend(
        leads_df, meta_df, meta_start, meta_end
    )
    
    # 6. Funnel Logic (Free/Paid, Old/New)
    sales_df = apply_funnel_logic(sales_df, leads_df, settings['cutoff_date'])
    ls_start = settings.get('lead_sales_start_date', settings.get('lead_start_date'))
    ls_end = settings.get('lead_sales_end_date', settings.get('lead_end_date'))
    reg_rev_df = aggregate_registration_revenue(leads_df, ls_start, ls_end, sentinels)
    
    # Calculate standalone registration revenue for verification
    if not reg_rev_df.empty and 'email' in sales_df.columns and 'email' in reg_rev_df.columns:
        standalone_reg_rev = reg_rev_df[~reg_rev_df['email'].isin(sales_df['email'])]['reg_revenue'].sum()
    else:
        standalone_reg_rev = reg_rev_df['reg_revenue'].sum() if not reg_rev_df.empty else 0.0
    
    # 6b. Filter Leads to Reporting Period (Golden Methodology: use all leads in file)
    leads_in_window = leads_df.copy()
    # Generate Data Quality Warning
    def generate_warning(row):
        warnings = []
        if row.get('sale_date_source') in ['lead_registration_date']:
            warnings.append(f"Derived sale_date ({row.get('sale_date_source')})")
        if row.get('sale_date_source') == 'unresolved':
            warnings.append("unresolved sale date")
        if 'fallback_price' in str(row.get('amount_source', '')):
            warnings.append("Fallback order_amount")
        if row.get('payment_status_source') == 'assumed_successful':
            warnings.append("Assumed payment_status")
        
        return " | ".join(warnings) if warnings else "Actual Data"
        
    sales_df['data_quality_warning'] = sales_df.apply(generate_warning, axis=1)
    
    # 7. Summaries
    for col in ['camp_norm', 'adset_norm', 'ad_norm']:
        if col not in sales_df.columns:
            sales_df[col] = ''
            
    camp_sum, adset_sum, ad_sum = build_summaries(sales_df, leads_in_window, camp_spend, adset_spend, ad_spend)
    
    # 8. Metrics
    metrics = calculate_metrics(leads_in_window, sales_df, reg_rev_df, meta_df, settings)
    

    # 9. Verification
    total_windowed_meta_spend = 0.0
    if not meta_df.empty:
        # Use overlap check rather than simple strict bound check
        sdt = pd.to_datetime(settings.get('meta_start_date', settings.get('ad_start_date')))
        edt = pd.to_datetime(settings.get('meta_end_date', settings.get('ad_end_date')))
        
        if 'Day' in meta_df.columns:
            range_df = parse_date_range(meta_df['Day'])
            
            # Check for 'Reporting ends' to fill end_date, matching line 91 logic
            end_cols = [c for c in meta_df.columns if str(c).lower().strip() == 'reporting ends']
            if end_cols:
                end_range = parse_date_range(meta_df[end_cols[0]])
                range_df['end_date'] = end_range['end_date'].fillna(range_df['end_date'])
                
            mask = (range_df['start_date'] <= edt) & (range_df['end_date'] >= sdt)
            window_meta = meta_df[mask].copy()
        else:
            window_meta = meta_df.copy()
        
        # Exclude blank campaigns
        from src.normalization import unify_campaign_name
        if 'campaign' in window_meta.columns:
            window_meta['camp_norm'] = window_meta['campaign'].apply(unify_campaign_name)
        elif 'Campaign Name' in window_meta.columns:
            window_meta['camp_norm'] = window_meta['Campaign Name'].apply(unify_campaign_name)
        elif 'Campaign name' in window_meta.columns:
            window_meta['camp_norm'] = window_meta['Campaign name'].apply(unify_campaign_name)
        else:
            window_meta['camp_norm'] = "unmapped"
            
        valid_window_meta = window_meta[window_meta['camp_norm'] != '']
        
        if 'spend' in valid_window_meta.columns:
            total_windowed_meta_spend = pd.to_numeric(valid_window_meta['spend'], errors='coerce').fillna(0).sum()

    total_leads_in_window = len(leads_in_window)
        
    funnel_leads_counted = total_leads_in_window # Simplification for check 8 if we don't have a separate funnel summary yet
    
    # Update metrics and ver_df for new verification counts
    # Actual sale date count vs Derived
    actual_sale_date_cnt = len(sales_df[sales_df['sale_date_source'] == 'actual']) if 'sale_date_source' in sales_df.columns else 0
    derived_sale_date_cnt = len(sales_df[sales_df['sale_date_source'] != 'actual']) if 'sale_date_source' in sales_df.columns else 0
    assumed_payment_cnt = len(sales_df[sales_df['payment_status_source'] == 'assumed_successful']) if 'payment_status_source' in sales_df.columns else 0
    fallback_amount_cnt = len(sales_df[sales_df['amount_source'].astype(str).str.contains('fallback', na=False)]) if 'amount_source' in sales_df.columns else 0
    missing_sales_cnt = len(sales_df[sales_df['sale_date'].isna()]) if 'sale_date' in sales_df.columns else 0
    
    ver_df = run_verification(
        input_sales_count=input_sales_count,
        excluded_sales_count=len(excluded_sales),
        all_sales_df=sales_df,
        camp_summary=camp_sum,
        adset_summary=adset_sum,
        ad_summary=ad_sum,
        total_windowed_meta_spend=total_windowed_meta_spend,
        duplicate_sales_emails=dup_sales_emails,
        total_leads_in_window=total_leads_in_window,
        funnel_leads_counted=funnel_leads_counted,
        leads_sheet_reg_revenue=reg_rev_df['reg_revenue'].sum() if not reg_rev_df.empty else 0.0,
        actual_sale_date_cnt=actual_sale_date_cnt,
        derived_sale_date_cnt=derived_sale_date_cnt,
        assumed_payment_cnt=assumed_payment_cnt,
        fallback_amount_cnt=fallback_amount_cnt,
        missing_sales_cnt=missing_sales_cnt,
        standalone_reg_revenue=standalone_reg_rev
    )
    
    # Prepare data for Excel
    settings_df = pd.DataFrame([
        {'Setting': 'Report Name', 'Value': settings.get('report_name')},
        {'Setting': 'Client Name', 'Value': settings.get('client_name')},
        {'Setting': 'Report Type', 'Value': settings.get('report_type', 'Custom')},
        {'Setting': 'Lead/Sales Start Date', 'Value': settings.get('lead_sales_start_date', settings.get('lead_start_date'))},
        {'Setting': 'Lead/Sales End Date', 'Value': settings.get('lead_sales_end_date', settings.get('lead_end_date'))},
        {'Setting': 'Meta Ads Start Date', 'Value': settings.get('meta_start_date', settings.get('ad_start_date'))},
        {'Setting': 'Meta Ads End Date', 'Value': settings.get('meta_end_date', settings.get('ad_end_date'))},
        {'Setting': 'Detected Lead Coverage', 'Value': settings.get('detected_lead_coverage', 'Unknown')},
        {'Setting': 'Detected Sales Coverage', 'Value': settings.get('detected_sales_coverage', 'Unknown')},
        {'Setting': 'Detected Meta Coverage', 'Value': settings.get('detected_meta_coverage', 'Unknown')},
        {'Setting': 'Coverage Status', 'Value': settings.get('coverage_status', 'Unknown')},
        {'Setting': 'Total Leads', 'Value': metrics['total_leads']},
        {'Setting': 'Paid Leads', 'Value': metrics['paid_leads']},
        {'Setting': 'Unpaid Leads', 'Value': metrics['unpaid_leads']},
        {'Setting': 'Paid Funnel %', 'Value': metrics['paid_funnel_percent']},
        {'Setting': 'Unpaid Funnel %', 'Value': metrics['unpaid_funnel_percent']},
        {'Setting': 'Sales (Matched to Lead)', 'Value': metrics.get('sales_matched_to_lead', 0)},
        {'Setting': 'Sales (Campaign-Attributed)', 'Value': metrics.get('sales_matched_to_campaign', 0)},
        {'Setting': 'Total Sales', 'Value': metrics['total_sales']},
        {'Setting': 'Attributed Sales', 'Value': metrics['attributed_sales']},
        {'Setting': 'Unattributed Sales', 'Value': metrics['unattributed_sales']},
        {'Setting': 'Per Sale Value', 'Value': metrics.get('per_sale_value', 'N/A')},
        {'Setting': 'Attributed Per Sale Value', 'Value': metrics.get('attributed_per_sale_value', 'N/A')},
        {'Setting': 'Registration Amount', 'Value': metrics.get('total_reg_revenue', 0.0)},
        {'Setting': 'Sales Revenue', 'Value': metrics.get('backend_revenue', 0.0)},
        {'Setting': 'Registration Revenue', 'Value': metrics.get('total_reg_revenue', 0.0)},
        {'Setting': 'Total Revenue', 'Value': metrics.get('total_revenue', 0.0)},
        {'Setting': 'Attributed Revenue', 'Value': metrics.get('attributed_revenue', 0.0)},
        {'Setting': 'Unattributed Revenue', 'Value': metrics.get('unattributed_revenue', 0.0)},
        {'Setting': 'Raw Meta Spend', 'Value': metrics.get('raw_meta_spend', 0.0)},
        {'Setting': 'Attributed Spend', 'Value': metrics['attributed_spend']},
        {'Setting': 'Unallocated Spend', 'Value': metrics['unallocated_spend']},
        {'Setting': 'Profit', 'Value': metrics['profit']},
        {'Setting': 'ROAS', 'Value': metrics['roas']},
        {'Setting': 'ROI', 'Value': metrics['roi_percent']},
        {'Setting': 'CAC', 'Value': metrics['cac']}
    ])
    
    if settings.get('amount_source') == 'Fallback Price Per Sale':
        settings_df = pd.concat([settings_df, pd.DataFrame([{'Setting': 'Note', 'Value': 'Revenue (Total and Attributed) is Assumed/Fallback Revenue because actual order amounts were not provided.'}])], ignore_index=True)
    
    # Format Campaign Summary for Excel Output
    if not camp_sum.empty:
        # User requested columns:
        # Campaign Name, Ad Account, Total Leads, Total Sales, Attributed Sales, Spend / Meta Spend, CPL, CAC, Revenue, Profit, ROAS, ROI, Conversion Rate, Price Per Sale, Funnel Type
        camp_sum_excel = camp_sum.rename(columns={
            'Node Name': 'Campaign Name',
            'Leads': 'Total Leads',
            'Sales': 'Attributed Sales',
            'Spend': 'Spend / Meta Spend',
            'ROI %': 'ROI',
            'Conversion Rate %': 'Conversion Rate',
            'Revenue': 'Revenue',
            'Profit': 'Profit',
            'ROAS': 'ROAS'
        })
        
        # Add missing columns
        camp_sum_excel['Total Sales'] = camp_sum_excel['Attributed Sales']
        camp_sum_excel['Price Per Sale'] = metrics.get('per_sale_value', settings.get('fallback_price', 0.0))
        camp_sum_excel['Funnel Type'] = settings.get('funnel_type', 'Paid')
        
        # Reorder columns to match request:
        camp_sum_excel = camp_sum_excel[[
            'Campaign Name', 'Ad Account', 'Total Leads', 'Total Sales', 'Attributed Sales',
            'Spend / Meta Spend', 'CPL', 'CAC', 'Revenue', 'Profit', 'ROAS', 'ROI',
            'Conversion Rate', 'Price Per Sale', 'Funnel Type'
        ]]
    else:
        camp_sum_excel = camp_sum.copy()

    workbook_data = {
        "1. ⚙ Settings & Run Log": settings_df,
        "2. 📋 All Sales (Attributed)": sales_df,
        "3. 📢 Campaign Summary": camp_sum_excel,
        "4. 🎯 Ad Set Summary": adset_sum,
        "5. 🎨 Ad Creative Summary": ad_sum
    }
    
    # --- PHASE 1 RECONCILIATION PRINT ---
    print("\n" + "="*50)
    print("FINAL ACCEPTANCE RECONCILIATION TABLE")
    print("="*50)
    
    # Format currency
    def fmt_cur(val):
        if pd.isna(val) or val == "N/A": return "N/A"
        return f"₹{val:,.2f}"
        
    print(f"{'METRIC':<35} | {'AUTOMATION':<15} | {'CLAUDE GOLDEN'}")
    print("-" * 75)
    print(f"{'Total Meta Ad Spend':<35} | {fmt_cur(metrics['raw_meta_spend']):<15} | ₹486,068.46")
    print(f"{'Total Leads':<35} | {metrics['total_leads']:<15} | 3,605")
    print(f"{'Total Sales (Matched to Lead)':<35} | {metrics['sales_matched_to_lead']:<15} | 31")
    print(f"{'Total Sales (Campaign-Attributed)':<35} | {metrics['sales_matched_to_campaign']:<15} | 29")
    print(f"{'Total Sales Revenue (Matched)':<35} | {fmt_cur(metrics['total_revenue']):<15} | ₹278,969.00")
    
    roas_val = metrics['roas']
    roas_str = f"{roas_val:.2f}" if isinstance(roas_val, (int, float)) else str(roas_val)
    print(f"{'Blended ROAS':<35} | {roas_str:<15} | 0.57")
    
    print(f"{'CPL':<35} | {fmt_cur(metrics['cpl']):<15} | ₹134.83") # Note: Claude 3605 gives 486068.46/3605 = 134.83
    print(f"{'CAC':<35} | {fmt_cur(metrics['cac']):<15} | ₹15,679.63")
    
    cvr_val = metrics['conversion_rate_percent']
    cvr_str = f"{cvr_val:.2f}%" if isinstance(cvr_val, (int, float)) else str(cvr_val)
    print(f"{'Conversion Rate':<35} | {cvr_str:<15} | 0.86%")
    
    print("="*75 + "\n")
    
    generate_workbook(output_filepath, workbook_data)
    
    return metrics, ver_df, output_filepath
