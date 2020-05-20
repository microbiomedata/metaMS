# MetaMS

**MetaMS** is a workflow for metabolomics data processing and annotation

## Current Version

### `1.1.1`

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
- Manual and automatic noise threshold calculation
- First and second derivatives peak picking methods
- Peak Area Calculation
- EIC Chromatogram deconvolution(TODO)

### Calibration

- Retention Index Linear XXX method 

### Compound Identification

- Automatic local (SQLite) or external (MongoDB or PostgreSQL) database check, generation, and search
- Automatic molecular match algorithm with all spectral similarity methods 

## MetaMS Installation

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

## Usage

```bash
metaMS dump_json_template MetamsFile.json
```
```bash
metaMS dump_corems_json_template CoremsFile.json
```

 Modify the MetamsFile.json and CoremsFile.json accordingly to your dataset and workflow parameters
make sure to include CoremsFile.json path inside the MetamsFile.json: "corems_json_path": "path_to_CoremsFile.json" 

```bash
metaMS run-gcms-workflow path_to_MetamsFile.json
```

## MetaMS Docker 

A docker image containing the MetaMS command line as the entry point

If you don't have docker installed, the easiest way is to [install docker for desktop](https://hub.docker.com/?overlay=onboarding)

- Pull from Docker Registry:

    ```bash
    docker pull corilo/metams:latest
    
    ```

- Build the image from source:

    ```bash
    docker build -t metams:latest .
    ```
- Run Workflow from Container:

    $(data_dir) = dir_containing the gcms data, MetamsFile.json and CoremsFile.json
    
    ```bash
    docker run -v $(data_dir):/metaB/data corilo/metams:latest run-gcms-workflow /metaB/data/MetamsFile.json    
    ```

- Getting the parameters templates:
    
    ```bash
    docker run -v $(data_dir):/metaB/data corilo/metams:latest dump_json_template /metaB/data/MetamsFile.json    
    ```
    
    ```bash
    docker run -v $(data_dir):/metaB/data corilo/metams:latest dump_corems_json_template /metaB/data/CoremsFile.json
    ```
    