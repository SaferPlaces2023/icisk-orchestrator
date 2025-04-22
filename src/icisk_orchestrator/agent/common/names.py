# DOC: names for teh graph components

# REGION: [Graph]

GRAPH = "ICISK-AGENT"

# ENDREGION: [Graph]


# REGION: [Chatbot]

CHATBOT = "chatbot"
CHATBOT_UPDATE_MESSAGES = "chatbot_update_messages"

# Endregion: [Chatbot]


# REGION: [Base Tools]

CODE_EDITOR_SUBGRAPH = "code_editor_subgraph"

CODE_EDITOR_TOOL = 'code_editor_tool'

CODE_EDITOR_TOOL_HANDLER = "code_editor_tool_handler"
CODE_EDITOR_TOOL_INTERRUPT = "code_editor_tool_interrupt"

# ENDREGION: [Base Tools]


# REGION: [SPI Calculation]

SPI_CALCULATION_SUBGRAPH = "spi_calculation_subgraph"

SPI_CALCULATION_NOTEBOOK_TOOL = "spi_calculation_notebook_tool"
SPI_CALCULATION_CODE_EDITOR_TOOL = "spi_calculation_code_editor_tool"   # ???: Very if used

SPI_CALCULATION_TOOL_HANDLER = "spi_calculation_tool_handler"
SPI_CALCULATION_TOOL_INTERRUPT = "spi_calculation_tool_interrupt"

# ENDREGION: [SPI Calculation]


# REGION: [CDS Forecast]

CDS_FORECAST_SUBGRAPH = "cds_forecast_subgraph"

CDS_FORECAST_NOTEBOOK_TOOL = "cds_forecast_notebook_tool"
CDS_FORECAST_CODE_EDITOR_TOOL = "cds_forecast_code_editor_tool"     # ???: Very if used

CDS_FORECAST_TOOL_HANDLER = "cds_forecast_tool_handler"
CDS_FORECAST_TOOL_INTERRUPT = "cds_forecast_tool_interrupt"

# ENDREGION: [CDS Forecast]

# REGION: [CDS Historic]

# CDS_HISTORIC_SUBGRAPH = "cds_historic_subgraph"   # TODO: Use 'CDS_FORECAST_SUBGRAPH'

CDS_HISTORIC_NOTEBOOK_TOOL = "cds_historic_notebook_tool"
# CDS_HISTORIC_CODE_EDITOR_TOOL = "cds_historic_code_editor_tool"   # ???: Very if used

CDS_HISTORIC_TOOL_HANDLER = "cds_historic_tool_handler"
CDS_HISTORIC_TOOL_INTERRUPT = "cds_historic_tool_interrupt"

# ENDREGION: [CDS Historic]