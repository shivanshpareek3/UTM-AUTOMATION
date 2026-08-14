import pandas as pd

df1 = pd.read_csv('/Users/apple/Downloads/FML-X-Satyam-2-Campaigns-1-Aug-2026-12-Aug-2026.csv')
df2 = pd.read_csv('/Users/apple/Downloads/SSA-X-SATYAM-KHANDELWAL-Campaigns-1-Aug-2026-12-Aug-2026.csv')

print("DF1 Spend:", df1['Amount spent (INR)'].sum())
print("DF2 Spend:", df2['Amount spent (INR)'].sum())

