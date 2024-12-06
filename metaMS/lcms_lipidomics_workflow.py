from dataclasses import dataclass
import toml
from pathlib import Path
import datetime
from multiprocessing import Pool
from typing import List
import click

from corems.mass_spectra.input.mzml import MZMLSpectraParser
from corems.mass_spectra.input.rawFileReader import ImportMassSpectraThermoMSFileReader

@dataclass
class LipidomicsWorkflowParameters:
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
    metabref_token_path : str
        The path to the metabref token file
        See https://metabref.emsl.pnnl.gov/api for more information for how to get a token
    scan_translator_path : str
        The path to the scan translator file, optional
    cores : int
        The number of cores to use for processing, optional

    """
    file_paths: tuple = ('data/...', 'data/...')
    output_directory: str = "output"
    corems_toml_path: str = None
    metabref_token_path: str = None
    scan_translator_path: str = None
    cores: int = 1

def check_lipidomics_workflow_params(lipid_workflow_params):
    # Check that corems_toml_path exists
    if not Path(lipid_workflow_params.corems_toml_path).exists():
        click.echo("Corems toml file not found, exiting workflow")
        return
    
    # Check that metabref_token_path exists
    if not Path(lipid_workflow_params.metabref_token_path).exists():
        click.echo("Metabref token file not found, exiting workflow")
        return
    
    # Check that scan_translator_path exists
    if not Path(lipid_workflow_params.scan_translator_path).exists():
        click.echo("Scan translator file not found, exiting workflow")
        return
    
    # Check that output_directory exists
    if not Path(lipid_workflow_params.output_directory).exists():
        click.echo("Output directory not found, exiting workflow")
        return
    
    # Check that file_paths exist
    for file_path in lipid_workflow_params.file_paths:
        if not Path(file_path).exists():
            click.echo(f"File path {file_path} not found, exiting workflow")
            return


def instantiate_lcms_obj(file_in):
    """Instantiate a corems LCMS object from a binary file.  Pull in ms1 spectra into dataframe (without storing as MassSpectrum objects to save memory)

    Parameters
    ----------
    file_in : str or Path
        Path to binary file
    verbose : bool
        Whether to print verbose output

    Returns
    -------
    myLCMSobj : corems LCMS object
        LCMS object with ms1 spectra in dataframe
    """
    # Instantiate parser based on binary file type
    if ".raw" in str(file_in):
        #TODO KRH: Add real functionality here
        pass
        #parser = ImportMassSpectraThermoMSFileReader(file_in)

    if ".mzML" in str(file_in):
        #parser = MZMLSpectraParser(file_in)
        pass

    # Instantiate lc-ms data object using parser and pull in ms1 spectra into dataframe (without storing as MassSpectrum objects to save memory)
    #myLCMSobj = parser.get_lcms_obj(spectra="ms1")
    myLCMSobj = None

    return myLCMSobj

def run_lipid_sp_ms1(file_in, out_path, params_toml, scan_translator):
    time_start = datetime.datetime.now()
    myLCMSobj = instantiate_lcms_obj(file_in)   
    # TODO KRH: Add signal processing and ms1 molecular search here

def run_lcms_lipidomics_workflow(
    lipidomics_workflow_paramaters_file=None,
    file_paths=None,
    output_directory=None,
    corems_toml_path=None,
    metabref_token_path=None,
    scan_translator_path=None,
    cores=None,
):
    if lipidomics_workflow_paramaters_file is not None:
        # Set the parameters from the toml file
        with open(lipidomics_workflow_paramaters_file, "r") as infile:
            lipid_workflow_params = LipidomicsWorkflowParameters(**toml.load(infile))
    else:
        lipid_workflow_params = LipidomicsWorkflowParameters(
            file_paths= file_paths.split(","),
            output_directory=output_directory,
            metabref_token_path=metabref_token_path,
            scan_translator_path=scan_translator_path,
            corems_toml_path=corems_toml_path,
            cores=cores,
        )
    
    # Make output dir and get list of files to process
    out_dir = Path(lipid_workflow_params.output_directory)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Check that all parameters are valid and exist
    check_lipidomics_workflow_params(lipid_workflow_params)

    # Organize input and output paths
    file_paths = [Path(file_path) for file_path in lipid_workflow_params.file_paths]
    files_list = list(file_paths)
    out_paths_list = [out_dir / f.stem for f in files_list]
    
    # Run signal processing, get associated ms1, add associated ms2, do ms1 molecular search, and export intermediate results
    cores = lipid_workflow_params.cores
    params_toml = lipid_workflow_params.corems_toml_path
    scan_translator = lipid_workflow_params.scan_translator_path
    
    """
    if cores == 1 or len(files_list) == 1:
        mz_dicts = []
        for file_in, file_out in list(zip(files_list, out_paths_list)):
            mz_dict = run_lipid_sp_ms1(
                file_in=str(file_in),
                out_path=str(file_out),
                params_toml=params_toml,
                scan_translator=scan_translator,
            )
            mz_dicts.append(mz_dict)
    elif cores > 1:
        pool = Pool(cores)
        args = [
            (
                str(file_in),
                str(file_out),
                params_toml,
                scan_translator,
            )
            for file_in, file_out in list(zip(files_list, out_paths_list))
        ]
        mz_dicts = pool.starmap(run_lipid_sp_ms1, args)
        pool.close()
        pool.join()
    print("Finished processing all files")
    """
    # TODO KRH: Add full lipidomics workflow here
