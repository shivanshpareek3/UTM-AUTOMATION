import pandas as pd
import json

from src.ingestion import read_file
from src.inspection import load_aliases, map_columns

def run():
    leads_path = '/Users/apple/Downloads/12-08-2026_leads.csv'
    sales_path = '/Users/apple/Downloads/12-08-2026_sales(1).csv'
    meta_paths = [
        '/Users/apple/Downloads/FML-X-Satyam-2-Campaigns-1-Aug-2026-12-Aug-2026.csv',
        '/Users/apple/Downloads/SSA-X-SATYAM-KHANDELWAL-Campaigns-1-Aug-2026-12-Aug-2026.csv'
    ]

    leads_df = read_file(leads_path)
    sales_df = read_file(sales_path)
    meta_df1 = read_file(meta_paths[0])
    meta_df2 = read_file(meta_paths[1])
    meta_df = pd.concat([meta_df1, meta_df2], ignore_index=True)

    aliases = load_aliases()
    
    # 1 & 2. META SPEND VERIFICATION
    print("==================================================")
    print("1 & 2. META SPEND VERIFICATION")
    print("==================================================")
    print(f"Meta Files: FML..., SSA...")
    print(f"Meta columns before mapping: {meta_df.columns.tolist()}")
    
    meta_mapped = map_columns(meta_df, aliases)
    print(f"Meta columns after mapping: {meta_mapped.columns.tolist()}")
    
    if 'Day' in meta_mapped.columns:
        date_col = 'Day'
    else:
        date_col = 'Unknown'
        
    if 'spend' in meta_mapped.columns:
        spend_col = 'spend'
    elif 'Amount Spent' in meta_mapped.columns:
        spend_col = 'Amount Spent'
    elif 'Amount Spent (INR)' in meta_df.columns:
        spend_col = 'Amount Spent (INR)'
    else:
        spend_col = 'Unknown'
        
    print(f"Detected Date Column: {date_col}")
    print(f"Detected Spend Column: {spend_col}")
    
    if date_col != 'Unknown' and spend_col != 'Unknown':
        meta_mapped[date_col] = pd.to_datetime(meta_mapped[date_col], errors='coerce')
        min_date = meta_mapped[date_col].min()
        max_date = meta_mapped[date_col].max()
        print(f"Min Date: {min_date}, Max Date: {max_date}")
        print(f"Total Rows Before Filter: {len(meta_mapped)}")
        print(f"Total Spend Before Filter: {meta_mapped[spend_col].sum()}")
        
        mask1 = (meta_mapped[date_col] >= '2026-08-01') & (meta_mapped[date_col] <= '2026-08-12')
        print(f"Rows after Aug 1-12 filter: {mask1.sum()}")
        print(f"Spend after Aug 1-12 filter: {meta_mapped.loc[mask1, spend_col].sum()}")
        
        mask2 = (meta_mapped[date_col] >= '2026-08-05') & (meta_mapped[date_col] <= '2026-08-10')
        print(f"Rows after Aug 5-10 filter: {mask2.sum()}")
        print(f"Spend after Aug 5-10 filter: {meta_mapped.loc[mask2, spend_col].sum()}")
        
        print("\nChecking exact spend rows...")
        print("Raw Spend Sum:", meta_mapped[spend_col].sum())
        
        # Why is pipeline giving 441,121.7?
        # Let's check what `map_columns` did.
        print("\nIs it possible map_columns created duplicates of spend?")
        print(meta_mapped[[c for c in meta_mapped.columns if 'spend' in c.lower() or 'amount' in c.lower()]].head())
        
        # Checking sum across the multiple spend columns
        for col in [c for c in meta_mapped.columns if 'spend' in c.lower()]:
            print(f"Sum of {col}: {meta_mapped[col].sum()}")

    # 3. LEAD DATE FILTER VERIFICATION
    print("\n==================================================")
    print("3. LEAD DATE FILTER VERIFICATION")
    print("==================================================")
    leads_mapped = map_columns(leads_df, aliases)
    if 'registration_date' in leads_mapped.columns:
        leads_mapped['registration_date'] = pd.to_datetime(leads_mapped['registration_date'], errors='coerce')
        min_ldate = leads_mapped['registration_date'].min()
        max_ldate = leads_mapped['registration_date'].max()
        print(f"Detected Lead Date Column: registration_date")
        print(f"Min Date: {min_ldate}, Max Date: {max_ldate}")
        print(f"Total Rows Before Filter: {len(leads_mapped)}")
        
        mask1 = (leads_mapped['registration_date'] >= '2026-08-01') & (leads_mapped['registration_date'] <= '2026-08-12')
        print(f"Rows for Aug 1-12: {mask1.sum()}")
        mask2 = (leads_mapped['registration_date'] >= '2026-08-05') & (leads_mapped['registration_date'] <= '2026-08-10')
        print(f"Rows for Aug 5-10: {mask2.sum()}")
        print(f"Rows outside Aug 1-12: {(~mask1).sum()}")
    else:
        print("No registration_date found.")

    # 4. SALES DATE FILTER VERIFICATION
    print("\n==================================================")
    print("4. SALES DATE FILTER VERIFICATION")
    print("==================================================")
    sales_mapped = map_columns(sales_df, aliases)
    if 'sale_date' in sales_mapped.columns:
        sales_mapped['sale_date'] = pd.to_datetime(sales_mapped['sale_date'], errors='coerce')
        mask1 = (sales_mapped['sale_date'] >= '2026-08-01') & (sales_mapped['sale_date'] <= '2026-08-12')
        mask2 = (sales_mapped['sale_date'] >= '2026-08-05') & (sales_mapped['sale_date'] <= '2026-08-10')
        print(f"Total Sales Rows: {len(sales_mapped)}")
        print(f"Sales inside Aug 1-12: {mask1.sum()}")
        print(f"Sales inside Aug 5-10: {mask2.sum()}")
        
    # 5. PAID / UNPAID VERIFICATION
    print("\n==================================================")
    print("5. PAID / UNPAID VERIFICATION")
    print("==================================================")
    with open('config/settings.json', 'r') as f:
        settings = json.load(f)
    paid_markers = settings.get('paid_markers', [])
    
    def get_paid_marker(row):
        for col in ['utm_medium', 'utm_source', 'campaign', 'source']:
            if col in row and pd.notna(row[col]):
                val = str(row[col]).lower()
                for marker in paid_markers:
                    if marker in val:
                        return f"Marker: '{marker}' in {col} ({val})"
        return "Unpaid"

    leads_mapped['classification'] = leads_mapped.apply(get_paid_marker, axis=1)
    print("Lead Classification Breakdown:")
    breakdown = leads_mapped['classification'].value_counts()
    print(breakdown)
    print(f"Total Leads: {len(leads_mapped)}, Sum of Breakdown: {breakdown.sum()}")

    # 7. REGISTRATION AMOUNT VERIFICATION
    print("\n==================================================")
    print("7. REGISTRATION AMOUNT VERIFICATION")
    print("==================================================")
    print("Leads Headers:", leads_df.columns.tolist())
    print("Sales Headers:", sales_df.columns.tolist())
    
    # 6. REVENUE VERIFICATION
    print("\n==================================================")
    print("6. REVENUE VERIFICATION")
    print("==================================================")
    if 'order_amount' in sales_mapped.columns:
        print(f"Total Raw Order Amount Sum: {sales_mapped['order_amount'].sum()}")
        print(f"Sum in Aug 1-12: {sales_mapped.loc[mask1, 'order_amount'].sum()}")
        print(f"Sum in Aug 5-10: {sales_mapped.loc[mask2, 'order_amount'].sum()}")
        print(f"Missing order_amount rows: {sales_mapped['order_amount'].isna().sum()}")
        print(f"Zero order_amount rows: {(sales_mapped['order_amount'] == 0).sum()}")

if __name__ == '__main__':
    run()
