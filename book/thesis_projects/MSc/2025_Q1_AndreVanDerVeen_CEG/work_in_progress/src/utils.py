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
import configparser
from datetime import datetime

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

def _load_ini(path):
    """Load ini file into a dictionary-like structure."""
    cp = configparser.ConfigParser(interpolation=None)
    cp.optionxform = str  # preserve case
    cp.read(path)
    return cp

def _generate_comparison_filename(file1, file2):
    # use stem names of INI files
    name1 = Path(file1).stem
    name2 = Path(file2).stem
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{name1}_vs_{name2}_{timestamp}.txt"
    return INI_COMPARISON / filename

def compare_inis(file1, file2): #, save_file=None):
    cp1 = _load_ini(file1)
    cp2 = _load_ini(file2)

    output = []

    output.append(f"\nComparing:\n  A = {file1}\n  B = {file2}\n")

    # Compare sections
    sections1 = set(cp1.sections())
    sections2 = set(cp2.sections())

    missing_in_B = sections1 - sections2
    missing_in_A = sections2 - sections1

    if missing_in_B:
        output.append("Sections present in A but missing in B:")
        for s in sorted(missing_in_B):
            output.append(f"  - {s}")

    if missing_in_A:
        output.append("Sections present in B but missing in A:")
        for s in sorted(missing_in_A):
            output.append(f"  - {s}")

    # Compare keys for shared sections
    shared_sections = sections1 & sections2
    for section in sorted(shared_sections):
        keys1 = set(cp1[section].keys())
        keys2 = set(cp2[section].keys())

        missing_keys_in_B = keys1 - keys2
        missing_keys_in_A = keys2 - keys1

        if missing_keys_in_B or missing_keys_in_A:
            output.append(f"\n[Section: {section}]")

        if missing_keys_in_B:
            output.append("  Keys present in A but missing in B:")
            for k in sorted(missing_keys_in_B):
                output.append(f"    - {k}")

        if missing_keys_in_A:
            output.append("  Keys present in B but missing in A:")
            for k in sorted(missing_keys_in_A):
                output.append(f"    - {k}")

        # Compare values for keys present in both
        for key in sorted(keys1 & keys2):
            v1 = cp1[section][key].strip()
            v2 = cp2[section][key].strip()
            if v1 != v2:
                output.append(f"\n  Value differs for: {section}.{key}")
                output.append(f"    A: {v1}")
                output.append(f"    B: {v2}")

    # Print to console
    #print("\n".join(output))
    INI_COMPARISON.mkdir(parents=True, exist_ok=True)

    auto_filename = _generate_comparison_filename(file1, file2)

    # Optionally save to file
    with open(auto_filename, "w") as f:
        f.write("\n".join(output))
