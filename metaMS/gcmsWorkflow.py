import cProfile
from dataclasses import dataclass
from multiprocessing import Pool
from pathlib import Path

import toml
from corems.encapsulation.input import parameter_from_json
from corems.mass_spectra.calc.GC_RI_Calibration import get_rt_ri_pairs
from corems.mass_spectra.input.andiNetCDF import ReadAndiNetCDF
from corems.molecular_id.search.compoundSearch import LowResMassSpectralMatch
from corems.molecular_id.search.database_interfaces import MetabRefGCInterface


@dataclass
class WorkflowParameters:
    """
    Data class to establish workflow parameters.

    Parameters
    ----------
    file_paths : tuple(str)
        Paths to files to process.
    calibration_reference_path : str
        FAMEs retention index reference SQLite database.
    calibration_file_path : str
        FAMEs retention index calibration filepath.
    nmdc_metadata_path : str
        Sample and processing metadata.
    corems_toml_path : str
        CoreMS configuration.
    output_directory : str
        Path to save outputs.
    output_filename : str
        Output filename.
    output_type :
        Output extension.

    """

    # Filepaths to process
    file_paths: tuple = ("data/...", "data/...")

    # RI FAMEs calibration files
    calibration_reference_path: str = "data/..."
    calibration_file_path: str = "data/..."

    # Sample/Process Metadata
    nmdc_metadata_path: str = "configuration/nmdc_metadata.json"

    # Configuration file for corems
    corems_toml_path: str = "configuration/corems.toml"
    output_directory: str = "data/..."
    output_filename: str = "data/..."
    output_type: str = "csv"

    # Token
    metabref_token_path: str = "configuration/..."


def worker(args):
    """
    Wraps `workflow_worker` using cProfile.

    """

    cProfile.runctx("workflow_worker(args)", globals(), locals(), "gc-ms.prof")


def run_gcms_metabolomics_workflow_wdl(
    file_paths,
    calibration_file_path,
    output_directory,
    output_filename,
    output_type,
    corems_toml_path,
    metabref_token_path,
    jobs,
    db_path=None,
):
    """
    GCMS metabolomics workflow with WDL.

    Parameters
    ----------
    file_paths : tuple(str)
        Paths to files to process.
    calibration_file_path : str
        FAMEs retention index calibration filepath.
    output_directory : str
        Path to save outputs.
    output_filename : str
        Output filename.
    output_type :
        Output extension.
    corems_toml_path : str
        CoreMS configuration.
    metabref_token_path : str
        Token to authenticate MetabRef database access.
    jobs : int
        Number of concurrent jobs.
    [unused] db_path : str
        Path to database.

    """

    import click

    # Store workflow parameters
    workflow_params = WorkflowParameters()
    workflow_params.file_paths = file_paths.split(",")
    workflow_params.calibration_file_path = calibration_file_path
    workflow_params.output_directory = output_directory
    workflow_params.output_filename = output_filename
    workflow_params.output_type = output_type
    workflow_params.corems_toml_path = corems_toml_path
    workflow_params.metabref_token_path = metabref_token_path

    # Load CoreMS settings
    click.echo("Loading CoreMS settings from %s" % workflow_params.corems_toml_path)

    # Create output directory
    dirloc = Path(workflow_params.output_directory)
    dirloc.mkdir(exist_ok=True)

    # Determine output filepath
    output_path = (
        Path(workflow_params.output_directory) / workflow_params.output_filename
    )

    # Load FAMEs calibration data
    gcms_cal_obj = get_gcms(
        workflow_params.calibration_file_path, workflow_params.corems_toml_path
    )

    # Load FAMEs calibration reference
    fames_ref_sql = MetabRefGCInterface().get_fames(format="sql")

    # Compute RT:RI pairs
    rt_ri_pairs = get_rt_ri_pairs(gcms_cal_obj, sql_obj=fames_ref_sql)

    # Prepare worker arguments with output directory and type
    worker_args = [
        (
            file_path,
            rt_ri_pairs,
            workflow_params.corems_toml_path,
            workflow_params.calibration_file_path,
            workflow_params.output_type,
            workflow_params.output_directory,
        )
        for file_path in workflow_params.file_paths
    ]

    # Run the remaining workflow and write outputs
    # If jobs == 1, run the workflow without multiprocessing as a loop
    if jobs == 1:
        for args in worker_args:
            run_workflow_worker_and_write(args)
        return
    
    else:
        # Create pool of workers and run the workflow
        with Pool(jobs) as pool:
            pool.map(run_workflow_worker_and_write, worker_args)

