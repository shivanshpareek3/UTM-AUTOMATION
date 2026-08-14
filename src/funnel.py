import pandas as pd
import numpy as np

def apply_funnel_logic(sales_df: pd.DataFrame, leads_df: pd.DataFrame, cutoff_date: str) -> pd.DataFrame:
    """
    Applies Old vs New lead logic and Free vs Paid webinar logic to sales.
    """
    if sales_df.empty:
        return sales_df
        
    df = sales_df.copy()
    cutoff_dt = pd.to_datetime(cutoff_date)
    
    # Merge registration info if not present
    if not leads_df.empty and 'email' in leads_df.columns:
        cols_to_keep = list(set(['email', 'registration_date', 'webinar_type', 'registration_fee']).intersection(leads_df.columns))
        leads_info = leads_df[cols_to_keep].drop_duplicates('email')
        df = pd.merge(df, leads_info, on='email', how='left')
        
    for col in ['registration_date', 'webinar_type', 'registration_fee']:
        if col not in df.columns:
            df[col] = None
                
    # Old vs New
    def is_old(reg_date):
        if pd.isna(reg_date):
            return 'New' # Assume new if missing
        return 'Old' if reg_date < cutoff_dt else 'New'
        
    df['new_old_lead'] = df['registration_date'].apply(is_old)
    
    # Free vs Paid logic
    # Clean webinar type
    df['webinar_type_clean'] = df['webinar_type'].astype(str).str.lower().str.strip()
    
    def calc_reg_fee(row):
        wt = str(row.get('webinar_type_clean', ''))
        fee = row.get('registration_fee', 0)
        try:
            fee = float(fee) if pd.notna(fee) else 0.0
        except ValueError:
            fee = 0.0
            
        if 'paid' in wt or fee > 0:
            return fee
        return 0.0
        
    df['registration_fee_applied'] = df.apply(calc_reg_fee, axis=1)
    df['total_revenue'] = df['order_amount'] + df['registration_fee_applied']
    
    return df

def aggregate_registration_revenue(leads_df: pd.DataFrame, start_date: str, end_date: str, sentinels: list) -> pd.DataFrame:
    """
    Aggregates registration fee revenue for all paid registrations in the window,
    even if they didn't purchase backend.
    """
    if leads_df.empty:
        return pd.DataFrame()
        
    df = leads_df.copy()
    start_dt = pd.to_datetime(start_date)
    end_dt = pd.to_datetime(end_date)
    
    if 'registration_date' in df.columns:
        df = df[(df['registration_date'] >= start_dt) & (df['registration_date'] <= end_dt)]
        
    def get_fee(row):
        wt = str(row.get('webinar_type', '')).lower()
        fee = row.get('registration_fee', 0)
        try:
            fee = float(fee) if pd.notna(fee) else 0.0
        except ValueError:
            fee = 0.0
        if 'paid' in wt or fee > 0:
            return fee
        return 0.0
        
    df['reg_revenue'] = df.apply(get_fee, axis=1)
    return df[df['reg_revenue'] > 0]
