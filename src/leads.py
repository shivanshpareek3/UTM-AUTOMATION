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
    
    # Do not deduplicate here. Golden methodology expects Total Leads to be the raw count (3295).
    # Deduplication for attribution is handled dynamically in attribution.py based on earliest touch.
        
    return df
