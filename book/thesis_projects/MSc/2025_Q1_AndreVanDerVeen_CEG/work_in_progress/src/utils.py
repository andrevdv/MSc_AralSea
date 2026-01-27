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
from pathlib import Path
import re
import pandas as pd
from functools import lru_cache

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
    area_m2 = _get_catchment_area(shape_name)  # default returns m²
    # Conversion: 1 mm/day over 1 m² = 1e-3 m³/day
    # Then divide by 86400 s/day to get m³/s
    conversion_factor = 1e-3 / 86400 * area_m2
    model_output_m3s = model_output * conversion_factor
    return model_output_m3s


@lru_cache(maxsize=None)
def _get_catchment_area(shape_name: str) -> float:
    return catchment_area_from_shapefile(shape_name)




def get_integer_multiple_bounds(
    shapefiles: Union[str, Path, Sequence[Union[str, Path]]],
    multiple: int = 3,
):
    """
    Get the bounding box of one or more shapefiles, expanded to the nearest integer
    multiples.
    Parameters
    ----------
    shapefiles : str, Path, or list of str/Path
        Path(s) to the shapefile(s).
    multiple : int, optional    
        The multiple to which the bounds should be expanded (default is 3).
    Returns
    -------
    tuple
        A tuple containing (lon_min, lat_min, lon_max, lat_max) expanded to the nearest multiples.
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
    """Generate a filename for the comparison output based on the two INI files being compared."""
    # use stem names of INI files
    name1 = Path(file1).stem
    name2 = Path(file2).stem
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{name1}_vs_{name2}_{timestamp}.txt"
    return INI_COMPARISON / filename

def compare_inis(file1, file2): #, save_file=None):
    """
    Compare two INI files and print differences to console and save to a file.
    Parameters
    ----------  
    file1 : str or Path
        Path to the first INI file.
    file2 : str or Path
        Path to the second INI file.
    """
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


# =====================================================
# GRDC READER TO LATEX TABLE
# =====================================================

def _metadata_patterns() -> dict:
    return {
        "GRDC-No.": r"GRDC-No\.\s*:\s*(\d+)",
        "Station": r"Station\s*:\s*(.+)",
        "Latitude (DD)": r"Latitude \(DD\)\s*:\s*([-\d\.]+)",
        "Longitude (DD)": r"Longitude \(DD\)\s*:\s*([-\d\.]+)",
        "Catchment area (km²)": r"Catchment area \(km²\)\s*:\s*([-\d\.]+)",
        "Time series": r"Time series\s*:\s*(.+)",
        "Data lines": r"Data lines\s*:\s*(\d+)",
        "Data Set Content": r"Data Set Content\s*:\s*(.+)",
    }

def _read_text_file(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="latin1")


def _extract_metadata(content: str, patterns: dict) -> dict:
    metadata = {}
    for key, pattern in patterns.items():
        match = re.search(pattern, content)
        metadata[key] = match.group(1).strip() if match else None
    return metadata

def _determine_frequency(content: str | None) -> str:
    if not content:
        return "-"
    content = content.upper()
    if "DAILY" in content:
        return "Daily"
    if "MONTHLY" in content:
        return "Monthly"
    return "-"

def _collect_metadata(folder: Path, patterns: dict) -> pd.DataFrame:
    records = []

    for txt_file in folder.glob("*.txt"):
        text = _read_text_file(txt_file)
        metadata = _extract_metadata(text, patterns)
        metadata["Frequency"] = _determine_frequency(metadata.get("Data Set Content"))
        records.append(metadata)

    return pd.DataFrame(records)

def _convert_numeric_columns(df: pd.DataFrame) -> pd.DataFrame:
    df["Data lines"] = df["Data lines"].astype("Int64")

    df["Catchment area (km²)"] = df["Catchment area (km²)"].apply(
        lambda x: int(float(x)) if pd.notna(x) else pd.NA
    )

    df["Data lines"] = df["Data lines"].map(
        lambda x: "-" if pd.isna(x) or x == 0 else f"{x:,}"
    )

    return df

def _round_coordinates(df: pd.DataFrame, decimals: int = 2) -> pd.DataFrame:
    for col in ["Latitude (DD)", "Longitude (DD)"]:
        df[col] = (
            df[col]
            .astype(float)
            .round(decimals)
            .map(lambda x: f"{x:.{decimals}f}" if pd.notna(x) else "-")
        )
    return df

def _copy_nonempty_timeseries(df: pd.DataFrame) -> pd.DataFrame:
    numeric = pd.to_numeric(
        df["Data lines"].str.replace(",", "").replace("-", ""),
        errors="coerce",
    )
    return df[numeric > 0].copy()

def _select_and_rename_columns(df: pd.DataFrame) -> pd.DataFrame:
    columns = {
        "GRDC-No.": "GRDC No.",
        "Station": "Station",
        "Latitude (DD)": "Lat (°N)",
        "Longitude (DD)": "Lon (°E)",
        "Catchment area (km²)": "Catchment (km²)",
        "Time series": "Time Series",
        "Data lines": "Data Lines",
        "Frequency": "Freq",
    }

    return df[list(columns.keys())].rename(columns=columns)

def _sanitize_latex(value):
    if isinstance(value, str):
        return (
            value.replace("_", r"\_")
                 .replace("&", r"\&")
                 .replace("%", r"\%")
        )
    return value


def _sanitize_dataframe_for_latex(df: pd.DataFrame) -> pd.DataFrame:
    return df.applymap(_sanitize_latex)

def _export_to_latex(
    df: pd.DataFrame,
    output_path: Path,
    caption: str,
    label: str,
    column_format: str,
):
    latex = df.to_latex(
        index=False,
        caption=caption,
        label=label,
        longtable=True,
        escape=False,
        column_format=column_format,
    )
    output_path.write_text(latex, encoding="utf-8")

def _simplify_daily_timeseries(ts):
    if pd.isna(ts):
        return "-"
    match = re.findall(r"(\d{4})", ts)
    if match and len(match) >= 2:
        return f"{match[0]} - {match[-1]}"
    return ts

def _split_by_frequency(df: pd.DataFrame):
    df_daily = df[df["Freq"] == "Daily"].copy()
    df_monthly = df[df["Freq"] == "Monthly"].copy()

    # Daily: simplify time series, remove Freq
    if not df_daily.empty:
        df_daily["Time Series"] = df_daily["Time Series"].apply(
            _simplify_daily_timeseries
        )
        df_daily.drop(columns=["Freq"], inplace=True)

    # Monthly: just remove Freq
    if not df_monthly.empty:
        df_monthly.drop(columns=["Freq"], inplace=True)

    return df_daily, df_monthly




def _export_daily_monthly_tables(
    df_daily: pd.DataFrame,
    df_monthly: pd.DataFrame,
    export_dir: Path,
    base_filename: str,
):
    if not df_monthly.empty:
        latex_monthly = df_monthly.to_latex(
            index=False,
            caption="Selected GRDC Station Metadata (Monthly)",
            label="tab:grdc_selected_metadata_monthly",
            longtable=True,
            escape=False,
            column_format="lp{4.3cm}llrlr",
        )
        (export_dir / f"{base_filename}_monthly.tex").write_text(
            latex_monthly, encoding="utf-8"
        )

    if not df_daily.empty:
        latex_daily = df_daily.to_latex(
            index=False,
            caption="Selected GRDC Station Metadata (Daily)",
            label="tab:grdc_selected_metadata_daily",
            longtable=True,
            escape=False,
            column_format="lp{4.3cm}llrlr",
        )
        (export_dir / f"{base_filename}_daily.tex").write_text(
            latex_daily, encoding="utf-8"
        )

    

def build_grdc_metadata_table(
    folder_path: Path,
    export_dir: Path | None = None,
    split_daily_monthly: bool = True,
    base_filename: str = "grdc_selected_metadata",
) -> pd.DataFrame:
    """
    Build cleaned GRDC station metadata tables.

    Parameters
    ----------
    folder_path : Path
        Directory containing GRDC station .txt files.
    export_dir : Path, optional
        Directory where LaTeX tables will be written.
    split_daily_monthly : bool, default True
        If True, exports separate daily and monthly tables.
    base_filename : str, default "grdc_selected_metadata"
        Base name for exported LaTeX files (without suffix).
    """

    patterns = _metadata_patterns()

    df = _collect_metadata(folder_path, patterns)
    df = _convert_numeric_columns(df)
    df = _round_coordinates(df)
    df = _copy_nonempty_timeseries(df)
    df = _select_and_rename_columns(df)
    df = _sanitize_dataframe_for_latex(df)

    if export_dir is not None:
        export_dir.mkdir(parents=True, exist_ok=True)

        if split_daily_monthly:
            df_daily, df_monthly = _split_by_frequency(df)
            _export_daily_monthly_tables(
                df_daily,
                df_monthly,
                export_dir,
                base_filename,
            )

    return df
