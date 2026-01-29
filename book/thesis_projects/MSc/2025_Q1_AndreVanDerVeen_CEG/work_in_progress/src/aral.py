"""
Aral Sea connected lake model.
Based on daily water balance including river inflow and evaporation.
"""
import pandas as pd
from scipy.interpolate import interp1d
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from pathlib import Path
import xarray as xr
from src.constants import MAKKINK_FACTOR

#Geometry stuff, needs update later to account for separate north and south basins
class LakeGeometry:
    """
    Represent the geometry of a lake using an area-height-volume (AHV) relationship.

    This class provides methods to compute lake surface elevation and area
    from a given volume, based on an AHV curve loaded from CSV.

    TODO expand with north south split etc

    Attributes
    ----------
    h_of_v : scipy.interpolate.interp1d
        Interpolation function for elevation (m) as a function of volume (km³).
    a_of_h : scipy.interpolate.interp1d
        Interpolation function for area (km²) as a function of elevation (m).
    """
    def __init__(self, ahv_csv):
        """
        Initialize LakeGeometry from an area-height-volume (AHV) CSV file.

        The CSV file must have columns:
            - elevation_m : lake surface elevation (meters)
            - volume_km3  : lake volume (km³)
            - area_km2    : lake surface area (km²)

        The constructor creates two interpolation functions:
            - elevation as a function of volume
            - area as a function of elevation

        Parameters
        ----------
        ahv_csv : str or Path
            Path to CSV file containing the AHV curve. Columns must be separated
            by ';' and decimal points may use ','.
        """
        if not Path(ahv_csv).exists():
            raise FileNotFoundError(f"AHV file not found: {ahv_csv}")
        
        df = pd.read_csv(ahv_csv, sep=';', decimal=',').sort_values("elevation_m")
        self.df = df  # Store the DataFrame for potential future use

        self.h_of_v = interp1d(
            df["volume_km3"],
            df["elevation_m"],
            bounds_error=False,
            fill_value="extrapolate"
        )

        self.a_of_h = interp1d(
            df["elevation_m"],
            df["area_km2"],
            bounds_error=False,
            fill_value="extrapolate"
        )

    def elevation_from_volume(self, V_km3):
        """
        Compute lake surface elevation from volume using interpolation.

        Parameters
        ----------
        V_km3 : float
            Lake volume in km³

        Returns
        -------
        float
            Lake surface elevation in meters
        """
        if V_km3 < 0:
            raise ValueError(f"Volume cannot be negative: {V_km3}")
        return float(self.h_of_v(V_km3))

    def area_from_volume(self, V_km3):
        """
        Compute lake surface area from volume using interpolation.

        Internally, it first computes elevation from volume, then uses the
        area-elevation relationship.

        Parameters
        ----------
        V_km3 : float
            Lake volume in km³

        Returns
        -------
        float
            Lake surface area in km²
        """
        if V_km3 < 0:
            raise ValueError(f"Volume cannot be negative: {V_km3}")
        h = self.elevation_from_volume(V_km3)

        return float(self.a_of_h(h))
    
    def plot_ahv_curve(self):
        """Plot the area-height-volume relationships for validation."""
        fig, axes = plt.subplots(1, 3, figsize=(18, 5))
        df = self.df

        # 1. Area vs Height
        axes[0].plot(df["elevation_m"], df["area_km2"], marker='o', color='tab:blue')
        axes[0].set_xlabel("Height [m]")
        axes[0].set_ylabel("Area [km²]")
        axes[0].set_title("Area vs Height")
        axes[0].grid(True)

        # 2. Volume vs Height
        axes[1].plot(df["elevation_m"], df["volume_km3"], marker='o', color='tab:green')
        axes[1].set_xlabel("Height [m]")
        axes[1].set_ylabel("Volume [km³]")
        axes[1].set_title("Volume vs Height")
        axes[1].grid(True)

        # 3. Volume vs Area
        axes[2].plot(df["area_km2"], df["volume_km3"], marker='o', color='tab:orange')
        axes[2].set_xlabel("Area [km²]")
        axes[2].set_ylabel("Volume [km³]")
        axes[2].set_title("Volume vs Area")
        axes[2].grid(True)

        fig.tight_layout()
        return fig, axes
    
