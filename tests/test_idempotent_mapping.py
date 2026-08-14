import pandas as pd
from src.inspection import map_columns

def test_map_columns_idempotent():
    # Setup aliases
    aliases = {
        "order_amount": ["order amount", "amount", "total"],
        "registration_amount": ["registration amount", "registration fee"]
    }
    
    # Input DataFrame
    df = pd.DataFrame({
        "order amount": [100, 200],
        "Registration Fee": [50, 75],
        "other_col": ["a", "b"]
    })
    
    # First mapping
    mapped_df_1 = map_columns(df, aliases)
    
    # Verify first mapping
    assert "order_amount" in mapped_df_1.columns
    assert "registration_amount" in mapped_df_1.columns
    assert "order amount" not in mapped_df_1.columns
    
    # Second mapping (idempotency check)
    mapped_df_2 = map_columns(mapped_df_1, aliases)
    
    # Should not create duplicate columns
    # Pandas allows duplicate column names, which would result in the series being ambiguous if not handled.
    col_counts = pd.Series(mapped_df_2.columns).value_counts()
    assert col_counts["order_amount"] == 1, "Duplicate order_amount column found!"
    assert col_counts["registration_amount"] == 1, "Duplicate registration_amount column found!"
    
    # Assert DataFrames are fundamentally the same after mapping twice
    assert mapped_df_1.equals(mapped_df_2), "Idempotent mapping failed; dataframes do not match."
