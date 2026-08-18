import pandas as pd
import logging
from typing import Tuple

logger = logging.getLogger(__name__)

def allocate_spend(sales_df: pd.DataFrame, meta_df: pd.DataFrame, leads_df: pd.DataFrame, start_date: str, end_date: str) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Allocate Meta spend to sales using 3-tier matching and proportional allocation.
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
    meta_df['Day'] = pd.to_datetime(meta_df['Day'], errors='coerce')
    start_dt = pd.to_datetime(start_date)
    end_dt = pd.to_datetime(end_date)
    
    # Filter by window
    window_meta = meta_df[(meta_df['Day'] >= start_dt) & (meta_df['Day'] <= end_dt)].copy()
    
    # Normalize Meta names for joining
    if 'spend' in window_meta.columns and 'Amount Spent' not in window_meta.columns:
        window_meta = window_meta.rename(columns={'spend': 'Amount Spent'})
        
    window_meta['camp_norm'] = window_meta.get('campaign', window_meta.get('Campaign Name', pd.Series(dtype=str))).apply(norm_camp)
    
    # Exclude rows where campaign is blank/null/NaN
    valid_meta = window_meta[window_meta['camp_norm'] != ''].copy()
    
    # Calculate top-level campaign spend from Meta
    camp_meta_spend = valid_meta.groupby(['camp_norm'])['Amount Spent'].sum().reset_index()
    
    # Prepare Leads for Lead Share Allocation
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
    
    # Remove campaigns that have 0 leads (unmappable) so they don't incorrectly get attributed to 0 sales
    camp_spend = camp_spend[camp_spend['camp_leads'] > 0].copy()

    # Ad Set Allocation (Lead Share)
    adset_spend = pd.merge(adset_leads, camp_spend[['camp_norm', 'Amount Spent', 'camp_leads']], on='camp_norm', how='inner')
    adset_spend['Amount Spent'] = adset_spend.apply(
        lambda r: r['Amount Spent'] * (r['adset_leads'] / r['camp_leads']) if r['camp_leads'] > 0 else 0.0, axis=1
    )
    
    # Ad Allocation (Lead Share)
    ad_spend = pd.merge(ad_leads, camp_spend[['camp_norm', 'Amount Spent', 'camp_leads']], on='camp_norm', how='inner')
    ad_spend['Amount Spent'] = ad_spend.apply(
        lambda r: r['Amount Spent'] * (r['ad_leads'] / r['camp_leads']) if r['camp_leads'] > 0 else 0.0, axis=1
    )
    
    # Strip down columns to match previous aggregation structure
    camp_spend = camp_spend[['camp_norm', 'Amount Spent']]
    adset_spend = adset_spend[['camp_norm', 'adset_norm', 'Amount Spent']]
    ad_spend = ad_spend[['camp_norm', 'adset_norm', 'ad_norm', 'Amount Spent']]
    
    if sales_df.empty:
        if 'attributed_spend' not in sales_df.columns:
            sales_df['attributed_spend'] = pd.Series(dtype=float)
        return sales_df, camp_spend, adset_spend, ad_spend

    # Count ALL attributed sales at each level pool
    # This correctly honors sales that have deep UTMs even if Meta spend is rolled up
    attr_sales = sales_df[sales_df['match_level'] != 'Unattributed']
    
    ad_sales_counts = attr_sales.groupby(['camp_norm', 'adset_norm', 'ad_norm']).size().reset_index(name='sales_count')
    adset_sales_counts = attr_sales.groupby(['camp_norm', 'adset_norm']).size().reset_index(name='sales_count')
    camp_sales_counts = attr_sales.groupby(['camp_norm']).size().reset_index(name='sales_count')
    
    # Calculate allocated spend at Ad Level
    ad_merged = pd.merge(ad_spend, ad_sales_counts, on=['camp_norm', 'adset_norm', 'ad_norm'], how='left')
    ad_merged['sales_count'] = ad_merged['sales_count'].fillna(0)
    
    ad_merged['allocated_spend'] = ad_merged.apply(lambda r: r['Amount Spent'] if r['sales_count'] > 0 else 0.0, axis=1)
    ad_merged['remaining_spend'] = ad_merged['Amount Spent'] - ad_merged['allocated_spend']
    ad_merged['spend_per_sale'] = ad_merged.apply(lambda r: r['Amount Spent'] / r['sales_count'] if r['sales_count'] > 0 else 0.0, axis=1)
    
    # Calculate allocated spend at Adset Level
    # Pool remaining spend from Ads into the Adset
    adset_pooled = ad_merged.groupby(['camp_norm', 'adset_norm'])['remaining_spend'].sum().reset_index()
    adset_merged = pd.merge(adset_spend, adset_pooled, on=['camp_norm', 'adset_norm'], how='left')
    # If there are no ads, the remaining spend is the adset spend itself
    adset_merged['remaining_spend'] = adset_merged['remaining_spend'].fillna(adset_merged['Amount Spent'])
    
    adset_merged = pd.merge(adset_merged, adset_sales_counts, on=['camp_norm', 'adset_norm'], how='left')
    adset_merged['sales_count'] = adset_merged['sales_count'].fillna(0)
    
    adset_merged['allocated_spend'] = adset_merged.apply(lambda r: r['remaining_spend'] if r['sales_count'] > 0 else 0.0, axis=1)
    adset_merged['remaining_spend2'] = adset_merged['remaining_spend'] - adset_merged['allocated_spend']
    adset_merged['spend_per_sale'] = adset_merged.apply(lambda r: r['remaining_spend'] / r['sales_count'] if r['sales_count'] > 0 else 0.0, axis=1)
    
    # Calculate allocated spend at Campaign Level
    # Pool remaining spend from Adsets into the Campaign
    camp_pooled = adset_merged.groupby(['camp_norm'])['remaining_spend2'].sum().reset_index()
    camp_merged = pd.merge(camp_spend, camp_pooled, on=['camp_norm'], how='left')
    camp_merged['remaining_spend2'] = camp_merged['remaining_spend2'].fillna(camp_merged['Amount Spent'])
    
    camp_merged = pd.merge(camp_merged, camp_sales_counts, on=['camp_norm'], how='left')
    camp_merged['sales_count'] = camp_merged['sales_count'].fillna(0)
    
    camp_merged['spend_per_sale'] = camp_merged.apply(lambda r: r['remaining_spend2'] / r['sales_count'] if r['sales_count'] > 0 else 0.0, axis=1)
    
    # Map back to sales
    ad_map = ad_merged.set_index(['camp_norm', 'adset_norm', 'ad_norm'])['spend_per_sale'].to_dict()
    adset_map = adset_merged.set_index(['camp_norm', 'adset_norm'])['spend_per_sale'].to_dict()
    camp_map = camp_merged.set_index(['camp_norm'])['spend_per_sale'].to_dict()
    
    def get_attributed_spend(row):
        lvl = row['match_level']
        if lvl == 'Unattributed':
            return 0.0
            
        c = row.get('camp_norm', '')
        a = row.get('adset_norm', '')
        ad = row.get('ad_norm', '')
        
        total_spend = 0.0
        total_spend += ad_map.get((c, a, ad), 0.0)
        total_spend += adset_map.get((c, a), 0.0)
        total_spend += camp_map.get(c, 0.0)
        
        return total_spend
        
    sales_df['attributed_spend'] = sales_df.apply(get_attributed_spend, axis=1)
    
    # Invariant Check
    total_attr = sales_df['attributed_spend'].sum()
    total_meta = window_meta['Amount Spent'].sum()
    
    if total_attr > total_meta + 0.01: # allow small float rounding diff
        logger.error(f"INVARIANT VIOLATION: Total Attributed ({total_attr}) > Meta Spend ({total_meta})")
        raise ValueError("Total Attributed Spend <= Total Windowed Meta Spend invariant violated.")
        
    return sales_df, camp_spend, adset_spend, ad_spend
