#empty for now
import fiona
import shapely.geometry
from pyproj import Geod
from src.paths import *
import pandas as pd
from typing import Union, Sequence
import numpy as np
import fiona
from shapely.geometry import shape, box


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

def get_integer_multiple_bounds(
    shapefiles: Union[str, Path, Sequence[Union[str, Path]]],
    multiple: int = 3,
):
    """
    docstring
    docstring
    docstring
    """

    # make list
    if isinstance(shapefiles, (str, Path)):
        shapefiles = [shapefiles]

    # --- collect all bounds ---
    min_xs, min_ys, max_xs, max_ys = [], [], [], []

    for shp in shapefiles:
        with fiona.open(shp) as src:
            for feat in src:
                geom = shape(feat["geometry"])
                minx, miny, maxx, maxy = geom.bounds
                min_xs.append(minx)
                min_ys.append(miny)
                max_xs.append(maxx)
                max_ys.append(maxy)

    # original bounds
    lon_min = min(min_xs)
    lat_min = min(min_ys)
    lon_max = max(max_xs)
    lat_max = max(max_ys)
    # --- convert to integer bounds ---
    lon_min_i = int(np.floor(lon_min))
    lat_min_i = int(np.floor(lat_min))
    lon_max_i = int(np.ceil(lon_max))
    lat_max_i = int(np.ceil(lat_max))

    # --- helper to expand to multiple ---
    def expand_to_multiple(min_val, max_val, multiple):
        extent = max_val - min_val
        remainder = extent % multiple
        if remainder != 0:
            max_val += (multiple - remainder)
        return min_val, max_val

    lon_min_f, lon_max_f = expand_to_multiple(lon_min_i, lon_max_i, multiple)
    lat_min_f, lat_max_f = expand_to_multiple(lat_min_i, lat_max_i, multiple)

    return lon_min_f, lat_min_f, lon_max_f, lat_max_f