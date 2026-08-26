import streamlit as st
import pandas as pd
import json
import os
import sys
import datetime
from dateutil.relativedelta import relativedelta

# Ensure src modules can be imported
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.ingestion import read_stream
from src.inspection import load_aliases, suggest_mapping
from src.pipeline import run_pipeline

st.set_page_config(page_title="UTM Sales Attribution Generator", layout="wide")

st.title("🚀 UTM Sales Attribution & Profitability Report Generator")

# State initialization
if 'reset' not in st.session_state:
    st.session_state.reset = False

# Sidebar settings
st.sidebar.header("⚙ Settings")
client_name = st.sidebar.text_input("Client / Report Name", "Antigravity Default")

cutoff_date = st.sidebar.date_input("New vs Old Lead Cutoff Date", pd.to_datetime("2024-01-01"))
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

# Main Layout
st.header("1. Upload Files")

col1, col2, col3 = st.columns(3)

with col1:
    leads_file = st.file_uploader("Leads File (CSV/XLSX)", type=['csv', 'xlsx'], key='leads')
with col2:
    sales_file = st.file_uploader("Sales File (CSV/XLSX)", type=['csv', 'xlsx'], key='sales')
with col3:
    meta_files = st.file_uploader("Meta Spend Files (CSV/XLSX)", type=['csv', 'xlsx'], accept_multiple_files=True, key='meta')

