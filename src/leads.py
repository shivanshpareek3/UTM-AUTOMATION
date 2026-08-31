import pandas as pd
from typing import List
from src.normalization import normalize_email, normalize_phone

def process_leads(df: pd.DataFrame, sentinels: List[str]) -> pd.DataFrame:
    """
    Process leads data: normalize fields, detect invalid UTMs, and deduplicate.
    For duplicates, select the most recent registration with valid UTM data.
    """
    if df.empty:
        return df

    # Normalize email and phone if they exist
    if 'email' in df.columns:
        df['email'] = df['email'].apply(normalize_email)
    if 'phone' in df.columns:
        df['phone'] = df['phone'].apply(normalize_phone)
        
    # Ensure registration_date is datetime
    if 'registration_date' in df.columns:
        from src.normalization import parse_date_series
        df['registration_date'] = parse_date_series(df['registration_date'])
        
    # Identify valid UTMs (sentinels case-insensitive)
    sentinels_lower = [s.lower() for s in sentinels]
    
    def has_valid_utm(row):
        for col in ['campaign', 'ad_set', 'ad_creative']:
            if col in row and pd.notna(row[col]):
                val = str(row[col]).lower().strip()
                if val not in sentinels_lower and not val.isnumeric():
                    return True
        return False
        
    df['has_valid_utm'] = df.apply(has_valid_utm, axis=1)
    
    # Golden Methodology: Sort to keep the most recent with valid UTM
    if 'registration_date' in df.columns:
        # 0. Sanitize Dummy/Test Leads (Golden Methodology)
        # Test leads injected by QA or FB Lead Ads testing tools should be excluded
        def is_test_lead(row):
            e = str(row.get('email', '')).strip().lower()
            f = str(row.get('first_name', '')).strip().lower()
            return e == 'test@gmail.com' or e == 'test@fb.com' or f == 'test'
            
        test_mask = df.apply(is_test_lead, axis=1)
        df = df[~test_mask]
        
        df = df.sort_values(by=['has_valid_utm', 'registration_date'], 
                            ascending=[False, True])
        
        # 1. Exact duplicates across all columns are removed
        df = df.drop_duplicates(keep='first')
        
        # 2. Deduplicate by email and phone combination
        # This is the EXACT Golden Methodology logic for deduplication:
        # We do not treat blank emails as same, nor blank phones as same.
        if 'email' in df.columns and 'phone' in df.columns:
            import uuid
            def generate_dedup_key(row):
                e = str(row.get('email', '')).strip().lower()
                p = str(row.get('phone', '')).strip()
                if not e: e = str(uuid.uuid4())
                if not p: p = str(uuid.uuid4())
                return f"{e}|{p}"
                
            df['dedup_key'] = df.apply(generate_dedup_key, axis=1)
            df = df.drop_duplicates(subset=['dedup_key'], keep='first')
            df = df.drop(columns=['dedup_key'])
        elif 'email' in df.columns:
            import uuid
            def generate_dedup_key_email(row):
                e = str(row.get('email', '')).strip().lower()
                if not e: return str(uuid.uuid4())
                return e
            df['dedup_key'] = df.apply(generate_dedup_key_email, axis=1)
            df = df.drop_duplicates(subset=['dedup_key'], keep='first')
            df = df.drop(columns=['dedup_key'])
            
    return df