class River:
    def __init__(self, data, q_col=None, name=None, factor: float = 86400/1e9, scaling: float = 1):
        """
        Wraps a river discharge time series for the lake model.

        Parameters
        ----------
        data : pd.DataFrame, pd.Series, xr.DataArray, xr.Dataset, str or Path
            Input time series. Can be:
            - pandas DataFrame or Series
            - xarray DataArray or Dataset
            - path to a NetCDF file (str or Path)
        q_col : str, optional
            Column name in DataFrame or Dataset (required if multiple variables)
        name : str, optional
            River name (for plotting)
        factor : float
            Unit conversion factor (e.g., m³/s → km³/day)
        scaling : float
            Additional scaling factor
        """
        self.name = name

        # Handle string / Path input (NetCDF)
        if isinstance(data, (str, Path)):
            ds = xr.open_dataset(data)
            if q_col is None:
                # Use the first variable by default
                var_name = list(ds.data_vars)[0]
            else:
                var_name = q_col
            self.Q_raw = ds[var_name].to_pandas()

        # Handle xarray DataArray / Dataset
        elif isinstance(data, xr.DataArray):
            self.Q_raw = data.to_pandas()
        elif isinstance(data, xr.Dataset):
            if q_col is None:
                # Use the first variable by default
                var_name = list(data.data_vars)[0]
            else:
                var_name = q_col
            self.Q_raw = data[var_name].to_pandas()

        # Handle pandas DataFrame / Series
        elif isinstance(data, pd.DataFrame):
            if q_col is None:
                raise ValueError("q_col must be provided when passing a DataFrame")
            self.Q_raw = data[q_col]
        elif isinstance(data, pd.Series):
            self.Q_raw = data
        else:
            raise TypeError(f"Unsupported data type: {type(data)}")

        # Ensure datetime index
        if not pd.api.types.is_datetime64_any_dtype(self.Q_raw.index):
            self.Q_raw.index = pd.to_datetime(self.Q_raw.index)

        # Apply conversion factor and scaling
        self.Q = self.Q_raw * factor * scaling

    def plot_yearly(self, skipna=True):
        """
        Plot yearly discharge as a bar chart.
        """
        yearly = self.Q.resample('YE').sum(min_count=1 if skipna else None)
        plt.figure(figsize=(10, 4))
        plt.bar(yearly.index.year, yearly.values, color='skyblue')
        plt.ylabel('Yearly Discharge (km³/yr)')
        plt.xlabel('Year')
        plt.title(f'{self.name} Yearly Discharge')
        plt.grid(True)
        plt.show()

    def plot_daily(self, skipna=True):
        """
        Plot daily discharge as a line chart.
        """
        daily = self.Q.copy()
        if skipna:
            daily = daily.dropna()
        plt.figure(figsize=(12, 4))
        plt.plot(daily.index, daily.values, color='dodgerblue')
        plt.ylabel('Daily Discharge (km³/day)')
        plt.xlabel('Date')
        plt.title(f'{self.name} Daily Discharge')
        plt.grid(True)
        plt.show()

class MultiRiver:
    def __init__(self, rivers, q_col=None, factor: float = 86400/1e9, scaling: float = 1):
        """
        Wrapper for multiple rivers.

        Parameters
        ----------
        rivers : dict
            Keys = river names, values = data (DataFrame/Series/xarray/NetCDF)
        q_col : str, optional
            Column name for DataFrames/Datasets with multiple variables
        factor, scaling : float
            Unit conversion and scaling
        """
        self.rivers = {}
        for name, data in rivers.items():
            if isinstance(data, River):
                self.rivers[name] = data
            else:
                self.rivers[name] = River(data, name=name)

    def plot_yearly(self):
        plt.figure(figsize=(12, 5))
        for name, river in self.rivers.items():
            yearly = river.Q.resample('YE').sum()
            plt.plot(yearly.index.year, yearly.values, marker='o', label=name)
        plt.ylabel('Yearly Discharge (km³/yr)')
        plt.xlabel('Year')
        plt.title('Yearly Discharge - Multiple Rivers')
        plt.grid(True)
        plt.legend()
        plt.show()

    def plot_daily(self):
        plt.figure(figsize=(12, 5))
        for name, river in self.rivers.items():
            daily = river.Q.dropna()
            plt.plot(daily.index, daily.values, label=name)
        plt.ylabel('Daily Discharge (km³/day)')
        plt.xlabel('Date')
        plt.title('Daily Discharge - Multiple Rivers')
        plt.grid(True)
        plt.legend()
        plt.show()

    

#fluxes
def discharge_to_km3day(Q_m3s):
    """
    converts discharge from m3s to km3day
    
    :param Q_m3s: Description
    """
    return Q_m3s * 86400 / 1e9


