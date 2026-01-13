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


# ------------------------------
# Outputs
# ------------------------------
OUTPUTS = ROOT / "outputs"
FIGURES = OUTPUTS / "figures"
MODEL_OUTPUT = OUTPUTS / "model_runs"
OUTPUT_HBV = MODEL_OUTPUT / "hbv"
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
