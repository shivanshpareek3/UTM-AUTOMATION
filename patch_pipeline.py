import re

with open('src/pipeline.py', 'r') as f:
    content = f.read()

# Fix the date filtering at line 256
old_filter = """
        if 'Day' in meta_df.columns:
            range_df = parse_date_range(meta_df['Day'])
            mask = (range_df['start_date'] <= edt) & (range_df['end_date'] >= sdt)
            window_meta = meta_df[mask].copy()
"""

new_filter = """
        if 'Day' in meta_df.columns:
            range_df = parse_date_range(meta_df['Day'])
            
            # Check for 'Reporting ends' to fill end_date, matching line 91 logic
            end_cols = [c for c in meta_df.columns if str(c).lower().strip() == 'reporting ends']
            if end_cols:
                end_range = parse_date_range(meta_df[end_cols[0]])
                range_df['end_date'] = end_range['end_date'].fillna(range_df['end_date'])
                
            mask = (range_df['start_date'] <= edt) & (range_df['end_date'] >= sdt)
            window_meta = meta_df[mask].copy()
"""
if old_filter in content:
    content = content.replace(old_filter, new_filter)
    print("Replaced old_filter.")
else:
    print("old_filter not found!")

# Fix the Campaign name casing logic in pipeline.py
old_camp = """
        elif 'Campaign Name' in window_meta.columns:
            window_meta['camp_norm'] = window_meta['Campaign Name'].apply(unify_campaign_name)
"""
new_camp = """
        elif 'Campaign Name' in window_meta.columns:
            window_meta['camp_norm'] = window_meta['Campaign Name'].apply(unify_campaign_name)
        elif 'Campaign name' in window_meta.columns:
            window_meta['camp_norm'] = window_meta['Campaign name'].apply(unify_campaign_name)
"""
if old_camp in content:
    content = content.replace(old_camp, new_camp)
    print("Replaced old_camp in pipeline.")

with open('src/pipeline.py', 'w') as f:
    f.write(content)
