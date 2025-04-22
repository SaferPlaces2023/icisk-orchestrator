import os

import nbformat as nbf

from bson import ObjectId


class Collections():
    """
    Class representing the collections in the database.
    """
    
    USERS = 'users'
    NOTEBOOKS = 'notebooks'
    CHATS = 'chats'


class Record():
    """
    Base record in a mongodb collection.
    """
    
    def __init__(self, _id: str | ObjectId = None):
        if isinstance(_id, str):
            self._id = ObjectId(_id)
        else:
            self._id = _id
            
    @property
    def as_dict(self):
        """
        Convert the record to a dictionary.
        """
        dict_obj = self.__dict__
        return dict_obj
    
    @property
    def as_anon_dict(self):
        dict_obj = self.as_dict
        if dict_obj.get('_id') is None:
            _ = dict_obj.pop('_id')
        return dict_obj
    
    @classmethod
    def from_dict(cls, d):
        return cls(**d)
  
  

class User(Record):
    """
    Class representing a user in mongodb
    """
    
    def __init__(self, user_id: str, email: str, **kwargs):
        super().__init__(**kwargs)
        self.user_id = user_id
        self.email = email
        
    @property
    def as_dict(self):
        """
        Convert the user to a dictionary.
        """
        obj = super().as_dict
        return obj
      


class Chat(Record):
    """
    Class representing a chat in mongodb
    """
    
    def __init__(self, user_id: str, thread_id: str, title: str, messages: list = [], **kwargs):
        super().__init__(**kwargs)
        self.user_id = user_id
        self.thread_id = thread_id
        self.title = title
        self.messages = messages
        self.pending_messages = []
        
    @property
    def as_dict(self):
        """
        Convert the chat to a dictionary.
        """
        obj = super().as_dict
        _ = obj.pop('pending_messages')
        return obj        
    
    def empty_pending(self):
        self.pending_messages = []
    
    def add_messages(self, messages: list | dict):
        """
        Add a message to the chat.
        """
        self.messages.extend(messages if isinstance(messages, list) else [messages])
        self.pending_messages.extend(messages if isinstance(messages, list) else [messages])


class Notebook(Record):
    """
    Class representing a notebook in mongodb
    """
    
    def __init__(
            self, 
            name: str, 
            source: str | nbf.NotebookNode = "{\"cells\": []}",     # DOC: Empty notebook by default
            authors: str | list[str] = [],                          # DOC: No author by default
            description: str = None,
            **kwargs
        ):
        super().__init__(**kwargs)
        self.name = name
        self.source = nbf.reads(source, as_version=4) if isinstance(source, str) else source
        self.authors = authors if isinstance(authors, list) else [authors]
        self.description = description
        
    @property
    def as_dict(self):
        """
        Convert the notebook to a dictionary.
        """
        obj = super().as_dict
        obj['source'] = nbf.writes(self.source)
        return obj
    
    @property
    def source_code(self):
        """
        Convert the notebook source to a string.
        """
        return nbf.writes(self.source)
    