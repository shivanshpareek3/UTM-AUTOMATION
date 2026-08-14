import re

with open('app/streamlit_app.py', 'r') as f:
    content = f.read()

# 1. Remove old sidebar date limits and validations
# From `st.sidebar.markdown("### Lead Tracking Window (Max 1 Year)")` down to `if (ad_end_date - ad_start_date).days > 7: ... st.stop()`
content = re.sub(
    r'st\.sidebar\.markdown\("### Lead Tracking Window.*?st\.sidebar\.error\("Ads tracking window cannot exceed 7 days\."\)\n    st\.stop\(\)\n',
    '',
    content,
    flags=re.DOTALL
)

# 2. Fix the initial settings block which references those old variables
settings_block = """cutoff_date = st.sidebar.date_input("New vs Old Lead Cutoff Date", pd.to_datetime("2024-01-01"))
fallback_price = st.sidebar.number_input("Fallback Price Per Sale", value=8999.0)
zero_roi_threshold = st.sidebar.number_input("Zero-ROI Waste Threshold", value=5000.0)
currency = st.sidebar.text_input("Currency", "INR")

settings = {
    'report_name': client_name,
    'client_name': client_name,
    'cutoff_date': str(cutoff_date),
    'fallback_price': float(fallback_price),
    'zero_roi_threshold': float(zero_roi_threshold),
    'currency': currency,
    # These will be updated in the main flow
    'sale_date_source': 'Actual Sale Date',
    'payment_status_source': 'Actual Payment Status',
    'amount_source': 'Actual Order Amount',
    'custom_sale_date': None
}
"""

content = re.sub(
    r'cutoff_date = st\.sidebar\.date_input\("New vs Old Lead Cutoff Date".*?\'custom_sale_date\': None\n}',
    settings_block,
    content,
    flags=re.DOTALL
)

