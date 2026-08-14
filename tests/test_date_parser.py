import pytest
import pandas as pd
import numpy as np
from src.normalization import parse_date_series

def test_parse_date_series():
    inputs = [
        "11/08/2026 8:47 pm (Indian Standard Time)", # A
        "25/12/2026", # B
        "2026-08-11", # C
        "2026-08-11 20:47:00", # D
        "2026-08-11T20:47:00", # E
        "", # F
        None, # F
        np.nan, # F
        "not a date", # G
        "01/02/2026" # H (ambiguous)
    ]
    
    series = pd.Series(inputs)
    parsed = parse_date_series(series)
    
    # A
    assert parsed.iloc[0].strftime("%Y-%m-%d") == "2026-08-11"
    # B
    assert parsed.iloc[1].strftime("%Y-%m-%d") == "2026-12-25"
    # C
    assert parsed.iloc[2].strftime("%Y-%m-%d") == "2026-08-11"
    # D
    assert parsed.iloc[3].strftime("%Y-%m-%d") == "2026-08-11"
    # E
    assert parsed.iloc[4].strftime("%Y-%m-%d") == "2026-08-11"
    
    # F (blank, None, NaN)
    assert pd.isna(parsed.iloc[5])
    assert pd.isna(parsed.iloc[6])
    assert pd.isna(parsed.iloc[7])
    
    # G (invalid)
    assert pd.isna(parsed.iloc[8])
    
    # H (ambiguous -> defaults to day first)
    assert parsed.iloc[9].strftime("%Y-%m-%d") == "2026-02-01"
