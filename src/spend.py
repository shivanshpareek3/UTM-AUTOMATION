import pandas as pd
import logging
from typing import Tuple

logger = logging.getLogger(__name__)

def allocate_spend(sales_df: pd.DataFrame, meta_df: pd.DataFrame, leads_df: pd.DataFrame, start_date: str, end_date: str) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Allocate Meta spend using the Golden Methodology:
    - Campaign Spend = actual Meta billed spend.
    - Ad Set Spend = Campaign Spend * (Ad Set Leads / Campaign Leads)
    - Ad Spend = Campaign Spend * (Ad Leads / Campaign Leads)
    - Placement Spend = Campaign Spend * (Placement Leads / Campaign Leads)
    Returns: (sales_df, campaign_summary, adset_summary, ad_summary, placement_summary)
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
        sales_df['placement_norm'] = sales_df['placement'].apply(norm) if 'placement' in sales_df.columns else ""

    if meta_df.empty:
        return sales_df, pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
        
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
    
    valid_meta['Amount Spent Num'] = pd.to_numeric(valid_meta['Amount Spent'], errors='coerce').fillna(0.0)
    
    # Calculate top-level campaign spend from Meta
    camp_meta_spend = valid_meta.groupby(['camp_norm'])['Amount Spent Num'].sum().reset_index()
    camp_meta_spend = camp_meta_spend.rename(columns={'Amount Spent Num': 'Amount Spent'})
    
    # Prepare Leads for proportional raw spend splitting for summaries
    if not leads_df.empty:
        leads_df['camp_norm'] = leads_df['campaign'].apply(norm_camp) if 'campaign' in leads_df.columns else ""
        leads_df['adset_norm'] = leads_df['ad_set'].apply(norm) if 'ad_set' in leads_df.columns else ""
        leads_df['ad_norm'] = leads_df['ad_creative'].apply(norm) if 'ad_creative' in leads_df.columns else ""
        leads_df['placement_norm'] = leads_df['placement'].apply(norm) if 'placement' in leads_df.columns else ""
        
        camp_leads = leads_df.groupby(['camp_norm']).size().reset_index(name='camp_leads')
        adset_leads = leads_df.groupby(['camp_norm', 'adset_norm']).size().reset_index(name='adset_leads')
        ad_leads = leads_df.groupby(['camp_norm', 'adset_norm', 'ad_norm']).size().reset_index(name='ad_leads')
        placement_leads = leads_df.groupby(['camp_norm', 'placement_norm']).size().reset_index(name='placement_leads')
    else:
        camp_leads = pd.DataFrame(columns=['camp_norm', 'camp_leads'])
        adset_leads = pd.DataFrame(columns=['camp_norm', 'adset_norm', 'adset_leads'])
        ad_leads = pd.DataFrame(columns=['camp_norm', 'adset_norm', 'ad_norm', 'ad_leads'])
        placement_leads = pd.DataFrame(columns=['camp_norm', 'placement_norm', 'placement_leads'])

    # Merge campaign spend with campaign leads
    camp_spend = pd.merge(camp_meta_spend, camp_leads, on='camp_norm', how='left')
    camp_spend['camp_leads'] = camp_spend['camp_leads'].fillna(0)

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
    
    # Placement Allocation (Lead Share)
    placement_spend = pd.merge(placement_leads, camp_spend[['camp_norm', 'Amount Spent', 'camp_leads']], on='camp_norm', how='inner')
    placement_spend['Amount Spent'] = placement_spend.apply(
        lambda r: r['Amount Spent'] * (r['placement_leads'] / r['camp_leads']) if r['camp_leads'] > 0 else 0.0, axis=1
    )
    
    # Strip down columns
    camp_spend_out = camp_spend[['camp_norm', 'Amount Spent']].copy()
    adset_spend_out = adset_spend[['camp_norm', 'adset_norm', 'Amount Spent']].copy()
    ad_spend_out = ad_spend[['camp_norm', 'adset_norm', 'ad_norm', 'Amount Spent']].copy()
    placement_spend_out = placement_spend[['camp_norm', 'placement_norm', 'Amount Spent']].copy()
    
    return sales_df, camp_spend_out, adset_spend_out, ad_spend_out, placement_spend_out
