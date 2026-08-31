import pandas as pd
from typing import List, Dict
from difflib import SequenceMatcher
import logging

logger = logging.getLogger(__name__)

def attribute_sales(sales_df: pd.DataFrame, leads_df: pd.DataFrame, sentinels: List[str]) -> pd.DataFrame:
    """
    Attribute sales using the priority:
    1. Sales Sheet UTM
    2. Leads DB by Email
    3. Leads DB by Phone
    4. Unattributed
    """
    if sales_df.empty:
        return sales_df
        
    df = sales_df.copy()
    
    # 1. Earliest Touch Deduplication for Leads
    # We want to match against the EARLIEST registration of a buyer.
    # The leads_df is already sorted by registration_date ascending (from process_leads).
    # We will create lookups by email and phone, keeping the FIRST occurrence.
    
    if not leads_df.empty:
        # Create a valid leads dataframe (ignoring empty emails/phones for lookups)
        # Note: We do not restrict to has_valid_utm for the match itself. 
        # A buyer is a buyer regardless of UTM. We just inherit whatever UTM they have.
        if 'email' in leads_df.columns:
            leads_for_email = leads_df[leads_df['email'].astype(str).str.strip() != '']
            leads_by_email = leads_for_email.drop_duplicates(subset=['email'], keep='first').set_index('email')
        else:
            leads_by_email = pd.DataFrame()
            
        if 'phone' in leads_df.columns:
            leads_for_phone = leads_df[leads_df['phone'].astype(str).str.strip() != '']
            leads_by_phone = leads_for_phone.drop_duplicates(subset=['phone'], keep='first').set_index('phone')
        else:
            leads_by_phone = pd.DataFrame()
    else:
        leads_by_email = pd.DataFrame()
        leads_by_phone = pd.DataFrame()

    sentinels_lower = [s.lower() for s in sentinels]
    
    def has_valid_utm_row(row):
        for col in ['campaign', 'ad_set', 'ad_creative']:
            if col in row:
                val = row[col]
                if pd.notna(val):
                    val = str(val).lower().strip()
                    if val and val not in sentinels_lower and not val.isnumeric():
                        return True
        return False

    def determine_attribution(row) -> Dict:
        # Priority 1: Sales Sheet UTM (if the sales row natively has a valid UTM)
        if has_valid_utm_row(row):
            return {
                'campaign': row.get('campaign'),
                'ad_set': row.get('ad_set'),
                'ad_creative': row.get('ad_creative'),
                'attribution_source': 'Sales Sheet UTM',
                'matched_to_lead': False
            }
            
        # Extract email and phone from sales row
        email = str(row.get('email', '')).strip().lower()
        if email in ('nan', 'none', 'null'):
            email = ''
            
        phone = str(row.get('phone', '')).strip()
        if phone in ('nan', 'none', 'null'):
            phone = ''
            
        # Priority 2: Leads DB by Email
        if email and not leads_by_email.empty and email in leads_by_email.index:
            lead = leads_by_email.loc[email]
            return {
                'campaign': lead.get('campaign'),
                'ad_set': lead.get('ad_set'),
                'ad_creative': lead.get('ad_creative'),
                'attribution_source': 'Leads DB (email)',
                'matched_to_lead': True
            }
            
        # Priority 3: Leads DB by Phone
        if phone and not leads_by_phone.empty and phone in leads_by_phone.index:
            lead = leads_by_phone.loc[phone]
            return {
                'campaign': lead.get('campaign'),
                'ad_set': lead.get('ad_set'),
                'ad_creative': lead.get('ad_creative'),
                'attribution_source': 'Leads DB (phone)',
                'matched_to_lead': True
            }
            
        # Priority 4: Unattributed
        return {
            'campaign': None,
            'ad_set': None,
            'ad_creative': None,
            'attribution_source': 'Unattributed',
            'matched_to_lead': False
        }

    # Apply attribution
    attr_results = df.apply(determine_attribution, axis=1, result_type='expand')
    
    # Merge attribution results into df
    for col in ['campaign', 'ad_set', 'ad_creative', 'attribution_source', 'matched_to_lead']:
        df[col] = attr_results[col]
        
    # Determine Match Level
    def get_match_level(row):
        def is_valid(key):
            val = row.get(key)
            if pd.isna(val): return False
            return str(val).strip() != ""
            
        if row['attribution_source'] == 'Unattributed':
            return 'Unattributed'
        if is_valid('campaign') and is_valid('ad_set') and is_valid('ad_creative'):
            return 'Ad Level'
        if is_valid('campaign') and is_valid('ad_set'):
            return 'Adset Level'
        if is_valid('campaign'):
            return 'Campaign Level'
        return 'Unattributed'
        
    df['match_level'] = df.apply(get_match_level, axis=1)
    
    # Finally, verify if the matched lead ACTUALLY has a campaign UTM
    # (Because it's only a "Campaign-Attributed Sale" if it has a campaign)
    df['matched_to_campaign'] = df.apply(lambda r: r['matched_to_lead'] and r['match_level'] != 'Unattributed', axis=1)
    
    return df

