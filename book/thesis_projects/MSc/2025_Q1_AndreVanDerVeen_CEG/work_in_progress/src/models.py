from tqdm.notebook import tqdm
import pandas as pd
import ewatercycle.models
from src.paths import OUTPUT_HBV,INI_FILES
from src.utils import mmday_to_m3s
import pickle
import xarray as xr
from pathlib import Path
from datetime import datetime
import numpy as np
import shutil
import pandas as pd
import os
import json

def run_HBV_model(forcing, parameter_set, initial_conditions, show_progress=True, delete_files = False, leave_pbar = True):
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
    config_file, config_dir = model.setup(parameters=parameter_set, initial_storage=initial_conditions)
    model.initialize(config_file)

    Q_m = []
    time = []

    # Determine total steps for progress bar
    total_steps = int((model.end_time - model.start_time) / model.time_step)

    if show_progress:
        pbar = tqdm(total=total_steps, desc="Running HBV model",mininterval=1.0, leave=leave_pbar)

    while model.time < model.end_time:
        model.update()
        Q_m.append(model.get_value("Q")[0])
        time.append(pd.Timestamp(model.time_as_datetime))

        if show_progress:
            pbar.update(1)

    if show_progress:
        pbar.close()

    config_dir = Path(config_dir)
    #print(f"config_dir = {config_dir}")
    if config_dir.exists() and config_dir.is_dir() and delete_files==True:
        #check it only contains HBV_config.json
        files = list(config_dir.iterdir())
        if len(files) == 1 and files[0].name == "HBV_config.json":
            shutil.rmtree(config_dir)
        else:
            print(f"Folder {config_dir} not deleted: contains other files")

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

def run_PCRGLOBWB_model(forcing_path,ini_name, start_date,end_date):
    """
    Placeholder for running the PCR-GLOBWB model.
    """
    from tqdm import tqdm as classic_tqdm
    # Convert ISO 8601 strings to datetime objects
    start_time = datetime.strptime(start_date, '%Y-%m-%dT%H:%M:%SZ')
    end_time = datetime.strptime(end_date, '%Y-%m-%dT%H:%M:%SZ')

    # Calculate the number of days for the progression bar
    delta = end_time - start_time
    number_of_days = delta.days

    pbar = classic_tqdm(total=number_of_days, desc="Initializing model", mininterval=1.0)


    # can be hardcoded, location of all the pcr-glob data on ewatercycle
    pcr_glob_directory = Path("/data/shared/parameter-sets/pcrglobwb_global")
    

    forcing = ewatercycle.forcing.sources["PCRGlobWBForcing"].load(
    directory=forcing_path,
    )

    parameter_set = ewatercycle.parameter_sets.ParameterSet(
    name="custom_parameter_set",
    directory=pcr_glob_directory,
    config= INI_FILES / ini_name,
    target_model="pcrglobwb",
    supported_model_versions={"setters"},
    )

    model = ewatercycle.models.PCRGlobWB(
    parameter_set=parameter_set,
    forcing=forcing
    )

    model_config, model_dir = model.setup(
    start_time = start_date,
    end_time = end_date,
    max_spinups_in_years=0
    )

    model.initialize(model_config)

    pbar.set_description("Running model")
    while model.time < model.end_time:

        model.update()
        pbar.update(1)



    pbar.close()
    tqdm.write("Model run finished!")

    model.finalize()

def generate_HBV_parameters(n_particles: int):
    """
    Docstring for generate_HBV_parameters
    
    :param n_particles: Description
    :type n_particles: int
    """
    p_min = np.array([0,   0.2,  40,    .5,   .001,   1,     .01,  .0001,   0.01]) #hardcoded for now TODO
    p_max =np.array([25,    1,  800,   4,    .3,     15,    .02,   .01,      0.8]) #hardcoded for now TODO

    array_random_num = np.array([[np.random.random() for i in range(len(p_max))] for i in range(n_particles)])
    generated_parameters = p_min + array_random_num * (p_max-p_min)

    return generated_parameters

