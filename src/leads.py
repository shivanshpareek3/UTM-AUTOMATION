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
    
    # Sort so that we can keep the most recent with valid UTM
    # Primary sort: email (to group), secondary: has_valid_utm (True first), tertiary: registration_date (descending)
    if 'registration_date' in df.columns and 'email' in df.columns:
        df = df.sort_values(by=['email', 'has_valid_utm', 'registration_date'], 
                            ascending=[True, False, False])
        
        # Deduplicate by email
        df = df.drop_duplicates(subset=['email'], keep='first')
        
    return df