def run_gcms_metabolomics_workflow(workflow_params_file, jobs):
    """
    GC/MS metabolomics workflow.

    Parameters
    ----------
    workflow_params_file : str
        Path to workflow parameters file.
    jobs : int
        Number of concurrent jobs.

    """

    import click

    # Load workflow settings
    click.echo("Loading search settings from %s" % workflow_params_file)
    workflow_params = load_workflow_parameters(workflow_params_file)

    # Create output directory
    dirloc = Path(workflow_params.output_directory)
    dirloc.mkdir(exist_ok=True)

    # Determine output filepath
    output_path = (
        Path(workflow_params.output_directory) / workflow_params.output_filename
    )

    # Load FAMEs calibration data
    gcms_cal_obj = get_gcms(
        workflow_params.calibration_file_path, workflow_params.corems_toml_path
    )

    # Load FAMEs calibration reference
    MetabRefGCInterface().set_token(workflow_params.metabref_token_path)
    fames_ref_sql = MetabRefGCInterface().get_fames(format="sql")

    # Compute RT:RI pairs
    rt_ri_pairs = get_rt_ri_pairs(gcms_cal_obj, sql_obj=fames_ref_sql)

    # Prepare worker arguments
    worker_args = [
        (
            file_path,
            rt_ri_pairs,
            workflow_params.corems_toml_path,
            workflow_params.calibration_file_path,
            workflow_params.output_type,
            workflow_params.output_directory,
        )
        for file_path in workflow_params.file_paths
    ]

    # Run the remaining workflow and write outputs
    # If jobs == 1, run the workflow without multiprocessing as a loop
    if jobs == 1:
        for args in worker_args:
            run_workflow_worker_and_write(args)
        return
    
    else:
        # Create pool of workers and run the workflow
        with Pool(jobs) as pool:
            pool.map(run_workflow_worker_and_write, worker_args)


def read_toml(path):
    """
    Read TOML file.

    Parameters
    ----------
    path : str
        Path to TOML file.

    Returns
    -------
    dict
        Dictionary of parameter:value pairs.

    """

    with open(path, "r", encoding="utf8") as stream:
        return toml.load(stream)


def load_workflow_parameters(path):
    """
    Load workflow configuration parameters from file.

    Parameters
    ----------
    path : str
        Path to parameters file.

    Returns
    -------
    :obj:`WorkflowParameters`
        Data class containing workflow parameters.

    """

    return WorkflowParameters(**read_toml(path))


def load_corems_parameters(path):
    """
    Load workflow configuration parameters from file.

    Parameters
    ----------
    path : str
        Path to parameters file.

    Returns
    -------
    dict
        Dictionary of parameter:value pairs.

    """

    return read_toml(path)


# Function for running the workflow_worker and writing out the output
def run_workflow_worker_and_write(
        args
):
    """
    Function for running the workflow_worker and writing out the output.

    Parameters
    ----------
    args : tuple
        Arguments fed to worker.
        args = (file_path, rt_ri_pairs, corems_params_file, cal_file_path, output_type, output_directory)

    Returns
    -------
    None, but writes out the output to the specified directory.
    """
    # Unpack arguments
    file_path, rt_ri_pairs, corems_params_file, cal_file_path, output_type, output_directory = args

    # Repack arguments for workflow_worker
    wrk_args = (file_path, rt_ri_pairs, corems_params_file, cal_file_path)

    # Run workflow
    gcms = workflow_worker(wrk_args)

    # Determine output path
    input_path = Path(file_path)
    # if output_directory doesn't exist, create it
    Path(output_directory).mkdir(parents=True, exist_ok=True)
    output_path = Path(output_directory) / input_path.name
    eval("gcms.to_" + output_type + "(output_path)")


def workflow_worker(args):
    """
    Wrap data processing functionality for parallel execution. Loads GC data,
    applies calibration, performs spectral search.

    Parameters
    ----------
    args : tuple
        Arguments fed to worker.

    Returns
    -------
    gcms
        GCMS object.

    """

    # Unpack arguments
    file_path, ref_dict, corems_params_file, cal_file_path = args

    # Load data
    gcms = get_gcms(file_path, corems_params_file)

    # Calibrate retention indices
    gcms.calibrate_ri(ref_dict, cal_file_path)

    # Load reference database
    ref_db_sql = MetabRefGCInterface().get_library(format="sql")

    # Perform search
    lowResSearch = LowResMassSpectralMatch(gcms, sql_obj=ref_db_sql)
    lowResSearch.run()

    return gcms


def get_gcms(file_path, corems_params):
    """
    Convenience function to load and process file according to CoreMS configuration
    parameters.

    Parameters
    ----------

    """

    # Read NetCDF file
    reader_gcms = ReadAndiNetCDF(file_path)

    # Process data
    reader_gcms.run()

    # Export to GCMS object
    gcms = reader_gcms.get_gcms_obj()

    # Set parameters from file
    parameter_from_json.load_and_set_toml_parameters_gcms(
        gcms, parameters_path=corems_params
    )

    # Process chromatogram
    gcms.process_chromatogram()

    return gcms
