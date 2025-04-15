import os
import time
import subprocess


if __name__ == "__main__":

    
    # DOC: Run langgraph server
    run_langraph_commands = [
        f"cd {os.getcwd()}",
        f"langgraph dev --config src/agent/langgraph.json"
    ]
    run_langraph = " && ".join(run_langraph_commands)
    
    langgraph_process = subprocess.run(f'start "langgraph agent" cmd /k "{run_langraph}"', shell = True)
    
    
    # DOC: Wait for langgraph server to start
    time.sleep(5)
    
    
    # DOC: Run streamlit server
    run_streamlit_commands = [
        f"cd {os.getcwd()}",
        "streamlit run src/webapp/app.py"
    ]
    run_streamlit = " && ".join(run_streamlit_commands)
    
    streamlit_process = subprocess.run(f'start "streamlit app" cmd /k "{run_streamlit}"', shell = True)