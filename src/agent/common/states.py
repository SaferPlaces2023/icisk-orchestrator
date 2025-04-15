"""Define the state structures for the agent."""

from __future__ import annotations

from langgraph.graph import MessagesState
from langgraph.graph.message import AnyMessage


# DOC: This is a basic state that will be used by all nodes in the graph. It ha one key: "messages" : list[AnyMessage]
class BaseGraphState(MessagesState):
    """Basic state"""
    
