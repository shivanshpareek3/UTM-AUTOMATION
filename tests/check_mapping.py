from src.ingestion import read_file
from src.inspection import load_aliases, map_columns
leads_df = read_file('/Users/apple/Downloads/20260825_071521_GlobalJobMasterclass1530328_subscriber.csv')
aliases = load_aliases()
mapped = map_columns(leads_df, aliases)
print("Mapped columns:", list(mapped.columns))
print("Head:", mapped[['campaign']].head(2))
