from dataclasses import dataclass
import toml
from pathlib import Path
import datetime
from multiprocessing import Pool
from typing import List
import click
import warnings

from corems.mass_spectra.input.mzml import MZMLSpectraParser
from corems.mass_spectra.input.rawFileReader import ImportMassSpectraThermoMSFileReader
from corems.mass_spectra.output.export import LipidomicsExport
from corems.encapsulation.input.parameter_from_json import (
    load_and_set_toml_parameters_lcms,
)

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
        raise FileNotFoundError("Corems toml file not found, exiting workflow")
    
    # Check that metabref_token_path exists
    if not Path(lipid_workflow_params.metabref_token_path).exists():
        raise FileNotFoundError("Metabref token file not found, exiting workflow")
    
    # Check that scan_translator_path exists
    if not Path(lipid_workflow_params.scan_translator_path).exists():
        raise FileNotFoundError("Scan translator file not found, exiting workflow")
    
    # Check that output_directory exists
    if not Path(lipid_workflow_params.output_directory).exists():
        raise FileNotFoundError("Output directory not found, exiting workflow")
    
    # Check that file_paths exist
    for file_path in lipid_workflow_params.file_paths:
        if not Path(file_path).exists():
            raise FileNotFoundError(f"File path {file_path} not found, exiting workflow")
    
    # Check that all file_paths end in .raw or .mzML
    for file_path in lipid_workflow_params.file_paths:
        if ".raw" not in file_path and ".mzML" not in file_path:
            raise ValueError(f"File path {file_path} is not a .raw or .mzML file, exiting workflow")

    #TODO KRH: Add a check that we can access the metabref API with the token

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
        parser = ImportMassSpectraThermoMSFileReader(file_in)

    if ".mzML" in str(file_in):
        parser = MZMLSpectraParser(file_in)

    # Instantiate lc-ms data object using parser and pull in ms1 spectra into dataframe (without storing as MassSpectrum objects to save memory)
    myLCMSobj = parser.get_lcms_obj(spectra="ms1")

    return myLCMSobj

def set_params_on_lcms_obj(myLCMSobj, params_toml):
    """Set parameters on the LCMS object

    Parameters
    ----------
    myLCMSobj : corems LCMS object
        LCMS object to set parameters on
    params_toml : str or Path
        Path to toml file with parameters

    Returns
    -------
    None, sets parameters on the LCMS object
    """
    # Load parameters from toml file
    load_and_set_toml_parameters_lcms(myLCMSobj, params_toml)

    # If myLCMSobj is a positive mode, remove Cl from atoms used in molecular search
    # This cuts down on the number of molecular formulas searched hugely
    if myLCMSobj.polarity == "positive":
        myLCMSobj.parameters.mass_spectrum["ms1"].molecular_search.usedAtoms.pop("Cl")
    elif myLCMSobj.polarity == "negative":
        myLCMSobj.parameters.mass_spectrum["ms1"].molecular_search.usedAtoms.pop("Na")

def load_scan_translator(scan_translator=None):
    """Translate scans using a scan translator

    Parameters
    ----------
    scan_translator : str or Path
        Path to scan translator yaml file

    Returns
    -------
    scan_dict : dict
        Dict with keys as parameter keys and values as lists of scans
    """
    # Convert the scan translator to a dictionary
    if scan_translator is None:
        scan_translator_dict = {"ms2": {"scan_filter": "", "resolution": "high"}}
    else:
        # Convert the scan translator to a dictionary
        if isinstance(scan_translator, str):
            scan_translator = Path(scan_translator)
        # read in the scan translator from toml
        with open(scan_translator, "r") as f:
            scan_translator_dict = toml.load(f)
    for param_key in scan_translator_dict.keys():
        if scan_translator_dict[param_key]["scan_filter"] == "":
            scan_translator_dict[param_key]["scan_filter"] = None
    return scan_translator_dict

