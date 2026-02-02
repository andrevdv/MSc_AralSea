# Aral Sea - Andre van der Veen
This repository contains the Python-based framework developed as part of my Master’s thesis in Hydrology at TU Delft. It focuses on assessing the combined effects of climate change and human activities on the water balance and river discharge of the Aral Sea basin.

The project includes:

* Data processing workflows for meteorological forcing and hydrological observations.

* Hydrological modeling tools for simulating river discharge, lake volume, and water balance components.

* Scenario analyses to explore the impacts of different climate and water management conditions.

While the framework is tailored to the Aral Sea, parts of the workflows and tools are designed to be reusable for other river basins or hydrological studies.

- [Overview](#overview)
- [Contact](#contact)
- [Folder Structure](#folder-structure)
- [Examples](#examples)


## Overview
Python source code lives in [`/src/`](./work_in_progress/src/) in modular `.py` files:

- [`forcing.py`](./work_in_progress/src/forcing.py) – everything related to meteorological forcing
- [`models.py`](./work_in_progress/src/models.py) – functions for simulating hydrological models
- [`paths.py`](./work_in_progress/src/paths.py) – file to standardize paths used in the work
- [`constants.py`](./work_in_progress/src/constants.py) – physical constants and model parameters
etc

Other main folders:

- [`/data/`](./work_in_progress/data/) – raw and processed input data
- [`/forcing/`](./work_in_progress/forcing/) – meteorological forcing generation and storage
- [`/outputs/`](./work_in_progress/outputs/) – generated outputs (time series, plots, figures, analysis)
- [`/notebooks/`](./work_in_progress/notebooks/) – Jupyter notebooks for analysis and visualization
- [`/model_runs/`](./work_in_progress/model_runs/) – model runs for scenario analysis




## Examples

## Contact
**Author:** [André van der Veen](https://github.com/andrevdv)  
**Institution:** [TU Delft](https://www.tudelft.nl/)  
**Project Link:** [Aral Sea Hydrology Thesis](https://github.com/andrevdv/MSc_AralSea)




## Abstract