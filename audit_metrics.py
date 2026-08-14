import pandas as pd
import json
import warnings
warnings.filterwarnings('ignore')

from src.ingestion import read_file
from src.pipeline import run_pipeline

def run_audit():
    leads_path = '/Users/apple/Downloads/12-08-2026_leads.csv'
    sales_path = '/Users/apple/Downloads/12-08-2026_sales(1).csv'
    meta_paths = [
        '/Users/apple/Downloads/FML-X-Satyam-2-Campaigns-1-Aug-2026-12-Aug-2026.csv',
        '/Users/apple/Downloads/SSA-X-SATYAM-KHANDELWAL-Campaigns-1-Aug-2026-12-Aug-2026.csv'
    ]

    leads_df = read_file(leads_path)
    sales_df = read_file(sales_path)
    meta_dfs = [read_file(p) for p in meta_paths]

    with open('config/settings.json', 'r') as f:
        settings_base = json.load(f)
        
    settings_base['amount_source'] = 'Actual Order Amount'
    settings_base['sale_date_source'] = 'Actual Sale Date'
    settings_base['payment_status_source'] = 'Actual Payment Status'
    
    # Check registration amounts in leads
    # print columns for context
    print("Leads columns:", leads_df.columns.tolist())
    
    def run_report(start_date, end_date, name):
        s = settings_base.copy()
        s['report_name'] = name
        s['lead_sales_start_date'] = start_date
        s['lead_sales_end_date'] = end_date
        s['meta_start_date'] = start_date
        s['meta_end_date'] = end_date
        
        metrics, ver_df, path = run_pipeline(leads_df.copy(), sales_df.copy(), [m.copy() for m in meta_dfs], s, f"output/{name}.xlsx")
        
        # Invariants Check
        print(f"\n==============================================")
        print(f"REPORT: {name} ({start_date} -> {end_date})")
        print(f"==============================================")
        
        print("\n1. LEADS & FUNNEL")
        print(f"Total Leads: {metrics['total_leads']}")
        print(f"Paid Leads: {metrics['paid_leads']}")
        print(f"Unpaid Leads: {metrics['unpaid_leads']}")
        print(f"Paid Funnel %: {metrics['paid_funnel_percent']}")
        print(f"Unpaid Funnel %: {metrics['unpaid_funnel_percent']}")
        
        print("\n2. SALES & REVENUE")
        print(f"Total Sales: {metrics['total_sales']}")
        print(f"Attributed Sales: {metrics['attributed_sales']}")
        print(f"Unattributed Sales: {metrics['unattributed_sales']}")
        print(f"Per Sale Value: {metrics.get('per_sale_value', 'N/A')}")
        print(f"Attributed Per Sale Value: {metrics.get('attributed_per_sale_value', 'N/A')}")
        print(f"Sales Revenue: {metrics['backend_revenue']}")
        print(f"Registration Revenue: {metrics['total_reg_revenue']}")
        print(f"Total Revenue: {metrics['total_revenue']}")
        print(f"Attributed Revenue: {metrics['attributed_revenue']}")
        print(f"Unattributed Revenue: {metrics['unattributed_revenue']}")
        
        print("\n3. META SPEND & ATTRIBUTION")
        print(f"Raw Meta Spend: {metrics['raw_meta_spend']}")
        print(f"Attributed Spend: {metrics['attributed_spend']}")
        print(f"Unallocated Spend: {metrics['unallocated_spend']}")
        print(f"Spend Attribution %: {metrics['spend_attribution_rate']}")
        
        print("\n4. FINANCIAL PERFORMANCE")
        print(f"Profit: {metrics['profit']}")
        print(f"ROAS: {metrics['roas']}")
        print(f"ROI %: {metrics['roi_percent']}")
        print(f"CAC: {metrics['cac']}")
        
        print("\n--- INVARIANTS CHECK ---")
        print(f"Leads match (Total == Paid + Unpaid): {metrics['total_leads'] == metrics['paid_leads'] + metrics['unpaid_leads']}")
        print(f"Sales match (Total == Attr + Unattr): {metrics['total_sales'] == metrics['attributed_sales'] + metrics['unattributed_sales']}")
        print(f"Spend constraint (Attr <= Raw): {round(metrics['attributed_spend'], 2) <= round(metrics['raw_meta_spend'], 2)}")
        print(f"Revenue constraint (Attr <= Total): {metrics['attributed_revenue'] <= metrics['total_revenue']}")
        
        prof = metrics['attributed_revenue'] - metrics['attributed_spend']
        print(f"Profit matches formula: {round(metrics['profit'], 2) == round(prof, 2)}")
        
        roas = metrics['attributed_revenue'] / metrics['attributed_spend'] if metrics['attributed_spend'] > 0 else 'N/A'
        print(f"ROAS matches formula: {metrics['roas'] == roas}")
        
        roi = prof / metrics['attributed_spend'] * 100 if metrics['attributed_spend'] > 0 else 'N/A'
        print(f"ROI matches formula: {metrics['roi_percent'] == roi}")
        
        cac = metrics['attributed_spend'] / metrics['attributed_sales'] if metrics['attributed_spend'] > 0 and metrics['attributed_sales'] > 0 else 'N/A'
        print(f"CAC matches formula: {metrics['cac'] == cac}")

    run_report('2026-08-01', '2026-08-12', 'audit_report_1')
    run_report('2026-08-05', '2026-08-10', 'audit_report_2')

if __name__ == '__main__':
    run_audit()
