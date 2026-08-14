import pandas as pd
import sys
from src.ingestion import read_file

def audit_meta_and_sales(leads_path, sales_path, meta1_path, meta2_path):
    print("--- Meta 1 ---")
    m1 = read_file(meta1_path)
    print(f"File 1 Rows: {len(m1)}")
    print(f"Columns: {m1.columns.tolist()}")
    print(m1.head(10))
         
    # Check for summary rows (e.g., Campaign Name is empty or 'Total')
    if 'Campaign name' in m1.columns:
         summary_rows = m1[m1['Campaign name'].isna()]
         print(f"Summary rows found: {len(summary_rows)}")
         if len(summary_rows) > 0:
             print(summary_rows)
             
    print("\n--- Meta 2 ---")
    m2 = read_file(meta2_path)
    print(f"File 2 Rows: {len(m2)}")
    print(f"Columns: {m2.columns.tolist()}")
    if 'Amount spent (INR)' in m2.columns:
        print(f"Total Amount Spent: {m2['Amount spent (INR)'].sum()}")
    elif 'Amount Spent' in m2.columns:
         print(f"Total Amount Spent: {m2['Amount Spent'].sum()}")
    else:
         print("No Amount Spent column found.")
         
    if 'Campaign name' in m2.columns:
         summary_rows = m2[m2['Campaign name'].isna()]
         print(f"Summary rows found: {len(summary_rows)}")
         if len(summary_rows) > 0:
             print(summary_rows)

    print("\n--- Sales File ---")
    s = pd.read_csv(sales_path)
    print(f"Sales Rows: {len(s)}")
    print(f"Sales Columns: {s.columns.tolist()}")
    if 'order_amount' in s.columns:
        print(f"Total actual order_amount: {s['order_amount'].sum()}")
    else:
        print("No order_amount column found in raw Sales.")

if __name__ == '__main__':
    audit_meta_and_sales(
        sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
    )
