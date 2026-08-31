import pandas as pd
from src.ingestion import read_file
from src.inspection import load_aliases, map_columns
from src.pipeline import run_pipeline

def investigate():
    leads_path = '/Users/apple/Downloads/20260829_042031_GlobalJobMasterclass1530328_subscriber.csv'
    sales_path = '/Users/apple/Downloads/29th Aug - sale.csv'
    meta1_path = '/Users/apple/Downloads/Abhishek-Pal-X-FML-22-28th-Aug.csv'
    meta2_path = '/Users/apple/Downloads/FML-X-Abhishek-Pal-22-28-Aug.csv'
    
    print("Loading data...")
    leads_df = read_file(leads_path)
    sales_df = read_file(sales_path)
    meta_df1 = read_file(meta1_path)
    meta_df2 = read_file(meta2_path)
    
    print(f"Raw Leads Count: {len(leads_df)}")
    
    # Let's see what happens during mapping
    aliases = load_aliases()
    leads_mapped = map_columns(leads_df, aliases)
    sales_mapped = map_columns(sales_df, aliases)
    meta1_mapped = map_columns(meta_df1, aliases)
    meta2_mapped = map_columns(meta_df2, aliases)
    
    print(f"Mapped Leads Count: {len(leads_mapped)}")
    
    settings = {
        'report_name': 'Final Recon',
        'client_name': 'Abhishek Pal',
        'cutoff_date': '2026-08-01',
        'funnel_type': 'Paid',
        'fallback_price': 8999.0,
        'paid_funnel_price': 8999.0,
        'zero_roi_threshold': 5000.0,
        'currency': 'INR',
        'sale_date_source': 'Actual Sale Date',
        'payment_status_source': 'Actual Payment Status',
        'amount_source': 'Actual Order Amount',
        'lead_sales_start_date': '2026-08-22',
        'lead_sales_end_date': '2026-08-28',
        'meta_start_date': '2026-08-22',
        'meta_end_date': '2026-08-28',
        'lead_start_date': '2026-08-22',
        'lead_end_date': '2026-08-28',
        'ad_start_date': '2026-08-22',
        'ad_end_date': '2026-08-28'
    }
    
    # We want to see exact exclusions. 
    # The pipeline does:
    # process_leads
    # filter_by_date
    from src.leads import process_leads
    from src.normalization import parse_date_series
    
    processed = process_leads(leads_mapped.copy(), ['paid', 'cpc', 'cpm', 'facebook'])
    print(f"After process_leads: {len(processed)}")
    
    if 'registration_date' in processed.columns:
        processed['date_col'] = parse_date_series(processed['registration_date'])
        
        # Check NaT
        nat_count = processed['date_col'].isna().sum()
        print(f"Blank/invalid dates: {nat_count}")
        
        # Check out of bounds
        out_of_bounds = processed[(processed['date_col'] < '2026-08-22') | (processed['date_col'] > '2026-08-28')]
        print(f"Out of bounds dates: {len(out_of_bounds)}")
        
        in_bounds = processed[(processed['date_col'] >= '2026-08-22') & (processed['date_col'] <= '2026-08-28')]
        print(f"In bounds dates: {len(in_bounds)}")
        
    print("\nRunning full pipeline to generate Reconciliation Table:")
    metrics, ver_df, xl = run_pipeline(leads_mapped, sales_mapped, [meta1_mapped, meta2_mapped], settings, 'output/final_golden.xlsx')
    

if __name__ == "__main__":
    investigate()
