import pandas as pd
from src.ingestion import read_file
from src.inspection import load_aliases, map_columns
leads_df = read_file('/Users/apple/Downloads/20260825_071521_GlobalJobMasterclass1530328_subscriber.csv')
meta_df = read_file('/Users/apple/Downloads/FML-X-ABHISHEK-PAL-Campaigns-15-Aug-2026-21-Aug-2026.csv')
aliases = load_aliases()
l_map = map_columns(leads_df, aliases)
m_map = map_columns(meta_df, aliases)
l_c = set(l_map['campaign'].dropna().str.lower().str.strip().unique())
m_c = set(m_map['campaign'].dropna().str.lower().str.strip().unique())
print("Intersection:", l_c.intersection(m_c))
