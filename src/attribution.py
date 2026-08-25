import pandas as pd
from typing import List, Dict
from difflib import SequenceMatcher
import logging

logger = logging.getLogger(__name__)

def attribute_sales(sales_df: pd.DataFrame, leads_df: pd.DataFrame, sentinels: List[str]) -> pd.DataFrame:
    """
    Attribute sales using the priority:
    1. Normalized Email
    2. Normalized Phone (last 10 digits)
    """
    if sales_df.empty:
        return sales_df
        
    df = sales_df.copy()
    
    if not leads_df.empty:
        leads_valid = leads_df.copy()
        
        # Lead deduplication: sort by created_at ascending and retain the earliest/first touch
        if 'created_at' in leads_valid.columns:
            leads_valid['created_at'] = pd.to_datetime(leads_valid['created_at'], errors='coerce')
            leads_valid = leads_valid.sort_values(by='created_at', ascending=True)
            
        # Deduplicate by email
        if 'email' in leads_valid.columns:
            leads_by_email = leads_valid.drop_duplicates(subset=['email'], keep='first').set_index('email')
        else:
            leads_by_email = pd.DataFrame()
            
        # Deduplicate by phone
        if 'phone' in leads_valid.columns:
            leads_by_phone = leads_valid.drop_duplicates(subset=['phone'], keep='first').set_index('phone')
        else:
            leads_by_phone = pd.DataFrame()
    else:
        leads_by_email = pd.DataFrame()
        leads_by_phone = pd.DataFrame()

    def determine_attribution(row) -> Dict:
        # Priority 1: Leads DB by Email
        email = row.get('email')
        if pd.notna(email) and not leads_by_email.empty and email in leads_by_email.index:
            lead = leads_by_email.loc[email]
            return {
                'campaign': lead.get('campaign'),
                'ad_set': lead.get('ad_set'),
                'ad_creative': lead.get('ad_creative'),
                'placement': lead.get('placement'),
                'attribution_source': 'Leads DB (email)'
            }
            
        # Priority 2: Leads DB by Phone
        phone = row.get('phone')
        if pd.notna(phone) and not leads_by_phone.empty and phone in leads_by_phone.index:
            lead = leads_by_phone.loc[phone]
            return {
                'campaign': lead.get('campaign'),
                'ad_set': lead.get('ad_set'),
                'ad_creative': lead.get('ad_creative'),
                'placement': lead.get('placement'),
                'attribution_source': 'Leads DB (phone)'
            }
            
        return {
            'campaign': 'Unattributed',
            'ad_set': 'Unattributed',
            'ad_creative': 'Unattributed',
            'placement': 'Unattributed',
            'attribution_source': 'Unattributed'
        }

    attributed_data = df.apply(determine_attribution, axis=1)
    attr_df = pd.DataFrame(attributed_data.tolist(), index=df.index)
    
    for col in ['campaign', 'ad_set', 'ad_creative', 'placement', 'attribution_source']:
        if col in attr_df.columns:
            df[col] = attr_df[col]

    # Determine Match Level
    def get_match_level(row):
        if row['attribution_source'] == 'Unattributed':
            return 'Unattributed'
        if pd.notna(row['campaign']) and pd.notna(row['ad_set']) and pd.notna(row['ad_creative']):
            return 'Ad Level'
        if pd.notna(row['campaign']) and pd.notna(row['ad_set']):
            return 'Adset Level'
        if pd.notna(row['campaign']):
            return 'Campaign Level'
        return 'Unattributed'
        
    df['match_level'] = df.apply(get_match_level, axis=1)
    
    return df