if st.button("🔄 Reset / Clear"):
    st.session_state.clear()
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
    raw_leads_df = load_df(leads_file)
    raw_sales_df = load_df(sales_file)
    meta_dfs_raw = [load_df(f) for f in meta_files if f is not None]
    
    raw_meta_df = pd.concat(meta_dfs_raw, ignore_index=True) if meta_dfs_raw else pd.DataFrame()
    
    aliases = load_aliases()

    st.header("2. Input Inspection & Column Mapping")
    st.write("Review and adjust the column mappings for each uploaded file.")
    
    def render_mapping_ui(df, file_label, schema_fields, required_fields, missing_text="-- Ignore/Missing --"):
        if df is None or df.empty:
            st.error(f"No data found for {file_label}")
            return {}
            
        st.subheader(f"{file_label} Mapping")
        orig_cols = list(df.columns)
        mapping = {}
        
        cols = st.columns(3)
        for i, field in enumerate(schema_fields):
            col = cols[i % 3]
            is_req = field in required_fields
            label = f"**{field}** {'*(Required)*' if is_req else '*(Optional)*'}"
            suggested = suggest_mapping(field, orig_cols, aliases)
            options = [missing_text] + orig_cols
            default_index = options.index(suggested) if suggested in options else 0
            
            with col:
                selected = st.selectbox(label, options=options, index=default_index, key=f"map_{file_label}_{field}")
                if selected != missing_text:
                    mapping[selected] = field
                    
        return mapping
        
    leads_schema = ['email', 'phone', 'registration_date', 'campaign', 'ad_set', 'ad_creative', 'placement', 'lead_status', 'webinar_type', 'registration_fee']
    leads_req = ['registration_date', 'campaign'] 
    
    sales_schema = ['email', 'phone', 'sale_date', 'payment_status', 'order_amount']
    sales_req = [] 
    
    meta_schema = ['campaign', 'spend', 'Day', 'ad_set', 'ad']
    meta_req = ['campaign', 'spend', 'Day']
    
    with st.expander("Column Mappings (Click to review or change)", expanded=True):
        leads_mapping = render_mapping_ui(raw_leads_df, "Leads", leads_schema, leads_req)
        st.divider()
        sales_mapping = render_mapping_ui(raw_sales_df, "Sales", sales_schema, sales_req)
        st.divider()
        meta_mapping = render_mapping_ui(raw_meta_df, "Meta Ads", meta_schema, meta_req)

    def apply_mapping(df, mapping):
        if df.empty:
            return df.copy()
        return df.rename(columns=mapping)
        
    leads_df = apply_mapping(raw_leads_df, leads_mapping)
    sales_df = apply_mapping(raw_sales_df, sales_mapping)
    meta_df = apply_mapping(raw_meta_df, meta_mapping)
    meta_dfs = [apply_mapping(rdf, meta_mapping) for rdf in meta_dfs_raw]
    
    st.header("3. Schema Validation")
    validation_errors = []
    
    if 'email' not in leads_df.columns and 'phone' not in leads_df.columns:
        validation_errors.append("Leads: At least one identity field ('email' OR 'phone') must be mapped.")
    if 'registration_date' not in leads_df.columns:
        validation_errors.append("Leads: 'registration_date' field has not been mapped.")
    if 'campaign' not in leads_df.columns:
        validation_errors.append("Leads: 'campaign' field has not been mapped.")
        
    if 'email' not in sales_df.columns and 'phone' not in sales_df.columns:
        validation_errors.append("Sales: At least one identity field ('email' OR 'phone') must be mapped.")
        
    if 'campaign' not in meta_df.columns:
        validation_errors.append("Meta Ads: 'campaign' field has not been mapped.")
    if 'spend' not in meta_df.columns:
        validation_errors.append("Meta Ads: 'spend' field has not been mapped.")
    if 'Day' not in meta_df.columns:
        validation_errors.append("Meta Ads: 'Day' field has not been mapped.")
        
    if validation_errors:
        for err in validation_errors:
            st.error(f"❌ {err}")
        st.warning("Please correct the mappings above before proceeding.")
        st.stop()
    else:
        st.success("✅ Required schema mapping validated successfully.")
        if 'webinar_type' not in leads_df.columns:
            leads_df['webinar_type'] = 'unknown'
        if 'registration_fee' not in leads_df.columns:
            leads_df['registration_fee'] = 0.0

    st.header("4. Report Period Configuration")
    
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
    elif preset == "Last 30 Days":
        def_l_start = def_m_start = today - datetime.timedelta(days=30)
    elif preset == "This Month":
        def_l_start = def_m_start = today.replace(day=1)
        nxt = (today.replace(day=28) + datetime.timedelta(days=4))
        def_l_end = def_m_end = nxt - datetime.timedelta(days=nxt.day)
    elif preset == "Yesterday":
        def_l_start = def_l_end = def_m_start = def_m_end = today - datetime.timedelta(days=1)
        
    col_d1, col_d2 = st.columns(2)
    with col_d1:
        st.markdown("#### LEAD / SALES PERIOD")
        ls_start = st.date_input("Start Date", value=def_l_start, key='ls_start')
        ls_end = st.date_input("End Date", value=def_l_end, key='ls_end')
    with col_d2:
        st.markdown("#### META ADS PERIOD")
        meta_start = st.date_input("Start Date", value=def_m_start, key='m_start')
        meta_end = st.date_input("End Date", value=def_m_end, key='m_end')
        
    if ls_start > ls_end or meta_start > meta_end:
        st.error("Start Date cannot be after End Date.")
        st.stop()
        
    cov_leads = "Full" if not pd.isna(lead_min) else "Unknown"
    cov_sales = "Full" if not pd.isna(sales_min) else "Unknown"
    cov_meta = "Full" if not pd.isna(meta_min) else "Unknown"
    
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
    settings['coverage_status'] = f"Leads: {cov_leads}, Sales: {cov_sales}, Meta: {cov_meta}"

    st.header("5. Sales Data Resolution")
    
    col_res1, col_res2, col_res3 = st.columns(3)
    
    with col_res1:
        sale_date_source = st.selectbox(
            "Fallback Sale Date (When missing)", 
            options=["Actual Sale Date", "Lead Registration Date"],
            index=0
        )
        settings['sale_date_source'] = sale_date_source
        
    with col_res2:
        payment_status_source = st.selectbox(
            "Payment Status Source",
            options=["Actual Payment Status", "Treat All Imported Sales as Successful", "Exclude Sales Without Payment Status"]
        )
        settings['payment_status_source'] = payment_status_source
        
    with col_res3:
        amount_source = st.selectbox(
            "Order Amount Source",
            options=["Actual Order Amount", "Fallback Price Per Sale"]
        )
        settings['amount_source'] = amount_source

    st.header("6. Generate Report")
    if st.button("🚀 Generate Report"):
        with st.status("Processing Pipeline...", expanded=True) as status:
            st.write("✓ Data mapped successfully")
            
            try:
                output_path = "output/report.xlsx"
                os.makedirs("output", exist_ok=True)
                
                metrics, ver_df, xl_path = run_pipeline(
                    leads_df, sales_df, meta_dfs, settings, output_path
                )
                
                status.update(label="Processing Complete!", state="complete", expanded=False)
                
                st.header("7. Final Metrics Summary")
                st.markdown("#### SECTION 1: LEADS & FUNNEL")
                ml1, ml2, ml3, ml4, ml5 = st.columns(5)
                ml1.metric("Total Leads", metrics.get('total_leads'))
                ml2.metric("Paid Leads", metrics.get('paid_leads'))
                ml3.metric("Unpaid Leads", metrics.get('unpaid_leads'))
                ml4.metric("Paid Funnel %", f"{metrics.get('paid_funnel_percent', 0):.2f}%")
                ml5.metric("Unpaid Funnel %", f"{metrics.get('unpaid_funnel_percent', 0):.2f}%")
                
                st.markdown("#### SECTION 2: SALES & REVENUE")
                mc1, mc2, mc3 = st.columns(3)
                mc1.metric("Total Sales", metrics.get('total_sales'))
                mc2.metric("Attributed Sales", metrics.get('attributed_sales'))
                mc3.metric("Unattributed Sales", metrics.get('unattributed_sales'))
                
                st.markdown("#### SECTION 3: META SPEND & ATTRIBUTION")
                ms1, ms2, ms3 = st.columns(3)
                ms1.metric("Raw Meta Spend", f"{currency} {metrics.get('raw_meta_spend', 0):,.2f}")
                ms2.metric("Attributed Spend", f"{currency} {metrics.get('attributed_spend', 0):,.2f}")
                ms3.metric("Unallocated Spend", f"{currency} {metrics.get('unallocated_spend', 0):,.2f}")
                
                st.markdown("#### SECTION 4: FINANCIAL PERFORMANCE")
                mf1, mf2, mf3, mf4 = st.columns(4)
                mf1.metric("Profit", f"{currency} {metrics.get('profit', 0):,.2f}")
                mf2.metric("ROAS", f"{metrics.get('roas', 0):.2f}x" if metrics.get('roas') != "N/A" else "N/A")
                mf3.metric("ROI %", f"{metrics.get('roi_percent', 0):.1f}%" if metrics.get('roi_percent') != "N/A" else "N/A")
                mf4.metric("CAC", f"{currency} {metrics.get('cac', 0):,.2f}" if metrics.get('cac') != "N/A" else "N/A")
                
                st.header("8. Verification Result")
                st.dataframe(ver_df, use_container_width=True)
                
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
