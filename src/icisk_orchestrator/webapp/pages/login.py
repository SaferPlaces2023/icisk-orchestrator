import os

import streamlit as st

from db import DBI
from webapp import langgraph_interface as lgi
from webapp.session.state import session_manager



st.set_page_config(page_title="ICisk AI Agent — Login", page_icon="🔐", layout="wide")



def validate_login(user_id: str):
    """
    Validate the user ID and set up the session.
    """
    user = DBI.user_by_id(user_id)
    if user is not None:
        return True
    else:
        return False


_, center_col, _ = st.columns([1, 1, 1], vertical_alignment="center") 

with center_col:   
    
    st.markdown("## **🔐 ICisk AI Agent — Login**")

    with st.form("login-form"):
        st.markdown("Please enter your user ID to log in. If you don't have an account, please contact the administrator.")
        
        user_id = st.text_input("User ID", placeholder="your-icisk-ai-agent-user-id")

        if st.form_submit_button("Login"):
            if validate_login(user_id=user_id):
                session_manager.setup(user_id=user_id)
                st.rerun()
            else:
                st.divider()
                st.error("Invalid user ID. Please try again.")
                st.stop()
                
# TODO: Maybe some description, footer, credits, etc.