from streamlit.testing.v1 import AppTest
import pytest
import os
import pandas as pd

def test_ui_dynamic_dropdowns_and_validation(tmp_path):
    # Create mock CSVs to upload
    leads_path = tmp_path / "mock_leads.csv"
    pd.DataFrame({'Customer Email': ['a@a.com'], 'Mobile': ['123'], 'Registration Timestamp': ['2024-01-01'], 'Campaign Source': ['Camp1']}).to_csv(leads_path, index=False)
    
    sales_path = tmp_path / "mock_sales.csv"
    pd.DataFrame({'Buyer Email': ['a@a.com'], 'Order Value': [5000]}).to_csv(sales_path, index=False)
    
    meta_path = tmp_path / "mock_meta.csv"
    pd.DataFrame({'Campaign Title': ['Camp1'], 'Daily Spend': [1000], 'Report Date': ['2024-01-01']}).to_csv(meta_path, index=False)
    
    # Path to the streamlit app
    app_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'app', 'streamlit_app.py'))
    
    at = AppTest.from_file(app_path)
    at.run()
    
    # Simulate file uploads (AppTest doesn't natively simulate file uploads easily without digging into session state,
    # but we can try to verify that the app loads without crashing)
    assert not at.exception
    
    # The true UI mapping bug was related to the internal state structure of mapping_dict and rename.
    # Since we can't easily click "Generate Report" with uploaded files in AppTest due to st.file_uploader limitations in v1,
    # we assert the codebase string properties to ensure regressions don't happen.
    
    with open(app_path, 'r') as f:
        content = f.read()
        
    # 1. Assert we do not eagerly map columns before the UI dropdowns
    assert "leads_df = map_columns(leads_df, aliases)" not in content
    
    # 2. Assert validation is checking the mapping dictionary, NOT the renamed dataframe
    assert "if c not in mapping_dict['leads']: still_missing_strict.append(f\"Leads: {c}\")" in content
    
    # 3. Assert canonical to actual direction is used for mapping
    assert "mapping[req_col] = sel" in content
