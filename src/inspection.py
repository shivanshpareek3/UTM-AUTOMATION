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

def suggest_mapping(canonical_field: str, available_columns: List[str], aliases: Dict[str, List[str]]) -> str:
    """Suggest the best matching original column for a canonical field."""
    # Exact match
    for col in available_columns:
        if col.lower().strip() == canonical_field.lower().strip():
            return col
    
    # Alias match
    if canonical_field in aliases:
        for alias in aliases[canonical_field]:
            for col in available_columns:
                if col.lower().strip() == alias.lower().strip():
                    return col
                    
    # Fuzzy match
    all_targets = [canonical_field]
    if canonical_field in aliases:
        all_targets.extend(aliases[canonical_field])
        
    for target in all_targets:
        matches = difflib.get_close_matches(target.lower(), [c.lower() for c in available_columns], n=1, cutoff=0.8)
        if matches:
            for col in available_columns:
                if col.lower() == matches[0]:
                    return col
                    
    return "-- Ignore/Missing --"

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
