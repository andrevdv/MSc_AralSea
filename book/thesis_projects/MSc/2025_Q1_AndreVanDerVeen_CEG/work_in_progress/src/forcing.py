from pathlib import Path
from src.paths import *
from src.utils import get_integer_multiple_bounds
import ewatercycle.forcing
import matplotlib.pyplot as plt
import xarray as xr

def setup_ERA5_forcing(shape_name: str, start: str, end: str):
    """
    Setup and generate forcing data for a given shapefile and dataset.

    Parameters
    ----------
    shape_name : str
        Name of the shapefile (should match folder and shapefile name)
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

    #year for naming
    year_span = f"{start[:4]}-{end[:4]}"

    # Directory where forcing outputs will be stored
    forcing_dir = (
        FORCING_ERA5
        / shape_name
        / year_span

    )
    forcing_dir.mkdir(parents=True, exist_ok=True)

    # Generate forcing using eWaterCycle
    forcing = ewatercycle.forcing.sources["LumpedMakkinkForcing"].generate(
        dataset="ERA5",
        start_time=start,
        end_time=end,
        shape=shapefile,
        directory=forcing_dir
    )

    return forcing

def setup_CMIP_historical_forcing(shape_name:str, start: str, end:str):

    # Path to the shapefile
    shapefile = SHAPEFILES / shape_name / f"{shape_name}.shp"
    
    #year for naming
    year_span = f"{start[:4]}-{end[:4]}"

    # Directory where forcing outputs will be stored
    forcing_dir =(
        FORCING_CMIP_HIST 
        / shape_name
        / year_span
    ) 
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

def load_lumped_forcing(shape_name: str, forcing_type: str, year_span: str, base_forcing_dir=None):
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
    load_location = base_forcing_dir / f"{forcing_type}"/ f"{shape_name}" /year_span  / "work" / "diagnostic" / "script"

    # Load the forcing
    forcing = ewatercycle.forcing.sources["LumpedMakkinkForcing"].load(directory=load_location)
    
    return forcing

def _ensure_dataset(obj):
    if isinstance(obj, xr.Dataset):
        return obj
    return xr.open_dataset(obj)


def plot_ERA5_forcing(forcing_obj, shape_name: str = None):
    """
    Plot precipitation, temperature, shortwave radiation, and potential evaporation
    from a loaded ERA5 forcing object.
    """




    ERA5_data = {
        'precipitation pr': _ensure_dataset(forcing_obj['pr']),
        'temperature tas': _ensure_dataset(forcing_obj['tas']),
        'incoming_shortwave_radiation rsds': _ensure_dataset(forcing_obj['rsds']),
        'potential_evaporation evspsblpot': _ensure_dataset(forcing_obj['evspsblpot'])
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

def create_forcing_slice(forcing_obj, start, end):
    """
    Temporarily slice ERA5 forcing data in memory.
    To use in HBV (and Leakybucket?)

    NOT WORKING FOR NOW, HBV ONLY ACCEPTS REAL EWATERCYCLE FORCING

    Parameters
    ----------
    forcing_obj : dict-like
        Must contain paths for 'pr', 'tas', 'rsds', 'evspsblpot'
    start, end : str
        Time slice, e.g. "1990-01-01", "2014-12-31"

    Returns
    -------
    dict[str, xarray.Dataset]
        Sliced datasets (not written to disk)
    """
    #NOT WORKING FOR NOW, HBV ONLY ACCEPTS REAL EWATERCYCLE FORCING
    sliced = {}

    for var in ["pr", "tas", "rsds", "evspsblpot"]:
        ds = xr.open_dataset(forcing_obj[var])
        sliced[var] = ds.sel(time=slice(start, end))

    return sliced


def setup_ERA5_PCR_forcing(shape_name: str, start: str, end: str):
    """
    Setup and generate forcing data for a given shapefile.
    To be used with PCR-GLOBWB model.

    Parameters
    ----------
    shape_name : str
        Name of the shapefile (should match folder and shapefile name)
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

    #year for naming
    year_span = f"{start[:4]}-{end[:4]}"

    # Directory where forcing outputs will be stored
    forcing_dir = (
        FORCING_PCRGLOB
        / f"ERA5_{year_span}"
        / shape_name

    )
    forcing_dir.mkdir(parents=True, exist_ok=True)

    esmvaltool_padding = 2

    lon_min_f, lat_min_f, lon_max_f, lat_max_f = get_integer_multiple_bounds(
    shapefile, #   <----- add shapefiles here
    multiple=3, #makes sure resolution is always correct
    )

    pcrglobwb_forcing = ewatercycle.forcing.sources["PCRGlobWBForcing"].generate(
        dataset="ERA5",
        start_time=start,
        end_time=end,
        start_time_climatology=start,
        end_time_climatology=end,
        shape=shapefile,
        extract_region={
        "start_longitude": lon_min_f - esmvaltool_padding,
        "end_longitude": lon_max_f + esmvaltool_padding,
        "start_latitude": lat_min_f - esmvaltool_padding,
        "end_latitude": lat_max_f + esmvaltool_padding,},
        directory = forcing_dir
        )
    
    return pcrglobwb_forcing



