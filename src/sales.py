import pandas as pd
from typing import List, Tuple
from src.normalization import normalize_email

def process_sales(df: pd.DataFrame, settings: dict) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Filter sales based on payment status and resolve missing amounts.
    Return (valid_sales, excluded_sales).
    """
    if df.empty:
        return df, pd.DataFrame()
        
    fallback_price = settings.get('fallback_price', 0.0)
    payment_status_source = settings.get('payment_status_source', 'Actual Payment Status')
        
    if 'email' in df.columns:
        df['email'] = df['email'].apply(normalize_email)
        
    if 'phone' in df.columns:
        from src.normalization import normalize_phone
        df['phone'] = df['phone'].apply(normalize_phone)
        
    if 'sale_id' not in df.columns:
        df['sale_id'] = range(1, len(df) + 1)
        
    # Ensure sale_date is datetime
    if 'sale_date' in df.columns:
        from src.normalization import parse_date_series
        df['sale_date'] = parse_date_series(df['sale_date'])
        
    # Apply fallback price if order_amount is missing or invalid
    if 'order_amount' not in df.columns:
        df['order_amount'] = fallback_price
        df['amount_source'] = 'fallback_price'
    else:
        def resolve_amount(x):
            val = pd.to_numeric(x, errors='coerce')
            if pd.isna(val):
                return fallback_price, 'fallback_price'
            return val, 'actual'
        
        amounts_and_sources = df['order_amount'].apply(resolve_amount)
        df['order_amount'] = [a[0] for a in amounts_and_sources]
        df['amount_source'] = [a[1] for a in amounts_and_sources]
        
    # Filter by payment status
    excluded_sales = pd.DataFrame()
    
    if payment_status_source == "Treat All Imported Sales as Successful":
        if 'payment_status' not in df.columns:
            df['payment_status'] = 'assumed_successful'
        else:
            df['payment_status'] = df['payment_status'].fillna('assumed_successful')
            
        if 'payment_status_source' not in df.columns:
            df['payment_status_source'] = df['payment_status'].apply(
                lambda x: 'assumed_successful' if x == 'assumed_successful' else 'actual'
            )
    else:
        # Standard filtering logic
        valid_statuses = ['successful', 'captured', 'completed', 'success', 'paid']
        invalid_statuses = ['failed', 'pending', 'refunded', 'cancelled']
        
        if 'payment_status' not in df.columns:
            if payment_status_source == "Exclude Sales Without Payment Status":
                excluded_sales = df.copy()
                excluded_sales['exclusion_reason'] = 'Missing Payment Status'
                df = pd.DataFrame(columns=df.columns)
            else:
                # If actual is selected but column missing, Streamlit will block, but here we just return df
                pass
            df['payment_status_source'] = 'actual' if not df.empty else ''
        else:
            def is_valid(status):
                if pd.isna(status):
                    return payment_status_source != "Exclude Sales Without Payment Status"
                s = str(status).lower().strip()
                if any(inv in s for inv in invalid_statuses):
                    return False
                return True
                
            is_valid_mask = df['payment_status'].apply(is_valid)
            excluded_sales = df[~is_valid_mask].copy()
            if not excluded_sales.empty:
                excluded_sales['exclusion_reason'] = 'Invalid Payment Status'
            df = df[is_valid_mask].copy()
            df['payment_status_source'] = 'actual'
            
            if payment_status_source == "Exclude Sales Without Payment Status":
                # Ensure na values are actually excluded (handled in is_valid)
                pass

    return df, excluded_sales
