:github_url: https://github.com/microbiomedata/metaMS/blob/master/docs/index.rst

..
   Note: The above `github_url` field is used to force the target of the "Edit on GitHub" link
         to be the specified URL. That makes it so the link will work, regardless of the Sphinx
         site the file is incorporated into. You can learn more about the `github_url` field at:
         https://sphinx-rtd-theme.readthedocs.io/en/stable/configuring.html#confval-github_url

Metabolomics Workflow
==============================

.. image:: metams_workflow2024.svg

Workflow Overview
-------

The gas chromatography-mass spectrometry (GC-MS) based metabolomics workflow (metaMS) has been developed by leveraging PNNL's CoreMS software framework.
The current software design allows for the orchestration of the metabolite characterization pipeline, i.e., signal noise reduction, m/z based Chromatogram Peak Deconvolution,
abundance threshold calculation, peak picking, spectral similarity calculation and molecular search, similarity score calculation, and confidence filtering, all in a single step.

Workflow Availability
---------------------

The workflow is available in GitHub:
https://github.com/microbiomedata/metaMS

The container is available at Docker Hub (microbiomedata/metaMS):
https://hub.docker.com/r/microbiomedata/metams

The python package is available on PyPi:
https://pypi.org/project/metaMS/

The databases are available by request.
Please contact NMDC (support@microbiomedata.org) for access.

Requirements for Execution
--------------------------

- Docker Container Runtime
  
  or  
- Python Environment >= 3.10
- Python Dependencies are listed on requirements.txt

Execution Details
~~~~~~~~~~~~~~~~

Please refer to: 

https://github.com/microbiomedata/metaMS#metams-installation

Hardware Requirements
--------------------------
- To run this application, you need a processor with at least 2.0 GHz speed, 8GB of RAM, 10GB of free hard disk space


Workflow Dependencies
---------------------

Software
~~~~~~~~~~~~~~~~~~~~

- CoreMS (2-clause BSD)
- Click (BSD 3-Clause "New" or "Revised" License)

Database
~~~~~~~~~~~~~~~~
- Available at https://metabref.emsl.pnnl.gov/

Test datasets
-------------
https://github.com/microbiomedata/metaMS/tree/master/data/raw_data/GCMS_FAMES_01_GCMS-01_20191023.cdf


Inputs
~~~~~~~~

- Supported format for low resolution GC-MS data:  
   - ANDI NetCDF for GC-MS (.cdf)
- Fatty Acid Methyl Esters Calibration File:
   - ANDI NetCDF for GC-MS (.cdf) - C8 to C30
- Parameters:
    - CoreMS Parameter File (.json)
    - MetaMS Parameter File (.json)

Outputs
~~~~~~~~

- Metabolites data-table
    - CSV, TAB-SEPARATED TXT
    - HDF: CoreMS HDF5 format
    - XLSX : Microsoft Excel
- Workflow Metadata:
    - JSON

Version History
---------------

- Current version is 3.3.1

Point of contact
----------------

Package maintainer: Yuri E. Corilo <corilo@pnnl.gov>