def run_ensemble_HBV(n_particles: int, forcing, delete_files = True):
    """
    Docstring for run_ensemble_HBV
    
    :param n_particles: Description
    :type n_particles: int
    :param forcing: Description
    """
    list_parameters = generate_HBV_parameters(n_particles) #store somewhere TODO

    s_0 = np.array([0,  100,  0,  5, 0]) #hardcoded storage TODO

    all_series = []

    for i in tqdm(range(n_particles), desc="Running HBV particles"):
        s = run_HBV_model(
            forcing=forcing,
            parameter_set=list_parameters[i],
            initial_conditions=s_0,
            show_progress=True,
            delete_files=delete_files,
            leave_pbar=False,
        )
        all_series.append(s)
    
    df_all = pd.concat(all_series, axis=1)
    df_all.columns = [f"particle_{i}" for i in range(n_particles)]

    return df_all

# ===========================================================================
# better way of calibration?
# using scipy optimize
# more text to be added here
# ===========================================================================

parameter_names = [
    "Imax",  # 0
    "Ce",    # 1
    "Sumax", # 2
    "Beta",  # 3
    "Pmax",  # 4
    "Tlag",  # 5
    "Kf",    # 6
    "Ks",    # 7
    "FM"     # 8
]


# history tracking
history = {
    "theta_norm": [],
    "theta_phys": [],
    "objective": []
}

p_min = np.array([0, 0.2, 40, 0.5, 0.001, 1, 0.01, 0.0001, 0.01])
p_max = np.array([25, 1, 800, 4, 0.3, 15, 0.02, 0.01, 0.8])

# scale parameters
def scale(theta):
    return (theta - p_min) / (p_max - p_min)

def unscale(x):
    return p_min + x * (p_max - p_min)




bounds = list(zip(p_min, p_max))
def run_hbv_single(theta, forcing,shape_name):
    s_0 = np.array([0, 100, 0, 5, 0])  # later: make configurable

    model_output   = run_HBV_model(
        forcing=forcing,
        parameter_set=theta,
        initial_conditions=s_0,
        show_progress=False,
        delete_files=True,
        leave_pbar=False,
    )

    model_output_m3 = mmday_to_m3s(model_output, shape_name)

    # assume sim is a pd.Series of discharge
    return model_output_m3


def objective(theta_norm, forcing, q_obs, years, shape_name):
    theta = unscale(theta_norm) 
    sim = run_hbv_single(theta, forcing, shape_name)


    # --- hydrograph fit ---
    nse_val = 1 - np.sum((sim - q_obs)**2) / np.sum((q_obs - q_obs.mean())**2)


    # --- yearly volume error ---
    vol_errs = []
    for y in np.unique(years):
        mask = years == y
        sim_y = sim[mask].sum()
        obs_y = q_obs[mask].sum()
        vol_errs.append((sim_y - obs_y) / obs_y)

    vol_term = np.mean(np.square(vol_errs))

    # combined objective
    J = (1 - nse_val) + vol_term

    return float(J)



# call_counter = {"n": 0}
# def objective_safe(theta_norm, forcing, q_obs, years, shape_name):
#     #call_counter["n"] += 1
#     #print(f"Objective call {call_counter['n']}")
    
#     # unscale first
#     theta = unscale(theta_norm)
    
#     sim = run_hbv_single(theta, forcing, shape_name)
    
#     nse_val = 1 - np.sum((sim - q_obs)**2) / np.sum((q_obs - q_obs.mean())**2)
    
#     # vol_errs = []
#     # for y in np.unique(years):
#     #     mask = years == y
#     #     sim_y = sim[mask].sum()
#     #     obs_y = q_obs[mask].sum()
#     #     vol_errs.append((sim_y - obs_y) / obs_y)
#     # vol_term = np.mean(np.square(vol_errs))
    
#     return float(1 - nse_val)   # + vol_term)

