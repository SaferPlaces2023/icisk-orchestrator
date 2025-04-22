# DOC: Chatbot node and router

from typing_extensions import Literal

from langgraph.graph import END
from langgraph.types import Command

from langgraph.prebuilt import ToolNode

from agent import utils
from agent import names as N
from agent.common.states import BaseGraphState
from agent.nodes.tools import (
    CDSHistoricNotebookTool,
    CDSForecastNotebookTool,
    SPICalculationNotebookTool,
    CodeEditorTool
)



cds_historic_notebook_tool = CDSHistoricNotebookTool()
cds_forecast_notebook_tool = CDSForecastNotebookTool()
spi_calculation_notebook_tool = SPICalculationNotebookTool()
base_code_editor_tool = CodeEditorTool()

tools_map = {
    cds_historic_notebook_tool.name : cds_historic_notebook_tool,
    cds_forecast_notebook_tool.name : cds_forecast_notebook_tool,
    spi_calculation_notebook_tool.name : spi_calculation_notebook_tool,
    base_code_editor_tool.name : base_code_editor_tool
}

tool_node = ToolNode([tool for tool in tools_map.values()])

llm_with_tools = utils._base_llm.bind_tools([tool for tool in tools_map.values()])



def chatbot_update_messages(state: BaseGraphState):
    """Update the messages in the state with the new messages."""
    messages = state.get("node_params", dict()).get(N.CHATBOT_UPDATE_MESSAGES, dict()).get("update_messages", [])
    return {'messages': messages, 'node_params': dict()}


def chatbot(state: BaseGraphState) -> Command[Literal[END, N.CHATBOT_UPDATE_MESSAGES, N.CDS_FORECAST_SUBGRAPH, N.SPI_CALCULATION_SUBGRAPH, N.CODE_EDITOR_SUBGRAPH]]:     # type: ignore
    state["messages"] = state.get("messages", [])
    
    if len(state["messages"]) > 0:
        
        if state.get("node_params", dict()).get(N.CHATBOT_UPDATE_MESSAGES, None) is not None:
            return Command(goto=N.CHATBOT_UPDATE_MESSAGES)
            
        ai_message = llm_with_tools.invoke(state["messages"])
        
        if hasattr(ai_message, "tool_calls") and len(ai_message.tool_calls) > 0:
            
            # DOC: get the first tool call, discard others (this is ugly asf) edit: this works btw → i.e.: "get spi and compare with temp" will call cds-tool then call spi-tool then call code-editor-tool (don't know why it works))
            tool_call = ai_message.tool_calls[0]
            ai_message.tool_calls = [tool_call] 
            
            if tool_call['name'] == cds_forecast_notebook_tool.name or \
                tool_call['name'] == cds_historic_notebook_tool.name:
                return Command(goto = N.CDS_FORECAST_SUBGRAPH, update = { "messages": [ ai_message ], "node_history": [N.CHATBOT, N.CDS_FORECAST_SUBGRAPH] })
            elif tool_call['name'] == spi_calculation_notebook_tool.name:
                return Command(goto = N.SPI_CALCULATION_SUBGRAPH, update = { "messages": [ ai_message ], "node_history": [N.CHATBOT, N.SPI_CALCULATION_SUBGRAPH] })
            elif tool_call['name'] == base_code_editor_tool.name:
                return Command(goto = N.CODE_EDITOR_SUBGRAPH, update = { "messages": [ ai_message ], "node_history": [N.CHATBOT, N.CODE_EDITOR_SUBGRAPH] })

        return Command(goto = END, update = { "messages": [ ai_message ], "requested_agent": None, "node_params": dict(), "node_history": [N.CHATBOT] })
    
    return Command(goto = END, update = { "messages": [], "requested_agent": None, "node_params": dict(), "node_history": [N.CHATBOT] })