import os

import streamlit as st

from db import DBI
from webapp import langgraph_interface as lgi
from webapp.session.state import WebAppState



st.set_page_config(page_title="ICisk AI Agent — Login", page_icon="🔐", layout="wide")

_, center_col, _ = st.columns([1, 1, 1], vertical_alignment="center") 

with center_col:   
    
    st.markdown("## **🔐 ICisk AI Agent — Login**")

    with st.form("login-form"):
        st.markdown("Please enter your user ID to log in. If you don't have an account, please contact the administrator.")
        
        user_id = st.text_input("User ID", placeholder="your-icisk-ai-agent-user-id")

        if st.form_submit_button("Submit"):
            user = DBI.user_by_id(user_id)
            if user is not None or user_id.lower() == "admin":  # TODO: remove admin check
                st.session_state.app = WebAppState(user_id=user_id)
                st.rerun()
                
                
# TODO: Maybe some description, footer, credits, etc.