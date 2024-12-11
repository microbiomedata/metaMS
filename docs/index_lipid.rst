Lipidomics Workflow
==============================

Summary
-------

The liquid chromatography-mass spectrometry (LC-MS)-based lipidomics workflow ( part of MetaMS) 
is built using PNNL’s CoreMS software framework. The workflow leverages many features of CoreMS as well as PNNL’s MetabRef LC-MS database to process LC-MS/MS data and identify lipids. 
The initial signal processing includes peak picking, integration of mass features, deconvolution of MS1, and calculation of peak shape metrics. 
The workflow associates MS1 spectra with their corresponding MS2 spectra (only for data-dependent acqusition, currently). 
It uses the MS2 spectra to search an in-silico spectra database for lipids and uses the MS1 data to assign a molecular formula. 
Each candidate lipid assignment is given two confidence scores: one for its match to the predicted molecular formula based on the mass accuracy and fine isotopic structure 
and a second for the MS2 spectral matching for filtering and selecting the best match.


Workflow Diagram
------------------

.. image:: metamsworkflow.png


Workflow Dependencies
---------------------

Third party software
~~~~~~~~~~~~~~~~~~~~

- CoreMS version 3.0 or greater (2-clause BSD)
- Click (BSD 3-Clause "New" or "Revised" License)

Database 
~~~~~~~~~~~~~~~~
- PNNL Metabolomics LC-MS in silico Spectral Database (https://metabref.emsl.pnnl.gov/)

Workflow Availability
---------------------

The workflow is available in GitHub:
https://github.com/microbiomedata/metaMS

The container is available at Docker Hub (microbiomedata/metaMS):
https://hub.docker.com/r/microbiomedata/metams

The python package is available on PyPi:
https://pypi.org/project/metaMS/

The database is available by request.
Please contact NMDC (support@microbiomedata.org) for access.

Test datasets
-------------
#TODO KRH: add test datasets somewhere

Execution Details
---------------------

This workflow should be executed using the provided wdl file (wdl/metaMS_lipidomics.wdl).

Example command to run the workflow:
```
miniwdl run wdl/metaMS_lipidomics.wdl -i wdl/metams_input_lipidomics.json --verbose --no-cache --copy-input-files
```

Inputs
~~~~~~~~
Only data-dependent acquisition is supported at this time, but both HCD and CID fragmentation are supported.
Data must be collected in profile mode for MS1. 

To use the wdl, inputs should be specified in a json file.  See example input json file in wdl/metaMS_lipidomics.wdl.

The following inputs are required:
- Supported file formats for LC-MS data:  
   - ThermoFisher mass spectrometry data files (.raw)
   - mzML mass spectrometry data files (.mzml)
- Parameter files:
   - CoreMS Parameter file (.toml).  See example in configuration/lipid_configs/emsl_lipidomics_corems_params.toml.
   - Scan Translator Parameter file (.toml).  See example in configuration/lipid_configs/emsl_lipidomics_scan_translator_params.toml.
   - MetabRef configuration key (metabref.token).  See MetabRef documentation (https://metabref.emsl.pnnl.gov/api) for how to generate a token.
- Cores (optional):
   - How many cores to use for processing.  Default is 1. 

Outputs
~~~~~~~~

- Metabolites data-table
    - Peak data table with annotated lipids (.csv)
    - HDF: CoreMS HDF5 format
- Workflow Metadata:
    - TOML : CoreMS TOML format


Requirements for Execution
--------------------------

- Docker Container Runtime
  
  or 
- Python Environment >= 3.11
- .NET or appropriate runtime (i.e. pythonnet).  Only if processing ThermoFisher raw files.
- Python Dependencies are listed on requirements.txt

Hardware Requirements
--------------------------
- To run this application, we reccomend a processor with at least 2.0 GHz speed, 8GB of RAM, 10GB of free hard disk space

Version History
---------------

- #TODO KRH: add version history

Point of contact
----------------

Package maintainer: Katherine R. Heal <katherine.heal@pnnl.gov>
