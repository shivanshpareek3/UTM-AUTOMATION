import pandas as pd
from src.ingestion import read_file
from src.inspection import load_aliases, map_columns
from src.normalization import normalize_email, normalize_phone, parse_date_series

print("Script created")
