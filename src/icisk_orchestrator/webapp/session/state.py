import os

import nest_asyncio; nest_asyncio.apply()
import asyncio

import streamlit as st

from db import DBI
from webapp import langgraph_interface as lgi



class GUI():
    def __init__(self):
        self.chat_input = dict()
        self.file_downloader = dict()
    
    @property 
    def filenames(self):
        return DBI.notebooks_by_author(st.session_state.app.user_id, retrieve_source=False)
    
    def request_download(self, filename):
        if filename not in self.file_downloader:
            self.file_downloader[filename] = dict()
        self.file_downloader[filename].update({'requested': True})
        
    def is_requested_download(self, filename):
        return self.file_downloader.get(filename, dict()).get('requested', False)


class WebAppState():
    
    def __init__(self, user_id):
        self.user_id = user_id
        self.thread_id = asyncio.run(lgi.create_thread(lgi.get_langgraph_client(), self.user_id))
        self.chat_history = []  # INFO: this is relative to Chat Messages (to be rendered in GUI)
        self.gui = GUI()  # INFO: this is relative to GUI Components properties
        self.graph_messages = []  # INFO: this is relative to Graph State Messages
    
    
class SessionManager():
    
    def setup(self, user_id: str):
        """
        Setup the web app state.
        
        Parameters:
            user_id (str): The user ID.
        """
        
        st.session_state.app = WebAppState(user_id=user_id)
        
    @property
    def user_id(self):
        return st.session_state.app.user_id if hasattr(st.session_state, 'app') else None
    
    @property
    def thread_id(self):
        return st.session_state.app.thread_id if hasattr(st.session_state, 'app') else None
    
    @property
    def client(self):
        return lgi.get_langgraph_client() if hasattr(st.session_state, 'app') else None
    
    @property
    def chat_history(self):
        return st.session_state.app.chat_history if hasattr(st.session_state, 'app') else None
    
    @property
    def gui(self):
        return st.session_state.app.gui if hasattr(st.session_state, 'app') else None
    
    @property
    def graph_messages(self):
        return st.session_state.app.graph_messages if hasattr(st.session_state, 'app') else None
    
    
    def is_interrupted(self):
        if len(self.graph_messages) > 0:
            return self.graph_messages[-1].get("is_interrupt", False)
        return False
    
    def get_interrupt_key(self):
        if self.is_interrupted():
            return self.graph_messages[-1].get('response_key', 'response')
        return None
    

# DOC: Initialize the session manager
session_manager = SessionManager()