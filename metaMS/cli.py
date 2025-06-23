from pathlib import Path

import click
import toml
from corems.encapsulation.output.parameter_to_json import dump_gcms_settings_toml

from metaMS.gcmsWorkflow import (
    WorkflowParameters,
    run_gcms_metabolomics_workflow,
    run_gcms_metabolomics_workflow_wdl,
)

from metaMS.lcms_lipidomics_workflow import (
    LipidomicsWorkflowParameters,
    run_lcms_lipidomics_workflow,
)

from metaMS.lcms_metabolomics_workflow import (
    LCMetabolomicsWorkflowParameters,
    run_lcms_metabolomics_workflow,
)


@click.group()
def cli():
    # saving for toplevel options
    pass


@cli.command()
@click.argument("file_paths", required=True, type=str)
@click.argument("calibration_file_path", required=True, type=str)
@click.argument("output_directory", required=True, type=str)
@click.argument("output_filename", required=True, type=str)
@click.argument("output_type", required=True, type=str)
@click.argument("corems_toml_path", required=True, type=str)
@click.option("--nmdc_metadata_path", default=None, type=str)
@click.option("--metabref_token_path", type=str, default=None, help="Path to the metabref token file")
@click.option("--jobs", "-j", default=4, help="'cpu's'")
def run_gcms_wdl_workflow(
    file_paths,
    calibration_file_path,
    output_directory,
    output_filename,
    output_type,
    corems_toml_path,
    nmdc_metadata_path,
    metabref_token_path,
    jobs,
):
    """Run the GCMS workflow\n
    gcms_workflow_paramaters_toml_file = toml file with workflow parameters\n
    output_types = csv, excel, pandas, json set on the parameter file\n
    corems_toml_path = toml file with corems parameters\n
    --jobs = number of processes to run in parallel\n
    """
    metabref_token_path = ""
    click.echo("Running gcms workflow")
    run_gcms_metabolomics_workflow_wdl(
        file_paths=file_paths,
        calibration_file_path=calibration_file_path,
        output_directory=output_directory,
        output_filename=output_filename,
        output_type=output_type,
        corems_toml_path=corems_toml_path,
        metabref_token_path=metabref_token_path,
        jobs=jobs,
    )

@cli.command()
@click.argument("gcms_workflow_paramaters_file", required=True, type=str)
@click.option("--jobs", "-j", default=4, help="'cpu's'")
@click.option(
    "--nmdc",
    "-n",
    is_flag=True,
    help="Creates NMDC metadata mapping and save each result individually",
)
def run_gcms_workflow(gcms_workflow_paramaters_file, jobs, nmdc):
    """Run the GCMS workflow\n
    gcms_workflow_paramaters_toml_file = toml file with workflow parameters\n
    output_types = csv, excel, pandas, toml set on the parameter file\n
    corems_toml_path = toml file with corems parameters\n
    --jobs = number of processes to run in parallel\n
    """
    click.echo("Running gcms workflow")
    if nmdc:
        raise NotImplementedError("NMDC flag mo longer supported, metadata is now generated separately")
    else:
        run_gcms_metabolomics_workflow(gcms_workflow_paramaters_file, jobs)

@cli.command(name="dump-gcms-toml-template")
@click.argument("toml_file_name", required=True, type=str)
def dump_gcms_toml_template(toml_file_name):
    """Dumps a toml file template
    to be used as the workflow parameters input for the GCMS workflow
    """
    ref_lib_path = Path(toml_file_name).with_suffix(".toml")
    with open(ref_lib_path, "w") as workflow_param:
        toml.dump(WorkflowParameters().__dict__, workflow_param)


@cli.command(name="dump-gcms-corems-toml-template")
@click.argument("toml_file_name", required=True, type=str)
def dump_gcms_corems_toml_template(toml_file_name):
    """Dumps a CoreMS toml file template
    to be used as the workflow parameters input
    """
    path_obj = Path(toml_file_name).with_suffix(".toml")
    dump_gcms_settings_toml(file_path=path_obj)


@cli.command(name="dump-lipidomics-toml-template")
@click.argument("toml_file_name", required=True, type=str)
def dump_lipidomics_toml_template(toml_file_name):
    """
    Writes a toml file template to run the lipidomics workflow, starting with the input file

    Parameters
    ----------
    toml_file_name : str
        The name of the toml file to write the parameters to
    """
    ref_lib_path = Path(toml_file_name).with_suffix(".toml")
    with open(ref_lib_path, "w") as workflow_param:
        toml.dump(LipidomicsWorkflowParameters().__dict__, workflow_param)


