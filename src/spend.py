import pandas as pd
import logging
from typing import Tuple

logger = logging.getLogger(__name__)

def allocate_spend(leads_df: pd.DataFrame, meta_df: pd.DataFrame, start_date: str, end_date: str) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    if not meta_df.empty and 'spend' not in meta_df.columns:
        raise KeyError("The required canonical field 'spend' is missing from the Meta data. Please ensure you mapped the raw spend column correctly in the UI.")
    """
    Allocate Meta spend to adsets and ads using lead-proportion allocation.
    Returns: (camp_spend, adset_spend, ad_spend)
    """
    from src.normalization import unify_campaign_name, clean_text
    def norm(val):
        return clean_text(val).lower() if pd.notna(val) else ''
    def norm_camp(val):
        return unify_campaign_name(val)

    if meta_df.empty:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
        
    window_meta = meta_df.copy()
    
    # Normalize Meta names for joining
    window_meta['camp_norm'] = window_meta.get('campaign', window_meta.get('Campaign Name', pd.Series(dtype=str))).apply(norm_camp)
    
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
    
    # 1. Billed Campaign Spend (Actual Meta Spend)
    camp_spend = window_meta.groupby(['camp_norm'])['spend'].sum().reset_index()
    
    # Process leads to count proportions
    if leads_df.empty:
        adset_spend = window_meta.groupby(['camp_norm', 'adset_norm'])['spend'].sum().reset_index()
        ad_spend = window_meta.groupby(['camp_norm', 'adset_norm', 'ad_norm'])['spend'].sum().reset_index()
        return camp_spend, adset_spend, ad_spend
        
        
    # Standardize lead UTMs
    leads = leads_df.copy()
    leads['camp_norm'] = leads['campaign'].apply(norm_camp) if 'campaign' in leads.columns else ""
    leads['adset_norm'] = leads['ad_set'].apply(norm) if 'ad_set' in leads.columns else ""
    leads['ad_norm'] = leads['ad_creative'].apply(norm) if 'ad_creative' in leads.columns else ""
    
    # Calculate Lead counts
    camp_leads = leads.groupby('camp_norm').size().reset_index(name='camp_leads')
    adset_leads = leads.groupby(['camp_norm', 'adset_norm']).size().reset_index(name='adset_leads')
    ad_leads = leads.groupby(['camp_norm', 'adset_norm', 'ad_norm']).size().reset_index(name='ad_leads')
    
    # Calculate Adset Allocated Spend
    adset_spend = pd.merge(adset_leads, camp_leads, on='camp_norm', how='left')
    adset_spend = pd.merge(adset_spend, camp_spend, on='camp_norm', how='left')
    adset_spend['spend'] = adset_spend['spend'].fillna(0)
    adset_spend['camp_leads'] = adset_spend['camp_leads'].fillna(1).replace(0, 1) # Prevent div/0
    adset_spend['allocated_spend'] = adset_spend['spend'] * (adset_spend['adset_leads'] / adset_spend['camp_leads'])
    adset_spend = adset_spend[['camp_norm', 'adset_norm', 'allocated_spend']].rename(columns={'allocated_spend': 'spend'})
    
    # Calculate Ad Allocated Spend
    ad_spend = pd.merge(ad_leads, camp_leads, on='camp_norm', how='left')
    ad_spend = pd.merge(ad_spend, camp_spend, on='camp_norm', how='left')
    ad_spend['spend'] = ad_spend['spend'].fillna(0)
    ad_spend['camp_leads'] = ad_spend['camp_leads'].fillna(1).replace(0, 1)
    ad_spend['allocated_spend'] = ad_spend['spend'] * (ad_spend['ad_leads'] / ad_spend['camp_leads'])
    ad_spend = ad_spend[['camp_norm', 'adset_norm', 'ad_norm', 'allocated_spend']].rename(columns={'allocated_spend': 'spend'})
    
    return camp_spend, adset_spend, ad_spend