def volume_error(sim, obs):
    return abs(1 - np.sum(sim) / np.sum(obs))


call_counter = {"n": 0}

def objective_safe(theta_norm, forcing, q_obs, shape_name):
    """
    Safe objective function for CMA-ES calibration of the HBV model.

    This function unscales the normalized parameter vector, runs the HBV model 
    for a single catchment, computes hydrological performance metrics 
    (NSE, KGE, and volume error), and combines them into a weighted objective 
    function. The function also records the history of parameters and metrics 
    for analysis.

    Parameters
    ----------
    theta_norm : array_like
        Normalized parameter vector (values in [0,1]) for HBV.
    forcing : pd.DataFrame or dict
        Meteorological forcing data (e.g., precipitation, temperature) for the model.
    q_obs : array_like or pd.Series
        Observed streamflow time series corresponding to the simulation period.
    years : array_like
        List or array of years corresponding to the simulation period.
    shape_name : str
        Identifier for the catchment or model configuration to simulate.

    Returns
    -------
    float
        Weighted objective function value:
            obj_val = 0.3*(1-NSE) + 0.3*(1-KGE) + 0.4*VolumeError

    Notes
    -----
    - NSE: Nash-Sutcliffe Efficiency, evaluates hydrograph fit.
    - KGE: Kling-Gupta Efficiency (2009), evaluates correlation, variability, and bias.
    - VolumeError: Absolute error in total simulated vs. observed streamflow volume, 
      important for endorheic basins where long-term water balance is critical.
    - History of parameters and metrics is stored in the global `history` dictionary.
    - The global `call_counter` dictionary tracks the number of function evaluations.
    """
    
    call_counter["n"] += 1

    # Unscale parameters for HBV
    theta_phys = unscale(theta_norm)

    # Run HBV
    sim = run_hbv_single(theta_phys, forcing, shape_name)

    # --- Metrics ---
    nse = 1 - np.sum((sim - q_obs)**2) / np.sum((q_obs - q_obs.mean())**2)

    r = np.corrcoef(sim, q_obs)[0, 1]
    alpha = np.std(sim) / np.std(q_obs)
    beta = np.mean(sim) / np.mean(q_obs)
    kge = 1 - np.sqrt((r - 1)**2 + (alpha - 1)**2 + (beta - 1)**2)

    vol_err = volume_error(sim, q_obs)

    # --- Combined objective ---
    obj_val = 0.3 * (1 - nse) + 0.3 * (1 - kge) + 0.4 * vol_err

    # --- Store in history ---
    history.setdefault("theta_norm", []).append(theta_norm.copy())
    history.setdefault("theta_phys", []).append(theta_phys.copy())
    history.setdefault("objective", []).append(obj_val)
    history.setdefault("nse", []).append(nse)
    history.setdefault("kge", []).append(kge)
    history.setdefault("vol_err", []).append(vol_err)

    return obj_val
    
def save_history(history, filename, folder="results", fmt="csv"):
    """
    Save CMA-ES calibration history to file.

    Parameters
    ----------
    history : dict
        Dictionary containing CMA-ES calibration history.
        Expected keys: 'theta_norm', 'theta_phys', 'objective', 'nse', 'kge', 'vol_err', ...
    filename : str
        Name of the file (without extension) to save.
    folder : str, optional
        Folder to save the file in (default is "results"). Created if it does not exist.
    fmt : str, optional
        File format: "csv", "json", or "pkl" (default is "csv").
    """
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, filename + "." + fmt)

    # Convert history to DataFrame if possible
    df = pd.DataFrame(history)

    if fmt == "csv":
        df.to_csv(path, index=False)
    elif fmt == "json":
        df.to_json(path, orient="records", indent=2)
    elif fmt == "pkl":
        df.to_pickle(path)
    else:
        raise ValueError("Unsupported format. Choose 'csv', 'json', or 'pkl'.")

    print(f"History saved to {path}")

#TODO: add function for cma-es (note to self: see work document)