def check_scan_translator(myLCMSobj, scan_translator):
    """Check if scan translator is provided and that it maps correctly to scans and parameters"""
    scan_translator_dict = load_scan_translator(scan_translator)
    # Check that the scan translator maps correctly to scans and parameters
    scan_df = myLCMSobj.scan_df
    scans_pulled_out = []
    for param_key in scan_translator_dict.keys():
        assert param_key in myLCMSobj.parameters.mass_spectrum.keys()
        assert "scan_filter" in scan_translator_dict[param_key].keys()
        assert "resolution" in scan_translator_dict[param_key].keys()
        # Pull out scans that match the scan filter
        scan_df_sub = scan_df[
            scan_df.scan_text.str.contains(
                scan_translator_dict[param_key]["scan_filter"]
            )
        ]
        scans_pulled_out.extend(scan_df_sub.scan.tolist())
        if len(scan_df_sub) == 0:
            raise ValueError(
                "No scans pulled out by scan translator for parameter key: ",
                param_key,
                " and scan filter: ",
                scan_translator_dict[param_key]["scan_filter"],
            )

    # Check that the scans pulled out by the scan translator are not overlapping and assert error if they are
    if len(set(scans_pulled_out)) != len(scans_pulled_out):
        raise ValueError("Overlapping scans pulled out by scan translator")

def add_mass_features(myLCMSobj, scan_translator):
    """Process ms1 spectra and perform molecular search

    This includes peak picking, adding and processing associated ms1 spectra,
    integration of mass features, annotation of c13 mass features, deconvolution of ms1 mass features,
    and adding of peak shape metrics of mass features to the mass feature dataframe.

    Parameters
    ----------
    myLCMSobj : corems LCMS object
        LCMS object to process
    scan_translator : str or Path
        Path to scan translator yaml file

    Returns
    -------
    None, processes the LCMS object
    """
    # Process ms1 spectra
    myLCMSobj.find_mass_features()
    myLCMSobj.add_associated_ms1(
        auto_process=True, use_parser=False, spectrum_mode="profile"
    )
    myLCMSobj.integrate_mass_features(drop_if_fail=True)
    myLCMSobj.find_c13_mass_features()
    myLCMSobj.deconvolute_ms1_mass_features()
    myLCMSobj.add_peak_metrics()

    # Add associated ms2 spectra to mass features
    scan_dictionary = load_scan_translator(scan_translator=scan_translator)
    for param_key in scan_dictionary.keys():
        scan_filter = scan_dictionary[param_key]["scan_filter"]
        if scan_filter == "":
            scan_filter = None
        myLCMSobj.add_associated_ms2_dda(
            spectrum_mode="centroid", ms_params_key=param_key, scan_filter=scan_filter
        )

def export_results(myLCMSobj, out_path, molecular_metadata=None, final=False):
    """Export results to hdf5 and csv as a lipid report

    Parameters
    ----------
    myLCMSobj : corems LCMS object
        LCMS object to process
    out_path : str or Path
        Path to output file
    molecular_metadata : dict
        Dict with molecular metadata
    final : bool
        Whether to export final results

    Returns
    -------
    None, exports results to hdf5 and csv as a lipid report
    """
    exporter = LipidomicsExport(out_path, myLCMSobj)
    exporter.to_hdf(overwrite=True)
    if final:
        # Do not show warnings, these are expected
        exporter.report_to_csv(molecular_metadata=molecular_metadata)
    else:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            exporter.report_to_csv()


def run_lipid_sp_ms1(file_in, out_path, params_toml, scan_translator):
    time_start = datetime.datetime.now()
    myLCMSobj = instantiate_lcms_obj(file_in)           
    set_params_on_lcms_obj(myLCMSobj, params_toml)
    check_scan_translator(myLCMSobj, scan_translator)
    add_mass_features(myLCMSobj, scan_translator)
    myLCMSobj.remove_unprocessed_data()
    #TODO KRH: add molecular search here
    export_results(myLCMSobj, out_path=out_path, final=False)
    precursor_mz_list = list(
        set(
            [
                v.mz
                for k, v in myLCMSobj.mass_features.items()
                if len(v.ms2_scan_numbers) > 0 and v.isotopologue_type is None
            ]
        )
    )
    mz_dict = {myLCMSobj.polarity: precursor_mz_list}
    return mz_dict
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

    click.echo("Starting lipidomics workflow for " + str(len(files_list)) + " files, using " +  str(cores) + " core(s)")
    
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
    # TODO KRH: Add full lipidomics workflow here
