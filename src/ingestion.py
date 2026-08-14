import pandas as pd
import os

import io

def _smart_read_excel(file_obj) -> pd.DataFrame:
    # Read Excel sheets
    try:
        xl = pd.ExcelFile(file_obj)
    except Exception as e:
        return pd.read_excel(file_obj) # Fallback
        
    sheets = xl.sheet_names
    target_sheet = sheets[0]
    
    for s in sheets:
        if s.strip().lower() == "raw data report":
            target_sheet = s
            break
            
    # Try reading the sheet normally first to see if headers are on row 0
    df = pd.read_excel(file_obj, sheet_name=target_sheet)
    
    # Check if this is a meta report with shifted headers
    # Often they have a metadata block and real headers below
    has_meta_anchors = any(col for col in df.columns if isinstance(col, str) and ("Campaign name" in col or "Amount spent" in col))
    
    if not has_meta_anchors:
        # Scan first 50 rows for actual headers
        df_scan = pd.read_excel(file_obj, sheet_name=target_sheet, header=None, nrows=50)
        for i, row in df_scan.iterrows():
            row_vals = [str(x).lower() for x in row.values]
            if "campaign name" in row_vals or "amount spent (inr)" in row_vals or "amount spent" in row_vals:
                # Found the header row
                df = pd.read_excel(file_obj, sheet_name=target_sheet, header=i)
                break
                
    return df

def read_file(filepath: str) -> pd.DataFrame:
    """Read a CSV or XLSX file and return a pandas DataFrame."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")
        
    ext = os.path.splitext(filepath)[1].lower()
    
    if ext == '.csv':
        df = pd.read_csv(filepath)
    elif ext in ['.xlsx', '.xls']:
        df = _smart_read_excel(filepath)
    else:
        raise ValueError(f"Unsupported file format: {ext}")
        
    return df

def read_stream(file_obj, filename: str) -> pd.DataFrame:
    """Read from a stream (like Streamlit UploadedFile)."""
    ext = os.path.splitext(filename)[1].lower()
    if ext == '.csv':
        return pd.read_csv(file_obj)
    elif ext in ['.xlsx', '.xls']:
        return _smart_read_excel(file_obj)
    else:
        raise ValueError(f"Unsupported file format: {ext}")
