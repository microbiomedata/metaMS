from dataclasses import dataclass

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
    cores : int
        The number of cores to use for processing   

    """

    directory: str = 'data/...'
    output_directory: str = 'output/...'
    corems_toml_path: str = 'configuration/lipidomics_corems.toml'
    cores: int = 1
    
def run_lcms_lipidomics_workflow(directory, output_directory, corems_toml_path, cores):
    # Put a dummy function here for now
    pass