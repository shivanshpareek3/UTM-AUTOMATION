import pytest
import pandas as pd
import os
from src.workbook import generate_workbook
from src.verification import run_verification

def test_generate_workbook(tmp_path):
    settings_df = pd.DataFrame({'Key': ['Report Name'], 'Value': ['Test']})
    sales_df = pd.DataFrame({'sale_id': [1], 'total_revenue': [100.0], 'attributed_spend': [50.0], 'attribution_source': ['Sales Sheet UTM']})
    camp_sum = pd.DataFrame({'Node Name': ['C1'], 'Sales': [1], 'Revenue': [100.0], 'Spend': [50.0]})
    adset_sum = pd.DataFrame({'Node Name': ['C1>A1'], 'Sales': [1], 'Revenue': [100.0], 'Spend': [50.0]})
    ad_sum = pd.DataFrame({'Node Name': ['C1>A1>AD1'], 'Sales': [1], 'Revenue': [100.0], 'Spend': [50.0]})
    
    ver_df = run_verification(
        input_sales_count=1,
        excluded_sales_count=0,
        all_sales_df=sales_df,
        camp_summary=camp_sum,
        adset_summary=adset_sum,
        ad_summary=ad_sum,
        total_windowed_meta_spend=50.0,
        duplicate_sales_emails=0,
        total_leads_in_window=1,
        funnel_leads_counted=1,
        leads_sheet_reg_revenue=0.0
    )
    
    data = {
        "1. ⚙ Settings & Run Log": settings_df,
        "2. 📋 All Sales (Attributed)": sales_df,
        "3. 📢 Campaign Summary": camp_sum,
        "4. 🎯 Ad Set Summary": adset_sum,
        "5. 🎨 Ad Creative Summary": ad_sum,
        "12. ✅ Verification": ver_df
    }
    
    out_file = tmp_path / "report.xlsx"
    generate_workbook(str(out_file), data)
    
    assert os.path.exists(out_file)
    
    # Verify we can read it back and all sheets are there
    excel_file = pd.ExcelFile(out_file)
    assert "1. ⚙ Settings & Run Log" in excel_file.sheet_names
    assert "12. ✅ Verification" in excel_file.sheet_names
    
    read_ver = pd.read_excel(out_file, sheet_name="12. ✅ Verification")
    assert not read_ver.empty
    
    # All our dummy data should PASS
    assert (read_ver['Status'] == 'PASS').all()
