import os
import time
import subprocess


if __name__ == "__main__":

    # DOC: Run streamlit server
    run_streamlit_commands = "streamlit run src/icisk_orchestrator/webapp/app.py"
    
    streamlit_process = subprocess.run(run_streamlit_commands, shell = True)
