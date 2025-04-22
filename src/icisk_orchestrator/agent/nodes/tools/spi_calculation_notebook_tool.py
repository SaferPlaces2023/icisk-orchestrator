import os
import datetime
import dateutil.relativedelta

from enum import Enum

import nbformat as nbf

from typing import Optional
from pydantic import BaseModel, Field
from langchain_core.callbacks import (
    AsyncCallbackManagerForToolRun,
    CallbackManagerForToolRun,
)

from agent import utils
from agent.common import names as N
from agent.common.notebook_templates.nbt_spi import notebook_template as nbt_spi_template
from agent.nodes.base import BaseAgentTool

from db import DBI, DBS



# DOC: This is a tool that exploits I-Cisk API to calculate SPI (Standard Precipitation Index) for a given location in a give time period.

class SPICalculationNotebookTool(BaseAgentTool):
    
    
    # DOC: Tool input schema
    class InputSchema(BaseModel):
        
        area: None | str | list[float] = Field(
            title = "Area",
            description = """The area of interest for the forecast data. If not specified use None as default.
            It   could be a bouning-box defined by [min_x, min_y, max_x, max_y] coordinates provided in EPSG:4326 Coordinate Reference System.
            Otherwise it can be the name of a country, continent, or specific geographic area.""",
            examples=[
                None,
                "Italy",
                "Paris",
                "Continental Spain",
                "Alps",
                [12, 52, 14, 53],
                [-5.5, 35.2, 5.58, 45.10],
            ]
        )
        reference_period: None | tuple = Field(
            title = "Reference Period",
            description = f"Tuple of two integere representing the start and end year of the reference period. Default is (1981, 2010).",
            examples = [
                None,
                (1981, 2010),
                (1990, 2000),
                (2000, 2020),
            ],
            default = (1981, 2010)
        )
        period_of_interest: None | tuple = Field(
            title = "Period of Interest",
            description = f"Tuple of two elements representing the start and end month in YYYY-MM format of the period of interest for which SPI has to be calculated. Default is form previous to current month { tuple( [ (datetime.datetime.now()-dateutil.relativedelta.relativedelta(months=1)).strftime('%Y-%m'), datetime.datetime.now().strftime('%Y-%m') ] ) }",
            examples = [
                None,
                ("2025-01", "2025-02"),
                ("2024-12", "2025-01"),
                ("2024-03", "2025-03"),
            ],
            default = tuple( [ (datetime.datetime.now()-dateutil.relativedelta.relativedelta(months=1)).strftime('%Y-%m'), datetime.datetime.now().strftime('%Y-%m') ] )
        )
        jupyter_notebook: None | str = Field(
            title = "Jupyter Notebook",
            description = f"The path to the jupyter notebook that was used to build the data ingest procedure. If not specified is None",
            examples = [
                None,
                "C:/Users/username/appdata/local/temp/output-<variable>.ipynb",
                "/path/to/output-<variable>-<date>.ipynb",
                "S3://bucket-name/path/to/<location>-<varibale>-data.ipynb",
            ],
            default = None
        )
        
    # DOC: Additional tool args
    notebook: DBS.Notebook = None


    # DOC: Initialize the tool with a name, description and args_schema
    def __init__(self, **kwargs):
        super().__init__(
            name = N.SPI_CALCULATION_NOTEBOOK_TOOL,
            description = """Build a new Jupyter notebook for calculating the Standardized Precipitation Index (SPI) for a given region and return the path where the notebook is saved.
            The tool uses the Climate Data Store (CDS) API to retrieve the necessary data from "ERA5-Land monthly averaged data from 1950 to present" dataset
            Use this tool when user asks for an help in SPI calculation even if user does not provide region.""",
            args_schema = SPICalculationNotebookTool.InputSchema,
            **kwargs
        )
        self.output_confirmed = True    # INFO: There is already the execution_confirmed:True
        
        
    # DOC: Validation rules ( i.e.: valid init and lead time ... ) 
    def _set_args_validation_rules(self) -> dict:
        
        return {
            'area': [
                lambda **ka: f"Invalid area coordinates: {ka['area']}. It should be a list of 4 float values representing the bounding box [min_x, min_y, max_x, max_y]." 
                    if isinstance(ka['area'], list) and len(ka['area']) != 4 else None  
            ],
            'reference_period': [
                lambda **ka: f"Invalid reference_period: {ka['reference_period']}. It should be a tuple of start and ending year as integers."
                    if type(ka['reference_period']) not in (tuple, list) or len(ka['reference_period']) != 2 else None,
                lambda **ka: f"Invalid reference_period: {ka['reference_period']}. It should be in the past, at least in the previous year."
                    if ka['reference_period'][1] > datetime.datetime.now().year else None
            ],
            'period_of_interest': [
                lambda **ka: f"Invalid period_of_interest: {ka['period_of_interest']}. It should be a tuple of two elements representing the start and end month in YYYY-MM format."
                    if type(ka['period_of_interest']) not in (tuple, list) or len(ka['period_of_interest']) != 2 else None,
                lambda **ka: f"Invalid start period_of_interest: {ka['period_of_interest'][0]}. It should be in the format YYYY-MM."
                    if utils.try_default(lambda: datetime.datetime.strptime(ka['period_of_interest'][0], "%Y-%m"), None) is None else None,
                lambda **ka: f"Invalid end period_of_interest: {ka['period_of_interest'][1]}. It should be in the format YYYY-MM."
                    if utils.try_default(lambda: datetime.datetime.strptime(ka['period_of_interest'][1], "%Y-%m"), None) is None else None,
                lambda **ka: f"Invalid lead time: {ka['period_of_interest'][1]}. It should be greater than start period_of_interest {ka['period_of_interest'][0]}."
                    if datetime.datetime.strptime(ka['period_of_interest'][0], "%Y-%m") >= datetime.datetime.strptime(ka['period_of_interest'][1], "%Y-%m") else None,
                lambda **ka: f"Invalid period_of_interest: {ka['period_of_interest']}. It can't be mor than six months in the future."
                    if datetime.datetime.strptime(ka['period_of_interest'][1], "%Y-%m") > (datetime.datetime.now() + dateutil.relativedelta.relativedelta(months=6)) else None,
            ],
            'jupyter_notebook': [
                lambda **ka: f"Invalid notebook path: {ka['jupyter_notebook']}. It should be a valid jupyter notebook file path."
                    if ka['jupyter_notebook'] is not None and not ka['jupyter_notebook'].lower().endswith('.ipynb') else None
            ]
        }
    
    
    # DOC: Inference rules ( i.e.: from location name to bbox ... )
    def _set_args_inference_rules(self) -> dict:
        
        def infer_area(**ka):
            def bounding_box_from_location_name(area):
                if type(area) is str:
                    area = utils.ask_llm(
                        role = 'system',
                        message = f"""Please provide the bounding box coordinates for the area: {area} with format [min_x, min_y, max_x, max_y] in EPSG:4326 Coordinate Reference System. 
                        Provide only the coordinates list without any additional text or explanation.""",
                        eval_output = True
                    )
                    self.execution_confirmed = False
                return area
            return bounding_box_from_location_name(ka['area'])
        
        def infer_jupyter_notebook(**ka):
            if ka['jupyter_notebook'] is None:
                return f"icisk-ai_spi-calculation_{datetime.datetime.now().isoformat(timespec='seconds').replace(':','-')}.ipynb"
            return ka['jupyter_notebook']
        
        return {
            'area': infer_area,
            'jupyter_notebook': infer_jupyter_notebook
        }
        
    
     # DOC: Preapre notebook cell code template
    def prepare_notebook(self, jupyter_notebook):
        self.notebook = DBI.notebook_by_name(author=self.graph_state.get('user_id'), notebook_name=jupyter_notebook, retrieve_source=True)
        if self.notebook is None:
            self.notebook = DBS.Notebook(
                name = jupyter_notebook,
                authors = self.graph_state.get('user_id'),
                source = nbf.v4.new_notebook()
            )
          
        self.notebook.source.cells.extend(nbt_spi_template.cells)    
        
        
    # DOC: Execute the tool → Build notebook, write it to a file and return the path to the notebook and the zarr output file
    def _execute(
        self,
        area: str | list[float],
        reference_period: tuple = (1981, 2010),
        period_of_interest: tuple = ((datetime.datetime.now()-dateutil.relativedelta.relativedelta(months=1)).strftime('%Y-%m'), datetime.datetime.now().strftime('%Y-%m')),
        jupyter_notebook: str = None,
    ): 
        # TODO: move to utils
        def necessary_imports(code: str | list[str], context_code: str | list[str] = None):
            lines = code if type(code) is list else [code]
            context_code = context_code if type(context_code) is list else [context_code] if context_code is not None else []
            lines = [ l for l in lines if l.strip() not in context_code ]
            return '\n'.join(lines)
            
        
        self.prepare_notebook(jupyter_notebook)    
        nb_values = {
            'area': area,
            'reference_period': reference_period,
            'period_of_interest': period_of_interest,
        }
        for ic,cell in enumerate(self.notebook.source.cells):
            if cell.cell_type in ("markdown", "code"):
                cell.source = utils.safe_code_lines(cell.source, format_dict=nb_values if cell.metadata.get("need_format", False) else None)
                if cell.metadata.get("check_import", False):
                    previous_import_code = '\n'.join([c.source for c in self.notebook.source.cells[:ic] if c.metadata.get("check_import", False)])
                    cell.source = necessary_imports(cell.source, context_code=previous_import_code)
        self.notebook.source.cells = [cell for cell in self.notebook.source.cells if cell.cell_type != "code" or cell.source.replace('\n', '').strip() != ""]
            
                
        DBI.save_notebook(self.notebook)
        
        return {
            "notebook": jupyter_notebook
        }
        
    
    # DOC: Try running AgentTool → Will check required, validity and inference over arguments thatn call and return _execute()
    def _run(
        self, 
        area: str | list[float],
        reference_period: tuple = (1981, 2010),
        period_of_interest: tuple = ((datetime.datetime.now()-dateutil.relativedelta.relativedelta(months=1)).strftime('%Y-%m'), datetime.datetime.now().strftime('%Y-%m')),
        jupyter_notebook: str = None,
        run_manager: None | Optional[CallbackManagerForToolRun] = None
    ) -> dict:
        
        return super()._run(
            tool_args = {
                "area": area,
                "reference_period": reference_period,
                "period_of_interest": period_of_interest,
                "jupyter_notebook": jupyter_notebook
            },
            run_manager=run_manager
        )