# 3. Insert the Date Range detection and UI before Sales Data Resolution
date_ui_block = """    # --- DATE RANGE DETECTION & UI ---
    st.header("3. Report Period Configuration")
    
    import datetime
    from dateutil.relativedelta import relativedelta
    
    lead_min, lead_max, sales_min, sales_max, meta_min, meta_max = pd.NaT, pd.NaT, pd.NaT, pd.NaT, pd.NaT, pd.NaT
    
    if 'registration_date' in leads_df.columns:
        l_dates = pd.to_datetime(leads_df['registration_date'], errors='coerce').dropna()
        if not l_dates.empty: lead_min, lead_max = l_dates.min(), l_dates.max()
            
    if 'sale_date' in sales_df.columns:
        s_dates = pd.to_datetime(sales_df['sale_date'], errors='coerce').dropna()
        if not s_dates.empty: sales_min, sales_max = s_dates.min(), s_dates.max()
            
    if not meta_df.empty and 'Day' in meta_df.columns:
        m_dates = pd.to_datetime(meta_df['Day'], errors='coerce').dropna()
        if not m_dates.empty: meta_min, meta_max = m_dates.min(), m_dates.max()

    st.markdown("### Detected Data Coverage")
    st.write(f"**Leads:** {lead_min.date() if pd.notna(lead_min) else 'None'} → {lead_max.date() if pd.notna(lead_max) else 'None'}")
    st.write(f"**Sales:** {sales_min.date() if pd.notna(sales_min) else 'None'} → {sales_max.date() if pd.notna(sales_max) else 'None'}")
    st.write(f"**Meta Ads:** {meta_min.date() if pd.notna(meta_min) else 'None'} → {meta_max.date() if pd.notna(meta_max) else 'None'}")

    preset = st.selectbox("Quick Period Presets", [
        "Custom", "Today", "Yesterday", "Last 7 Days", "Last 30 Days", "Last 90 Days", 
        "This Month", "Last Month", "This Quarter", "Last Quarter", "Year to Date", "Previous Year", "Full Available Data"
    ])
    
    today = datetime.date.today()
    def_l_start = def_l_end = def_m_start = def_m_end = today
    
    if preset == "Full Available Data":
        valid_ls = [d for d in [lead_min, sales_min] if pd.notna(d)]
        valid_le = [d for d in [lead_max, sales_max] if pd.notna(d)]
        def_l_start = min(valid_ls).date() if valid_ls else today
        def_l_end = max(valid_le).date() if valid_le else today
        def_m_start = meta_min.date() if pd.notna(meta_min) else today
        def_m_end = meta_max.date() if pd.notna(meta_max) else today
    elif preset == "Last 7 Days":
        def_l_start = def_m_start = today - datetime.timedelta(days=7)
    elif preset == "Last 30 Days":
        def_l_start = def_m_start = today - datetime.timedelta(days=30)
    elif preset == "Last 90 Days":
        def_l_start = def_m_start = today - datetime.timedelta(days=90)
    elif preset == "This Month":
        def_l_start = def_m_start = today.replace(day=1)
        nxt = (today.replace(day=28) + datetime.timedelta(days=4))
        def_l_end = def_m_end = nxt - datetime.timedelta(days=nxt.day)
    elif preset == "Last Month":
        last_m = today.replace(day=1) - datetime.timedelta(days=1)
        def_l_start = def_m_start = last_m.replace(day=1)
        def_l_end = def_m_end = last_m
    elif preset == "Year to Date":
        def_l_start = def_m_start = today.replace(month=1, day=1)
    elif preset == "Previous Year":
        def_l_start = def_m_start = today.replace(year=today.year-1, month=1, day=1)
        def_l_end = def_m_end = today.replace(year=today.year-1, month=12, day=31)
    elif preset == "This Quarter":
        q_month = ((today.month - 1) // 3) * 3 + 1
        def_l_start = def_m_start = today.replace(month=q_month, day=1)
    elif preset == "Last Quarter":
        q_month = ((today.month - 1) // 3) * 3 + 1
        last_q = today.replace(month=q_month, day=1) - datetime.timedelta(days=1)
        def_l_start = def_m_start = last_q.replace(month=((last_q.month - 1) // 3) * 3 + 1, day=1)
        def_l_end = def_m_end = last_q
    elif preset == "Yesterday":
        def_l_start = def_l_end = def_m_start = def_m_end = today - datetime.timedelta(days=1)
    elif preset == "Custom":
        pass # use today default
        
    # Use session state to force update if preset changes, but Streamlit native behavior:
    # We will just pass the calculated default values into date_input. 
    # If a user selects a preset, it re-renders with these new values.
    
    col_d1, col_d2 = st.columns(2)
    with col_d1:
        st.markdown("#### LEAD / SALES PERIOD")
        ls_start = st.date_input("Start Date", value=def_l_start, key='ls_start')
        ls_end = st.date_input("End Date", value=def_l_end, key='ls_end')
    with col_d2:
        st.markdown("#### META ADS PERIOD")
        meta_start = st.date_input("Start Date", value=def_m_start, key='m_start')
        meta_end = st.date_input("End Date", value=def_m_end, key='m_end')
        
    if ls_start > ls_end:
        st.error("Lead/Sales Start Date cannot be after End Date.")
        st.stop()
    if meta_start > meta_end:
        st.error("Meta Start Date cannot be after End Date.")
        st.stop()
        
    # Coverage warnings
    cov_leads = "Full"
    cov_sales = "Full"
    cov_meta = "Full"
    
    if pd.notna(lead_min) and (ls_start < lead_min.date() or ls_end > lead_max.date()): cov_leads = "Partial"
    if pd.notna(sales_min) and (ls_start < sales_min.date() or ls_end > sales_max.date()): cov_sales = "Partial"
    if pd.notna(meta_min):
        if meta_start < meta_min.date() or meta_end > meta_max.date():
            cov_meta = "Partial"
            st.warning(f"⚠ Partial Meta Data Coverage: Meta data is available only from {meta_min.date()} to {meta_max.date()}. The report can still be generated, but Meta spend outside this period cannot be calculated.")
    
    settings['report_type'] = preset
    settings['lead_sales_start_date'] = str(ls_start)
    settings['lead_sales_end_date'] = str(ls_end)
    settings['meta_start_date'] = str(meta_start)
    settings['meta_end_date'] = str(meta_end)
    # Backwards compatibility keys
    settings['lead_start_date'] = str(ls_start)
    settings['lead_end_date'] = str(ls_end)
    settings['ad_start_date'] = str(meta_start)
    settings['ad_end_date'] = str(meta_end)
    
    settings['detected_lead_coverage'] = f"{lead_min.date() if pd.notna(lead_min) else 'None'} → {lead_max.date() if pd.notna(lead_max) else 'None'}"
    settings['detected_sales_coverage'] = f"{sales_min.date() if pd.notna(sales_min) else 'None'} → {sales_max.date() if pd.notna(sales_max) else 'None'}"
    settings['detected_meta_coverage'] = f"{meta_min.date() if pd.notna(meta_min) else 'None'} → {meta_max.date() if pd.notna(meta_max) else 'None'}"
    
    if cov_meta == "Partial":
        settings['coverage_status'] = "Partial Meta Coverage"
    else:
        settings['coverage_status'] = f"Leads: {cov_leads}, Sales: {cov_sales}, Meta: {cov_meta}"

    # --- END DATE RANGE DETECTION ---

    st.header("4. Sales Data Resolution")"""

content = content.replace('    st.header("3. Sales Data Resolution")', date_ui_block)
content = content.replace('    st.header("4. Generate Report")', '    st.header("5. Generate Report")')
content = content.replace('                st.header("5. Final Metrics Summary")', '                st.header("6. Final Metrics Summary")')
content = content.replace('                st.header("6. Verification Result")', '                st.header("7. Verification Result")')


with open('app/streamlit_app.py', 'w') as f:
    f.write(content)
