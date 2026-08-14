# Fix Series Ambiguity Error

## Root Cause
The `ValueError: The truth value of a Series is ambiguous` is caused by `map_columns` creating duplicate columns when called multiple times. 
Streamlit calls `map_columns` to render the UI, and then `run_pipeline` calls it a second time. 
Because `map_columns` breaks its alias-search loop upon the *first* match, the first execution renames `"Amount Received (Sub)"` to `"order_amount"`. The second execution no longer finds `"Amount Received (Sub)"` (as it was renamed), so it finds the *second* match `"Mango Price(Sub)"` and renames it to `"order_amount"`.
This results in a DataFrame containing **two** `"order_amount"` columns, causing `sales_df['order_amount'].apply()` to pass a Series to `resolve_amount(x)`, which subsequently crashes on `if pd.isna(x):`.

## Proposed Changes
### `src/inspection.py`
[MODIFY]
Update `map_columns` to be fully idempotent. If a `logical_name` already exists in `df.columns`, skip searching for its aliases entirely.

```python
    for logical_name, alias_list in aliases.items():
        if logical_name in df.columns:
            continue
```

## Verification Plan
1. Add a regression test `test_double_map_columns` in `tests/test_regressions.py` that calls `map_columns` twice and ensures no duplicate columns are created.
2. Run `pytest tests/ -q` to ensure 100% pass rate.
3. Rerun the Playwright UI end-to-end test.
