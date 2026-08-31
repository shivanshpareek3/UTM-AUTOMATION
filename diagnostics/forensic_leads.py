import pandas as pd
import numpy as np

# Load raw file
file_path = '/Users/apple/Downloads/20260829_042031_GlobalJobMasterclass1530328_subscriber.csv'
df_raw = pd.read_csv(file_path)

print(f"Total raw lines: {len(df_raw)}")

# How many are entirely blank?
df_non_empty = df_raw.dropna(how='all')
print(f"After dropping completely blank rows: {len(df_non_empty)}")

# Check how many have a valid email or phone
df_valid_contact = df_non_empty.dropna(subset=['email', 'phone'], how='all')
print(f"After dropping rows with no email AND no phone: {len(df_valid_contact)}")

# Let's count how many have just empty email
df_valid_email = df_non_empty.dropna(subset=['email'])
print(f"Rows with non-empty email: {len(df_valid_email)}")

