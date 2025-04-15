import os

class SessionManager():
    
    def __init__(self):
        self.base_dir = os.getcwd()

    def get_session_files(self):
        return os.listdir(os.path.join(self.base_dir, "src", "session", "files"))
    
SimpleSessionManager = SessionManager()