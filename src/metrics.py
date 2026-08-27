import pandas as pd

def calculate_metrics(leads_df: pd.DataFrame, sales_df: pd.DataFrame, reg_rev_df: pd.DataFrame, meta_df: pd.DataFrame, settings: dict = None) -> dict:
    """
    Calculate high-level metrics using the Golden Methodology.
    """
    total_leads = len(leads_df)
    total_sales = len(sales_df)
    
    funnel_type = settings.get('funnel_type', 'Paid') if settings else 'Paid'
    if funnel_type == 'Paid':
        fallback_val = float(settings.get('fallback_price', 8999.0)) if settings else 8999.0
        funnel_price = float(settings.get('paid_funnel_price', fallback_val)) if settings else fallback_val
    else:
        funnel_price = 0.0
        
    if not meta_df.empty:
        # Exclude blank campaigns
        from src.normalization import unify_campaign_name
        meta_df_copy = meta_df.copy()
        if 'campaign' in meta_df_copy.columns:
            meta_df_copy['camp_norm'] = meta_df_copy['campaign'].apply(unify_campaign_name)
        elif 'Campaign Name' in meta_df_copy.columns:
            meta_df_copy['camp_norm'] = meta_df_copy['Campaign Name'].apply(unify_campaign_name)
        elif 'Campaign name' in meta_df_copy.columns:
            meta_df_copy['camp_norm'] = meta_df_copy['Campaign name'].apply(unify_campaign_name)
        else:
            meta_df_copy['camp_norm'] = "unmapped"
            
        valid_meta = meta_df_copy[meta_df_copy['camp_norm'] != '']
        raw_meta_spend = 0.0
        attributed_spend = 0.0
        
        if 'spend' in valid_meta.columns:
            valid_meta['spend'] = pd.to_numeric(valid_meta['spend'], errors='coerce').fillna(0)
            raw_meta_spend = valid_meta['spend'].sum()
        else:
            valid_meta['spend'] = 0.0
    else:
        raw_meta_spend = 0.0
        attributed_spend = 0.0
        
    if 'attribution_source' in sales_df.columns:
        attributed_sales_df = sales_df[sales_df['attribution_source'] != 'Unattributed']
        unattributed_sales_df = sales_df[sales_df['attribution_source'] == 'Unattributed']
    else:
        attributed_sales_df = pd.DataFrame()
        unattributed_sales_df = sales_df
        
    attributed_sales = len(attributed_sales_df)
    unattributed_sales = len(unattributed_sales_df)
    
    # Calculate Attributed Spend (Spend of campaigns that generated >= 1 sale)
    if not meta_df.empty and not attributed_sales_df.empty:
        from src.normalization import unify_campaign_name
        attr_camps = set(attributed_sales_df['campaign'].dropna().apply(unify_campaign_name)) if 'campaign' in attributed_sales_df.columns else set()
        attributed_spend = valid_meta[valid_meta['camp_norm'].isin(attr_camps)]['spend'].sum()
    else:
        attributed_spend = 0.0
        
    unallocated_spend = raw_meta_spend - attributed_spend
    
    # Calculate revenue using Matched Sales * realised_sale_value
    attributed_revenue = attributed_sales * funnel_price
    
    attributed_leads = len(leads_df[leads_df['has_valid_utm'] == True]) if 'has_valid_utm' in leads_df.columns else 0
    unattributed_leads = total_leads - attributed_leads
    lead_attribution_rate = (attributed_leads / total_leads * 100) if total_leads > 0 else "N/A"
    
    backend_revenue = sales_df['order_amount'].sum() if 'order_amount' in sales_df.columns else 0.0
    reg_revenue_sales = sales_df['registration_fee_applied'].sum() if 'registration_fee_applied' in sales_df.columns else 0.0
    total_reg_revenue = reg_rev_df['reg_revenue'].sum() if not reg_rev_df.empty else 0.0
    total_revenue = backend_revenue + total_reg_revenue
    unattributed_revenue = total_revenue - attributed_revenue
    
    profit = attributed_revenue - attributed_spend
    
    paid_markers = settings.get('paid_markers', [
        "paid", "cpc", "cpm", "ppc", "paid_social", "paid_search",
        "google", "facebook", "instagram", "meta", "linkedin",
        "youtube", "bing", "snapchat", "twitter", "ads", "advertisement"
    ]) if settings else []
    
    # Calculate Paid/Unpaid Leads
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

    # Calculate Paid Funnel % and Unpaid Funnel %
    paid_funnel_pct = (paid_leads / total_leads * 100) if total_leads > 0 else 0.0
    unpaid_funnel_pct = (unpaid_leads / total_leads * 100) if total_leads > 0 else 0.0

    spend_attribution_rate = (attributed_spend / raw_meta_spend * 100) if raw_meta_spend > 0 else "N/A"
    roas = (attributed_revenue / attributed_spend) if attributed_spend > 0 else "N/A"
    roi = (profit / attributed_spend * 100) if attributed_spend > 0 else "N/A"
    cpl = (attributed_spend / total_leads) if total_leads > 0 else "N/A"
    cac = (attributed_spend / attributed_sales) if (attributed_spend > 0 and attributed_sales > 0) else "N/A"
    cvr = (total_sales / total_leads * 100) if total_leads > 0 else "N/A"
    
    per_sale_value = (total_revenue / total_sales) if total_sales > 0 else "N/A"
    attributed_per_sale_value = (attributed_revenue / attributed_sales) if attributed_sales > 0 else "N/A"

    return {
        'total_leads': total_leads,
        'attributed_leads': attributed_leads,
        'unattributed_leads': unattributed_leads,
        'lead_attribution_rate': lead_attribution_rate,
        'total_sales': total_sales,
        'attributed_sales': attributed_sales,
        'unattributed_sales': unattributed_sales,
        'backend_revenue': backend_revenue,
        'total_reg_revenue': total_reg_revenue,
        'total_revenue': total_revenue,
        'attributed_revenue': attributed_revenue,
        'unattributed_revenue': unattributed_revenue,
        'raw_meta_spend': raw_meta_spend,
        'attributed_spend': attributed_spend,
        'unallocated_spend': unallocated_spend,
        'spend_attribution_rate': spend_attribution_rate,
        'profit': profit,
        'roas': roas,
        'roi_percent': roi,
        'cpl': cpl,
        'cac': cac,
        'conversion_rate_percent': cvr,
        'paid_leads': paid_leads,
        'unpaid_leads': unpaid_leads,
        'paid_funnel_percent': paid_funnel_pct,
        'unpaid_funnel_percent': unpaid_funnel_pct,
        'per_sale_value': per_sale_value,
        'attributed_per_sale_value': attributed_per_sale_value
    }
