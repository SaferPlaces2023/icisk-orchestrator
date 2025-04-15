import nest_asyncio; nest_asyncio.apply()
import asyncio
import streamlit as st

from webapp import utils
from webapp import langgraph_interface as lgi

# from ..session import SimpleSessionManager


# REGION: Classes -------------------------------------------------------------

class GUI():
    def __init__(self):
        self.chat_input = dict()

class WebAppState():
    
    def __init__(self):
        self.thread_id = asyncio.run(lgi.create_thread(self.client))
        self.chat_history = []  # INFO: this is relative to Chat Messages (to be rendered in GUI)
        self.graph_messages = []  # INFO: this is relative to Graph State Messages
        self.gui = GUI()  # INFO: this is relative to GUI Components properties
        
    @property
    def client(self):
        return lgi.get_langgraph_client()
    
    def is_interrupted(self):
        if len(self.graph_messages) > 0:
            return self.graph_messages[-1].get("is_interrupt", False)
        return False
    
    def get_interrupt_key(self):
        if self.is_interrupted():
            return self.graph_messages[-1].get('response_key', 'response')
        return None

# ENDREGION: Classes ----------------------------------------------------------


if "app" not in st.session_state:
    st.session_state.app = WebAppState()

        
        
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
    
    # with st.chat_message("user"):
    #     st.markdown("**Upload a file or send a message:**")
    #     file = st.file_uploader("Upload", label_visibility="collapsed")
    #     send_button = st.button("Send")



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
    
    with st.expander("📁 Session files"):
        col1, col2 = st.columns([5, 1])
        with col1:
            file_uploader = st.file_uploader("Upload", label_visibility="collapsed")
        with col2:
            send_button = st.button("Send")
    
    # INFO: First sidebar element (Will be used for displaying generated code)
    with st.expander("💻 Code generated"):
        code = '''# Example code generated by the agent (demo only — it will be dinamically filled with LLM generation tool)

spi_ts = 1

region = [-9.6, 35.9, 4.3, 43.8] # min_lon, min_lat, max_lon, max_lat

reference_period = (1981, 2010) # start_year, end_year

period_of_interest = ('2024-08', '2025-02') # start_month, end_month

cds_client = cdsapi.Client(url='https://cds.climate.copernicus.eu/api', key=getpass.getpass("YOUR CDS-API-KEY")) # CDS client
        '''
        st.code(code, language="python")
        
    # INFO: Second sidebar element (Will be used for displaying graph state)
    with st.expander("📊 Graph state"):
        st.markdown("Graph state will be displayed here")