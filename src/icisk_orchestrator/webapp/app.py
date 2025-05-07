import os
import streamlit as st



login_page = st.Page('pages/login.py', title="Login", icon=":material/login:")

chat_page = st.Page('pages/chat.py', title="AI-Chat", icon=":material/chat:")

# code_page = st.Page('pages/code.py', title="AI-Code", icon=":material/chat:")


go_sandbox = False
if go_sandbox:
    sandbox_page = st.Page('pages/sandbox.py', title="Sandbox", icon=":material/chat:")
    pg = st.navigation([sandbox_page])
    pg.run()

else:

    if 'app' not in st.session_state:
        pg = st.navigation([login_page])
    else:
        pg = st.navigation([
            chat_page,
            # code_page     # TODO: will come later
        ])
        
    pg.run()