def compute_total_river_inflow(i, rivers, connected=True):
    """
    Compute river inflow(s) for timestep i.

    Parameters
    ----------
    i : int
        Time index
    rivers : list of River
        List of River objects
    connected : bool
        If True, sum all rivers into one inflow
        If False, can be used for split-lake routing (future)

    Returns
    -------
    float
        Total inflow (connected case)
    """
    if connected:
        return sum(r.Q.iloc[i] for r in rivers)
    else:
        # Placeholder for future north/south split
        # e.g., return {'north': rivers[1].Q.iloc[i], 'south': rivers[0].Q.iloc[i]}
        return sum(r.Q.iloc[i] for r in rivers)

def compute_evaporation_km3day(evap_flux_kg_m2_s, area_km2):
    """
    Convert potential evaporation flux to km3/day.

    Parameters
    ----------
    evap_flux_kg_m2_s : float
        Evaporation flux in kg m^-2 s^-1
    area_km2 : float
        Lake area in km^2

    Returns
    -------
    float
        Evaporation in km3/day
    """
    # kg/m²/s → mm/day
    evap_mm_day = evap_flux_kg_m2_s * 86400
    
    # mm/day → km³/day
    evap_km3_day = evap_mm_day / 1e6 * area_km2

    # makkink conversion factor open water evaporation
    evap_km3_day = MAKKINK_FACTOR * evap_km3_day
    return evap_km3_day



## Daily status update - Volume balance
def update_volume(
    V_prev,
    Q_in,
    evap,
    Q_gw=0.0,
    scale_inflow=1.0
):
    """
    updates the volume for the volume balance model. rudimentary right now.
    """
    V_new = (
        V_prev
        + scale_inflow * Q_in
        - Q_gw
        - evap
    )
    return max(V_new, 0.0)

# --- main model ---
def run_connected_aral_model(
    aral_meteo: xr.Dataset,     # xarray Dataset with meteo forcing, must containg [evspsblpot]
    rivers: list["River"],      # list of River objects, e.g., [River_Amu_Darya, River_Syr_Darya]
    ahv_csv: str,              # path to A-H-V CSV file with columns: elevation_m, volume_km3, area_km2
    V0_km3: float = 1100,       # initial lake volume [km3]
    start_time=None,  # optional: datetime-like string or pd.Timestamp
    end_time=None     # optional: datetime-like string or pd.Timestamp
)-> pd.DataFrame:
    """
    Connected Aral Sea daily water balance model.

    Parameters
    ----------
    aral_meteo : xarray.Dataset
        Meteorological forcing, must contain 'evspsblpot'
    rivers : list of River
        List of River objects (must have .Q attribute)
    ahv_csv : str
        Path to A-H-V CSV file
    V0_km3 : float
        Initial lake volume [km3]

    Returns
    -------
    pandas.DataFrame
        Columns: time, volume_km3, area_km2, elevation_m
    """

        # --- Slice meteorological forcing ---
    if start_time is not None or end_time is not None:
        aral_meteo = aral_meteo.sel(
            time=slice(start_time, end_time)
        )

    # --- Slice river time series ---
    for r in rivers:
        if start_time is not None or end_time is not None:
            mask = (r.Q_raw.index >= pd.to_datetime(start_time)) & \
                   (r.Q_raw.index <= pd.to_datetime(end_time))
            r.Q = r.Q_raw.loc[mask] * (r.Q / r.Q_raw).iloc[0]  # keeps factor/scaling applied

    n = min(len(aral_meteo.time), min(len(r.Q) for r in rivers))


    V = pd.Series(index=range(n), dtype=float)
    A = pd.Series(index=range(n), dtype=float)
    H = pd.Series(index=range(n), dtype=float)
    Q_in_series = pd.Series(index=range(n), dtype=float)
    evap_series = pd.Series(index=range(n), dtype=float)

    V.iloc[0] = V0_km3
    geom = LakeGeometry(ahv_csv)

    for i in range(1, n):
        # Geometry
        A.iloc[i] = geom.area_from_volume(V.iloc[i-1])
        H.iloc[i] = geom.elevation_from_volume(V.iloc[i-1])

        # Total river inflow from all River objects
        Q_in = compute_total_river_inflow(i, rivers)
        Q_in_series.iloc[i] = Q_in

        # Evaporation
        evap = compute_evaporation_km3day(
            aral_meteo["evspsblpot"].isel(time=i).values,
            A.iloc[i]
        )
        evap_series.iloc[i] = evap

        # Update volume
        V.iloc[i] = update_volume(
            V.iloc[i-1], Q_in, evap
        )

    return pd.DataFrame({
        "time": aral_meteo.time.values[:n],
        "volume_km3": V,
        "area_km2": A,
        "elevation_m": H,
        "Q_in_km3day": Q_in_series,
        "evap_km3day": evap_series,
    })


