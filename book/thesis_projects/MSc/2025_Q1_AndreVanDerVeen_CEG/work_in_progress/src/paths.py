from pathlib import Path

# ------------------------------
# Project Root
# ------------------------------
ROOT = Path(__file__).resolve().parents[1]  # work_in_progress

# ------------------------------
# Data folders
# ------------------------------
DATA = ROOT / "data"
GRDC = DATA / "grdc"           
BATHYMETRY = DATA / "bathymetry"
SHAPEFILES = DATA / "shapefiles"


# ------------------------------
# Forcing
# ------------------------------
FORCING_FOLDER = ROOT / "forcing"
FORCING_OUTPUT = FORCING_FOLDER / "output"
FORCING_ERA5 = FORCING_OUTPUT / "ERA5"
FORCING_CMIP_HIST = FORCING_OUTPUT / "CMIP_HIST"
FORCING_CMIP_FUT = FORCING_OUTPUT / "CMIP_FUT"
FORCING_PCRGLOB = FORCING_OUTPUT / "PCRGLOBWB"

# ------------------------------
# Outputs
# ------------------------------
OUTPUTS = ROOT / "outputs"
FIGURES = OUTPUTS / "figures"
MODEL_OUTPUT = OUTPUTS / "model_runs"
OUTPUT_HBV = MODEL_OUTPUT / "HBV"
OUTPUT_PCRGLOB = MODEL_OUTPUT / "pcr-globwb"


# ------------------------------
# Notebooks
# ------------------------------
NOTEBOOKS = ROOT / "notebooks"

# ------------------------------
# Model Runs (intermediate folders)
# ------------------------------
MODEL_RUNS = ROOT / "model_runs"
RUNS_HBV = MODEL_RUNS / "hbv"
RUNS_LB = MODEL_RUNS / "leakybucket"
RUNS_PCR = MODEL_RUNS / "pcrglobwb"
