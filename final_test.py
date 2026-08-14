import pandas as pd
import sys
import os

from src.ingestion import read_file
from src.inspection import load_aliases, map_columns
from src.pipeline import run_pipeline
import json

def run_test():
    try:
        leads_path = "/Users/apple/Downloads/Lead Sheet Abhishek pal .csv"
        sales_path = "/Users/apple/Downloads/Sales .csv"
        meta1_path = "/Users/apple/Downloads/FML-X-ABHISHEK-PAL-Ad-account-Report.xlsx"
        meta2_path = "/Users/apple/Downloads/Abhishek-Pal-FML-Ad-account-Report.xlsx"
        
        print("Reading files...")
        leads_df = read_file(leads_path)
        sales_df = read_file(sales_path)
        meta1_df = read_file(meta1_path)
        meta2_df = read_file(meta2_path)
        
        leads_loaded = len(leads_df)
        sales_loaded = len(sales_df)
        meta1_rows = len(meta1_df)
        meta2_rows = len(meta2_df)
        
        print(f"Leads loaded: {leads_loaded}")
        print(f"Sales loaded: {sales_loaded}")
        print(f"Meta files loaded: 2")
        print(f"Meta 1 rows: {meta1_rows}")
        print(f"Meta 2 rows: {meta2_rows}")
        
        aliases = load_aliases()
        leads_df = map_columns(leads_df, aliases)
        sales_df = map_columns(sales_df, aliases)
        meta1_df = map_columns(meta1_df, aliases)
        meta2_df = map_columns(meta2_df, aliases)
        
        settings = {
            'report_name': 'Final Test Run',
            'client_name': 'Abhishek Pal',
            'start_date': '2026-01-01',
            'end_date': '2026-12-31',
            'cutoff_date': '2026-01-01',
            'fallback_price': 999.0,
            'zero_roi_threshold': 5000.0,
            'currency': 'INR',
            'sale_date_source': 'Lead Registration Date',
            'payment_status_source': 'Treat All Imported Sales as Successful',
            'amount_source': 'Fallback Price Per Sale',
            'custom_sale_date': None
        }
        
        output_filepath = "/Users/apple/Desktop/UTM automation/output/final_test_report.xlsx"
        os.makedirs(os.path.dirname(output_filepath), exist_ok=True)
        
        metrics, ver_df, xl_path = run_pipeline(
            leads_df, sales_df, [meta1_df, meta2_df], settings, output_filepath
        )
        
        print(f"\nFinal Test Report Metrics:")
        print(f"Total Revenue: {metrics.get('total_revenue')}")
        print(f"Total Meta Spend: {metrics.get('total_spend')}")
        print(f"Total Profit: {metrics.get('profit')}")
        print(f"ROAS: {metrics.get('roas')}")
        
        all_sales = pd.read_excel(xl_path, sheet_name="2. 📋 All Sales (Attributed)")
        excluded_sales = pd.read_excel(xl_path, sheet_name="13. 🚫 Excluded Sales")
        
        unattributed_sales = metrics.get('unattributed_sales', 0)
        attributed_sales = metrics.get('attributed_sales', 0)
        total_valid_sales = metrics.get('total_sales', 0)
        
        print(f"Total Valid Sales Included: {total_valid_sales}")
        print(f"Attributed Sales: {attributed_sales}")
        print(f"Unattributed Sales: {unattributed_sales}")
        print(f"Excluded Sales (Unresolved Dates): {len(excluded_sales[excluded_sales['exclusion_reason'] == 'Unresolved Sale Date']) if 'exclusion_reason' in excluded_sales.columns else 0}")
        
        derived_dates = len(all_sales[all_sales['sale_date_source'] == 'lead_registration_date']) if 'sale_date_source' in all_sales.columns else 0
        assumed_payments = len(all_sales[all_sales['payment_status_source'] == 'assumed_successful']) if 'payment_status_source' in all_sales.columns else 0
        fallback_amounts = len(all_sales[all_sales['amount_source'] == 'fallback_price']) if 'amount_source' in all_sales.columns else 0
        
        print(f"Derived sale dates: {derived_dates}")
        print(f"Assumed-successful payments: {assumed_payments}")
        print(f"Fallback-price sales: {fallback_amounts}")
        
        print(f"\nVerification Result:")
        for idx, row in ver_df.iterrows():
            print(f"{row['Check Name']}: {row['Status']} (Expected: {row['Expected']}, Actual: {row['Actual']})")
        
        print(f"\nExcel file path: {xl_path}")
        
    except Exception as e:
        print(f"Error during execution: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_test()
