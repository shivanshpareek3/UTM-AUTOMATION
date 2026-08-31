import pandas as pd

df = pd.read_csv('/Users/apple/Downloads/20260829_042031_GlobalJobMasterclass1530328_subscriber.csv')

print("Total raw leads:", len(df))

# 1. Exact duplicates
exact_dupes = len(df) - len(df.drop_duplicates())
print("Exact row duplicates (all columns match):", exact_dupes)

# 2. Missing emails
missing_email = df['email'].isna().sum() if 'email' in df.columns else 0
print("Missing email:", missing_email)

# 3. Missing both email and phone
df['has_email'] = df['email'].notna() & (df['email'].astype(str).str.strip() != '')
df['has_phone'] = df['phone'].notna() & (df['phone'].astype(str).str.strip() != '')
missing_both = (~df['has_email'] & ~df['has_phone']).sum()
print("Missing BOTH email and phone:", missing_both)

# Let's drop exact duplicates and see
df_dedup = df.drop_duplicates()
print("Total after dropping exact duplicates:", len(df_dedup))
