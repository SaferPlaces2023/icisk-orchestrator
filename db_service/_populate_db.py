import os
from pymongo import MongoClient

if __name__ == "__main__":
    
    print("Populating database with initial data...")
    
    # TODO: Maybe import from DBI
    _DB_NAME = 'icisk_orchestrator_db'
    _CONNECTION_STRING = os.environ.get("MONGODB_DOMAIN",'mongodb://localhost:27017/')
    
    client = MongoClient(_CONNECTION_STRING)
    db = client[_DB_NAME]
    
    db['users'].insert_many([
        {
            "user_id": "admin",
            "email": "tommaso.redaelli@gecosistema.com"
        }, {
            "user_id": "test",
            "email": "tommaso.redaelli@gecosistema.com"
        }
    ])
    
    client.close()
    client = None