import pandas as pd
from src.ingestion import read_file
from src.inspection import load_aliases, map_columns
from src.normalization import normalize_email, normalize_phone, parse_date_series

file_path = '/Users/apple/Downloads/20260829_042031_GlobalJobMasterclass1530328_subscriber.csv'
df = read_file(file_path)
aliases = load_aliases()
df = map_columns(df, aliases)

df['email'] = df['email'].apply(normalize_email)
df['phone'] = df['phone'].apply(normalize_phone)
df['registration_date'] = parse_date_series(df['registration_date'])

df_email_only = df.drop_duplicates(subset=['email'])
df_email_phone = df.drop_duplicates(subset=['email', 'phone'])

dropped = df_email_phone[~df_email_phone.index.isin(df_email_only.index)]

# Date filtering logic from pipeline
settings = {
    'lead_start_date': '2026-08-01',
    'lead_end_date': '2026-08-31'
}
sdt = pd.to_datetime(settings['lead_start_date'])
edt = pd.to_datetime(settings['lead_end_date'])
if edt.hour == 0 and edt.minute == 0 and edt.second == 0:
    edt = edt + pd.Timedelta(days=1, microseconds=-1)

# Inside date window
valid_dates = dropped[(dropped['registration_date'].isna()) | ((dropped['registration_date'] >= sdt) & (dropped['registration_date'] <= edt))]
print(f"Dropped records in date window: {len(valid_dates)}")
for idx, row in valid_dates.iterrows():
    print(f"{row['email']}, {row['phone']}, Date: {row['registration_date']}")
