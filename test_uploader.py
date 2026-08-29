import streamlit as st

st.write(st.__version__)

f = st.file_uploader("Upload")
if f:
    st.write(getattr(f, "file_id", "no file_id"))
    st.write(getattr(f, "id", "no id"))
    
    if st.button("Click me to rerun"):
        pass
