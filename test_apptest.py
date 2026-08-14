from streamlit.testing.v1 import AppTest
import time

print("Starting AppTest...")
at = AppTest.from_file("app/streamlit_app.py", default_timeout=30)
at.run()
print("App loaded. Title:", at.title[0].value)

# Upload files
leads_path = '/Users/apple/Downloads/12-08-2026_leads.csv'
sales_path = '/Users/apple/Downloads/12-08-2026_sales(1).csv'
meta_path1 = '/Users/apple/Downloads/FML-X-Satyam-2-Campaigns-1-Aug-2026-12-Aug-2026.csv'
meta_path2 = '/Users/apple/Downloads/SSA-X-SATYAM-KHANDELWAL-Campaigns-1-Aug-2026-12-Aug-2026.csv'

with open(leads_path, "rb") as f: leads_bytes = f.read()
with open(sales_path, "rb") as f: sales_bytes = f.read()
with open(meta_path1, "rb") as f: meta1_bytes = f.read()
with open(meta_path2, "rb") as f: meta2_bytes = f.read()

# Try to upload using AppTest API
at.file_uploader(key="leads").set_value(leads_bytes)
at.file_uploader(key="sales").set_value(sales_bytes)
# Meta is multiple files, wait, set_value accepts a list for multiple files?
# Let's see if we can do this without crashing.
try:
    at.file_uploader(key="meta").set_value([meta1_bytes, meta2_bytes])
except Exception as e:
    print("Multiple files upload error:", e)

at.run()
print("Files uploaded and app re-run.")

# Check if mapping succeeded
success_msgs = [m.value for m in at.success]
print("Success messages:", success_msgs)

# Set dates
print("Setting custom dates to 2026-08-01 -> 2026-08-12")
import datetime
at.date_input(key='ls_start').set_value(datetime.date(2026, 8, 1))
at.date_input(key='ls_end').set_value(datetime.date(2026, 8, 12))
at.date_input(key='m_start').set_value(datetime.date(2026, 8, 1))
at.date_input(key='m_end').set_value(datetime.date(2026, 8, 12))
at.run()

# Click Generate Report
print("Clicking Generate Report...")
# Find the button
gen_btn = next((b for b in at.button if b.label == "🚀 Generate Report"), None)
if gen_btn:
    gen_btn.click().run()
else:
    print("Could not find Generate Report button")

# Output metrics
print("\n--- METRICS 1 ---")
for metric in at.metric:
    print(f"{metric.label}: {metric.value}")

# Check verification
print("\nVerification Success:", [s.value for s in at.success])
if at.error:
    print("Errors:", [e.value for e in at.error])

print("\nSetting custom dates to 2026-08-05 -> 2026-08-10")
at.date_input(key='ls_start').set_value(datetime.date(2026, 8, 5))
at.date_input(key='ls_end').set_value(datetime.date(2026, 8, 10))
at.date_input(key='m_start').set_value(datetime.date(2026, 8, 5))
at.date_input(key='m_end').set_value(datetime.date(2026, 8, 10))
at.run()

gen_btn = next((b for b in at.button if b.label == "🚀 Generate Report"), None)
if gen_btn:
    gen_btn.click().run()

print("\n--- METRICS 2 ---")
for metric in at.metric:
    print(f"{metric.label}: {metric.value}")
