import re

with open("app/streamlit_app.py", "r") as f:
    content = f.read()

# I will replace the block from "if still_missing_strict:" down to "if st.button"
pattern = re.compile(r'    if still_missing_strict:.*?if st\.button\("🚀 Generate Report"\):', re.DOTALL)

replacement = """    if still_missing_strict:
        st.error(f"❌ Cannot generate report. The following required columns are missing: {', '.join(still_missing_strict)}")
        st.stop()
        
    if st.button("🚀 Generate Report"):"""

content = pattern.sub(replacement, content)

with open("app/streamlit_app.py", "w") as f:
    f.write(content)
