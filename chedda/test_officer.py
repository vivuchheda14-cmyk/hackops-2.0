import streamlit as st

from database import init_db, save_complaint
from officer_portal import show_officer_portal

st.set_page_config(page_title="Officer Portal Test")

init_db()

# Add sample data only once per Streamlit session
if "sample_added" not in st.session_state:
    complaint = {
        "type": "Smoke",
        "location": "Andheri, Mumbai",
        "description": "Thick black smoke reported near an industrial area"
    }

    save_complaint(complaint)
    st.session_state.sample_added = True

# Display officer portal
show_officer_portal()