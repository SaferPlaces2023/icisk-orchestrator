from langgraph_sdk.client import get_client, LangGraphClient, Command
import os
# from icisk_chat.logger import Logger, fmsg

LANGGRAPH_HOST = os.environ.get("LANGGRAPH_HOST", "http://localhost:2024")

def get_langgraph_client():
    print(f"Connecting to LangGraph at {LANGGRAPH_HOST}")
    client = get_client(url=LANGGRAPH_HOST)    # TODO: set url to env variable
    print(f"Connected to LangGraph at {LANGGRAPH_HOST}")
    print(f"Client: {client}")
    return client

    
async def create_thread(client, user_id):
    thread = await client.threads.create()
    thread_id = thread['thread_id']
    _ = await client.runs.create(
        thread_id,
        "agent",
        stream_mode = "updates",
        input = { 'user_id': user_id }
    )
    print(f"Thread {thread_id} assigned to user {user_id}")
    return thread['thread_id']


async def ask_agent(
    client, 
    thread_id: str, 
    message: str,
    
    interrupt_response_key: str = None,
    tool_choice: str = None
):
    
    run_args = dict()
    
    if interrupt_response_key is not None:
        run_args['command'] = Command(resume={interrupt_response_key: message})
    else:
        run_args['input'] = {"messages": [{"role": "human", "content": message}]}
        # DOC: Tool choice pass thorough chatbot node, the send only when input
        if tool_choice is not None: 
            run_args['input']['node_params'] = {'chatbot': {'tool_choice': tool_choice}}
    
    async for chunk in client.runs.stream(
        thread_id,
        "agent",
        stream_mode="updates",
        **run_args
    ):
        if chunk.event == "updates":
            
            # Logger.info(fmsg("Received updates from agent", m=chunk.data, s=1, ls=True, pp=True))
            print(f'\n\nReceived updates from agent: {chunk.data} \n\n')
            
            yield chunk.data