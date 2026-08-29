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
    
    # Ensure leads_df has valid UTMs indexed for fast lookup
    if not leads_df.empty:
        # Leads should already be deduplicated and have 'has_valid_utm' boolean
        leads_valid = leads_df[leads_df.get('has_valid_utm', pd.Series(True, index=leads_df.index))]
        leads_by_email = leads_valid.set_index('email') if 'email' in leads_valid.columns else pd.DataFrame()
        leads_by_phone = leads_valid.set_index('phone') if 'phone' in leads_valid.columns else pd.DataFrame()
    else:
        leads_by_email = pd.DataFrame()
        leads_by_phone = pd.DataFrame()
        leads_valid = pd.DataFrame()
        
    # Pre-compute fuzzy mapping for sales that don't exact match
    email_fuzzy_map = {}
    sales_emails = df['email'].dropna().unique() if 'email' in df.columns else []
    lead_emails = leads_valid['email'].dropna().unique() if 'email' in leads_valid.columns else []
    
    lead_emails_by_len = {}
    for le in lead_emails:
        if pd.notna(le):
            lead_emails_by_len.setdefault(len(str(le)), []).append(le)
    
    for se in sales_emails:
        if se in lead_emails:
            continue
        best_match = None
        best_score = 0
        if pd.notna(se):
            str_se = str(se)
            L1 = len(str_se)
            for L2, group in lead_emails_by_len.items():
                if 2 * min(L1, L2) / (L1 + L2) > 0.95:
                    for le in group:
                        score = SequenceMatcher(None, str_se, str(le)).ratio()
                        if score > best_score:
                            best_score = score
                            best_match = le
        if best_score > 0.95: # VERY HIGH threshold
            email_fuzzy_map[se] = best_match
            logger.info(f"Fuzzy Email Match: {se} -> {best_match} (Score: {best_score:.2f})")
            
    name_fuzzy_map = {}
    if 'name' in df.columns and 'first_name' in leads_valid.columns:
        sales_names = df['name'].dropna().unique()
        
        lead_names_by_len = {}
        for idx, lead in leads_valid.iterrows():
            ln = lead.get('first_name')
            if pd.notna(ln):
                clean_ln = str(ln).lower().strip()
                lead_names_by_len.setdefault(len(clean_ln), []).append((clean_ln, ln, lead))
                
        for sn in sales_names:
            best_n_match = None
            best_n_score = 0
            best_lead = None
            if pd.notna(sn):
                clean_sn = str(sn).lower().strip()
                L1 = len(clean_sn)
                for L2, group in lead_names_by_len.items():
                    if 2 * min(L1, L2) / (L1 + L2) >= 0.95:
                        for clean_ln, orig_ln, lead in group:
                            score = SequenceMatcher(None, clean_sn, clean_ln).ratio()
                            if score > best_n_score:
                                best_n_score = score
                                best_n_match = orig_ln
                                best_lead = lead
            if best_n_score >= 0.95:
                name_fuzzy_map[sn] = best_lead
                logger.info(f"Fuzzy Name Match: {sn} -> {best_n_match} (Score: {best_n_score:.2f})")
        
    sentinels_lower = [s.lower() for s in sentinels]
    
    def has_valid_utm_row(row):
        for col in ['campaign', 'ad_set', 'ad_creative']:
            if col in row and pd.notna(row[col]):
                val = str(row[col]).lower().strip()
                if val not in sentinels_lower and not val.isnumeric():
                    return True
        return False

    def determine_attribution(row) -> Dict:
        # Priority 1: Sales Sheet UTM
        if has_valid_utm_row(row):
            return {
                'campaign': row.get('campaign'),
                'ad_set': row.get('ad_set'),
                'ad_creative': row.get('ad_creative'),
                'attribution_source': 'Sales Sheet UTM'
            }
            
        # Priority 2: Leads DB by Email
        email = row.get('email')
        if pd.notna(email) and not leads_by_email.empty and email in leads_by_email.index:
            lead = leads_by_email.loc[email]
            # Handle case where multiple leads might somehow exist despite deduplication
            if isinstance(lead, pd.DataFrame):
                lead = lead.iloc[0]
            return {
                'campaign': lead.get('campaign'),
                'ad_set': lead.get('ad_set'),
                'ad_creative': lead.get('ad_creative'),
                'attribution_source': 'Leads DB (email)'
            }
            
        # Priority 3: Leads DB by Phone
        phone = row.get('phone')
        if pd.notna(phone) and not leads_by_phone.empty and phone in leads_by_phone.index:
            lead = leads_by_phone.loc[phone]
            if isinstance(lead, pd.DataFrame):
                lead = lead.iloc[0]
            return {
                'campaign': lead.get('campaign'),
                'ad_set': lead.get('ad_set'),
                'ad_creative': lead.get('ad_creative'),
                'attribution_source': 'Leads DB (phone)'
            }
            
        # Priority 4: Fuzzy Email Match (>0.95)
        if pd.notna(email) and email in email_fuzzy_map:
            fuzzy_email = email_fuzzy_map[email]
            lead = leads_by_email.loc[fuzzy_email]
            if isinstance(lead, pd.DataFrame):
                lead = lead.iloc[0]
            return {
                'campaign': lead.get('campaign'),
                'ad_set': lead.get('ad_set'),
                'ad_creative': lead.get('ad_creative'),
                'attribution_source': 'Leads DB (fuzzy email)'
            }
            
        # Priority 5: Fuzzy Name Match (>0.95)
        name = row.get('name')
        if pd.notna(name) and name in name_fuzzy_map:
            lead = name_fuzzy_map[name]
            return {
                'campaign': lead.get('campaign'),
                'ad_set': lead.get('ad_set'),
                'ad_creative': lead.get('ad_creative'),
                'attribution_source': 'Leads DB (fuzzy name)'
            }
            
        # Priority 6: Unattributed
        return {
            'campaign': None,
            'ad_set': None,
            'ad_creative': None,
            'attribution_source': 'Unattributed'
        }

    # Apply attribution
    attr_results = df.apply(determine_attribution, axis=1, result_type='expand')
    
    # Merge attribution results into df
    for col in ['campaign', 'ad_set', 'ad_creative', 'attribution_source']:
        df[col] = attr_results[col]
        
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
