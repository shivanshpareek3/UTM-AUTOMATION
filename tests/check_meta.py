from src.ingestion import read_file
from src.inspection import load_aliases, map_columns
meta_df = read_file('/Users/apple/Downloads/FML-X-ABHISHEK-PAL-Campaigns-15-Aug-2026-21-Aug-2026.csv')
aliases = load_aliases()
mapped = map_columns(meta_df, aliases)
print("Mapped columns:", list(mapped.columns))
print("Head:", mapped[['campaign', 'spend']].head(2))
