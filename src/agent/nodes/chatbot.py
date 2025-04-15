# DOC: Chatbot node and router

from typing_extensions import Literal

from langgraph.graph import END
from langgraph.types import Command

from agent import utils
from agent import names as N
from agent.common.states import BaseGraphState
from agent.nodes.tools import (
    CDSForecastNotebookTool,
    SPICalculationNotebookTool,
    CodeEditorTool
)



cds_forecast_notebook_tool = CDSForecastNotebookTool()
spi_calculation_notebook_tool = SPICalculationNotebookTool()
base_code_editor_tool = CodeEditorTool()

multi_agent_tools = {
    cds_forecast_notebook_tool.name : cds_forecast_notebook_tool,
    spi_calculation_notebook_tool.name : spi_calculation_notebook_tool,
    base_code_editor_tool.name : base_code_editor_tool
}

llm_with_tools = utils._base_llm.bind_tools([tool for tool in multi_agent_tools.values()])



def chatbot(state: BaseGraphState) -> Command[Literal[END, N.CDS_FORECAST_SUBGRAPH, N.SPI_CALCULATION_SUBGRAPH, N.CODE_EDITOR_SUBGRAPH]]:     # type: ignore
    state["messages"] = state.get("messages", [])
    
    ai_message = llm_with_tools.invoke(state["messages"])
    
    if hasattr(ai_message, "tool_calls") and len(ai_message.tool_calls) > 0:
        
        # DOC: get the first tool call, discard others (this is ugly asf) edit: this works btw ("get spi and compare with temp" > cds tool then spi tool then code editor tool (don't know why it works))
        tool_call = ai_message.tool_calls[0]
        ai_message.tool_calls = [tool_call] 
        
        if tool_call['name'] == cds_forecast_notebook_tool.name:
            return Command(goto = N.CDS_FORECAST_SUBGRAPH, update = { "messages": [ ai_message ] })
        elif tool_call['name'] == spi_calculation_notebook_tool.name:
            return Command(goto = N.SPI_CALCULATION_SUBGRAPH, update = { "messages": [ ai_message ] })
        elif tool_call['name'] == base_code_editor_tool.name:
            return Command(goto = N.CODE_EDITOR_SUBGRAPH, update = { "messages": [ ai_message ] })

    return Command(goto = END, update = { "messages": [ ai_message ], "requested_agent": None, "nodes_params": dict() })