with open('src/metrics.py', 'r') as f:
    content = f.read()

old_camp = """
        elif 'Campaign Name' in meta_df_copy.columns:
            meta_df_copy['camp_norm'] = meta_df_copy['Campaign Name'].apply(unify_campaign_name)
"""
new_camp = """
        elif 'Campaign Name' in meta_df_copy.columns:
            meta_df_copy['camp_norm'] = meta_df_copy['Campaign Name'].apply(unify_campaign_name)
        elif 'Campaign name' in meta_df_copy.columns:
            meta_df_copy['camp_norm'] = meta_df_copy['Campaign name'].apply(unify_campaign_name)
"""
if old_camp in content:
    content = content.replace(old_camp, new_camp)
    print("Replaced old_camp in metrics.")

with open('src/metrics.py', 'w') as f:
    f.write(content)
