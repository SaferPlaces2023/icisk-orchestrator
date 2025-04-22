import os
import datetime

import nbformat as nbf

notebook_template = nbf.v4.new_notebook()
notebook_template.cells.extend([
    nbf.v4.new_code_cell("""
        # Section "Dependencies"

        %%capture

        import os
        import json
        import datetime
        import requests
        import getpass
        import pprint

        import numpy as np
        import pandas as pd

        !pip install zarr xarray
        import xarray as xr

        !pip install s3fs
        import s3fs

        !pip install "cdsapi>=0.7.4"
        import cdsapi
        
        !pip install cartopy
        import cartopy.crs as ccrs
        import cartopy.feature as cfeature
    """, metadata={"check_import": True})
    
    # TODO: And many more ...
    
])