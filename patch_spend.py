with open('src/spend.py', 'r') as f:
    content = f.read()

old_camp = """
    window_meta['camp_norm'] = window_meta.get('campaign', window_meta.get('Campaign name', window_meta.get('Campaign Name', pd.Series(dtype=str)))).apply(norm_camp)
"""
# This already handles 'Campaign name'!
if old_camp in content:
    print("spend.py already handles Campaign name correctly!")
