import os

import nest_asyncio; nest_asyncio.apply()
import asyncio

import streamlit as st

from db import DBI, DBS
from agent.nodes.base.base_tool_interrupt import BaseToolInterrupt
from webapp import langgraph_interface as lgi



class GUI():
    def __init__(self):
        self.chat_input = dict()
        self.file_downloader = dict()
        self.tool_choice: str = None
    
    @property 
    def filenames(self) -> list | None:
        return DBI.notebooks_by_author(st.session_state.app.user_id, retrieve_source=False)
    
    def request_download(self, filename):
        if filename not in self.file_downloader:
            self.file_downloader[filename] = dict()
        self.file_downloader[filename].update({'requested': True})
        
    def is_requested_download(self, filename):
        return self.file_downloader.get(filename, dict()).get('requested', False)
    
    @property
    def chat_register(self) -> dict | None:
        return DBI.chat_by_user_id(st.session_state.app.user_id, retrieve_messages=False)
   
    def update_tool_choice(self, value: str | None):
        if value is None or value == 'All tools (default)':
            self.tool_choice = None
        else:
            self.tool_choice = value


class Interrupt():
    
    def __init__(self, interrupt_type: BaseToolInterrupt.BaseToolInterruptType, resume_key: str = 'response', interrupt_data: dict = dict()):
        self.interrupt_type = interrupt_type
        self.resume_key = resume_key
        self.interrupt_data = interrupt_data if interrupt_data is not None else dict()
    
    @property
    def as_dict(self):
        return {
            'interrupt_type': str(self.interrupt_type),
            'resume_key': self.resume_key,
            'interrupt_data': self.interrupt_data
        }
    
        

class WebAppState():
    
    def __init__(self, user_id):
        self.user_id = user_id
        self.thread_id = asyncio.run(lgi.create_thread(lgi.get_langgraph_client(), self.user_id))
        self.chat_history = []                      # DOC: relative to Chat Messages (to be rendered in GUI)
        self.chat: DBS.Chat = None
        self.gui = GUI()                            # TODO: To be deleted, will use self.chat.messages ( + filter by author when rendering )
        self.interrupt: Interrupt = None            # DOC: graph is interrupted, we have to handle resume command  
        self.node_history = []                      # TEST: relative to graph visited node history
    
    
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
    def chat(self) -> DBS.Chat | None:
        return st.session_state.app.chat if hasattr(st.session_state, 'app') else None
    def new_chat(self, title: str = 'New Chat'):
        st.session_state.app.chat = DBS.Chat(user_id=self.user_id, thread_id=self.thread_id, title=title,  messages=[] )
    def update_chat(self, messages: list | dict):
        if self.chat is None:
            messages = messages if isinstance(messages, list) else [messages]
            self.new_chat(title=messages[0].get('content', 'New Chat') if len(messages)>0 else 'New Chat')
        self.chat.add_messages(messages)
        DBI.update_chat(self.chat)
    def close_chat(self):
        if self.chat is not None:
            DBI.update_chat(self.chat)
            st.session_state.app.chat = None
            st.session_state.app.chat_history = []
    
    @property
    def gui(self) -> GUI | None:
        return st.session_state.app.gui if hasattr(st.session_state, 'app') else None
    
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
    

# DOC: Initialize the session manager
session_manager = SessionManager()