from tqdm.notebook import tqdm
import pandas as pd
import ewatercycle.models
from src.paths import OUTPUT_HBV
from src.utils import mmday_to_m3s
import pickle
import xarray as xr

def run_HBV_model(forcing, parameter_set, initial_conditions, show_progress=True):
    """
    Run the HBV model with a given forcing and parameters.

    Parameters
    ----------
    forcing : ewatercycle.forcing.Forcing
        The forcing object (e.g., ERA5_forcing)
    parameter_set : dict
        HBV model parameter set
    initial_conditions : dict
        Initial storage values
    show_progress : bool
        If True, show a tqdm progress bar

    Returns
    -------
    pd.Series
        Modelled discharge time series
    """
    # Initialize model
    model = ewatercycle.models.HBV(forcing=forcing)
    config_file, _ = model.setup(parameters=parameter_set, initial_storage=initial_conditions)
    model.initialize(config_file)

    Q_m = []
    time = []

    # Determine total steps for progress bar
    total_steps = int((model.end_time - model.start_time) / model.time_step)

    if show_progress:
        pbar = tqdm(total=total_steps, desc="Running HBV model",mininterval=1.0)

    while model.time < model.end_time:
        model.update()
        Q_m.append(model.get_value("Q")[0])
        time.append(pd.Timestamp(model.time_as_datetime))

        if show_progress:
            pbar.update(1)

    if show_progress:
        pbar.close()

    # Finalize model (shuts down container)
    model.finalize()

    # Return as pandas Series
    model_output = pd.Series(data=Q_m, name="Modelled_discharge", index=time)
    return model_output

def plot_HBV_output(model_output: pd.Series):
    """
    Plot the HBV model output time series.

    Parameters
    ----------
    model_output : pd.Series
        Modelled discharge time series
    """
    import matplotlib.pyplot as plt

    plt.figure(figsize=(12, 6))
    plt.plot(model_output.index, model_output.values, label="Modelled Discharge", color='tab:blue')
    plt.xlabel("Time")
    plt.ylabel("Discharge (mm/d)")
    plt.title("HBV Modelled Discharge Time Series")
    plt.legend()
    plt.grid(linestyle="--", alpha=0.5)
    plt.show()


def save_HBV_results(model_output: pd.Series, shape_name: str, forcing_type: str): 
    """
    Save HBV model output as CSV, NetCDF, and pickle.
    Also converts results to m3/s using shapefile

    Parameters
    ----------
    model_output : pd.Series
        Modelled discharge time series in mm/day
    shape_name : str
        Name of the shapefile / catchment
    forcing_type : str
        Type of forcing (ERA5, CMIP, etc.)
    """
    # Directory where outputs will be stored
    output_dir = OUTPUT_HBV / f"{shape_name}" / f"{forcing_type}"
    output_dir.mkdir(parents=True, exist_ok=True)

    start_year = model_output.index[0].year
    end_year = model_output.index[-1].year

    #conversion to m3/s
    model_output_m3 = mmday_to_m3s(model_output,shape_name )

    #make df
    df = pd.DataFrame({
        "mm_day": model_output,
        "m3_s": model_output_m3
    })

    # generate name
    base_filename = f"{shape_name}_{forcing_type}_{start_year}-{end_year}"

    # Save CSV (mm/day
    csv_file = output_dir / f"{base_filename}.csv"
    df.to_csv(csv_file, index_label="time")

    # Save as pickle
    pkl_file = output_dir / f"{base_filename}.pkl"
    with open(pkl_file, "wb") as f:
        pickle.dump(df, f)

    # Save as netcdf
    ds = xr.Dataset({
        "discharge_mm_day": ("time", model_output.values, {"units": "mm/day"}),
        "discharge_m3_s": ("time", model_output_m3.values, {"units": "m3/s"})
    }, coords={"time": model_output.index})
    nc_file = output_dir / f"{base_filename}.nc"
    ds.to_netcdf(nc_file)

    

    return {"csv": csv_file, "pkl": pkl_file, "nc": nc_file}









