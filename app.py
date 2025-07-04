import streamlit as st

st.set_page_config(
    page_title="Election Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🗳️ Election Analytics Dashboard")
st.write("Use the sidebar to navigate between **District**, **Local Body**, and **Other** insights.")
