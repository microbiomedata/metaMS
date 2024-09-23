# Table of Contents  
- Introduction
  - [MetaMS](#MetaMS)  
  - [Version](#current-version)  
  - [Data Input](#data-input-formats)  
  - [Data Output](#data-output-formats)  
  - [Data Structure](#data-structure-types)  
  - [Features](#available-features)  
  - [Code Documentation](https://emsl-computing.github.io/MetaMS/)  

- Installation
  - [PyPi](#metams-installation)  

- Execution:  
  - [CLI](#execution)  
  - [MiniWDL](#MiniWDL)  
  - [Docker Container](#metams-docker-container)  
# MetaMS

**MetaMS** is a workflow for metabolomics data processing and annotation

## Current Version

### `2.2.3`

### Data input formats

- ANDI NetCDF for GC-MS (.cdf)
- CoreMS self-containing Hierarchical Data Format (.hdf5)
- ChemStation Agilent (Ongoing)

### Data output formats

- Pandas data frame (can be saved using pickle, h5, etc)
- Text Files (.csv, tab separated .txt, etc)
- Microsoft Excel (xlsx)
- JSON for workflow metadata
- Self-containing Hierarchical Data Format (.hdf5) including raw data and ime-series data-point for processed data-sets with all associated metadata stored as json attributes

### Data structure types

- GC-MS

## Available features

### Signal Processing

- Baseline detection, subtraction, smoothing 
- m/z based Chromatogram Peak Deconvolution,
- Manual and automatic noise threshold calculation
- First and second derivatives peak picking methods
- Peak Area Calculation


### Calibration

- Retention Index Linear XXX method 

### Compound Identification

- Automatic local (SQLite) or external (MongoDB or PostgreSQL) database check, generation, and search
- Automatic molecular match algorithm with all spectral similarity methods 

## MetaMS Installation

Make sure you have python 3.9.13 installed before continue

- PyPi:     
```bash
pip3 install metams
```

- From source:
 ```bash
pip3 install --editable .
```

To be able to open chemstation files a installation of pythonnet is needed:
- Windows: 
    ```bash
    pip3 install pythonnet
    ```

- Mac and Linux:
    ```bash
    brew install mono
    pip3 install pythonnet   
    ```

## Execution

```bash
metaMS dump-toml-template metams.toml
```
```bash
metaMS dump-corems-toml-template corems.toml
```

 Modify the metams.toml and corems.toml accordingly to your dataset and workflow parameters
make sure to include corems.json path inside the metams.toml: "corems_toml_path": "path_to_corems.toml" 

```bash
metaMS run-gcms-workflow path_to_metams.toml
```

## MiniWDL 

Make sure you have python 3.9.13 installed before continue

MiniWDL uses the microbiome/metaMS image so there is not need to install metaMS

- Change wdl/metams_input.json to specify the data location

- Change data/corems.toml to specify the workflow parameters

Install miniWDL:
```bash
pip3 install miniwdl
```

Call:
```bash
miniwdl run wdl/metaMS.wdl -i wdl/metams_input.json --verbose --no-cache --copy-input-files
```
## MetaMS Docker Container

You will need docker and docker compose: 

If you don't have it installed, the easiest way is to [install docker for desktop](https://www.docker.com/products/docker-desktop/)

- Pull from Docker Registry:

    ```bash
    docker pull microbiomedata/metams:latest
    
    ```
- or Build the image from source:

    ```bash
    docker build -t microbiomedata/metams:latest .
    ```
- Run Workflow from Container:

    $(data_dir) = full path of directory containing the gcms data
    $(config_dir) = full path of directory containing configuration and parameters metams.toml and corems.toml
    ```bash
    docker run -v $(data_dir):/metaB/data -v $(config_dir):/metaB/configuration microbiomedata/metams:latest metaMS run-gcms-workflow /metaB/configuration/metams.toml
    ```

- Getting the parameters templates:
    
    ```bash
    docker run -v $(config_dir):/metaB/configuration microbiomedata/metams:latest metaMS dump-json-template /metaB/configuration/metams.toml
    ```
    
    ```bash
    docker run -v $(config_dir):/metaB/configuration microbiomedata/metams:latest metaMS dump-corems-json-template /metaB/configuration/corems.toml
    ```

## Disclaimer

This material was prepared as an account of work sponsored by an agency of the
United States Government.  Neither the United States Government nor the United
States Department of Energy, nor Battelle, nor any of their employees, nor any
jurisdiction or organization that has cooperated in the development of these
materials, makes any warranty, express or implied, or assumes any legal
liability or responsibility for the accuracy, completeness, or usefulness or
any information, apparatus, product, software, or process disclosed, or
represents that its use would not infringe privately owned rights.

Reference herein to any specific commercial product, process, or service by
trade name, trademark, manufacturer, or otherwise does not necessarily
constitute or imply its endorsement, recommendation, or favoring by the United
States Government or any agency thereof, or Battelle Memorial Institute. The
views and opinions of authors expressed herein do not necessarily state or
reflect those of the United States Government or any agency thereof.

                 PACIFIC NORTHWEST NATIONAL LABORATORY
                              operated by
                                BATTELLE
                                for the
                   UNITED STATES DEPARTMENT OF ENERGY
                    under Contract DE-AC05-76RL01830