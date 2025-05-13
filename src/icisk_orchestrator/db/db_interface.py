# Deps
from functools import singledispatchmethod

from pymongo import MongoClient
from bson import ObjectId

import nbformat as nbf

from db import DBS, db_utils
import os
# DB general

_DB_NAME = 'icisk_orchestrator_db'   # TODO: Change to env var
_CONNECTION_STRING = os.environ.get("MONGODB_DOMAIN",'mongodb://localhost:27017/') #'mongodb://localhost:27017/'   # TODO: Change to env var

class DatabaseInterface():    
    
    client = None
    db = None
    
    def __init__(self):
        print('Initializing DatabaseInterface')
        print(f'Connection string: {_CONNECTION_STRING}')
        print(f'Database name: {_DB_NAME}')
        self.connection_string = _CONNECTION_STRING
        self.db_name = _DB_NAME
        
        
    def connect(self):
        print('Connecting to database')
        print(f'Connection string: {self.connection_string}')
        print(f'Database name: {self.db_name}')

        if self.client is None:
            self.client = MongoClient(self.connection_string)
            self.db = self.client[self.db_name]
        
    def disconnect(self):
        if self.client is not None:
            self.client.close()
            self.client = None
            
    
    def save_notebook(
        self, 
        notebook: DBS.Notebook
    ):
        """
        Save a notebook to the database.
        
        Parameters:
            notebook_name (str): The name of the notebook.
            notebook_source (nbf.NotebookNode): The source of the notebook.
            authors (list[str]): List of authors.
            notebook_description (str): Description of the notebook.
        """
        
        self.connect()
        
        notebooks_collection = self.db[DBS.Collections.NOTEBOOKS]
        
        # DOC: All notebooks will be visible to admin
        if 'admin' not in notebook.authors:
            notebook.authors.append('admin')
        
        # DOC: If notebook_id is None, we are creating a new notebook, otherwise we are updating an existing one
        if notebook._id is None:
            insert_result = notebooks_collection.insert_one(notebook.as_anon_dict)
            print(f'Inserted notebook result: {insert_result}')
        else:
            notebooks_collection.update_one(
                { '_id': notebook._id },
                { '$set': notebook.as_anon_dict }
            )
            
            
    def notebook_by_name(self, author: str, notebook_name: str, retrieve_source: bool = False) -> DBS.Notebook:
        """
        Retrieve a notebook by its name.
        
        Parameters:
            notebook_name (str): The name of the notebook.
            retrieve_source (bool): Whether to retrieve the source of the notebook or not.
        
        Returns:
            dict: Notebook document.
        """
        
        self.connect()
        
        notebooks_collection = self.db[DBS.Collections.NOTEBOOKS]
        
        # DOC: Retrieve the notebook by its name
        if retrieve_source:
            notebook = notebooks_collection.find_one({ 'authors': author, 'name': notebook_name })
        else:
            notebook = notebooks_collection.find_one({ 'authors': author, 'name': notebook_name }, { 'source': 0 })
        
        notebook = db_utils.cast_to_schema(DBS.Notebook, notebook)
        return notebook
        
        
    def notebooks_by_author(self, author: str, retrieve_source: bool = False):
        """
        Retrieve all notebooks by a given author.
        
        Parameters:
            author (str): The author of the notebooks.
            retrieve_source (bool): Whether to retrieve the source of the notebooks or not.
        
        Returns:
            list: List of notebooks by the author.
        """
        
        self.connect()
        
        notebooks_collection = self.db['notebooks']
        
        # DOC: Retrieve all notebooks by the author
        if retrieve_source:
            notebooks = list(notebooks_collection.find({ 'authors': author }))
        else:
            notebooks = list(notebooks_collection.find({ 'authors': author }, { 'source': 0 }))
        
        notebooks = db_utils.cast_to_schema(DBS.Notebook, notebooks)
        return notebooks
        
        
    def user_by_id(self, user_id: str):
        """
        Retrieve a user by its ID.
        
        Parameters:
            user_id (str): The ID of the user.
        
        Returns:
            dict: User document.
        """
        print("USER BY ID")
        print(f'User ID: {user_id}')
        print(f'User ID type: {type(user_id)}')
        
        self.connect()
        
        users_collection = self.db[DBS.Collections.USERS]
        
        # DOC: Retrieve the user by its ID
        user = users_collection.find_one({ 'user_id': user_id })
        
        user = db_utils.cast_to_schema(DBS.User, user)
        
        return user
    
    
    def chat_by_thread_id(self, thread_id: str):
        self.connect()
        chats_collection = self.db[DBS.Collections.CHATS]
        chat = chats_collection.find_one({ 'thread_id': thread_id })
        chat = db_utils.cast_to_schema(DBS.Chat, chat)
        return chat
    
    
    def update_chat(self, chat: DBS.Chat):
        """
        Update a chat in the database.
        
        Parameters:
            _id (str | ObjectId): The ID of the chat.
            user_id (str): The ID of the user.
            messages (list | dict): The messages to be added to the chat.
        """
        
        self.connect()
        
        chats_collection = self.db[DBS.Collections.CHATS]
        
        if self.chat_by_thread_id(thread_id = chat.thread_id) is None:
            # DOC: If the chat does not exist, create a new one
            chats_collection.insert_one(chat.as_anon_dict)
        else:
            chats_collection.update_one(
                { 'thread_id': chat.thread_id },
                { "$push": { "messages": { "$each": chat.pending_messages } } }
            )
        
        chat.empty_pending()
        
        
    def chat_by_user_id(self, user_id: str, retrieve_messages: bool = False):
        """
        Retrieve a chat by its user ID.
        
        Parameters:
            user_id (str): The ID of the user.
        
        Returns:
            dict: Chat document.
        """
        
        self.connect()
        
        chats_collection = self.db[DBS.Collections.CHATS]
        
        # DOC: Retrieve the chat by its user ID
        chats = list(chats_collection.find({ 'user_id': user_id }, { 'messages': 0 }))
        
        chats = db_utils.cast_to_schema(DBS.Chat, chats)
        
        return chats
                
        
    

# DOC: Singleton instance of the DatabaseInterface class
DBI = DatabaseInterface()