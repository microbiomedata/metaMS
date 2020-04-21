import json
from multiprocessing import Pool
from pathlib import Path

import click

from metaMS.gcmsWorkflow import run_gcms_metabolomics_workflow, WorkflowParameters

@click.group()
def cli():
    #saving for toplevel options 
    pass   

@cli.command()
@click.argument('gcms_workflow_paramaters_file', required=True, type=str)
@click.option('--jobs','-j', default=4, help='CPUs')
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
@click.argument('json_file_name', required=True, type=str, )
def dump_json_template(json_file_name):
    '''Dumps a json file template
        to be used as the workflow parameters input 
    '''
    ref_lib_path = Path(json_file_name).with_suffix('.json')
    with open(ref_lib_path, 'w') as workflow_param:
    
        json.dump(WorkflowParameters().__dict__, workflow_param, indent=4)




        