# Description

This Snakemake workflow is for modelling Aral Sea water levels under historical and future climate scenarios. This is developed as part of a Master's Thesis at the Delft University of Technology.

In short:

- The workflow first generates ERA5 re analysis and CMIP6 climatological forcing for different model and different SSP scenarios.
- These forcings are used in PCR-GLOBWB2 global hydrological model to model the discharges of the Amu Darya and Syr Darya. 
- The discharges of these rivers is consequently fed into an Aral Sea volume balance model to simulate the Aral Sea water levels, both historical and projections to the future. 
- Various related figures, tables, etc are also derived from this workflow

## Repository structure



## Requirements
- for now: requirements.txt

## Installation
- 

## Usage
- edit .yaml for paths
- experiment planner 
- list some snakemake commands
- Jupyter notebooks are available in the [notebooks](./notebooks/) folder.
- 

- [Input data folder](input_data/)


## Input data
- short description, refer to data.md in data folder?

## Run examples

- Preview workflow (dry-run):

```bash
snakemake -n
```

- Run the full workflow with 4 cores:

```bash
snakemake -j 4
```

- Run Snakemake with nohup + 8 cores + logging
```bash
nohup snakemake -j 8 > snakemake.log 2>&1 &
```


## citation

## license

- my license (MIT?)
- eWaterycle
- ERA5
- CMIP
- PCR GLOBWB
- GRDC
- Dahiti/INTAS




## contact

- studentmail (will cease to exist?)
- github?
- ewatercycle for projects repo?
- OrcID https://orcid.org/0009-0009-5611-8888