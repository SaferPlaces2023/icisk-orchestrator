import os
import time
import subprocess


if __name__ == "__main__":

    
    # DOC: Run langgraph server
    run_langraph_commands = "langgraph dev --config src/icisk_orchestrator/agent/langgraph.json"
    
    langgrpah_process = subprocess.run(run_langraph_commands, shell = True)
    