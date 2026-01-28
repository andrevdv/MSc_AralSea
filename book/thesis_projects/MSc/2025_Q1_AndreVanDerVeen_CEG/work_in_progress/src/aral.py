"""

"""
import pandas as pd
from scipy.interpolate import interp1d
import numpy as np

#Geometry stuff, needs update later to account for separate north and south basins
class LakeGeometry:
    def __init__(self, ahv_csv):
        df = pd.read_csv(ahv_csv).sort_values("elevation_m")

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
            fill_value=0.0
        )

    def elevation_from_volume(self, V_km3):
        return float(self.h_of_v(V_km3))

    def area_from_volume(self, V_km3):
        h = self.elevation_from_volume(V_km3)
        return float(self.a_of_h(h))
    
class River:
    def __init__(self, df, q_col, name=None, factor=1.0):
        """
        Wraps a river discharge time series for the lake model.

        Parameters
        ----------
        df : pandas.DataFrame
            Time series with at least the discharge column
        q_col : str
            Name of the column containing discharge
        name : str, optional
            River name (for plotting or debugging)
        factor : float, optional
            Unit conversion factor (e.g., m³/s → km³/day)
        """
        self.name = name
        self.Q = df[q_col] * factor
    
def discharge_to_km3day(Q_m3s):
    return Q_m3s * 86400 / 1e9

##fluxes
def discharge_to_km3day(Q_m3s):
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

def compute_evaporation_km3day(pot_evap_mps, area_km2):
    area_m2 = area_km2 * 1e6
    evap_m3day = pot_evap_mps * area_m2 * 86400
    return evap_m3day / 1e9



## Daily status update - Volume balance
def update_volume(
    V_prev,
    Q_in,
    evap,
    Q_gw=0.0,
    scale_inflow=1.0
):
    V_new = (
        V_prev
        + scale_inflow * Q_in
        - Q_gw
        - evap
    )
    return max(V_new, 0.0)

# --- main model ---
def run_connected_aral_model(
    aral_meteo,
    rivers,      # list of River objects, e.g., [River_Amu_Darya, River_Syr_Darya]
    ahv_csv,
    V0_km3
):
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
    n = len(aral_meteo.time)

    V = pd.Series(index=range(n), dtype=float)
    A = pd.Series(index=range(n), dtype=float)
    H = pd.Series(index=range(n), dtype=float)

    V.iloc[0] = V0_km3
    geom = LakeGeometry(ahv_csv)

    for i in range(1, n):
        # Geometry
        A.iloc[i] = geom.area_from_volume(V.iloc[i-1])
        H.iloc[i] = geom.elevation_from_volume(V.iloc[i-1])

        # Total river inflow from all River objects
        Q_in = compute_total_river_inflow(i, rivers)

        # Evaporation
        evap = compute_evaporation_km3day(
            aral_meteo["evspsblpot"].isel(time=i).values,
            A.iloc[i]
        )

        # Update volume
        V.iloc[i] = update_volume(
            V.iloc[i-1], Q_in, evap
        )

    return pd.DataFrame({
        "time": aral_meteo.time.values,
        "volume_km3": V,
        "area_km2": A,
        "elevation_m": H
    })
