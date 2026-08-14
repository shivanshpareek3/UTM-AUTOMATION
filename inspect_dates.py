import pandas as pd
import warnings
warnings.filterwarnings('ignore')

from src.ingestion import read_file
from src.inspection import load_aliases, map_columns
from src.leads import process_leads

def inspect_dates():
    leads_path = "/Users/apple/Downloads/Lead Sheet Abhishek pal .csv"
    sales_path = "/Users/apple/Downloads/Sales .csv"
    meta1_path = "/Users/apple/Downloads/FML-X-ABHISHEK-PAL-Ad-account-Report.xlsx"
    meta2_path = "/Users/apple/Downloads/Abhishek-Pal-FML-Ad-account-Report.xlsx"
    
    print("Inspecting Leads...")
    l = read_file(leads_path)
    a = load_aliases()
    l = map_columns(l, a)
    l = process_leads(l, ['--'])
    
    if 'registration_date' in l.columns:
        print(f"Leads Min Date: {l['registration_date'].min()}")
        print(f"Leads Max Date: {l['registration_date'].max()}")
        print(f"Total Leads: {len(l)}")
    
    print("\nInspecting Sales...")
    s = read_file(sales_path)
    s = map_columns(s, a)
    if 'sale_date' in s.columns:
        s['sale_date'] = pd.to_datetime(s['sale_date'], errors='coerce')
        print(f"Sales Min Date (if any): {s['sale_date'].min()}")
        print(f"Sales Max Date (if any): {s['sale_date'].max()}")
    else:
        print("Sales has no 'sale_date' column natively.")
    print(f"Total Sales: {len(s)}")
    
    print("\nInspecting Meta 1...")
    m1 = read_file(meta1_path)
    m1 = map_columns(m1, a)
    if 'Day' in m1.columns:
        m1['Day'] = pd.to_datetime(m1['Day'], errors='coerce')
        print(f"Meta 1 Min Date: {m1['Day'].min()}")
        print(f"Meta 1 Max Date: {m1['Day'].max()}")
    print(f"Total Meta 1 rows: {len(m1)}")
    
    print("\nInspecting Meta 2...")
    m2 = read_file(meta2_path)
    m2 = map_columns(m2, a)
    if 'Day' in m2.columns:
        m2['Day'] = pd.to_datetime(m2['Day'], errors='coerce')
        print(f"Meta 2 Min Date: {m2['Day'].min()}")
        print(f"Meta 2 Max Date: {m2['Day'].max()}")
    print(f"Total Meta 2 rows: {len(m2)}")

if __name__ == '__main__':
    inspect_dates()
