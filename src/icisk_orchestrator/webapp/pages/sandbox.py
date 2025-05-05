import os

import streamlit as st

from db import DBI
from webapp import langgraph_interface as lgi
from webapp.session.state import session_manager

import streamlit.components.v1 as components

st.set_page_config(page_title="Sandbox", page_icon="🔐", layout="wide")

st.markdown("#### Sandbox")

# region: jupy client

components.iframe("http://localhost:8888", height=500)