@cli.command(name="run-lipidomics-workflow")
@click.option(
    "-p",
    "--paramaters_file",
    required=False,
    type=str,
    help="The path to the toml file with the lipidomics workflow parameters",
)
@click.option(
    "-i",
    "--file_paths",
    required=False,
    type=str,
    help="The path to the directory with the input files",
)
@click.option(
    "-o",
    "--output_directory",
    required=False,
    type=str,
    help="The directory where the output files will be stored",
)
@click.option(
    "-c",
    "--corems_params",
    required=False,
    type=str,
    help="The path corems parameters toml file",
)
@click.option(
    "-d", "--db_location", required=False, type=str, help="The path to the local database"
)
@click.option(
    "-s", "--scan_translator_path", required=False, type=str, help="The path to the scan translator file"
)
@click.option(
    "-j", "--cores", required=False, type=int, help="'cpu's to use for processing"
)
def run_lipidomics_workflow(
    paramaters_file, 
    file_paths, 
    output_directory, 
    corems_params, 
    db_location, 
    scan_translator_path, 
    cores
    ):
    """Run the lipidomics workflow

    Parameters
    ----------
    paramaters_file : str
        The path to the toml file with the lipidomics workflow parameters
    file_paths : str
        The paths to the input files, separated by commas as one string
    output_directory : str
        The directory where the output files will be stored
    corems_params : str
        The path corems parameters toml file
    db_location : str
        The path to the sqlite database for lipid spectra searching
    scan_translator_path : str
        The path to the scan translator file
    cores : int
        The number of cores to use for processing
    """
    if paramaters_file is not None:
        if cores is not None or file_paths is not None:
            click.echo("Using parameters file, ignoring other parameters")
        run_lcms_lipidomics_workflow(
            lipidomics_workflow_paramaters_file=paramaters_file
        )
    else:
        if cores is None:
            cores = 1
        if file_paths is None:
            click.echo("No file paths provided, no data to process")
            return
        if corems_params is None:
            click.echo("No corems parameters provided")
        if scan_translator_path is None:
            click.echo("No scan translator provided")
        if output_directory is None:
            click.echo(
                "Must provide an output directory if not using a parameters file"
            )
            return
        if db_location is None:
            click.echo("No database path provided")
            return
        run_lcms_lipidomics_workflow(
            file_paths=file_paths,
            output_directory=output_directory,
            corems_toml_path=corems_params,
            db_location=db_location,
            scan_translator_path=scan_translator_path,
            cores=cores,
        )


@cli.command(name="dump-lcms-metabolomics-toml-template")
@click.argument("toml_file_name", required=True, type=str)
def dump_lipidomics_toml_template(toml_file_name):
    """
    Writes a toml file template to run the lipidomics workflow, starting with the input file

    Parameters
    ----------
    toml_file_name : str
        The name of the toml file to write the parameters to
    """
    ref_lib_path = Path(toml_file_name).with_suffix(".toml")
    with open(ref_lib_path, "w") as workflow_param:
        toml.dump(LipidomicsWorkflowParameters().__dict__, workflow_param)


@cli.command(name="run-lcms-metabolomics-workflow")
@click.option(
    "-p",
    "--paramaters_file",
    required=False,
    type=str,
    help="The path to the toml file with the lipidomics workflow parameters",
)
@click.option(
    "-i",
    "--file_paths",
    required=False,
    type=str,
    help="The path to the directory with the input files",
)
@click.option(
    "-o",
    "--output_directory",
    required=False,
    type=str,
    help="The directory where the output files will be stored",
)
@click.option(
    "-c",
    "--corems_params",
    required=False,
    type=str,
    help="The path corems parameters toml file",
)
@click.option(
    "-m", "--msp_file_path", required=False, type=str, help="The path to the local database"
)
@click.option(
    "-s", "--scan_translator_path", required=False, type=str, help="The path to the scan translator file"
)
@click.option(
    "-j", "--cores", required=False, type=int, help="'cpu's to use for processing"
)
def run_lcmsmetab_workflow(
    paramaters_file, 
    file_paths, 
    output_directory, 
    corems_params, 
    msp_file_path, 
    scan_translator_path, 
    cores
    ):
    """Run the LC metabolomics workflow

    Parameters
    ----------
    paramaters_file : str
        The path to the toml file with the workflow parameters
    file_paths : str
        The paths to the input files, separated by commas as one string
    output_directory : str
        The directory where the output files will be stored
    corems_params : str
        The path corems parameters toml file
    msp_file_path : str
        The path to the sqlite database for spectra searching
    scan_translator_path : str
        The path to the scan translator file
    cores : int
        The number of cores to use for processing
    """
    if paramaters_file is not None:
        if cores is not None or file_paths is not None:
            click.echo("Using parameters file, ignoring other parameters")
        run_lcms_metabolomics_workflow(
            lcmsmetab_workflow_parameters_file=paramaters_file
        )
    else:
        if cores is None:
            cores = 1
        click.echo(cores)
        if file_paths is None:
            click.echo("No file paths provided, no data to process")
            return
        click.echo(file_paths)
        if corems_params is None:
            click.echo("No corems parameters provided")
        click.echo(corems_params)
        if scan_translator_path is None:
            click.echo("No scan translator provided")
        click.echo(scan_translator_path)
        if output_directory is None:
            click.echo(
                "Must provide an output directory if not using a parameters file"
            )
            return
        click.echo(output_directory)
        if msp_file_path is None:
            click.echo("No database path provided")
            return
        click.echo(msp_file_path)
        run_lcms_metabolomics_workflow(
            file_paths=file_paths,
            output_directory=output_directory,
            corems_toml_path=corems_params,
            msp_file_path=msp_file_path,
            scan_translator_path=scan_translator_path,
            cores=cores,
        )
