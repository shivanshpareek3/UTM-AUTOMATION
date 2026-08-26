import pandas as pd
import json
import logging
from typing import Dict, List, Tuple
import difflib

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_aliases(alias_path: str = 'config/aliases.json') -> Dict[str, List[str]]:
    with open(alias_path, 'r') as f:
        return json.load(f)

def map_columns(df: pd.DataFrame, aliases: Dict[str, List[str]]) -> pd.DataFrame:
    """Map DataFrame columns to standard logical names using aliases."""
    df_mapped = df.copy()
    mapped_originals = {}
    
    # Create a lowercased mapping of existing columns
    col_map_lower = {str(col).lower().strip(): col for col in df.columns}
    
    for logical_name, alias_list in aliases.items():
        if logical_name in df.columns:
            continue
        for alias in alias_list:
            if alias.lower().strip() in col_map_lower:
                original_col = col_map_lower[alias.lower().strip()]
                if original_col not in mapped_originals:
                    mapped_originals[original_col] = []
                if logical_name not in mapped_originals[original_col]:
                    mapped_originals[original_col].append(logical_name)
                break # Map the first matching alias for this logical name
                
    for original_col, logical_names in mapped_originals.items():
        if not logical_names:
            continue
        first_logical = logical_names[0]
        df_mapped = df_mapped.rename(columns={original_col: first_logical})
        for extra_logical in logical_names[1:]:
            df_mapped[extra_logical] = df_mapped[first_logical]
            
    return df_mapped

def check_missing_columns(df: pd.DataFrame, required_columns: List[str]) -> List[str]:
    """Return a list of required columns that are missing from the dataframe."""
    missing = []
    for col in required_columns:
        if col not in df.columns:
            missing.append(col)
    return missing

import re

def normalize_text(text: str) -> str:
    """Normalize text by lowercasing and removing non-alphanumeric characters."""
    text = str(text).lower()
    return re.sub(r'[^a-z0-9]', '', text)

def suggest_mapping(canonical_field: str, available_columns: List[str], aliases: Dict[str, List[str]]) -> str:
    """Suggest the best matching original column for a canonical field."""
    # 1. Exact match (case-sensitive)
    for col in available_columns:
        if col == canonical_field:
            return col
            
    # 1.5. Exact match (case-insensitive and stripped)
    for col in available_columns:
        if col.lower().strip() == canonical_field.lower().strip():
            return col

    # 2. Normalized exact match
    norm_canonical = normalize_text(canonical_field)
    for col in available_columns:
        if normalize_text(col) == norm_canonical:
            return col

    # 3. Known alias match (exact or normalized)
    if canonical_field in aliases:
        for alias in aliases[canonical_field]:
            # Try exact case-insensitive alias match first
            for col in available_columns:
                if col.lower().strip() == alias.lower().strip():
                    return col
            # Then try normalized alias match
            norm_alias = normalize_text(alias)
            for col in available_columns:
                if normalize_text(col) == norm_alias:
                    return col

    # 4. High-confidence field-specific heuristic (strictly constrained to prevent false positives)
    for col in available_columns:
        lower_col = col.lower().strip()
        # Ensure we don't accidentally map 'customer name' to 'email' if we ever did fuzzy matching.
        # We only use very strict inclusion.
        if canonical_field == 'email' and 'email' in lower_col and 'name' not in lower_col:
            return col
        elif canonical_field == 'phone' and ('phone' in lower_col or 'mobile' in lower_col or 'contact' in lower_col) and 'name' not in lower_col:
            return col
        elif canonical_field == 'registration_date' and (
            ('registration' in lower_col and ('date' in lower_col or 'time' in lower_col)) or 
            ('created' in lower_col and 'at' in lower_col)
        ):
            return col
        elif canonical_field == 'campaign' and 'campaign' in lower_col and 'source' not in lower_col and 'medium' not in lower_col and 'name' not in lower_col:
            return col
        elif canonical_field == 'ad_set' and ('adset' in lower_col or 'ad set' in lower_col):
            return col
        elif canonical_field == 'ad_creative' and ('creative' in lower_col):
            return col
        elif canonical_field == 'spend' and ('spend' in lower_col or 'spent' in lower_col) and 'name' not in lower_col:
            return col
        elif canonical_field == 'sale_date' and ('sale' in lower_col or 'order' in lower_col or 'purchase' in lower_col) and 'date' in lower_col:
            return col
        elif canonical_field == 'Day' and ('date' in lower_col or 'day' in lower_col) and 'name' not in lower_col:
            return col

    # 5. Otherwise
    return '-- Ignore/Missing --'

def inspect_file(filename: str, df: pd.DataFrame, required_columns: List[str] = None):
    """Log file inspection details."""
    logger.info(f"Inspecting file: {filename}")
    logger.info(f"Row count: {len(df)}")
    logger.info(f"Columns: {list(df.columns)}")
    
    if required_columns:
        missing = check_missing_columns(df, required_columns)
        if missing:
            logger.warning(f"Missing required columns in {filename}: {missing}")
            
    # Count distinct values for attribution columns if they exist
    for col in ['utm_source', 'utm_medium', 'utm_content']:
        if col in df.columns:
            logger.info(f"Distinct {col} values: {df[col].nunique()}")
            
    return df
