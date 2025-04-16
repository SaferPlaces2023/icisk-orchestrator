import os

from db import DBI

class SessionManager():
    
    def __init__(self):
        self.base_dir = os.getcwd()

    def get_session_files(self):
        return os.listdir(os.path.join(self.base_dir, "src", "icisk_orchestrator", "session", "files"))
    
SimpleSessionManager = SessionManager()