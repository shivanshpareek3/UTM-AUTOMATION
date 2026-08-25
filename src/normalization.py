import pandas as pd
import re

def clean_text(text) -> str:
    """Trim whitespace and collapse multiple spaces."""
    if pd.isna(text):
        return ""
    text = str(text)
    # Fix common mojibake
    text = text.replace('‚Äì', '–').replace('‚Äî', '—')
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def parse_date_series(series: pd.Series) -> pd.Series:
    """
    Intelligently parse a date series without breaking ISO standards.
    - Cleans parenthesized timezones e.g., '(Indian Standard Time)'.
    - Uses strict ISO parsing for YYYY-MM-DD.
    - Uses dayfirst=True for DD/MM/YYYY.
    - Ambiguous dates like 01/02/2026 are assumed to be day-first (DD/MM/YYYY) 
      which aligns with typical Indian/European setups.
    """
    def _parse_single(date_val):
        if pd.isna(date_val):
            return pd.NaT
        text = str(date_val).strip()
        text = re.sub(r'\s*\([^)]*\)$', '', text).strip()
        if not text or text.lower() in ('nan', 'none', 'not a date', 'null'):
            return pd.NaT
            
        # 1. ISO Format (YYYY-MM-DD...)
        if re.match(r'^\d{4}-\d{2}-\d{2}', text):
            return pd.to_datetime(text, errors='coerce')
            
        # 2. DD/MM/YYYY or DD-MM-YYYY Format
        if re.match(r'^\d{1,2}[/-]\d{1,2}[/-]\d{4}', text):
            return pd.to_datetime(text, dayfirst=True, errors='coerce')
            
        # Fallback
        return pd.to_datetime(text, errors='coerce')
        
    return series.apply(_parse_single)

def normalize_email(email) -> str:
    """Lowercase and trim email."""
    if pd.isna(email) or email is None:
        return ""
    email_str = str(email).lower().strip()
    if email_str in ('nan', 'null', 'none'):
        return ""
    # Remove all spaces inside email
    email_str = re.sub(r'\s+', '', email_str)
    return email_str

def normalize_phone(phone) -> str:
    """Remove spaces, hyphens, brackets, +91 from phone numbers."""
    if pd.isna(phone) or phone is None:
        return ""
    
    if isinstance(phone, float):
        try:
            phone = str(int(phone))
        except ValueError:
            phone = str(phone)
    else:
        phone = str(phone).strip()
        
    # Remove .0 suffix if it came from a float string
    if phone.endswith('.0'):
        phone = phone[:-2]
        
    # Remove everything except digits
    digits = re.sub(r'\D', '', phone)
    
    # Golden methodology: last 10 digits
    if len(digits) > 10:
        digits = digits[-10:]
        
    return digits

def unify_campaign_name(campaign) -> str:
    """Case-insensitive matching for campaign, with targeted normalizations."""
    if pd.isna(campaign):
        return ""
    text = clean_text(campaign).lower()
    
    # Standardize URL encodings that may appear differently
    import urllib.parse
    text = urllib.parse.unquote(text)
    
    # Targeted safe, dynamic normalization for the proven campaign family:
    if "foremostleads-gs-13-09" in text:
        # Dynamically strip <...> variations within this specific proven family
        import re
        text = re.sub(r'<[^>]+>', '', text).strip()
        
    return text
