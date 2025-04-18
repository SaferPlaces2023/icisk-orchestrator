import os

import nest_asyncio; nest_asyncio.apply()
import asyncio

import streamlit as st

from db import DBI
from agent.nodes.base.base_tool_interrupt import BaseToolInterrupt
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


class Interrupt():
    
    def __init__(self, interrupt_type: BaseToolInterrupt.BaseToolInterruptType, resume_key: str = 'response', interrupt_data: dict = dict()):
        self.interrupt_type = interrupt_type
        self.resume_key = resume_key
        self.interrupt_data = interrupt_data if interrupt_data is not None else dict()
        

class WebAppState():
    
    def __init__(self, user_id):
        self.user_id = user_id
        self.thread_id = asyncio.run(lgi.create_thread(lgi.get_langgraph_client(), self.user_id))
        self.chat_history = []                      # DOC: relative to Chat Messages (to be rendered in GUI)
        self.gui = GUI()                            # DOC: relative to GUI Components properties
        self.graph_messages = []                    # DOC: relative to Graph State Messages
        self.node_history = []                      # DOC: relative to graph visited node history
        self.interrupt: Interrupt = None            # DOC: graph is interrupted, we have to handle resume command  
    
    
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
    
    @property
    def node_history(self):
        return st.session_state.app.node_history if hasattr(st.session_state, 'app') else None
    @node_history.setter
    def node_history(self, value):
        self.node_history.append(value) if hasattr(st.session_state, 'app') else None
    
    @property
    def interrupt(self) -> Interrupt | None:
        return st.session_state.app.interrupt if hasattr(st.session_state, 'app') else None
    @interrupt.setter
    def interrupt(self, value: Interrupt | None):
        if hasattr(st.session_state, 'app'):
            st.session_state.app.interrupt = value
    
    
    def is_interrupted(self):
        return self.interrupt is not None
        # if len(self.graph_messages) > 0:
        #     return self.graph_messages[-1].get("is_interrupt", False)
        # return False
    
    def get_interrupt_key(self):
        if self.is_interrupted():
            return self.graph_messages[-1].get('response_key', 'response')
        return None
    

# DOC: Initialize the session manager
session_manager = SessionManager()