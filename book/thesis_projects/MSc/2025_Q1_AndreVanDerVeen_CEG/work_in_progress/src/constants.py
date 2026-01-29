"""
# Constants for the Aral Sea thesis project
"""
import numpy as np

# ==============================================================================
# HBV MODEL PARAMETERS
# ==============================================================================
#--------------------------
# Dummy parameters placeholder

DUMMY_HBV_PARAMS =  [
    7.085,  # Imax
    0.837,  # Ce
    76.373, # Sumax
    1.112,  # Beta
    0.245,  # Pmax
    7.801,  # Tlag
    0.096,  # Kf
    0.003,  # Ks
    0.226   # FM
]

# Initial conditions placeholder
DUMMY_HBV_INITIAL = np.array([
    0,      # Si
    100,    # Su
    0,      # Sf
    5,      # Ss
    0       # Sp
])

PARAMETER_NAMES = [
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

INITIAL_CONDITION_NAMES = [
    "Si",  # 0
    "Su",  # 1
    "Sf",  # 2
    "Ss",  # 3
    "Sp"   # 4
]

HBV_PARAM_BOUNDS = {
    "min": np.array([0, 0.2, 40, 0.5, 0.001, 1, 0.01, 0.0001, 0.01]),
    "max": np.array([25, 1, 800, 4, 0.3, 15, 0.02, 0.01, 0.8])
}

# Parameter names for the model (descriptive)
PARAMETER_NAMES_LONG = [
    "Imax_interception_max_storage",     # 0: Maximum interception storage (mm)
    "Ce_effective_precipitation_coeff",  # 1: Effective precipitation coefficient (-)
    "Sumax_max_soil_moisture",           # 2: Maximum soil moisture storage (mm)
    "Beta_shape_coefficient",            # 3: Shape coefficient (-)
    "Pmax_max_percolation_rate",         # 4: Maximum percolation rate (mm/day)
    "Tlag_lag_time",                      # 5: Lag time for response (days)
    "Kf_fast_flow_recession",             # 6: Fast flow recession coefficient (1/day)
    "Ks_slow_flow_recession",             # 7: Slow flow recession coefficient (1/day)
    "FM_fraction_melt"                    # 8: Fraction of snowmelt contributing to flow (-)
]

# Initial condition names for the model (descriptive)
INITIAL_CONDITION_NAMES_LONG = [
    "Si_initial_interception_storage",   # 0: Initial interception storage (mm)
    "Su_initial_upper_zone_storage",     # 1: Initial upper zone storage (mm)
    "Sf_initial_fast_flow_storage",      # 2: Initial fast flow storage (mm)
    "Ss_initial_slow_flow_storage",      # 3: Initial slow flow storage (mm)
    "Sp_initial_percolation_storage"     # 4: Initial percolation storage (mm)
]

TYUMEN_ARYK_HBV_PARAMS_CMAES = [
    22.459392,  # Imax
    0.690535,   # Ce
    188.080331, # Sumax
    0.669292,   # Beta
    0.281391,   # Pmax
    2.097142,   # Tlag
    0.014930,   # Kf
    0.009363,   # Ks
    0.135953   # FM
]



# ==============================================================================
# CMA-ES CALIBRATION SETTINGS
# ==============================================================================
CMAES_DEFAULT_POPSIZE = 15
CMAES_DEFAULT_MAXFEVALS = 500
CMAES_DEFAULT_SIGMA = 0.1


# Objective function weights
OBJECTIVE_WEIGHTS = {
'nse': 0.3,
'kge': 0.3,
'volume_error': 0.4,
}

# ==============================================================================
# CLIMATE MODEL SETTINGS
# ==============================================================================
# Default CMIP6 models
DEFAULT_CMIP6_MODELS = {
'historical': 'MPI-ESM1-2-HR', 
'future': 'MPI-ESM1-2-HR' #, EC-Earth3
}

# SSP scenarios
SSP_SCENARIOS = ['ssp126', 'ssp245', 'ssp585'] #these have the best data coverage



# ==============================================================================
# PCR-GLOBWB SETTINGS
# ==============================================================================
# Grid resolution requirements
PCRGLOBWB_RESOLUTION_MULTIPLE = 3 # degrees, for get_integer_multiple_bounds
PCRGLOBWB_ESMVALTOOL_PADDING = 2 # degrees, padding for forcing extraction



# ==============================================================================
# Aral Sea Model Constants
# ==============================================================================
MAKKINK_FACTOR = 1.15