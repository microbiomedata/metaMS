from dataclasses import dataclass
import toml
from pathlib import Path


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

    directory: str = "data/..."
    output_directory: str = "output/..."
    corems_toml_path: str = "configuration/lipidomics_corems.toml"
    metabref_token_path: str = None
    scan_translator_path: str = None
    cores: int = 1


def run_lcms_lipidomics_workflow(
    lipidomics_workflow_paramaters_file=None,
    directory=None,
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
            directory=directory,
            output_directory=output_directory,
            metabref_token_path=metabref_token_path,
            scan_translator_path=scan_translator_path,
            corems_toml_path=corems_toml_path,
            cores=cores,
        )
    
    # Make output dir and get list of files to process
    out_dir = Path(lipid_workflow_params.output_directory)
    out_dir.mkdir(parents=True, exist_ok=True)

    file_dir = Path(lipid_workflow_params.directory)
    files_list = list(file_dir.glob("*.raw"))
    out_paths_list = [out_dir / f.stem for f in files_list]
        
    # TODO KRH: Add full lipidomics workflow here
