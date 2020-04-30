from dataclasses import dataclass
from multiprocessing import Pool
from pathlib import Path
import json

from corems.mass_spectra.input.andiNetCDF import ReadAndiNetCDF
from corems.encapsulation.input import parameter_from_json
from corems.mass_spectra.calc.GC_RI_Calibration import get_rt_ri_pairs
from corems.molecular_id.search.compoundSearch import LowResMassSpectralMatch
import cProfile

@dataclass
class WorkflowParameters:
    
    file_paths: tuple = ('data/...', 'data/...')
    calibration_file_path: str = 'data/...'
    output_directory: str = 'data/...'
    output_filename: str = 'data/...'
    output_type: str = 'csv'
    corems_json_path: str = 'data/corems.json'

def worker(args):

    cProfile.runctx('workflow_worker(args)', globals(), locals(), 'gc-ms.prof')

def run_gcms_metabolomics_workflow(workflow_params_file, jobs):
    
    workflow_params = read_workflow_parameter(workflow_params_file)

    rt_ri_pairs = get_calibration_rtri_pairs(workflow_params.calibration_file_path, workflow_params.corems_json_path)   

    worker_args = [(file_path, rt_ri_pairs, workflow_params.corems_json_path) for file_path in workflow_params.file_paths]
    #gcms_list = pool.map(workflow_worker, worker_args)
    pool = Pool(jobs)
    
    gcms_list = []
    for i, gcms in enumerate(pool.imap_unordered(worker, worker_args), 1):
        gcms_list.append(gcms)

    pool.close()
    pool.join()
    
    #output_path = '{DIR}/{NAME}'.format(DIR=workflow_params.output_directory, NAME=workflow_params.output_filename)
    
    dirloc = Path(workflow_params.output_directory)
    dirloc.mkdir(exist_ok=True)
    
    #for gcms in gcms_list:
        
    #    eval('gcms.to_'+ workflow_params.output_type + '(output_path, highest_score=False)')

def read_workflow_parameter(gcms_workflow_paramaters_json_file):
    with open(gcms_workflow_paramaters_json_file, 'r') as infile:
        return WorkflowParameters(**json.load(infile))    

def get_calibration_rtri_pairs(ref_file_path, corems_paramaters_json_file):
    
    gcms_ref_obj = get_gcms(ref_file_path, corems_paramaters_json_file)
    #sql_obj = start_sql_from_file()
    #rt_ri_pairs = get_rt_ri_pairs(gcms_ref_obj,sql_obj=sql_obj)
    # !!!!!! READ !!!!! use the previous two lines if db/pnnl_lowres_gcms_compounds.sqlite does not exist
    # and comment the next line
    rt_ri_pairs = get_rt_ri_pairs(gcms_ref_obj)
    return rt_ri_pairs


def workflow_worker(args):
    
    file_path, ref_dict, corems_params = args
    
    gcms = get_gcms(file_path, corems_params)
    
    gcms.calibrate_ri(ref_dict)
    
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

    parameter_from_json.load_and_set_parameters_gcms(gcms, settings_path=corems_params)
    
    gcms.process_chromatogram()

    return gcms       


def start_sql_from_file():
    
    from corems.molecular_id.input.nistMSI import ReadNistMSI
    ref_lib_path = Path("path_to/your_compound_ref_file.MSL")
    if ref_lib_path.exists:
        sql_obj = ReadNistMSI(ref_lib_path).get_sqlLite_obj()
        return sql_obj