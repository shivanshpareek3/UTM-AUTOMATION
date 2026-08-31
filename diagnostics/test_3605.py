import pandas as pd
from src.ingestion import read_file
from src.inspection import load_aliases, map_columns
from src.leads import process_leads

files = [
    '/Users/apple/Downloads/20260825_071521_GlobalJobMasterclass1530328_subscriber.csv',
    '/Users/apple/Downloads/20260829_042031_GlobalJobMasterclass1530328_subscriber.csv',
    '/Users/apple/Downloads/20260815_053436_GlobalJobMasterclass1530328_subscriber.csv'
]

aliases = load_aliases()
settings = {
    'cutoff_date': '2020-01-01',
    'lead_start_date': '2020-01-01',
    'lead_end_date': '2030-01-01'
}

for f in files:
    try:
        df = read_file(f)
        mapped = map_columns(df, aliases)
        processed = process_leads(mapped, settings)
        print(f"File: {f} | Raw rows: {len(df)} | Processed: {len(processed)}")
    except Exception as e:
        print(f"Error on {f}: {e}")
