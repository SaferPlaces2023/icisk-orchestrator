import os
from pymongo import MongoClient

if __name__ == "__main__":
    
    print("Populating database with initial data...")
    
    _DB_NAME = os.environ.get('MONGODB_NAME', 'icisk_orchestrator_db')
    _CONNECTION_STRING = os.environ.get("MONGODB_DOMAIN",'mongodb://localhost:27017/')
    
    client = MongoClient(_CONNECTION_STRING)
    db = client[_DB_NAME]
    
    USERS_COLLECTION = "users"
    
    ADMIN_USER_ID = os.environ.get("ADMIN_USER_ID", "admin")
    ADMIN_USER_EMAIL = os.environ.get("ADMIN_USER_EMAIL", None)
    
    admin_exists = db[USERS_COLLECTION].find_one({ 'user_id': ADMIN_USER_ID })
    if admin_exists is None:
        print(f"Creating admin user with id {ADMIN_USER_ID} and email {ADMIN_USER_EMAIL}")
        db[USERS_COLLECTION].insert_one({
            "user_id": ADMIN_USER_ID,
            "email": ADMIN_USER_EMAIL
        })
    else:
        print(f"Admin user with id {ADMIN_USER_ID} already exists")
        
        
    TEST_USER_ID = os.environ.get("TEST_USER_ID", "test")
    TEST_USER_EMAIL = os.environ.get("TEST_USER_EMAIL", None)
    
    test_exists = db[USERS_COLLECTION].find_one({ 'user_id': TEST_USER_ID })
    if test_exists is None:
        print(f"Creating test user with id {TEST_USER_ID} and email {TEST_USER_EMAIL}")
        db[USERS_COLLECTION].insert_one({
            "user_id": TEST_USER_ID,
            "email": TEST_USER_EMAIL
        })
    else:
        print(f"Test user with id {TEST_USER_ID} already exists")
    
    client.close()
    client = None