import pandas as pd
from io import BytesIO

with open('/Users/apple/Downloads/12-08-2026_leads.csv', 'rb') as f:
    b = BytesIO(f.read())
    
df_path = pd.read_csv('/Users/apple/Downloads/12-08-2026_leads.csv')
df_bytes = pd.read_csv(b)

print("df_path equal df_bytes?", df_path.equals(df_bytes))
