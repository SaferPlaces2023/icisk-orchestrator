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
from agent.nodes.base import BaseAgentTool

from db import DBI



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
    notebook: nbf.NotebookNode = nbf.v4.new_notebook()


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
        existing_jupyter_notebook = DBI.notebook_by_name(author=self.graph_state.get('user_id'), notebook_name=jupyter_notebook, retrieve_source=True)
        if existing_jupyter_notebook is not None:
            self.notebook = existing_jupyter_notebook
            
        self.notebook.cells.extend([
            nbf.v4.new_code_cell("""
                # Section "Dependencies"

                %%capture

                import os
                import math
                import datetime
                from dateutil.relativedelta import relativedelta
                import getpass

                import numpy as np
                import pandas as pd
                import xarray as xr

                import scipy.stats as stats
                from scipy.special import gammainc, gamma
                
                import matplotlib.pyplot as plt

                !pip install "cdsapi>=0.7.4"
                import cdsapi
                
                !pip install cartopy
                import cartopy.crs as ccrs
                import cartopy.feature as cfeature
            """),
            nbf.v4.new_code_cell("""
                # Section "Parameters"

                spi_ts = 1

                area = {area} # min_lon, min_lat, max_lon, max_lat

                reference_period = {reference_period} # start_year, end_year

                period_of_interest = {period_of_interest} # start_month, end_month

                cds_client = cdsapi.Client(url='https://cds.climate.copernicus.eu/api', key=getpass.getpass("YOUR CDS-API-KEY")) # CDS client
            """, metadata={"need_format": True}),
            nbf.v4.new_code_cell("""
                filename = f'era5_land__total_precipitation__{{"_".join([str(c) for c in area])}}__monthly__{{reference_period[0]}}_{{reference_period[1]:02d}}.nc'

                out_dir = 'tmpdir'
                os.makedirs(out_dir, exist_ok=True)

                cds_out_filename = os.path.join(out_dir, filename)

                if not os.path.exists(cds_out_filename):
                    cds_dataset = 'reanalysis-era5-land-monthly-means'
                    cds_query =  {{
                        'product_type': 'monthly_averaged_reanalysis',
                        'variable': 'total_precipitation',
                        'year': [str(year) for year in range(*reference_period)],
                        'month': [f'{{month:02d}}' for month in range(1, 13)],
                        'time': '00:00',
                        'area': [
                            area[3],  # N
                            area[0],  # W
                            area[1],  # S
                            area[2]   # E
                        ],
                        "data_format": "netcdf",
                        "download_format": "unarchived"
                    }}

                    cds_client.retrieve(cds_dataset, cds_query, cds_out_filename)

                cds_ref_data = xr.open_dataset(cds_out_filename)
            """),
            nbf.v4.new_code_cell("""
                # Get (Years, Years-Months) couple for the CDS api query. (We can query just one month at time)
                period_of_interest = (datetime.datetime.strptime(period_of_interest[0], "%Y-%m"), datetime.datetime.strptime(period_of_interest[1], "%Y-%m"))
                spi_start_date = period_of_interest[0] - relativedelta(months=spi_ts-1)
                spi_years_range = list(range(spi_start_date.year, period_of_interest[1].year+1))
                spi_month_range = []
                for iy,year in enumerate(range(spi_years_range[0], spi_years_range[-1]+1)):
                    if iy==0 and len(spi_years_range)==1:
                        spi_month_range.append([month for month in range(spi_start_date.month, period_of_interest[1].month+1)])
                    elif iy==0 and len(spi_years_range)>1:
                        spi_month_range.append([month for month in range(spi_start_date.month, 13)])
                    elif iy>0 and iy==len(spi_years_range)-1:
                        spi_month_range.append([month for month in range(1, period_of_interest[1].month+1)])
                    else:
                        spi_month_range.append([month for month in range(1, 13)])

                def build_cds_hourly_data_filepath(year, month):
                    dataset_part = 'reanalysis_era5_land__total_precipitation__hourly'
                    time_part = f'{{year}}-{{month[0]:02d}}_{{year}}-{{month[-1]:02d}}'
                    filename = f'{{dataset_part}}__{{"_".join([str(c) for c in area])}}__{{time_part}}.nc'
                    filedir = os.path.join(out_dir, dataset_part)
                    if not os.path.exists(filedir):
                        os.makedirs(filedir, exist_ok=True)
                    filepath = os.path.join(filedir, filename)
                    return filepath

                def floor_decimals(number, decimals=0):
                    factor = 10 ** decimals
                    return math.floor(number * factor) / factor

                def ceil_decimals(number, decimals=0):
                    factor = 10 ** decimals
                    return math.ceil(number * factor) / factor

                # CDS API query
                cds_poi_data_filepaths = []
                for q_idx, (year,year_months) in enumerate(zip(spi_years_range, spi_month_range)):
                    for ym in year_months:
                        cds_poi_data_filepath = build_cds_hourly_data_filepath(year, [ym])
                        if not os.path.exists(cds_poi_data_filepath):
                            cds_dataset = 'reanalysis-era5-land'
                            cds_query =  {{
                                'variable': 'total_precipitation',
                                'year': [str(year)],
                                'month': [f'{{month:02d}}' for month in year_months],
                                'day': [f'{{day:02d}}' for day in range(1, 32)],
                                'time': [f'{{hour:02d}}:00' for hour in range(0, 24)],
                                'area': [
                                    ceil_decimals(area[3], 1),    # N
                                    floor_decimals(area[0], 1),   # W
                                    floor_decimals(area[1], 1),   # S
                                    ceil_decimals(area[2], 1),    # E
                                ],
                                "data_format": "netcdf",
                                "download_format": "unarchived"
                            }}
                            cds_client.retrieve(cds_dataset, cds_query, cds_poi_data_filepath)

                    print(f'{{q_idx+1}}/{{len(year_months)}}/{{len(spi_years_range)}} - CDS API query completed')
                    cds_poi_data_filepaths.append(cds_poi_data_filepath)

                cds_poi_data = [xr.open_dataset(fp) for fp in cds_poi_data_filepaths]
                cds_poi_data = xr.concat(cds_poi_data, dim='valid_time')
                cds_poi_data = cds_poi_data.sel(valid_time=(cds_poi_data.valid_time.dt.date>=period_of_interest[0].date()) & (cds_poi_data.valid_time.dt.date<=period_of_interest[1].date()))
            """),
            nbf.v4.new_code_cell("""
                # Preprocess reference dataset
                cds_ref_data = cds_ref_data.drop_vars(['number', 'expver'])
                cds_ref_data = cds_ref_data.rename({{'valid_time': 'time', 'latitude': 'lat', 'longitude': 'lon'}})
                cds_ref_data = cds_ref_data * cds_ref_data['time'].dt.days_in_month
                cds_ref_data = cds_ref_data.assign_coords(
                    lat=np.round(cds_ref_data.lat.values, 6),
                    lon=np.round(cds_ref_data.lon.values, 6),
                )
                cds_ref_data = cds_ref_data.sortby(['time', 'lat', 'lon'])

                # Preprocess period-of-interest dataset
                cds_poi_data = cds_poi_data.drop_vars(['number', 'expver'])
                cds_poi_data = cds_poi_data.rename({{'valid_time': 'time', 'latitude': 'lat', 'longitude': 'lon'}})
                cds_poi_data = cds_poi_data.resample(time='1ME').sum()                                   # Resample to monthly total data
                cds_poi_data = cds_poi_data.assign_coords(time=cds_poi_data.time.dt.strftime('%Y-%m-01'))  # Set month day to 01
                cds_poi_data = cds_poi_data.assign_coords(time=pd.to_datetime(cds_poi_data.time))
                cds_poi_data['tp'] = cds_poi_data['tp'] / 12                                              # Convert total precipitation to monthly average precipitation
                cds_poi_data = cds_poi_data.assign_coords(
                    lat=np.round(cds_poi_data.lat.values, 6),
                    lon=np.round(cds_poi_data.lon.values, 6),
                )
                cds_poi_data = cds_poi_data.sortby(['time', 'lat', 'lon'])

                # Get whole dataset
                ts_dataset = xr.concat([cds_ref_data, cds_poi_data], dim='time')
                ts_dataset = ts_dataset.drop_duplicates(dim='time').sortby(['time', 'lat', 'lon'])
            """),
            nbf.v4.new_code_cell("""
                # Compute SPI function
                def compute_timeseries_spi(monthly_data, spi_ts, nt_return=1):
                    # Compute SPI index for a time series of monthly data
                    # REF: https://drought.emergency.copernicus.eu/data/factsheets/factsheet_spi.pdf
                    # REF: https://mountainscholar.org/items/842b69e8-a465-4aeb-b7ec-021703baa6af [ page 18 to 24 ]
                    
                    # SPI calculation needs finite-values and non-zero values
                    if all([md<=0 for md in monthly_data]):
                        return 0
                    if all([np.isnan(md) or md==0 for md in monthly_data]):
                        return np.nan
                    
                    df = pd.DataFrame({{'monthly_data': monthly_data}})

                    # Totalled data over t_scale rolling windows
                    if spi_ts > 1:
                        t_scaled_monthly_data = df.rolling(spi_ts).sum().monthly_data.iloc[spi_ts:]
                    else:
                        t_scaled_monthly_data = df.monthly_data

                    # Gamma fitted params
                    a, _, b = stats.gamma.fit(t_scaled_monthly_data, floc=0)

                    # Cumulative probability distribution
                    G = lambda x: stats.gamma.cdf(x, a=a, loc=0, scale=b)

                    m = (t_scaled_monthly_data==0).sum()
                    n = len(t_scaled_monthly_data)
                    q = m / n # zero prob

                    H = lambda x: q + (1-q) * G(x) # zero correction

                    t = lambda Hx: math.sqrt(
                        math.log(1 /
                        (math.pow(Hx, 2) if 0<Hx<=0.5 else math.pow(1-Hx, 2))
                    ))

                    c0, c1, c2 = 2.515517, 0.802853, 0.010328
                    d1, d2, d3 = 1.432788, 0.189269, 0.001308

                    Hxs = t_scaled_monthly_data[-spi_ts:].apply(H)
                    txs = Hxs.apply(t)

                    Z = lambda Hx, tx: ( tx - ((c0 + c1*tx + c2*math.pow(tx,2)) / (1 + d1*tx + d2*math.pow(tx,2) + d3*math.pow(tx,3) )) ) * (-1 if 0<Hx<=0.5 else 1)

                    spi_t_indexes = pd.DataFrame(zip(Hxs, txs), columns=['H','t']).apply(lambda x: Z(x.H, x.t), axis=1).to_list()

                    return np.array(spi_t_indexes[-nt_return]) if nt_return==1 else np.array(spi_t_indexes[-nt_return:])

                # Compute SPI over each cell
                month_spi_coverages = []
                for month in cds_poi_data.time:
                    month_spi_coverage = xr.apply_ufunc(
                        lambda tile_timeseries: compute_timeseries_spi(tile_timeseries, spi_ts=spi_ts, nt_return=1),
                        ts_dataset.sel(time=ts_dataset.time<=month).tp.sortby('time'),
                        input_core_dims = [['time']],
                        vectorize = True
                    )
                    month_spi_coverages.append((
                        month.dt.date.item(),
                        month_spi_coverage
                    ))

                # Create SPI dataset
                spi_times = [msc[0] for msc in month_spi_coverages]
                spi_grids = [msc[1] for msc in month_spi_coverages]

                spi_dataset = xr.concat(spi_grids, dim='time').to_dataset()
                spi_dataset = spi_dataset.assign_coords({{'time': spi_times}})
                spi_dataset = spi_dataset.rename_vars({{'tp': 'spi'}})

                spi_values = spi_dataset.spi.values
            """),
            nbf.v4.new_code_cell("""
                # variable "spi_dataset" is a xarray.Dataset with three dimensions ('time', 'lat', 'lon') and a 'spi' var related to those dimensions
                display(spi_dataset)

                # variable "spi_values" is a numpy.array with shape (time, lat, lon) and it is representig numerical values of spi index over each time for each lat-lon cell
                display(spi_values) 
            """)
        ])
        
        
    # DOC: Execute the tool → Build notebook, write it to a file and return the path to the notebook and the zarr output file
    def _execute(
        self,
        area: str | list[float],
        reference_period: tuple = (1981, 2010),
        period_of_interest: tuple = ((datetime.datetime.now()-dateutil.relativedelta.relativedelta(months=1)).strftime('%Y-%m'), datetime.datetime.now().strftime('%Y-%m')),
        jupyter_notebook: str = None,
    ): 
        self.prepare_notebook(jupyter_notebook)    
        nb_values = {
            'area': area,
            'reference_period': reference_period,
            'period_of_interest': period_of_interest,
        }
        for cell in self.notebook.cells:
            if cell.cell_type in ("markdown", "code"):
                cell.source = utils.safe_code_lines(cell.source, format_dict=nb_values if cell.metadata.get("need_format", False) else None)
        
        DBI.save_notebook(
            notebook_id = self.notebook.get('_id', None),
            notebook_name = self.notebook.get('name', jupyter_notebook),
            notebook_source = self.notebook['source'],
            authors = self.notebook.get('authors', self.graph_state.get('user_id')),
            notebook_description = self.notebook.get('description', None)
        )
        
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