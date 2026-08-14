import pytest
import pandas as pd
from src.leads import process_leads

def test_process_leads_deduplication():
    df = pd.DataFrame({
        'email': ['test@test.com', 'test@test.com'],
        'registration_date': ['2024-01-01 10:00:00', '2024-01-02 10:00:00'],
        'utm_source': ['FB', 'C1'],
        'utm_medium': ['FB', 'AD1']
    })
    
    sentinels = ['fb', 'facebook']
    
    processed = process_leads(df, sentinels)
    
    assert len(processed) == 1
    # Should pick the one with valid UTM (C1) despite it being later? 
    # Wait, the spec says "select the most recent registration that contains usable UTM data"
    # Actually, in our mock data, 2024-01-02 is more recent, and it has valid UTM.
    assert processed.iloc[0]['utm_source'] == 'C1'

def test_process_leads_fallback_to_invalid_if_no_valid():
    df = pd.DataFrame({
        'email': ['test@test.com', 'test@test.com'],
        'registration_date': ['2024-01-01 10:00:00', '2024-01-02 10:00:00'],
        'utm_source': ['FB', 'FB'],
        'utm_medium': ['FB', 'FB']
    })
    
    sentinels = ['fb', 'facebook']
    
    processed = process_leads(df, sentinels)
    
    assert len(processed) == 1
    # Both invalid, picks the most recent
    assert processed.iloc[0]['registration_date'].strftime('%Y-%m-%d') == '2024-01-02'
