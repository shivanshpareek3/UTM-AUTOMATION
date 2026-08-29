import streamlit as st
import pandas as pd
import json
import os
import sys

# Ensure src modules can be imported
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.ingestion import read_file, read_stream
from src.normalization import parse_date_series, parse_date_range
from src.pipeline import run_pipeline

st.set_page_config(page_title="UTM Sales Attribution Generator", layout="wide")

st.title("🚀 UTM Sales Attribution & Profitability Report Generator")

# State initialization
if 'reset_key' not in st.session_state:
    st.session_state.reset_key = 0

# Session state init for prices to maintain state across type changes
if 'fallback_price' not in st.session_state:
    st.session_state.fallback_price = 8999.0
if 'paid_funnel_price' not in st.session_state:
    st.session_state.paid_funnel_price = 8999.0

# Sidebar settings
st.sidebar.header("⚙ Settings")
client_name = st.sidebar.text_input("Client / Report Name", "Antigravity Default")

cutoff_date = st.sidebar.date_input("New vs Old Lead Cutoff Date", pd.to_datetime("2024-01-01"))
funnel_type = st.sidebar.radio("Funnel Type", ["Paid", "Free"])

if funnel_type == "Paid":
    paid_funnel_price = st.sidebar.number_input("Paid Funnel Price Per Sale", value=st.session_state.paid_funnel_price)
    st.session_state.paid_funnel_price = paid_funnel_price
else:
    paid_funnel_price = st.session_state.paid_funnel_price

fallback_price = st.sidebar.number_input("Fallback Price Per Sale", value=st.session_state.fallback_price)
st.session_state.fallback_price = fallback_price

zero_roi_threshold = st.sidebar.number_input("Zero-ROI Waste Threshold", value=5000.0)
currency = st.sidebar.text_input("Currency", "INR")

settings = {
    'report_name': client_name,
    'client_name': client_name,
    'cutoff_date': str(cutoff_date),
    'funnel_type': funnel_type,
    'fallback_price': float(fallback_price),
    'paid_funnel_price': float(paid_funnel_price),
    'zero_roi_threshold': float(zero_roi_threshold),
    'currency': currency,
    # These will be updated in the main flow
    'sale_date_source': 'Actual Sale Date',
    'payment_status_source': 'Actual Payment Status',
    'amount_source': 'Actual Order Amount',
    'custom_sale_date': None
}


# Main Layout
st.header("1. Upload Files")

col1, col2, col3 = st.columns(3)

with col1:
    leads_file = st.file_uploader("Leads File (CSV/XLSX)", type=['csv', 'xlsx'], key=f'leads_{st.session_state.reset_key}')
with col2:
    sales_file = st.file_uploader("Sales File (CSV/XLSX)", type=['csv', 'xlsx'], key=f'sales_{st.session_state.reset_key}')
with col3:
    meta_files = st.file_uploader("Meta Spend Files (CSV/XLSX)", type=['csv', 'xlsx'], accept_multiple_files=True, key=f'meta_{st.session_state.reset_key}')

if st.button("🔄 Reset / Clear"):
    # Preserve reset_key so we can increment it
    current_reset = st.session_state.reset_key
    st.session_state.clear()
    st.session_state.reset_key = current_reset + 1
    st.rerun()

def load_df(uploaded_file):
    if uploaded_file is None:
        return None
    try:
        return read_stream(uploaded_file, uploaded_file.name)
    except Exception as e:
        st.error(f"Error reading {uploaded_file.name}: {str(e)}")
        return None

