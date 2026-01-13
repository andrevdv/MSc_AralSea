from pathlib import Path
from src.paths import *
import ewatercycle.forcing
import matplotlib.pyplot as plt
import xarray as xr

def setup_ERA5_forcing(shape_name: str, forcing_type: str, start: str, end: str):
    """
    Setup and generate forcing data for a given shapefile and dataset.

    Parameters
    ----------
    shape_name : str
        Name of the shapefile (should match folder and shapefile name, lowercase)
    forcing_type : str
        Type of forcing dataset, e.g., "ERA5", "CMIP"
    start : str
        Start date in ISO format, e.g., "1950-01-01T00:00:00Z"
    end : str
        End date in ISO format, e.g., "2020-12-31T00:00:00Z"

    Returns
    -------
    ewatercycle.forcing.Forcing
        The generated forcing object
    """
    # Path to the shapefile
    shapefile = SHAPEFILES / shape_name / f"{shape_name}.shp"

    # Directory where forcing outputs will be stored
    forcing_dir = FORCING_OUTPUT / f"{forcing_type}" / f"{shape_name}"
    forcing_dir.mkdir(parents=True, exist_ok=True)

    # Generate forcing using eWaterCycle
    forcing = ewatercycle.forcing.sources["LumpedMakkinkForcing"].generate(
        dataset=forcing_type,
        start_time=start,
        end_time=end,
        shape=shapefile,
        directory=forcing_dir
    )

    return forcing

def setup_CMIP_historical_forcing(shape_name:str, start: str, end:str):

    # Path to the shapefile
    shapefile = SHAPEFILES / shape_name / f"{shape_name}.shp"

    # Directory where forcing outputs will be stored
    forcing_dir = FORCING_CMIP_HIST / f"{shape_name}"
    forcing_dir.mkdir(parents=True, exist_ok=True)

    cmip_historical =  {
        'project': 'CMIP6',
        'exp': 'historical',
        'dataset': 'MPI-ESM1-2-HR',
        "ensemble": 'r1i1p1f1',
        'grid': 'gn'
    }

    CMIP_forcing = ewatercycle.forcing.sources["LumpedMakkinkForcing"].generate(
        dataset=cmip_historical,
        start_time=start,
        end_time=end,
        shape=shapefile,
        directory=forcing_dir,
    )

    return CMIP_forcing













def load_lumped_forcing(shape_name: str, forcing_type: str, base_forcing_dir=None):
    """
    Load previously generated lumped forcing data for a given shapefile.

    Parameters
    ----------
    shape_name : str
        Name of the shapefile / catchment (lowercase, consistent with folder names)
    forcing_type : str
        Forcing type, e.g., "ERA5", "CMIP_HIST"
    base_forcing_dir : pathlib.Path, optional
        Base directory where forcing outputs are stored.
        If None, defaults to FORCING_OUTPUT from paths.py

    Returns
    -------
    ewatercycle.forcing.Forcing
        Loaded forcing object
    """


    # Use default forcing output folder if none provided
    if base_forcing_dir is None:
        base_forcing_dir = FORCING_OUTPUT

    # Construct the load path
    load_location = base_forcing_dir / f"{forcing_type}"/ f"{shape_name}"  / "work" / "diagnostic" / "script"

    # Load the forcing
    forcing = ewatercycle.forcing.sources["LumpedMakkinkForcing"].load(directory=load_location)
    
    return forcing


def plot_ERA5_forcing(forcing_obj, shape_name: str = None):
    """
    Plot precipitation, temperature, shortwave radiation, and potential evaporation
    from a loaded ERA5 forcing object.
    """
    ERA5_data = {
        'precipitation pr': xr.open_dataset(forcing_obj['pr']),
        'temperature tas': xr.open_dataset(forcing_obj['tas']),
        'incoming_shortwave_radiation rsds': xr.open_dataset(forcing_obj['rsds']),
        'potential_evaporation evspsblpot': xr.open_dataset(forcing_obj['evspsblpot'])
    }

    plt.figure(figsize=(15, 10))
    for i, (name, data) in enumerate(ERA5_data.items(), 1):
        plt.subplot(2, 2, i)
        variable_name = name.split(" ")[-1]
        title_name = name.split(" ")[0]
        data[variable_name].plot()
        plt.title(f"{title_name}")
        plt.grid(linestyle="--",alpha=0.5)
            
    if shape_name:
        plt.suptitle(f"ERA5 LumpedMakkink Forcing Data \n (shapefile = {shape_name})", fontsize=20)
    else:
        plt.suptitle(f"ERA5 LumpedMakkink Forcing Data", fontsize=20)
    plt.tight_layout()
    plt.show()


