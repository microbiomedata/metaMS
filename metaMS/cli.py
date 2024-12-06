from multiprocessing import Pool
from pathlib import Path

import click
import toml

from corems.encapsulation.output.parameter_to_json import dump_gcms_settings_toml

from metaMS.gcmsWorkflow import (
    WorkflowParameters,
    run_gcms_metabolomics_workflow,
    run_gcms_metabolomics_workflow_wdl,
    run_nmdc_metabolomics_workflow,
)
from metaMS.lcms_lipidomics_workflow import (
    LipidomicsWorkflowParameters,
    run_lcms_lipidomics_workflow,
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
@click.argument("nmdc_metadata_path", required=True, type=str)
@click.option("--jobs", "-j", default=4, help="'cpu's'")
def run_gcms_wdl_workflow(
    file_paths,
    calibration_file_path,
    output_directory,
    output_filename,
    output_type,
    corems_toml_path,
    nmdc_metadata_path,
    jobs,
):
    """Run the GCMS workflow\n
    gcms_workflow_paramaters_toml_file = toml file with workflow parameters\n
    output_types = csv, excel, pandas, json set on the parameter file\n
    corems_toml_path = toml file with corems parameters\n
    --jobs = number of processes to run in parallel\n
    """
    click.echo("Running gcms workflow")
    run_gcms_metabolomics_workflow_wdl(
        file_paths,
        calibration_file_path,
        output_directory,
        output_filename,
        output_type,
        corems_toml_path,
        jobs,
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
        run_nmdc_metabolomics_workflow(gcms_workflow_paramaters_file, jobs)
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


@cli.command(name="dump-lipidomics-corems-toml-template")
@click.argument("toml_file_name", required=True, type=str)
def dump_lipidomics_corems_toml_template(toml_file_name):
    """
    Writes a toml file with the CoreMS parameters to be used in the lipidomics workflow

    Parameters
    ----------
    toml_file_name : str
        The name of the toml file to write the parameters to
    """
    path_obj = Path(toml_file_name).with_suffix(".toml")
    print("dumping lipidomics corems toml template")
    pass
    # TODO KRH: add call for dumping lipidomics corems toml template from corems once we can import it


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
    "-t", "--token_path", required=False, type=str, help="The path to the metabref token"
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
    token_path, 
    scan_translator_path, 
    cores
    ):
    """Run the lipidomics workflow

    Parameters
    ----------
    #TODO KRH: Add this in
    """
    if paramaters_file is not None:
        if cores is not None or file_paths is not None:
        #TODO KRH: Add all other parameters above
            click.echo("Using parameters file, ignoring other parameters")
        #run_lcms_lipidomics_workflow(
        #    lipidomics_workflow_paramaters_file=paramaters_file
        #)
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
        if token_path is None:
            click.echo("No metabref token provided")
            return
        run_lcms_lipidomics_workflow(
            file_paths=file_paths,
            output_directory=output_directory,
            corems_toml_path=corems_params,
            metabref_token_path=token_path,
            scan_translator_path=scan_translator_path,
            cores=cores,
        )
