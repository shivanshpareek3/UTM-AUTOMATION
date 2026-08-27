import pandas as pd
import logging
from typing import Tuple

logger = logging.getLogger(__name__)

def allocate_spend(sales_df: pd.DataFrame, meta_df: pd.DataFrame, leads_df: pd.DataFrame, meta_start: str, meta_end: str) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
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
        return sales_df, pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame(columns=['camp_norm', 'placement_norm', 'Amount Spent'])
        
    window_meta = meta_df.copy()
    
    # Normalize Meta names for joining
    if 'spend' in window_meta.columns and 'Amount Spent' not in window_meta.columns:
        window_meta = window_meta.rename(columns={'spend': 'Amount Spent'})
        
    window_meta['Amount Spent'] = pd.to_numeric(window_meta['Amount Spent'], errors='coerce').fillna(0.0)
    window_meta['camp_norm'] = window_meta.get('campaign', window_meta.get('Campaign Name', window_meta.get('Campaign name', pd.Series(dtype=str)))).apply(norm_camp)
    
    # Safely handle missing ad_set/ad columns in Meta reports (e.g. Campaign-level reports)
    if 'ad_set' in window_meta.columns:
        window_meta['adset_norm'] = window_meta['ad_set'].apply(norm)
    elif 'Ad Set Name' in window_meta.columns:
        window_meta['adset_norm'] = window_meta['Ad Set Name'].apply(norm)
    else:
        window_meta['adset_norm'] = ""
        
    if 'ad' in window_meta.columns:
        window_meta['ad_norm'] = window_meta['ad'].apply(norm)
    elif 'Ad Name' in window_meta.columns:
        window_meta['ad_norm'] = window_meta['Ad Name'].apply(norm)
    else:
        window_meta['ad_norm'] = ""
    
    # Aggregate spend at each level
    ad_spend = window_meta.groupby(['camp_norm', 'adset_norm', 'ad_norm'])['Amount Spent'].sum().reset_index()
    adset_spend = window_meta.groupby(['camp_norm', 'adset_norm'])['Amount Spent'].sum().reset_index()
    camp_spend = window_meta.groupby(['camp_norm'])['Amount Spent'].sum().reset_index()
    
    if sales_df.empty:
        if 'attributed_spend' not in sales_df.columns:
            sales_df['attributed_spend'] = pd.Series(dtype=float)
        return sales_df, camp_spend, adset_spend, ad_spend, pd.DataFrame(columns=['camp_norm', 'placement_norm', 'Amount Spent'])

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
    adset_merged = pd.merge(adset_pooled, adset_sales_counts, on=['camp_norm', 'adset_norm'], how='left')
    adset_merged['sales_count'] = adset_merged['sales_count'].fillna(0)
    
    adset_merged['allocated_spend'] = adset_merged.apply(lambda r: r['remaining_spend'] if r['sales_count'] > 0 else 0.0, axis=1)
    adset_merged['remaining_spend2'] = adset_merged['remaining_spend'] - adset_merged['allocated_spend']
    adset_merged['spend_per_sale'] = adset_merged.apply(lambda r: r['remaining_spend'] / r['sales_count'] if r['sales_count'] > 0 else 0.0, axis=1)
    
    # Calculate allocated spend at Campaign Level
    # Pool remaining spend from Adsets into the Campaign
    camp_pooled = adset_merged.groupby(['camp_norm'])['remaining_spend2'].sum().reset_index()
    camp_merged = pd.merge(camp_pooled, camp_sales_counts, on=['camp_norm'], how='left')
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
        
    return sales_df, camp_spend, adset_spend, ad_spend, pd.DataFrame(columns=['camp_norm', 'placement_norm', 'Amount Spent'])
