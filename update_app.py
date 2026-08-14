import re

with open("app/streamlit_app.py", "r") as f:
    content = f.read()

# Replace import
content = content.replace("from src.ingestion import read_file", "from src.ingestion import read_file, read_stream")

# Replace load_df
new_load_df = """def load_df(uploaded_file):
    if uploaded_file is None:
        return None
    try:
        return read_stream(uploaded_file, uploaded_file.name)
    except Exception as e:
        st.error(f"Error reading {uploaded_file.name}: {str(e)}")
        return None"""

content = re.sub(r"def load_df\(uploaded_file\):.*?return None", new_load_df, content, flags=re.DOTALL)

with open("app/streamlit_app.py", "w") as f:
    f.write(content)

