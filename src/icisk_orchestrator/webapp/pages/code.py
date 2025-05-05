import os
import re
import time
import requests

import nbformat as nbf

import docker
import streamlit as st

from db import DBI
from webapp import langgraph_interface as lgi
from webapp.session.state import session_manager

import streamlit.components.v1 as components

st.set_page_config(page_title="Coder", page_icon="🔐", layout="wide")

st.markdown("##### AI code")

# region: jupy client

PROJECT_DIR = os.path.abspath(".")
TMP_DIR = os.path.join(PROJECT_DIR, "tmp_run")

notebooks = DBI.notebooks_by_author(author=session_manager.user_id, retrieve_source=True)
os.makedirs(os.path.join(TMP_DIR, session_manager.user_id), exist_ok=True)
for notebook in notebooks:
    notebook_path = os.path.join(TMP_DIR, session_manager.user_id, notebook.name)
    with open(notebook_path, "w", encoding='utf-8') as f:
        nbf.write(notebook.source, f)

with st.spinner("Loading code environment ...", show_time=True):
    client = docker.from_env()

    container = client.containers.run(
        "jupyter/base-notebook",
        detach=True,
        ports={"8888/tcp": 8888},
        volumes={
            os.path.join(TMP_DIR, session_manager.user_id): {'bind': '/home/jovyan', 'mode': 'rw'}
        },
        environment={
            'JUPYTER_ENABLE_LAB': 'yes'
        },
        command=[
            "start.sh", "jupyter", "lab",
            "--LabApp.allow_origin='*'",
            "--LabApp.disable_check_xsrf=True",
            "--LabApp.tornado_settings={\"headers\": {\"Content-Security-Policy\": \"frame-ancestors *\"}}"
        ],
    )

    
    time.sleep(10)   # FIXME: this is ugly
    
    logs = container.logs().decode("utf-8")
    match = re.search("token=([a-f0-9]+)", logs)
    
    token = match.group(1)
    
    print(token)
    
    components.iframe(f"http://localhost:8888/lab?token={token}", height=500)