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
    
    file_paths: tuple = ('data/...', 'data/...')
    #RI FAMES Calibration File
    calibration_file_path: str = 'data/...'
    #Sample/Process Metadata
    nmdc_metadata_path: str = 'configuration/nmdc_metadata.json' 
    #configuration file for corems
    corems_toml_path: str = 'configuration/corems.toml'
    output_directory: str = 'data/...'
    output_filename: str = 'data/...'
    output_type: str = 'csv'
    
def worker(args):

    cProfile.runctx('workflow_worker(args)', globals(), locals(), 'gc-ms.prof')

def run_gcms_metabolomics_workflow_wdl(file_paths, calibration_file_path, output_directory,output_filename, output_type, corems_toml_path, jobs, db_path=None):
    
    import click
    workflow_params = WorkflowParameters()
    workflow_params.file_paths = file_paths.split(",")
    workflow_params.calibration_file_path = calibration_file_path
    workflow_params.output_directory = output_directory
    workflow_params.output_filename = output_filename
    workflow_params.output_type = output_type
    workflow_params.corems_toml_path = corems_toml_path
    
    dirloc = Path(workflow_params.output_directory)
    dirloc.mkdir(exist_ok=True)
    output_path = Path(workflow_params.output_directory)/workflow_params.output_filename
    
    rt_ri_pairs = get_calibration_rtri_pairs(workflow_params.calibration_file_path, workflow_params.corems_toml_path)   

    worker_args = [(file_path, rt_ri_pairs, workflow_params.corems_toml_path, workflow_params.calibration_file_path ) for file_path in workflow_params.file_paths]
    #gcms_list = pool.map(workflow_worker, worker_args)
    pool = Pool(int(jobs))
    
    for i, gcms in enumerate(pool.imap_unordered(workflow_worker, worker_args), 1):
        eval('gcms.to_'+ workflow_params.output_type + '(output_path)')

    pool.close()
    pool.join()

def run_nmdc_metabolomics_workflow(workflow_params_file, jobs):
    
    import click
    dms_file_path = 'db/GC-MS Metabolomics Experiments to Process Final.xlsx'
    
    click.echo('Loading Searching Settings from %s' % workflow_params_file)
    workflow_params = read_workflow_parameter(workflow_params_file)
    
    dirloc = Path(workflow_params.output_directory)
    dirloc.mkdir(exist_ok=True)
    
    rt_ri_pairs = get_calibration_rtri_pairs(workflow_params.calibration_file_path, workflow_params.corems_toml_path)   

    worker_args = [(file_path, rt_ri_pairs, workflow_params.corems_toml_path, workflow_params.calibration_file_path) for file_path in workflow_params.file_paths]
    #gcms_list = pool.map(workflow_worker, worker_args)
    pool = Pool(jobs)
    
    for i, gcms in enumerate(pool.imap_unordered(workflow_worker, worker_args), 1):
        
        in_file_path = Path(workflow_params.file_paths[i])
        output_path = Path(workflow_params.output_directory)/in_file_path.name

        eval('gcms.to_'+ workflow_params.output_type + '(output_path, write_metadata=False)')
        
        #nmdc = NMDC_Metadata(in_file_path, workflow_params.calibration_file_path, output_path, dms_file_path)
        #nmdc.create_nmdc_metadata(gcms)

    pool.close()
    pool.join()
    

def run_gcms_metabolomics_workflow(workflow_params_file, jobs):
    import click
    click.echo('Loading Searching Settings from %s' % workflow_params_file)

    workflow_params = read_workflow_parameter(workflow_params_file)

    dirloc = Path(workflow_params.output_directory)
    dirloc.mkdir(exist_ok=True)
    output_path = Path(workflow_params.output_directory)/workflow_params.output_filename
    
    rt_ri_pairs = get_calibration_rtri_pairs(workflow_params.calibration_file_path, workflow_params.corems_toml_path)   

    worker_args = [(file_path, rt_ri_pairs, workflow_params.corems_toml_path, workflow_params.calibration_file_path) for file_path in workflow_params.file_paths]
    #gcms_list = pool.map(workflow_worker, worker_args)
    pool = Pool(jobs)
    
    for i, gcms in enumerate(pool.imap_unordered(workflow_worker, worker_args), 1):
        eval('gcms.to_'+ workflow_params.output_type + '(output_path)')

    pool.close()
    pool.join()
    
def read_workflow_parameter(gcms_workflow_paramaters_toml_file):
    with open(gcms_workflow_paramaters_toml_file, 'r') as infile:
        return WorkflowParameters(**toml.load(infile))    

def get_calibration_rtri_pairs(ref_file_path, corems_paramaters_toml_file):
    
    gcms_ref_obj = get_gcms(ref_file_path, corems_paramaters_toml_file)
    #sql_obj = start_sql_from_file()
    #rt_ri_pairs = get_rt_ri_pairs(gcms_ref_obj,sql_obj=sql_obj)
    # !!!!!! READ !!!!! use the previous two lines if db/EMSL_lowres_gcms_test_database.sqlite does not exist
    # and comment the next line
    rt_ri_pairs = get_rt_ri_pairs(gcms_ref_obj)
    return rt_ri_pairs

def workflow_worker(args):
    
    file_path, ref_dict, corems_params, cal_file_path = args
    
    gcms = get_gcms(file_path, corems_params)
    
    gcms.calibrate_ri(ref_dict, cal_file_path)
    
    # sql_obj = start_sql_from_file()
    # lowResSearch = LowResMassSpectralMatch(gcms, sql_obj=sql_obj)
    # !!!!!! READ !!!!! use the previous two lines if db/pnnl_lowres_gcms_compounds.sqlite does not exist
    # and comment the next line
    lowResSearch = LowResMassSpectralMatch(gcms)
    lowResSearch.run()

    return gcms

def get_gcms(file_path, corems_params):
    
    reader_gcms = ReadAndiNetCDF(file_path)
	
    reader_gcms.run()
    
    gcms = reader_gcms.get_gcms_obj()

    parameter_from_json.load_and_set_toml_parameters_gcms(gcms, parameters_path=corems_params)
    
    gcms.process_chromatogram()

    
    return gcms

def start_sql_from_file():
    
    from pathlib import Path
    from corems.molecular_id.input.nistMSI import ReadNistMSI

    ref_lib_path = Path("data/PNNLMetV20191015.MSL")
    if ref_lib_path.exists:
        sql_obj = ReadNistMSI(ref_lib_path).get_sqlLite_obj()
        return sql_obj


def run_gcms_mpi(workflow_params_file, replicas, rt_ri_pairs):
    
    import os, sys
    sys.path.append(os.getcwd()) 
    from mpi4py import MPI
    
    workflow_params = read_workflow_parameter(workflow_params_file)
    rt_ri_pairs = get_calibration_rtri_pairs(workflow_params.calibration_file_path, workflow_params.corems_toml_path) 
    worker_args = [(file_path, rt_ri_pairs, workflow_params.corems_toml_path, workflow_params.calibration_file_path) for file_path in workflow_params.file_paths]

    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()
    size = comm.Get_size()
    
    # will only run tasks up to the number of files paths selected in the EnviroMS File
    if rank < len(worker_args):
        workflow_worker(worker_args[rank])