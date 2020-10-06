import json
from multiprocessing import Pool
from pathlib import Path

import click

from metaMS.gcmsWorkflow import WorkflowParameters, run_gcms_metabolomics_workflow, run_gcms_metabolomics_workflow_wdl
from corems.encapsulation.output.parameter_to_json import dump_gcms_settings_json

@click.group()
def cli():
    #saving for toplevel options 
    pass

@cli.command()
@click.argument('file_paths', required=True, type=list)
@click.argument('calibration_file_path', required=True, type=str)
@click.argument('output_directory', required=True, type=str)
@click.argument('output_filename', required=True, type=str)
@click.argument('output_type', required=True, type=str)
@click.argument('corems_json_path', required=True, type=str)
@click.option('--jobs','-j', default=4, help="'cpu's'")
def run_gcms_wdl_workflow(file_paths, calibration_file_path, output_directory,output_filename, output_type, corems_json_path, jobs):
    '''Run the GCMS workflow\n
       gcms_workflow_paramaters_json_file = json file with workflow parameters\n
       output_types = csv, excel, pandas, json set on the parameter file\n
       corems_json_path = json file with corems parameters\n
       --jobs = number of processes to run in parallel\n 
    '''
    click.echo('Running gcms workflow')
    
    run_gcms_metabolomics_workflow_wdl(file_paths, calibration_file_path, output_directory,output_filename, output_type, corems_json_path, jobs)

@cli.command()
@click.argument('gcms_workflow_paramaters_file', required=True, type=str)
@click.option('--jobs','-j', default=4, help="'cpu's'")
def run_gcms_workflow(gcms_workflow_paramaters_file, jobs):
    '''Run the GCMS workflow\n
       gcms_workflow_paramaters_json_file = json file with workflow parameters\n
       output_types = csv, excel, pandas, json set on the parameter file\n
       corems_json_path = json file with corems parameters\n
       --jobs = number of processes to run in parallel\n 
    '''
    click.echo('Running gcms workflow')
    
    run_gcms_metabolomics_workflow(gcms_workflow_paramaters_file, jobs)

@cli.command()
@click.argument('json_file_name', required=True, type=str)
def dump_json_template(json_file_name):
    '''Dumps a json file template
        to be used as the workflow parameters input 
    '''
    ref_lib_path = Path(json_file_name).with_suffix('.json')
    with open(ref_lib_path, 'w') as workflow_param:
    
        json.dump(WorkflowParameters().__dict__, workflow_param, indent=4)

@cli.command()
@click.argument('json_file_name', required=True, type=str)
def dump_corems_json_template(json_file_name):
    '''Dumps a CoreMS json file template
        to be used as the workflow parameters input 
    '''
    path_obj = Path(json_file_name).with_suffix('.json')
    dump_gcms_settings_json(file_path=path_obj)
    


        