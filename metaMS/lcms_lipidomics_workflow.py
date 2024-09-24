from dataclasses import dataclass
from multiprocessing import Pool
from pathlib import Path

import toml

from corems.mass_spectra.input.andiNetCDF import ReadAndiNetCDF
from corems.encapsulation.input import parameter_from_json
from corems.mass_spectra.calc.GC_RI_Calibration import get_rt_ri_pairs
from corems.molecular_id.search.compoundSearch import LowResMassSpectralMatch

import cProfile

@dataclass
class WorkflowParameters:
    """
    Parameters for the lipidomics workflow

    Parameters
    ----------
    directory : str
        The directory where the data is stored, all files in the directory will be processed
    output_directory : str
        The directory where the output files will be stored
    corems_toml_path : str
        The path to the corems configuration file
    cores : int
        The number of cores to use for processing   

    """

    directory: str = 'data/...'
    output_directory: str = 'data/...'
    corems_toml_path: str = 'configuration/corems.toml'
    cores: int = 1
    
def run_lcms_lipidomics_workflow(directory, output_directory, corems_toml_path, cores):
    # Put a dummy function here for now
    pass