if leads_file and sales_file and meta_files:
    leads_df = load_df(leads_file)
    sales_df = load_df(sales_file)
    meta_dfs = [load_df(f) for f in meta_files if f is not None]
    
    meta_df = pd.concat(meta_dfs, ignore_index=True) if meta_dfs else pd.DataFrame()
        
    # --- NOW DO INSPECTION UI (SECTION 2) ---
    st.header("2. Input Inspection & Column Mapping")
    
    st.write(f"**Leads:** {len(leads_df)} rows | **Sales:** {len(sales_df)} rows | **Meta Accounts:** {len(meta_dfs)} files")
    
    # ---------------------------------------------------------
    # STATE MANAGEMENT FOR FILE CHANGES
    # ---------------------------------------------------------
    # Use name and size instead of file_id because Streamlit frequently regenerates file_id on button clicks
    current_file_ids = (
        getattr(leads_file, "name", "none") + str(getattr(leads_file, "size", 0)),
        getattr(sales_file, "name", "none") + str(getattr(sales_file, "size", 0)),
        tuple(getattr(m, "name", "none") + str(getattr(m, "size", 0)) for m in meta_files) if meta_files else ()
    )
    
    if "last_file_ids" not in st.session_state or st.session_state.last_file_ids != current_file_ids:
        # Clear mapping state
        keys_to_delete = [k for k in st.session_state.keys() if k.startswith("map_") or k.startswith("active_")]
        for k in keys_to_delete:
            del st.session_state[k]
        st.session_state.last_file_ids = current_file_ids

    # ---------------------------------------------------------
    # MAPPING UI
    # ---------------------------------------------------------
    strict_leads = ['email', 'registration_date', 'campaign', 'ad_set', 'ad_creative']
    opt_leads = ['name', 'webinar_type', 'registration_fee', 'phone', 'source', 'lead_status']
    strict_sales = ['email']
    opt_sales = ['name', 'phone', 'sale_date', 'order_amount', 'payment_status', 'order_id']
    strict_meta = ['campaign', 'spend', 'Date']
    opt_meta = ['ad_set', 'ad', 'Reporting starts', 'Reporting ends']
    
    mapping_dict = {'leads': {}, 'sales': {}, 'meta': []}
    
    def render_mapping_section(req_cols, df, section_title, prefix):
        st.markdown(f"### {section_title}")
        
        active_key = f"active_{prefix}"
        if active_key not in st.session_state:
            st.session_state[active_key] = req_cols[0][0]
            
        req_col_names = [c[0] for c in req_cols]
        
        col1, col2 = st.columns([1, 1])
        
        mapping = {}
        with col1:
            st.markdown("#### 1. Select Field to Map")
            active_field = st.radio(
                "Canonical Fields:", 
                options=req_col_names,
                key=f"radio_{prefix}",
                format_func=lambda x: f"{x} {'*(Required)*' if dict(req_cols)[x] else '*(Optional)*'}"
            )
            st.session_state[active_key] = active_field
            
            st.markdown("#### Current Mappings")
            for req_col, is_strict in req_cols:
                mapped_col = st.session_state.get(f"map_{prefix}_{req_col}")
                # Ensure the mapped column actually exists in the current dataframe
                if mapped_col and mapped_col not in df.columns:
                    del st.session_state[f"map_{prefix}_{req_col}"]
                    mapped_col = None
                    
                if mapped_col:
                    mapping[req_col] = mapped_col
                    col_a, col_b = st.columns([3, 1])
                    col_a.success(f"**{req_col}** ➔ `{mapped_col}`")
                    if col_b.button("Clear", key=f"clear_{prefix}_{req_col}"):
                        del st.session_state[f"map_{prefix}_{req_col}"]
                        st.rerun()
                else:
                    req_label = "*(Required)*" if is_strict else "*(Optional)*"
                    st.warning(f"**{req_col}** {req_label} ➔ Not mapped")
                    
        with col2:
            st.markdown(f"#### 2. Click Actual Column to Assign to **{active_field}**")
            st.markdown("*(Scroll if many columns)*")
            container = st.container(height=400)
            
            def assign_col(c, pfx, af):
                st.session_state[f"map_{pfx}_{af}"] = c
                
            for c in df.columns:
                is_mapped = False
                mapped_to = None
                for req_col, _ in req_cols:
                    if st.session_state.get(f"map_{prefix}_{req_col}") == c:
                        is_mapped = True
                        mapped_to = req_col
                        break
                
                if is_mapped:
                    container.button(f"✅ {c} (Mapped to {mapped_to})", key=f"btn_{prefix}_{c}", disabled=True)
                else:
                    container.button(c, key=f"btn_{prefix}_{c}", on_click=assign_col, args=(c, prefix, st.session_state[active_key]))
                    
        return mapping

    with st.container():
        l_reqs = [(c, True) for c in strict_leads] + [(c, False) for c in opt_leads]
        mapping_dict['leads'] = render_mapping_section(l_reqs, leads_df, f"SECTION A — LEADS FILE MAPPING ({leads_file.name})", "leads")
        st.divider()
        
        s_reqs = [(c, True) for c in strict_sales] + [(c, False) for c in opt_sales]
        mapping_dict['sales'] = render_mapping_section(s_reqs, sales_df, f"SECTION B — SALES FILE MAPPING ({sales_file.name})", "sales")
        st.divider()
        
        m_reqs = [(c, True) for c in strict_meta] + [(c, False) for c in opt_meta]
        if meta_files:
            for i, (m_file, m_df) in enumerate(zip(meta_files, meta_dfs)):
                m_map = render_mapping_section(m_reqs, m_df, f"SECTION C — META SPEND FILE {i+1} MAPPING ({m_file.name})", f"meta_{i}")
                mapping_dict['meta'].append(m_map)
                if i < len(meta_files) - 1:
                    st.markdown("---")
        
    # 1. Validation (Check if required canonical fields are mapped)
    still_missing_strict = []
    for c in strict_leads:
        if c not in mapping_dict['leads']: still_missing_strict.append(f"Leads: {c}")
    for c in strict_sales:
        if c not in mapping_dict['sales']: still_missing_strict.append(f"Sales: {c}")
        
    for i, m_map in enumerate(mapping_dict['meta']):
        for c in strict_meta:
            if c not in m_map: still_missing_strict.append(f"Meta File {i+1}: {c}")

    # 2. Invert the dicts (actual -> canonical) to apply renaming to dataframes
    inv_leads = {v: k for k, v in mapping_dict['leads'].items()}
    inv_sales = {v: k for k, v in mapping_dict['sales'].items()}
    
    # 3. Rename columns
    leads_df.rename(columns=inv_leads, inplace=True)
    sales_df.rename(columns=inv_sales, inplace=True)
    
    if meta_dfs:
        for i in range(len(meta_dfs)):
            inv_meta = {v: ('Day' if k == 'Date' else k) for k, v in mapping_dict['meta'][i].items()}
            meta_dfs[i].rename(columns=inv_meta, inplace=True)
            
    meta_df = pd.concat(meta_dfs, ignore_index=True) if len(meta_dfs) > 1 else meta_dfs[0]

    for req_col in opt_leads:
        if req_col not in mapping_dict['leads']:
            if req_col == 'webinar_type': leads_df[req_col] = 'unknown'
            elif req_col == 'registration_fee': leads_df[req_col] = 0.0

    # --- DATE RANGE DETECTION & UI (SECTION 3) ---
    st.header("3. Report Period Configuration")
    st.write("Automatic date detection is used for default values. You can manually select dates at any time.")
    
    import datetime
    from dateutil.relativedelta import relativedelta
    
    lead_min, lead_max, sales_min, sales_max, meta_min, meta_max = pd.NaT, pd.NaT, pd.NaT, pd.NaT, pd.NaT, pd.NaT
    
    if 'registration_date' in leads_df.columns:
        l_dates = parse_date_series(leads_df['registration_date']).dropna()
        if not l_dates.empty: lead_min, lead_max = l_dates.min(), l_dates.max()
            
    if 'sale_date' in sales_df.columns:
        s_dates = parse_date_series(sales_df['sale_date']).dropna()
        if not s_dates.empty: sales_min, sales_max = s_dates.min(), s_dates.max()
            
    if not meta_df.empty:
        # Check Day or Reporting starts/ends
        if 'Day' in meta_df.columns:
            range_df = parse_date_range(meta_df['Day'])
            if not range_df['start_date'].dropna().empty: meta_min = range_df['start_date'].min()
            if not range_df['end_date'].dropna().empty: meta_max = range_df['end_date'].max()
        elif 'Reporting starts' in meta_df.columns and 'Reporting ends' in meta_df.columns:
            s_d = parse_date_series(meta_df['Reporting starts']).dropna()
            e_d = parse_date_series(meta_df['Reporting ends']).dropna()
            if not s_d.empty: meta_min = s_d.min()
            if not e_d.empty: meta_max = e_d.max()

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
        pass
        
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
        
    cov_leads = "Full"
    cov_sales = "Full"
    cov_meta = "Full"
    
    def get_cov(s, e, dmin, dmax):
        if pd.isna(dmin) or pd.isna(dmax): return "Unknown"
        if e < dmin.date() or s > dmax.date(): return "Outside"
        if s < dmin.date() or e > dmax.date(): return "Partial"
        return "Full"
        
    cov_leads = get_cov(ls_start, ls_end, lead_min, lead_max)
    cov_sales = get_cov(ls_start, ls_end, sales_min, sales_max)
    cov_meta = get_cov(meta_start, meta_end, meta_min, meta_max)
    
    if "Outside" in [cov_leads, cov_sales]:
        st.warning("⚠️ Selected period is outside available data coverage for Leads/Sales. The report can still be generated.")
    elif "Partial" in [cov_leads, cov_sales]:
        st.warning("⚠️ Partial data coverage for selected period (Leads/Sales).")
        
    if cov_meta == "Outside":
        st.warning("⚠️ Selected period is outside available data coverage for Meta Ads.")
    elif cov_meta == "Partial":
        st.warning(f"⚠️ Partial data coverage for selected period (Meta Ads: available {meta_min.date()} to {meta_max.date()}).")
    
    settings['report_type'] = preset
    settings['lead_sales_start_date'] = str(ls_start)
    settings['lead_sales_end_date'] = str(ls_end)
    settings['meta_start_date'] = str(meta_start)
    settings['meta_end_date'] = str(meta_end)
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


    st.header("4. Sales Data Resolution")
    st.write("Configure how to handle missing or ambiguous sales data. *Using non-actual sources will explicitly label the data as assumed.*")
    
    col_res1, col_res2, col_res3 = st.columns(3)
    
    with col_res1:
        sale_date_source = st.selectbox(
            "Fallback Sale Date (When missing)", 
            options=["Actual Sale Date", "Lead Registration Date"],
            index=0
        )
        settings['sale_date_source'] = sale_date_source
        
        if sale_date_source == "Lead Registration Date":
            st.info("ℹ️ Missing sale dates will default to the Lead's Registration Date.")
            
    with col_res2:
        payment_status_source = st.selectbox(
            "Payment Status Source",
            options=["Actual Payment Status", "Treat All Imported Sales as Successful", "Exclude Sales Without Payment Status"]
        )
        settings['payment_status_source'] = payment_status_source
        
        if payment_status_source == "Treat All Imported Sales as Successful":
            st.warning("⚠️ Treating all imported sales as successful regardless of missing payment status.")
            
    with col_res3:
        amount_source = st.selectbox(
            "Order Amount Source",
            options=["Actual Order Amount", "Fallback Price Per Sale"]
        )
        settings['amount_source'] = amount_source
        
        if amount_source == "Fallback Price Per Sale":
            st.info(f"Actual order amount was unavailable; fallback price ({settings['fallback_price']}) is being used.")

    derived_strict_sales = []
    if sale_date_source != "Actual Sale Date":
        derived_strict_sales.append("Sales: sale_date")
    if payment_status_source != "Actual Payment Status" and payment_status_source != "Exclude Sales Without Payment Status":
        pass

    final_missing_strict = [c for c in still_missing_strict if c not in derived_strict_sales]

    st.header("5. Generate Report")
    
    if final_missing_strict:
        st.error(f"❌ Cannot generate report. The following required columns are missing and not derived: {', '.join(final_missing_strict)}")
        st.stop()
        
    if st.button("🚀 Generate Report"):

        with st.status("Processing Pipeline...", expanded=True) as status:
            st.write("✓ Files loaded")
            st.write("✓ Inputs inspected")
            st.write("✓ Data normalized")
            
            try:
                output_path = "output/report.xlsx"
                os.makedirs("output", exist_ok=True)
                
                metrics, ver_df, xl_path = run_pipeline(
                    leads_df, sales_df, meta_dfs, settings, output_path
                )
                
                st.write("✓ Leads processed")
                st.write("✓ Sales attributed")
                st.write("✓ Meta spend attributed")
                st.write("✓ Funnel calculated")
                st.write("✓ Metrics calculated")
                st.write("✓ Excel generated")
                st.write("✓ Verification completed")
                status.update(label="Processing Complete!", state="complete", expanded=False)
                
                st.header("6. Final Metrics Summary")
                
                st.markdown("#### SECTION 1: LEADS & FUNNEL")
                ml1 = st.columns(1)[0]
                ml1.metric("Total Leads", metrics.get('total_leads'))
                
                st.markdown("#### SECTION 2: SALES & REVENUE")
                mc1, mc2, mc3 = st.columns(3)
                mc1.metric("Total Sales", metrics.get('total_sales'))
                mc2.metric("Attributed Sales", metrics.get('attributed_sales'))
                mc3.metric("Unattributed Sales", metrics.get('unattributed_sales'))
                
                mc4, mc5, mc6, mc7, mc8 = st.columns(5)
                
                per_sale = metrics.get('per_sale_value')
                mc4.metric("Per Sale Value", f"{currency} {per_sale:,.2f}" if isinstance(per_sale, (int, float)) else per_sale)
                
                attr_per_sale = metrics.get('attributed_per_sale_value')
                mc5.metric("Attributed Per Sale Value", f"{currency} {attr_per_sale:,.2f}" if isinstance(attr_per_sale, (int, float)) else attr_per_sale)

                mc6.metric("Registration Amount", f"{currency} {metrics.get('total_reg_revenue', 0):,.2f}")
                mc7.metric("Sales Revenue", f"{currency} {metrics.get('backend_revenue', 0):,.2f}")
                mc8.metric("Registration Revenue", f"{currency} {metrics.get('total_reg_revenue', 0):,.2f}")

                mc9, mc10, mc11 = st.columns(3)
                total_rev = metrics.get('total_revenue', 0)
                mc9.metric("Total Revenue", f"{currency} {total_rev:,.2f}")
                
                attr_rev = metrics.get('attributed_revenue', 0)
                mc10.metric("Attributed Revenue", f"{currency} {attr_rev:,.2f}")
                
                unattr_rev = metrics.get('unattributed_revenue', 0)
                mc11.metric("Unattributed Revenue", f"{currency} {unattr_rev:,.2f}")
                
                st.markdown("#### SECTION 3: META SPEND & ATTRIBUTION")
                ms1, ms3 = st.columns(2)
                ms1.metric("Raw Meta Spend", f"{currency} {metrics.get('raw_meta_spend', 0):,.2f}")
                ms3.metric("Unallocated Spend", f"{currency} {metrics.get('unallocated_spend', 0):,.2f}")
                
                if metrics.get('attributed_spend', 0) == 0:
                    st.warning(f"₹0 — No Meta spend was attributable within the selected period.")
                
                st.markdown("#### SECTION 4: FINANCIAL PERFORMANCE")
                mf1, mf2, mf3, mf4 = st.columns(4)
                mf1.metric("Profit", f"{currency} {metrics.get('profit', 0):,.2f}")
                mf2.metric("ROAS", f"{metrics.get('roas', 0):.2f}x" if metrics.get('roas') != "N/A" else "N/A")
                mf3.metric("ROI %", f"{metrics.get('roi_percent', 0):.1f}%" if metrics.get('roi_percent') != "N/A" else "N/A")
                mf4.metric("CAC", f"{currency} {metrics.get('cac', 0):,.2f}" if metrics.get('cac') != "N/A" else "N/A")
                
                st.header("7. Verification Result")
                st.dataframe(ver_df, use_container_width=True)
                
                structural_fails = ver_df[
                    (ver_df['Status'] == 'FAIL') &
                    (~ver_df['Check Name'].str.startswith('G.')) &
                    (~ver_df['Check Name'].str.startswith('INV.'))
                ]
                golden_fails = ver_df[
                    (ver_df['Status'] == 'FAIL') &
                    (ver_df['Check Name'].str.startswith('G.'))
                ]
                invariant_fails = ver_df[
                    (ver_df['Status'] == 'FAIL') &
                    (ver_df['Check Name'].str.startswith('INV.'))
                ]

                if not structural_fails.empty:
                    failed_checks = structural_fails['Check Name'].tolist()
                    st.error(f"❌ STRUCTURAL CHECKS FAILED: {', '.join(failed_checks)}")
                elif not invariant_fails.empty:
                    failed_names = invariant_fails['Check Name'].tolist()
                    st.error(f"❌ FORMULA INVARIANTS FAILED (Revenue/Spend math is broken): {', '.join(failed_names)}")
                else:
                    st.success("✅ REPORT VALID: All structural checks passed.")

                if not golden_fails.empty:
                    st.info(f"ℹ️ {len(golden_fails)} Golden benchmark check(s) differ from the test dataset — expected for different client data.")

                with open(xl_path, "rb") as f:
                    st.download_button(
                        label="📥 Download Excel Workbook",
                        data=f,
                        file_name=f"UTM_Report_{client_name}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                        
            except Exception as e:
                status.update(label="Pipeline Failed", state="error", expanded=True)
                st.error(f"Error during processing: {str(e)}")
