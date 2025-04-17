import os
import streamlit as st



login_page = st.Page('pages/login.py', title="Login", icon=":material/login:")

chat_page = st.Page('pages/chat.py', title="AI Chat", icon=":material/chat:")


if 'app' not in st.session_state:
    pg = st.navigation([login_page])
else:
    pg = st.navigation([chat_page])
    
pg.run()