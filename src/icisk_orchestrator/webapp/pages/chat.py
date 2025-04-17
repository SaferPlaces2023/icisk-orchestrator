import os
import ast
import time

from io import StringIO

import nbformat as nbf

import nest_asyncio; nest_asyncio.apply()
import asyncio
import streamlit as st

from webapp import utils
from webapp import langgraph_interface as lgi

from db import DBI

from agent.common import names as AGENT_N



st.set_page_config(page_title="ICisk AI Agent", page_icon="🤖", layout="wide")
st.title("🧠 ICisk AI Agent")



with st.expander("# 💡 **What is this application?** "):
    st.markdown(
        """
        This is a multi-agent artificial intelligence system built with LangGraph and OpenAI models.  
        It is designed to assist users in the guided generation of interactive notebooks by leveraging the **ICisk** project APIs for the retrieval, processing, and visualization of climate data.  
            
        The goal is to simplify environmental data analysis through an intelligent conversational interface capable of guiding users step by step in building their data workflows.  
        
        **This is a demo version**. At the moment, it can assist with the calculation of the **Standardized Precipitation Index (SPI)**.  
        Additional processing capabilities will be available soon. 
        
        For more details, simply interact with the bot.
        """
    )
    
    

for message in st.session_state.app.chat_history:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])



    
def render_message(role, content):
    avatar = {
        "user": None,
        "assistant": None,
        "tool": "🛠️"
    }
    st.chat_message(role, avatar=avatar[role]).markdown(content)
    st.session_state.app.chat_history.append({"role": role, "content": content})



def render_user_prompt(prompt):
    render_message("user", prompt)


    
def render_agent_response(message):
    
    if len(message.get('tool_calls', [])) > 0:
        for tool_call in message['tool_calls']:
            header = f"##### Using tool: _{tool_call['name']}_"
            tool_table = utils.tool_args_md_table(tool_call['args'])
            content = f"{header}\n\n{tool_table}" if tool_table else header
            render_message("tool", content)
    
    if len(message.get('content', [])) > 0:
        if message.get('is_interrupt', False):
            message['content'] = f"**Interaction required [ _{message['interrupt_type']}_ ]: 💬**\n\n{message['content']}"
        render_message("assistant", message['content'])
        
        
        
def handle_response(response):
    for author, data in response.items():
        message = None
        if author == 'chatbot':
            messages = data.get('messages', [])
            message = messages[-1] if len(messages) > 0 else None
        elif author == '__interrupt__':
            message = data[0].get('value', None) if len(data) > 0 else None
            message['is_interrupt'] = True
        
        if message is not None and message.get('type', None) != 'system':
            render_agent_response(message)
            st.session_state.app.graph_messages.append(message)
    
            
if prompt := st.chat_input(key="chat-input", placeholder="Scrivi un messaggio"):
    render_user_prompt(prompt)
    
    async def run_chat():
        additional_args = {}
        if st.session_state.app.is_interrupted():
            additional_args['interrupt_response_key'] = st.session_state.app.get_interrupt_key()
        async for message in lgi.ask_agent(
            st.session_state.app.client, 
            st.session_state.app.thread_id, 
            prompt,
            **additional_args
        ):
            handle_response(message)
    
    asyncio.run(run_chat())
     

with st.sidebar:
    
    with st.expander("**📁 File manager**"):
        avaliable_files = st.session_state.app.gui.filenames
        
        if len(avaliable_files) == 0:
            st.markdown("No files uploaded yet.")
        
        else:
            for ifn,file_obj in enumerate(avaliable_files):
                filename = file_obj['name']
                col_name, col_view, col_download = st.columns([5, 1, 1], vertical_alignment="center")
                
                with col_name:
                    st.markdown(f"- **`{filename}`**")
                    
                with col_view:
                    if st.button("👁️", key=f"view_{filename}-{ifn}", help="view file"):
                        @st.dialog(filename, width="large")
                        def show_ipynb_code(source_code: str):
                            notebook = nbf.reads(source_code, as_version=4)
                            for cell in notebook.cells:
                                if cell.cell_type == 'code':
                                    st.code(cell.source, language='python')
                                elif cell.cell_type == 'markdown':
                                    st.markdown(cell.source)
                            if st.button("Close"):
                                st.rerun()  
                        show_ipynb_code.title = filename
                        show_ipynb_code(DBI.notebook_by_name(filename, retrieve_source=True)['source'])
                        
                with col_download:
                    if st.session_state.app.gui.is_requested_download(filename):
                        st.download_button(
                            label = "📥",
                            data = DBI.notebook_by_name(filename, retrieve_source=True)['source'],
                            file_name = filename,
                            mime = "json/ipynb",
                            key = f"download_{filename}-{ifn}"
                        )
                    else:
                        if st.button("📁", key=f"pre-download_{filename}-{ifn}", help="request download"):
                            st.session_state.app.gui.request_download(filename)
                            st.rerun()
                        
        st.divider()
        
        uploader_col, sender_col = st.columns([4, 1])
        
        with uploader_col:
            file_uploader = st.file_uploader("Upload", label_visibility="collapsed", type='ipynb')
        
        with sender_col:
            if st.button("Upload", help="upload file"):
                if file_uploader is not None:
                    DBI.save_notebook(
                        notebook_id = None,
                        notebook_name = file_uploader.name,
                        notebook_source = nbf.reads(StringIO(file_uploader.getvalue().decode("utf-8")).read(), as_version=4),
                        authors = st.session_state.app.user_id,
                        notebook_description = None
                    )
                st.rerun()
        
    # INFO: Second sidebar element (Will be used for displaying graph state)
    with st.expander("📊 Graph state"):
        st.markdown("Graph state will be displayed here")