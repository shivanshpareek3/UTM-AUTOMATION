import pytest
import pandas as pd
from src.leads import process_leads

def test_process_leads_deduplication():
    df = pd.DataFrame({
        'email': ['test@test.com', 'test@test.com'],
        'registration_date': ['2026-08-01', '2026-08-05'],
        'campaign': ['ads', 'ads']
    })
    sentinels = ['ads']
    processed = process_leads(df, sentinels)
    # Golden methodology: do not deduplicate here, keep all leads
    assert len(processed) == 2

def test_process_leads_fallback_to_invalid_if_no_valid():
    df = pd.DataFrame({
        'email': ['test@test.com', 'test@test.com'],
        'registration_date': ['2026-08-01', '2026-08-05'],
        'campaign': ['organic', 'direct']
    })
    sentinels = ['ads']
    processed = process_leads(df, sentinels)
    assert len(processed) == 2
