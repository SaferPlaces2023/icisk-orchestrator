from langgraph_sdk.client import get_client, LangGraphClient, Command

# from icisk_chat.logger import Logger, fmsg


def get_langgraph_client():
    client = get_client(url="http://localhost:2024")    # TODO: set url to env variable
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
):
    
    run_args = dict()
    if interrupt_response_key is not None:
        run_args['command'] = Command(resume={interrupt_response_key: message})
    else:
        run_args['input'] = {"messages": [{"role": "human", "content": message}]}
    
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