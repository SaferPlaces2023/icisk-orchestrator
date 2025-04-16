# Deps

from pymongo import MongoClient
from bson import ObjectId

import nbformat as nbf

# DB general

_DB_NAME = 'icisk_orchestrator_db'   # TODO: Change to env var
_CONNECTION_STRING = 'mongodb://localhost:27017/'   # TODO: Change to env var

class DatabaseInterface():    
    
    client = None
    db = None
    
    def __init__(self):
        self.connection_string = _CONNECTION_STRING
        self.db_name = _DB_NAME
        
        
    def connect(self):
        if self.client is None:
            self.client = MongoClient(self.connection_string)
            self.db = self.client[self.db_name]
        
    def disconnect(self):
        if self.client is not None:
            self.client.close()
            self.client = None
        
        
    def save_notebook(self, notebook_id: str, notebook_name: str, notebook_source: str | nbf.NotebookNode, authors: str | list[str], notebook_description: str = None):
        """
        Save a notebook to the database.
        
        Parameters:
            notebook_name (str): The name of the notebook.
            notebook_source (nbf.NotebookNode): The source of the notebook.
            authors (list[str]): List of authors.
            notebook_description (str): Description of the notebook.
        """
        
        self.connect()
        
        notebooks_collection = self.db['notebooks']     # TODO: Move names to db-schema-class
        
        # DOC: Get notebook source if filename is provided
        if isinstance(notebook_source, str):
            with open(notebook_source, 'r') as f:
                notebook_source = nbf.read(f, as_version=4)
        
        # DOC: All notebooks will be visible to admin
        if isinstance(authors, str):
            authors = [ authors ]
        if 'ADMIN' not in authors:
            authors.append('ADMIN')
        
        # DOC: Create the notebook document to be inserted or updated in the collection
        notebook_document = {
            'name': notebook_name,
            'source': nbf.writes(notebook_source),
            'authors': authors,
            'description': notebook_description,
        }
        
        # DOC: If notebook_id is None, we are creating a new notebook, otherwise we are updating an existing one
        if notebook_id is None:
            insert_result = notebooks_collection.insert_one(notebook_document)
            print(f'Inserted notebook result: {insert_result}')
        else:
            notebooks_collection.update_one(
                { '_id': ObjectId(notebook_id) },
                { '$set': notebook_document }
            )
            
            
    def notebook_by_name(self, notebook_name: str, retrieve_source: bool = False):
        """
        Retrieve a notebook by its name.
        
        Parameters:
            notebook_name (str): The name of the notebook.
            retrieve_source (bool): Whether to retrieve the source of the notebook or not.
        
        Returns:
            dict: Notebook document.
        """
        
        self.connect()
        
        notebooks_collection = self.db['notebooks']
        
        # DOC: Retrieve the notebook by its name
        if retrieve_source:
            return notebooks_collection.find_one({ 'name': notebook_name })
        else:
            return notebooks_collection.find_one({ 'name': notebook_name }, { 'source': 0 })
        
        
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
            return list(notebooks_collection.find({ 'authors': author }))
        else:
            return list(notebooks_collection.find({ 'authors': author }, { 'source': 0 }))
        
        

# DOC: Singleton instance of the DatabaseInterface class
DBI = DatabaseInterface()