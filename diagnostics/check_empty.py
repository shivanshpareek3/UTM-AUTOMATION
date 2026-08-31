import pandas as pd

file_path = '/Users/apple/Downloads/20260829_042031_GlobalJobMasterclass1530328_subscriber.csv'
df = pd.read_csv(file_path)

# Let's count completely null rows in 'email', 'name', 'phone'
df_clean = df.dropna(subset=['email', 'name', 'phone'], how='all')
print(f"After dropping rows with no email, name, or phone: {len(df_clean)}")

df_clean2 = df.dropna(subset=['email'])
print(f"Rows with email: {len(df_clean2)}")

# What about completely blank emails but not NaN?
blank_emails = df[df['email'].astype(str).str.strip() == '']
print(f"Blank string emails: {len(blank_emails)}")
