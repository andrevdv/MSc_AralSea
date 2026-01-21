from pathlib import Path
from src.paths import *
from src.utils import get_integer_multiple_bounds
import ewatercycle.forcing
import matplotlib.pyplot as plt
import xarray as xr
import xesmf as xe


# ===========================================================================
# FORCING GENERATION (LUMPED)
# - Generate lumped forcing for use in HBV, Leaky Bucket, etc.
# - Variables included:
#     * temperature
#     * precipitation
#     * incoming_shortwave_radiation
#     * potential_evaporation
# - Sources included:
#     * ERA5 (observations / reference)
#     * CMIP historical
#     * CMIP future (SSP scenarios)
# ===========================================================================


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

def setup_CMIP_historical_forcing(shape_name:str, start: str, end:str, model:str="MPI-ESM1-2-HR"):

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
        'dataset': model,
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

def setup_CMIP_future_forcing(shape_name:str, start: str, end:str, ssp:str, model:str="EC-Earth3"):


    # Path to the shapefile
    shapefile = SHAPEFILES / shape_name / f"{shape_name}.shp"
    
    #year for naming
    year_span = f"{start[:4]}-{end[:4]}"

    # Directory where forcing outputs will be stored
    forcing_dir =(
        FORCING_CMIP_FUT
        / model
        / ssp
        / shape_name
        / year_span
    ) 


    forcing_dir.mkdir(parents=True, exist_ok=True)

    cmip_dataset =  {
        'project': 'CMIP6',
        'activity': 'ScenarioMIP',
        'exp': ssp,
        'mip': 'day',
        'dataset': model,
        'ensemble': 'r1i1p1f1',
        'grid': '*'
    }

    CMIP_forcing = ewatercycle.forcing.sources["LumpedMakkinkForcing"].generate(
        dataset=cmip_dataset,
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


#NOT WORKING FOR NOW, HBV ONLY ACCEPTS REAL EWATERCYCLE FORCING
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

# ===========================================================================
# FORCING GENERATION (PCR-GLOBWB)
# - Generate combined PCR-GLOBWB forcing
# - Variables included:
#     * temperature
#     * precipitation
# - Includes:
#     * ERA5 (observations / reference)
#     * CMIP historical
#     * CMIP future (SSP scenarios)
# ===========================================================================

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

def setup_cmip_hist_PCR_forcing(shape_name: str, start: str, end: str, model:str= "MPI-ESM1-2-HR" ,ensemble:str = "r1i1p1f1"):
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

    cmip_historical =  {
        'project': 'CMIP6',
        'exp': 'historical',
        'dataset': model,
        "ensemble": ensemble,
        'grid': 'gn'
    }


    #year for naming
    year_span = f"{start[:4]}-{end[:4]}"

    # Directory where forcing outputs will be stored
    forcing_dir = (
        FORCING_PCRGLOB
        / f"CMIP6_{model}_{year_span}"
        / shape_name

    )
    forcing_dir.mkdir(parents=True, exist_ok=True)

    esmvaltool_padding = 2

    lon_min_f, lat_min_f, lon_max_f, lat_max_f = get_integer_multiple_bounds(
    shapefile, #   <----- add shapefiles here
    multiple=3, #makes sure resolution is always correct
    )



    pcrglobwb_forcing = ewatercycle.forcing.sources["PCRGlobWBForcing"].generate(
        dataset=cmip_historical,
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

def setup_cmip_fut_PCR_forcing(shape_name: str, start: str, end: str,ssp: str, model:str = "EC-Earth3", ensemble:str = "r1i1p1f1"):
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



    cmip_dataset =  {
    'project': 'CMIP6',
    'activity': 'ScenarioMIP',
    'exp': ssp,
    'mip': 'day',
    'dataset': model,
    'ensemble': ensemble,
    'grid': '*'
}


    #year for naming
    year_span = f"{start[:4]}-{end[:4]}"

    # Directory where forcing outputs will be stored
    forcing_dir = (
        FORCING_PCRGLOB
        / "CMIP6"
        / model
        / ssp
        / ensemble
        / year_span
        / shape_name
    )
    forcing_dir.mkdir(parents=True, exist_ok=True)

    esmvaltool_padding = 2

    lon_min_f, lat_min_f, lon_max_f, lat_max_f = get_integer_multiple_bounds(
    shapefile, #   <----- add shapefiles here
    multiple=3, #makes sure resolution is always correct
    )



    pcrglobwb_forcing = ewatercycle.forcing.sources["PCRGlobWBForcing"].generate(
        dataset=cmip_dataset,
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



# ===========================================================================
# REGRIDDING
# - Regrid CMIP forcing to ERA5 grid
# - Applies to precipitation and temperature variables
# - Overwrites original CMIP files 
# ===========================================================================

def regrid_pcrglobwb_forcing(cmip_forcing, era5_forcing):
    """
    Regrid CMIP PCR-GLOBWB forcing to match the ERA5 grid for precipitation and temperature.

    This function applies variable-aware regridding to the CMIP NetCDF files
    contained in the `cmip_forcing` object so that they exactly match the ERA5 grid
    defined in `era5_forcing`.

    Parameters
    ----------
    cmip_forcing : PCRGlobWBForcing
        CMIP forcing object loaded via ewatercycle.forcing.sources.load(). 
        Must have `precipitationNC`, `temperatureNC`, and `directory` attributes.
    era5_forcing : PCRGlobWBForcing
        ERA5 forcing object loaded via ewatercycle.forcing.sources.load(). 
        Provides the target grid for regridding.

    Warning
    -------
    This function **overwrites the original CMIP NetCDF files** in `cmip_forcing.directory`.
    Ensure you have a backup if you need to preserve the original data.
    """
    regrid_cmip_forcing_to_era5(
        cmip_path=cmip_forcing.directory / cmip_forcing.precipitationNC,
        era5_path=era5_forcing.directory / era5_forcing.precipitationNC,
    )
    regrid_cmip_forcing_to_era5(
        cmip_path=cmip_forcing.directory / cmip_forcing.temperatureNC,
        era5_path=era5_forcing.directory / era5_forcing.temperatureNC,
    )


def regrid_cmip_forcing_to_era5(
    cmip_path,
    era5_path,
    overwrite=True,
):
    """
    Regrid CMIP forcing exactly onto ERA5 grid.

    Parameters
    ----------
    cmip_path : Path or str
        CMIP forcing NetCDF file (source grid).
    era5_path : Path or str
        ERA5 forcing NetCDF file (target grid).
    overwrite : bool
        Overwrite CMIP file after regridding.

    Returns
    -------
    xr.Dataset
        Regridded dataset.
    """

    cmip_path = Path(cmip_path)
    era5_path = Path(era5_path)

    ds_cmip = xr.load_dataset(cmip_path)
    ds_era5 = xr.load_dataset(era5_path)

    # Basic grid sanity check
    for dim in ("lat", "lon"):
        if dim not in ds_cmip.dims or dim not in ds_era5.dims:
            raise ValueError(f"Missing '{dim}' dimension for regridding")

    # Detect variable type
    forcing_type = detect_forcing_variable(ds_cmip)

    # Choose regridding method
    if forcing_type == "precipitation":
        method = "bilinear"
        extrap_method = "nearest_s2d"
    elif forcing_type == "temperature":
        method = "bilinear"
        extrap_method = "nearest_s2d"
    else:
        raise RuntimeError("Unhandled forcing type")

    # Create regridder
    regridder = xe.Regridder(
        ds_cmip,
        ds_era5,
        method=method,
        extrap_method=extrap_method,
        #reuse_weights=True,
    )

    # Apply regridding
    ds_out = regridder(ds_cmip)

    # Preserve metadata
    ds_out.attrs.update(ds_cmip.attrs)
    ds_out.attrs["regridded_to"] = "ERA5"
    ds_out.attrs["regridding_method"] = method

    if overwrite:
        ds_out.to_netcdf(cmip_path)

    return ds_out

def detect_forcing_variable(ds):
    """
    Detect forcing variable type from dataset.

    Returns
    -------
    str
        One of: 'precipitation', 'temperature'
    """

    varnames = set(ds.data_vars)

    precip_vars = {"pr", "precipitation", "tp"}
    temp_vars = {"tas", "t2m", "temperature"}

    if varnames & precip_vars:
        return "precipitation"
    if varnames & temp_vars:
        return "temperature"

    raise ValueError(
        f"Could not detect forcing variable from variables: {varnames}"
    )


# ===========================================================================
# Bias correction forcing
# - Apply monthly bias factors to precipitation and temperature
# - Uses ERA5 as reference
# ===========================================================================

