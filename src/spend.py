import pandas as pd
import logging
from typing import Tuple

logger = logging.getLogger(__name__)

def allocate_spend(sales_df: pd.DataFrame, meta_df: pd.DataFrame, leads_df: pd.DataFrame, start_date: str, end_date: str) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Allocate Meta spend to sales using Campaign-Level 100% Attribution methodology.
    If a campaign has >= 1 valid attributed sale, 100% of its valid spend is attributed.
    Returns: (attributed_sales_df, campaign_summary, adset_summary, ad_summary)
    """
    from src.normalization import unify_campaign_name, clean_text
    def norm(val):
        return clean_text(val).lower() if pd.notna(val) else ''
    def norm_camp(val):
        return unify_campaign_name(val)

    if not sales_df.empty:
        sales_df['camp_norm'] = sales_df['campaign'].apply(norm_camp) if 'campaign' in sales_df.columns else ""
        sales_df['adset_norm'] = sales_df['ad_set'].apply(norm) if 'ad_set' in sales_df.columns else ""
        sales_df['ad_norm'] = sales_df['ad_creative'].apply(norm) if 'ad_creative' in sales_df.columns else ""

    if meta_df.empty:
        if not sales_df.empty:
            sales_df['attributed_spend'] = 0.0
        return sales_df, pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
        
    # Ensure dates are datetime
    meta_df['Day'] = pd.to_datetime(meta_df.get('Reporting starts', meta_df.get('Day', pd.Series(dtype=str))), errors='coerce')
    start_dt = pd.to_datetime(start_date)
    end_dt = pd.to_datetime(end_date)
    
    # Filter by window
    window_meta = meta_df[(meta_df['Day'] >= start_dt) & (meta_df['Day'] <= end_dt)].copy()
    
    # Normalize Meta names for joining
    if 'Amount spent (INR)' in window_meta.columns:
        window_meta = window_meta.rename(columns={'Amount spent (INR)': 'Amount Spent'})
    elif 'spend' in window_meta.columns and 'Amount Spent' not in window_meta.columns:
        window_meta = window_meta.rename(columns={'spend': 'Amount Spent'})
        
    window_meta['camp_norm'] = window_meta.get('campaign', window_meta.get('Campaign name', window_meta.get('Campaign Name', pd.Series(dtype=str)))).apply(norm_camp)
    
    # Exclude rows where campaign is blank/null/NaN
    valid_meta = window_meta[window_meta['camp_norm'] != ''].copy()
    
    # NEW GOLDEN RULE: Determine Eligibility based on Primary Meta Source
    # The Golden methodology restricts CAC attribution strictly to campaigns residing in the primary Meta source file 
    # (the source with the maximum total ad spend). Campaigns from secondary sources are treated as Unallocated.
    valid_meta['Amount Spent Num'] = pd.to_numeric(valid_meta['Amount Spent'], errors='coerce').fillna(0.0)
    
    if 'source_file_id' in valid_meta.columns:
        source_spend = valid_meta.groupby('source_file_id')['Amount Spent Num'].sum()
        primary_source_id = source_spend.idxmax() if not source_spend.empty else None
        valid_meta['is_primary_source'] = (valid_meta['source_file_id'] == primary_source_id) & (valid_meta['Amount Spent Num'] > 0)
    else:
        valid_meta['is_primary_source'] = True

    # Calculate top-level campaign spend from Meta
    camp_meta_spend = valid_meta.groupby(['camp_norm'])['Amount Spent Num'].sum().reset_index()
    camp_meta_spend = camp_meta_spend.rename(columns={'Amount Spent Num': 'Amount Spent'})
    camp_primary_presence = valid_meta.groupby(['camp_norm'])['is_primary_source'].any().reset_index()
    camp_meta_spend = pd.merge(camp_meta_spend, camp_primary_presence, on='camp_norm', how='left')
    
    # Prepare Leads for proportional raw spend splitting for summaries
    if not leads_df.empty:
        leads_df['camp_norm'] = leads_df['campaign'].apply(norm_camp) if 'campaign' in leads_df.columns else ""
        leads_df['adset_norm'] = leads_df['ad_set'].apply(norm) if 'ad_set' in leads_df.columns else ""
        leads_df['ad_norm'] = leads_df['ad_creative'].apply(norm) if 'ad_creative' in leads_df.columns else ""
        
        camp_leads = leads_df.groupby(['camp_norm']).size().reset_index(name='camp_leads')
        adset_leads = leads_df.groupby(['camp_norm', 'adset_norm']).size().reset_index(name='adset_leads')
        ad_leads = leads_df.groupby(['camp_norm', 'adset_norm', 'ad_norm']).size().reset_index(name='ad_leads')
    else:
        camp_leads = pd.DataFrame(columns=['camp_norm', 'camp_leads'])
        adset_leads = pd.DataFrame(columns=['camp_norm', 'adset_norm', 'adset_leads'])
        ad_leads = pd.DataFrame(columns=['camp_norm', 'adset_norm', 'ad_norm', 'ad_leads'])

    # Merge campaign spend with campaign leads
    camp_spend = pd.merge(camp_meta_spend, camp_leads, on='camp_norm', how='left')
    camp_spend['camp_leads'] = camp_spend['camp_leads'].fillna(0)

    # Ad Set Allocation (Lead Share for Raw Spend reporting)
    adset_spend = pd.merge(adset_leads, camp_spend[['camp_norm', 'Amount Spent', 'camp_leads']], on='camp_norm', how='inner')
    adset_spend['Amount Spent'] = adset_spend.apply(
        lambda r: r['Amount Spent'] * (r['adset_leads'] / r['camp_leads']) if r['camp_leads'] > 0 else 0.0, axis=1
    )
    
    # Ad Allocation (Lead Share for Raw Spend reporting)
    ad_spend = pd.merge(ad_leads, camp_spend[['camp_norm', 'Amount Spent', 'camp_leads']], on='camp_norm', how='inner')
    ad_spend['Amount Spent'] = ad_spend.apply(
        lambda r: r['Amount Spent'] * (r['ad_leads'] / r['camp_leads']) if r['camp_leads'] > 0 else 0.0, axis=1
    )
    
    # Strip down columns to match previous aggregation structure
    camp_spend_out = camp_spend[['camp_norm', 'Amount Spent']].copy()
    adset_spend_out = adset_spend[['camp_norm', 'adset_norm', 'Amount Spent']].copy()
    ad_spend_out = ad_spend[['camp_norm', 'adset_norm', 'ad_norm', 'Amount Spent']].copy()
    
    if sales_df.empty:
        if 'attributed_spend' not in sales_df.columns:
            sales_df['attributed_spend'] = pd.Series(dtype=float)
        return sales_df, camp_spend_out, adset_spend_out, ad_spend_out

    # Campaign-Level 100% Attribution
    # Count ALL attributed sales per campaign
    attr_sales = sales_df[sales_df['match_level'] != 'Unattributed']
    camp_sales_counts = attr_sales.groupby('camp_norm').size().reset_index(name='sales_count')
    
    camp_merged = pd.merge(camp_spend_out, camp_sales_counts, on='camp_norm', how='left')
    camp_merged['sales_count'] = camp_merged['sales_count'].fillna(0)
    
    # Merge the primary source presence to determine spend eligibility
    camp_merged = pd.merge(camp_merged, camp_meta_spend[['camp_norm', 'is_primary_source']], on='camp_norm', how='left')
    
    # Distribute the 100% campaign spend equally among its sales
    # ELIGIBILITY RULE: Campaign must have >= 1 sale AND belong to the Primary Meta Source to be eligible for spend attribution.
    camp_merged['spend_per_sale'] = camp_merged.apply(
        lambda r: r['Amount Spent'] / r['sales_count'] if (r['sales_count'] > 0 and r.get('is_primary_source', True)) else 0.0, axis=1
    )
    
    # Map back to sales
    camp_map = camp_merged.set_index('camp_norm')['spend_per_sale'].to_dict()
    
    def get_attributed_spend(row):
        if row['match_level'] == 'Unattributed':
            return 0.0
        c = row.get('camp_norm', '')
        return camp_map.get(c, 0.0)
        
    sales_df['attributed_spend'] = sales_df.apply(get_attributed_spend, axis=1)
    
    # Invariant Check
    total_attr = sales_df['attributed_spend'].sum()
    total_meta = window_meta['Amount Spent'].sum()
    
    import logging
    logger = logging.getLogger(__name__)
    if total_attr > total_meta + 0.01:
        logger.error(f"INVARIANT VIOLATION: Total Attributed ({total_attr}) > Meta Spend ({total_meta})")
        raise ValueError(f"Total Attributed Spend ({total_attr}) <= Total Windowed Meta Spend ({total_meta}) invariant violated.")
        
    return sales_df, camp_spend_out, adset_spend_out, ad_spend_out
