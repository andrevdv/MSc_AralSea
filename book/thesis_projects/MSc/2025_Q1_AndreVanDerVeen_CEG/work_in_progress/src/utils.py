#empty for now
import fiona
import shapely.geometry
from pyproj import Geod
from src.paths import *
import pandas as pd

def catchment_area_from_shapefile(shape_name, ellps="WGS84"):
    """
    Compute the area (in m²) of the first polygon in a shapefile.

    Parameters
    ----------
    shapefile_path : str
        Path to the shapefile (.shp)
    ellps : str, optional
        Ellipsoid for area calculation (default: WGS84)

    Returns
    -------
    float
        Absolute area of the polygon in square meters
    """
    # Load polygon
    shapefile = SHAPEFILES / shape_name / f"{shape_name}.shp"

    with fiona.open(shapefile) as src:
        poly = shapely.geometry.shape(src[0]["geometry"])

    # Define ellipsoid
    geod = Geod(ellps=ellps)

    # Compute area and perimeter
    area, _ = geod.geometry_area_perimeter(poly)

    return abs(area)

def mmday_to_m3s(model_output: pd.Series, shape_name: str) -> pd.Series:
    """
    Convert HBV model output from mm/day to m³/s using catchment area from shapefile.

    Parameters
    ----------
    model_output : pd.Series
        Modelled discharge in mm/day
    shape_name : str
        Name of the shapefile / catchment

    Returns
    -------
    pd.Series
        Discharge converted to m³/s
    """
    # Compute catchment area in m²
    area_m2 = catchment_area_from_shapefile(shape_name)  # default returns m²
    # Conversion: 1 mm/day over 1 m² = 1e-3 m³/day
    # Then divide by 86400 s/day to get m³/s
    conversion_factor = 1e-3 / 86400 * area_m2
    model_output_m3s = model_output * conversion_factor
    return model_output_m3s