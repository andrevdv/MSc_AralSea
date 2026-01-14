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

def run_HBV_model(forcing, parameter_set, initial_conditions, show_progress=True, delete_files = False):
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
        pbar = tqdm(total=total_steps, desc="Running HBV model",mininterval=1.0)

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
    print("starting model, might take a minute or so")
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

    # Convert ISO 8601 strings to datetime objects
    start_time = datetime.strptime(start_date, '%Y-%m-%dT%H:%M:%SZ')
    end_time = datetime.strptime(end_date, '%Y-%m-%dT%H:%M:%SZ')

    # Calculate the number of days for the progression bar
    delta = end_time - start_time
    number_of_days = delta.days

    pbar = tqdm(total=number_of_days, desc="Running model", mininterval=1.0)

    while model.time < model.end_time:

        model.update()
        pbar.update(1)



    pbar.close()
    print("Model run finished!")

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
            show_progress=False,
            delete_files=delete_files,
        )
        all_series.append(s)
    
    df_all = pd.concat(all_series, axis=1)
    df_all.columns = [f"particle_{i}" for i in range(n_particles)]

    return df_all



    















