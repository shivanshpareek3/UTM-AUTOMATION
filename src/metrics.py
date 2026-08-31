import pandas as pd

def calculate_metrics(leads_df: pd.DataFrame, sales_df: pd.DataFrame, reg_rev_df: pd.DataFrame, meta_df: pd.DataFrame, settings: dict = None) -> dict:
    """
    Calculate high-level metrics exactly following the Claude Golden Methodology.
    """
    total_leads = len(leads_df)
    total_sales = len(sales_df)
    
    # Identify Matched Sales
    # A sale is matched to a lead if email OR phone matches (matched_to_lead == True)
    if 'matched_to_lead' in sales_df.columns:
        matched_sales_df = sales_df[sales_df['matched_to_lead'] == True]
    else:
        matched_sales_df = sales_df[sales_df.get('attribution_source', '') != 'Unattributed']
        
    sales_matched_to_lead = len(matched_sales_df)
    
    # Identify Campaign-Matched Sales
    if 'matched_to_campaign' in sales_df.columns:
        campaign_matched_sales_df = sales_df[sales_df['matched_to_campaign'] == True]
    elif 'match_level' in matched_sales_df.columns:
        campaign_matched_sales_df = matched_sales_df[matched_sales_df['match_level'] != 'Unattributed']
    else:
        campaign_matched_sales_df = matched_sales_df
        
    # Golden Methodology: A sale is ONLY campaign-attributed if the campaign exists in Meta spend
    if not meta_df.empty and 'campaign_name' in meta_df.columns:
        from src.normalization import unify_campaign_name
        meta_camps = set(meta_df['campaign_name'].dropna().apply(unify_campaign_name))
        
        def check_valid_campaign(row):
            camp = str(row.get('campaign', '')).strip()
            if not camp or camp.lower() == 'nan': return False
            return unify_campaign_name(camp) in meta_camps
            
        if not campaign_matched_sales_df.empty:
            valid_mask = campaign_matched_sales_df.apply(check_valid_campaign, axis=1)
            campaign_matched_sales_df = campaign_matched_sales_df[valid_mask]
            
    sales_matched_to_campaign = len(campaign_matched_sales_df)
    
    # Revenue calculations
    # Golden Rule: Revenue = Matched Sales Revenue (NOT just campaign-attributed revenue)
    backend_revenue = sales_df['order_amount'].sum() if 'order_amount' in sales_df.columns else 0.0
    matched_backend_revenue = matched_sales_df['order_amount'].sum() if 'order_amount' in matched_sales_df.columns else 0.0
    
    total_reg_revenue = reg_rev_df['reg_revenue'].sum() if not reg_rev_df.empty else 0.0
    matched_reg_revenue = matched_sales_df['registration_fee_applied'].sum() if 'registration_fee_applied' in matched_sales_df.columns else 0.0
    
    # For Golden Report, the Headline Revenue is the revenue from Sales Matched to Lead
    total_revenue = matched_backend_revenue + total_reg_revenue # Total overall system revenue
    matched_revenue = matched_backend_revenue + matched_reg_revenue # Revenue used for ROAS/ROI
    
    # Meta Spend Calculation
    if not meta_df.empty and 'spend' in meta_df.columns:
        raw_meta_spend = meta_df['spend'].sum()
    else:
        raw_meta_spend = 0.0
        
    # The automation previously used 'attributed_spend'. The Golden Rule states Headline KPIs 
    # (ROAS, CAC, CPL) must use TOTAL META AD SPEND as the denominator.
    attributed_spend = sales_df['attributed_spend'].sum() if 'attributed_spend' in sales_df.columns else 0.0
    unallocated_spend = raw_meta_spend - attributed_spend
    
    # Profit Calculation
    # Profit/Loss = Matched Revenue - Total Spend
    profit = matched_revenue - raw_meta_spend
    
    # Headline KPIs
    blended_roas = (matched_revenue / raw_meta_spend) if raw_meta_spend > 0 else 0.0
    roi = (profit / raw_meta_spend * 100) if raw_meta_spend > 0 else 0.0
    cpl = (raw_meta_spend / total_leads) if total_leads > 0 else 0.0
    cac = (raw_meta_spend / sales_matched_to_lead) if sales_matched_to_lead > 0 else 0.0
    cvr = (sales_matched_to_lead / total_leads * 100) if total_leads > 0 else 0.0
    
    # Registration & Funnel logic
    paid_markers = settings.get('paid_markers', [
        "paid", "cpc", "cpm", "ppc", "paid_social", "paid_search",
        "google", "facebook", "instagram", "meta", "linkedin",
        "youtube", "bing", "snapchat", "twitter", "ads", "advertisement"
    ]) if settings else []
    
    paid_leads = 0
    unpaid_leads = 0
    if not leads_df.empty:
        def is_paid(row):
            for col in ['utm_medium', 'utm_source', 'campaign', 'source']:
                if col in row and pd.notna(row[col]):
                    val = str(row[col]).lower()
                    if any(marker in val for marker in paid_markers):
                        return True
            return False
            
        leads_df['is_paid'] = leads_df.apply(is_paid, axis=1)
        paid_leads = int(leads_df['is_paid'].sum())
        unpaid_leads = total_leads - paid_leads

    paid_funnel_pct = (paid_leads / total_leads * 100) if total_leads > 0 else 0.0
    unpaid_funnel_pct = (unpaid_leads / total_leads * 100) if total_leads > 0 else 0.0

    per_sale_value = (matched_revenue / sales_matched_to_lead) if sales_matched_to_lead > 0 else 0.0

    return {
        'total_leads': total_leads,
        'sales_rows': total_sales,
        'total_sales': total_sales, # for backwards compat
        'sales_matched_to_lead': sales_matched_to_lead,
        'sales_matched_to_campaign': sales_matched_to_campaign,
        
        # We store these into the variables expected by pipeline.py / summaries
        'attributed_sales': sales_matched_to_campaign,
        'unattributed_sales': total_sales - sales_matched_to_campaign,
        
        'backend_revenue': matched_backend_revenue,
        'total_reg_revenue': total_reg_revenue,
        'total_revenue': matched_revenue,
        'attributed_revenue': matched_revenue,
        'unattributed_revenue': backend_revenue - matched_backend_revenue,
        
        'raw_meta_spend': raw_meta_spend,
        'attributed_spend': attributed_spend,
        'unallocated_spend': unallocated_spend,
        
        'profit': profit,
        'roas': blended_roas,
        'roi_percent': roi,
        'cpl': cpl,
        'cac': cac,
        'conversion_rate_percent': cvr,
        
        'paid_leads': paid_leads,
        'unpaid_leads': unpaid_leads,
        'paid_funnel_percent': paid_funnel_pct,
        'unpaid_funnel_percent': unpaid_funnel_pct,
        'per_sale_value': per_sale_value,
        'attributed_per_sale_value': per_sale_value
    }