def plot_aral_results(df):
    """
    Plot Aral Sea simulation results as side-by-side time series.

    This function creates three horizontally aligned subplots showing:
    - Lake volume (km³)
    - Surface elevation (m)
    - Surface area (km²)

    Each subplot has a title, axis labels, grid, and formatted time axis.

    Parameters
    ----------
    df : pandas.DataFrame
        DataFrame containing simulation results with the following columns:
        - 'time' : datetime-like, time axis
        - 'volume_km3' : float, lake volume in km³
        - 'elevation_m' : float, lake surface elevation in meters
        - 'area_km2' : float, lake surface area in km²

    Returns
    -------
    None
        The function displays a matplotlib figure and does not return anything.
    """
    # Wider figure for side-by-side plots
    fig, axs = plt.subplots(1, 3, figsize=(18, 5))

    # Volume
    axs[0].plot(df['time'], df['volume_km3'], label='Volume', color='blue')
    axs[0].set_ylabel('Volume (km³)')
    axs[0].set_title('Aral Sea Volume')
    axs[0].set_xlabel('Time')
    axs[0].grid(True)

    # Elevation
    axs[1].plot(df['time'], df['elevation_m'], label='Elevation', color='orange')
    axs[1].set_ylabel('Elevation (m)')
    axs[1].set_title('Aral Sea Elevation')
    axs[1].set_xlabel('Time')
    axs[1].grid(True)

    # Area
    axs[2].plot(df['time'], df['area_km2'], label='Area', color='green')
    axs[2].set_ylabel('Area (km²)')
    axs[2].set_title('Aral Sea Area')
    axs[2].set_xlabel('Time')
    axs[2].grid(True)

    # Format x-axis as dates and rotate labels
    for ax in axs:
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
        plt.setp(ax.get_xticklabels(), rotation=45, ha='right')


    plt.tight_layout()
    plt.show()

def plot_aral_fluxes(df):
    """
    Plot yearly inflow and evaporation for the Aral Sea simulation.

    Creates two side-by-side subplots with the same y-axis scale.

    Parameters
    ----------
    df : pandas.DataFrame
        DataFrame containing simulation results with columns:
        - 'time' : datetime-like
        - 'Q_in_km3day' : daily inflow in km³/day
        - 'evap_km3day' : daily evaporation in km³/day

    Returns
    -------
    None
    """
    # Resample to yearly totals
    df_yearly = df.set_index("time").resample("YE").sum()

    # Determine shared y-axis limit
    y_max = 1.1 * max(df_yearly["Q_in_km3day"].max(), df_yearly["evap_km3day"].max())

    fig, axs = plt.subplots(1, 2, figsize=(15, 5))

    # Yearly inflow
    axs[0].bar(df_yearly.index.year, df_yearly["Q_in_km3day"], color='skyblue')
    axs[0].set_title("Yearly River Inflow")
    axs[0].set_xlabel("Year")
    axs[0].set_ylabel("Inflow (km³/yr)")
    axs[0].set_ylim(0, y_max)
    axs[0].grid(True)

    # Yearly evaporation
    axs[1].bar(df_yearly.index.year, df_yearly["evap_km3day"], color='salmon')
    axs[1].set_title("Yearly Evaporation")
    axs[1].set_xlabel("Year")
    axs[1].set_ylabel("Evaporation (km³/yr)")
    axs[1].set_ylim(0, y_max)
    axs[1].grid(True)

    plt.tight_layout()
    plt.show()

def save_aral_simulation(aral_df, save_dir, prefix="aral_sim"):
    """
    Save Aral Sea simulation results in CSV, pickle, and NetCDF formats.

    Parameters
    ----------
    aral_df : pandas.DataFrame
        Simulation results containing a 'time' column.
    save_dir : str or Path
        Directory where files will be saved.
    prefix : str, default "aral_sim"
        Prefix for the saved files.

    Returns
    -------
    dict
        Paths of the saved files.
    """
    save_dir = Path(save_dir)
    save_dir.mkdir(parents=True, exist_ok=True)

    paths = {}

    # CSV
    csv_path = save_dir / f"{prefix}.csv"
    aral_df.to_csv(csv_path, index=False)
    paths["csv"] = csv_path

    # Pickle
    pkl_path = save_dir / f"{prefix}.pkl"
    aral_df.to_pickle(pkl_path)
    paths["pkl"] = pkl_path

    # NetCDF via xarray
    nc_path = save_dir / f"{prefix}.nc"
    # Convert DataFrame to xarray
    ds = aral_df.set_index("time").to_xarray()
    ds.to_netcdf(nc_path)
    paths["nc"] = nc_path

    return paths

