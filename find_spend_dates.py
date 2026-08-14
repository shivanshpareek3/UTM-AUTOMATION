import pandas as pd
from src.ingestion import read_file

m1 = read_file('/Users/apple/Downloads/Abhishek-Pal-FML-Ad-account-Report.xlsx')
m2 = read_file('/Users/apple/Downloads/FML-X-ABHISHEK-PAL-Ad-account-Report.xlsx')

def process_meta(m_df, name):
    if 'Reporting Starts' in m_df.columns:
        date_col = 'Reporting Starts'
    elif 'Day' in m_df.columns:
        date_col = 'Day'
    else:
        return
    
    m_df[date_col] = pd.to_datetime(m_df[date_col], errors='coerce')
    spend_col = 'Amount Spent' if 'Amount Spent' in m_df.columns else 'spend'
    if spend_col not in m_df.columns:
        return
        
    summary = m_df.groupby(m_df[date_col].dt.date)[spend_col].sum().reset_index()
    summary = summary[summary[spend_col] > 0].sort_values(date_col)
    
    print(f"\n--- Spend for {name} ---")
    for _, row in summary.head(10).iterrows():
        print(f"{row[date_col]}: {row[spend_col]}")

process_meta(m1, 'Abhishek-Pal-FML-Ad-account-Report')
process_meta(m2, 'FML-X-ABHISHEK-PAL-Ad-account-Report')
