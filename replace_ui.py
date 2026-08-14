import re

with open("app/streamlit_app.py", "r") as f:
    content = f.read()

replacement = """    st.write(f"**Leads:** {len(leads_df)} rows | **Sales:** {len(sales_df)} rows | **Meta Accounts:** {len(meta_dfs)} files")
    
    # Required vs Optional columns
    strict_leads = ['email', 'registration_date', 'campaign', 'ad_set', 'ad_creative']
    opt_leads = ['webinar_type', 'registration_fee']
    strict_sales = ['email', 'sale_date']
    opt_sales = ['order_amount', 'payment_status']
    strict_meta = ['campaign', 'ad_set', 'ad', 'spend', 'Day']
    opt_meta = []
    
    missing_leads = [c for c in (strict_leads + opt_leads) if c not in leads_df.columns]
    missing_sales = [c for c in (strict_sales + opt_sales) if c not in sales_df.columns]
    missing_meta = [c for c in (strict_meta + opt_meta) if c not in meta_df.columns]
    
    needs_mapping = missing_leads or missing_sales or missing_meta
    
    def render_mapping(missing_cols, strict_cols, df, title):
        if not missing_cols: return
        st.subheader(title)
        for req_col in missing_cols:
            is_strict = req_col in strict_cols
            req_label = "*(Required)*" if is_strict else "*(Optional)*"
            
            # Format options with samples
            opts = ['-- Ignore/Missing --']
            for c in df.columns:
                sample_val = str(df[c].dropna().iloc[0])[:30] + '...' if not df[c].dropna().empty else 'empty'
                opts.append(f"{c} (e.g. {sample_val})")
                
            sel = st.selectbox(f"Select column for '{req_col}' {req_label}", options=opts, key=f"{title}_{req_col}")
            
            if sel != '-- Ignore/Missing --':
                actual_col = sel.split(" (e.g.")[0]
                df.rename(columns={actual_col: req_col}, inplace=True)
            else:
                if not is_strict:
                    # Provide safe defaults for optional fields if ignored
                    if req_col == 'webinar_type':
                        df[req_col] = 'unknown'
                        st.info(f"Using default 'unknown' for {req_col}")
                    elif req_col == 'registration_fee':
                        df[req_col] = 0.0
                        st.info(f"Using default 0.0 for {req_col}")
                        
    if needs_mapping:
        st.warning("⚠️ Some columns could not be automatically mapped. Please map them manually below:")
        with st.expander("Manual Column Mapping", expanded=True):
            render_mapping(missing_leads, strict_leads, leads_df, "Leads File Mapping")
            render_mapping(missing_sales, strict_sales, sales_df, "Sales File Mapping")
            render_mapping(missing_meta, strict_meta, meta_df, "Meta Spend File Mapping")
    else:
        st.success("✅ All required columns automatically mapped!")
        
    # Re-check strict columns after mapping
    still_missing_strict = []
    for c in strict_leads:
        if c not in leads_df.columns: still_missing_strict.append(f"Leads: {c}")
    for c in strict_sales:
        if c not in sales_df.columns: still_missing_strict.append(f"Sales: {c}")
    for c in strict_meta:
        if c not in meta_df.columns: still_missing_strict.append(f"Meta: {c}")
        
    st.header("3. Generate Report")
    
    if still_missing_strict:
        st.error(f"❌ Cannot generate report. The following required columns are missing: {', '.join(still_missing_strict)}")
    else:
        if st.button("🚀 Generate Report"):
"""

# Replace the block from `st.write(f"**Leads:...` to `if st.button("🚀 Generate Report"):`
pattern = re.compile(r'    st\.write\(f"\*\*Leads:\*\*.*?if st\.button\("🚀 Generate Report"\):', re.DOTALL)
content = pattern.sub(replacement, content)

with open("app/streamlit_app.py", "w") as f:
    f.write(content)
