from dataclasses import dataclass
import toml
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor  # Changed from multiprocessing import Pool
import click
import warnings
import pandas as pd
import gc
import pickle

from corems.mass_spectra.output.export import LCMSMetabolomicsExport

from corems.molecular_id.search.database_interfaces import MSPInterface
from metaMS.lcms_functions import (
    instantiate_lcms_obj,
    set_params_on_lcms_obj,
    load_scan_translator,
    check_scan_translator,
    add_mass_features,
    molecular_formula_search,
)

# Suppress specific warning from the corems.mass_spectrum.input.massList module
warnings.filterwarnings(
    "ignore",
    message="No isotopologue matched the formula_dict: {formula_dict}",
    module="corems.mass_spectrum.input.massList"
)

@dataclass
class LCMetabolomicsWorkflowParameters:
    """
    Parameters for the LC metabolomics workflow

    Parameters
    ----------
    directory : str
        The directory where the data is stored, all files in the directory will be processed
    output_directory : str
        The directory where the output files will be stored
    corems_toml_path : str
        The path to the corems configuration file
    msp_file_path : str
        The path to the local sqlite database used for searching ms2 spectra
    scan_translator_path : str
        The path to the scan translator file, optional
    cores : int
        The number of cores to use for processing, optional

    """
    file_paths: tuple = ('data/...', 'data/...')
    output_directory: str = "output"
    corems_toml_path: str = None
    msp_file_path: str = None
    scan_translator_path: str = None
    cores: int = 1

def check_lcmetab_workflow_params(lcmetab_workflow_params):
    """Check that all parameters are valid and exist

    Parameters
    ----------
    lcmetab_workflow_params : LCMetabolomicsWorkflowParameters
        Parameters for the LC metabolomics workflow

    Returns
    -------
    None, raises errors if parameters are not valid or do not exist
    """
    # Check that corems_toml_path exists
    if not Path(lcmetab_workflow_params.corems_toml_path).exists():
        raise FileNotFoundError("Corems toml file not found, exiting workflow")
    
    # Check that scan_translator_path exists
    if not Path(lcmetab_workflow_params.scan_translator_path).exists():
        raise FileNotFoundError("Scan translator file not found, exiting workflow")
    
    # Check that output_directory exists
    if not Path(lcmetab_workflow_params.output_directory).exists():
        raise FileNotFoundError("Output directory not found, exiting workflow")
    
    # Check that file_paths exist
    for file_path in lcmetab_workflow_params.file_paths:
        if not Path(file_path).exists():
            raise FileNotFoundError(f"File path {file_path} not found, exiting workflow")
    
    # Check that all file_paths end in .raw or .mzML
    for file_path in lcmetab_workflow_params.file_paths:
        if ".raw" not in file_path and ".mzML" not in file_path:
            raise ValueError(f"File path {file_path} is not a .raw or .mzML file, exiting workflow")
    
    # Check that msp_file_path exists
    if lcmetab_workflow_params.msp_file_path is not None:
        if not Path(lcmetab_workflow_params.msp_file_path).exists():
            raise FileNotFoundError("Database location not found, exiting workflow")

def determine_polarity(file_path):
    """Determine the polarity of the LCMS file

    Parameters
    ----------
    file_path : str or Path
        Path to the LCMS file

    Returns
    -------
    polarity : str
        Polarity of the LCMS file, either "positive" or "negative"
    """
    lcms_obj = instantiate_lcms_obj(file_path, spectra="none")
    return lcms_obj.polarity if lcms_obj.polarity else "unknown"

def export_results(myLCMSobj, out_path, molecular_metadata, final=False):
    """Export results to hdf5 and csv

    Parameters
    ----------
    myLCMSobj : corems LCMS object
        LCMS object to process
    out_path : str or Path
        Path to output file
    molecular_metadata : dict, optional
        Dict with molecular metadata
    final : bool, optional
        Whether to export final results

    Returns
    -------
    None, exports results to hdf5 and csv
    """
    exporter = LCMSMetabolomicsExport(out_path, myLCMSobj)
    exporter.to_hdf(overwrite=True)
    if final:
        # Do not show warnings, these are expected
        exporter.report_to_csv(molecular_metadata=molecular_metadata)
    else:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            exporter.report_to_csv()

def run_lcmetab_ms1(file_in, params_toml, scan_translator):
    """Run signal processing and associated mass feature generation for a metabolomics LCMS file
    
    Run signal processing, get associated ms1, do ms1 molecular search, 
    and export intermediate results from an input LCMS file

    Parameters
    ----------
    file_in : str or Path
        Path to input file (raw or mzML)
    params_toml : str or Path
        Path to toml file with parameters
    scan_translator : str or Path
        Path to scan translator file

    Returns
    -------
    mz_dict : dict
        Dict with keys "positive" and "negative" and values of lists of precursor mzs
    """  

    click.echo(f"...instantiating LCMS object for {file_in}")
    myLCMSobj = instantiate_lcms_obj(file_in)
    set_params_on_lcms_obj(myLCMSobj, params_toml)
    
    # If the ms1 data are centroided, switch the peak picking method to centroided persistent homology
    # and set the noise threshold method to relative abundance
    ms1_scan_df = myLCMSobj.scan_df[myLCMSobj.scan_df.ms_level == 1]
    if all(x == "centroid" for x in ms1_scan_df.ms_format.to_list()):
        click.echo("Centroided MS1 data detected, switching peak picking method to centroided persistent homology")
        myLCMSobj.parameters.lc_ms.peak_picking_method = "centroided_persistent_homology"
        myLCMSobj.parameters.mass_spectrum[
            "ms1"
        ].mass_spectrum.noise_threshold_method = "relative_abundance"

    myLCMSobj.parameters.mass_spectrum[
        "ms1"
    ].mass_spectrum.noise_threshold_min_relative_abundance = 0.1

    check_scan_translator(myLCMSobj, scan_translator)
    add_mass_features(myLCMSobj, scan_translator)

    del ms1_scan_df
    gc.collect()
    
    myLCMSobj.remove_unprocessed_data()
    molecular_formula_search(myLCMSobj)

    return myLCMSobj

def prepare_metadata(msp_file_path, generate_lr_metadata=True, polarity=None):
    """Prepare metadata for ms2 spectral search

    Parameters
    ----------
    msp_file_path : str
        Path to sqlite database
    generate_lr_metadata : bool, optional
        Whether to generate low resolution metadata, default is True
    polarity : str, optional
        Polarity to prepare metadata for, can be "positive", "negative", or None (which will prepare for both polarities)

    Returns
    -------
    None, but saves the metadata to a file named "metadata.pkl" in the current directory
        
    Notes
    -------
    Also writes out files for the flash entropy search databases and molecular metadata
    """
    # Check if polarity is valid and if none, set to both polarities
    if polarity not in ["positive", "negative", None]:
        raise ValueError("Polarity must be 'positive', 'negative', or None")
    if polarity is None:
        polarity = "both"

    print("Parsing MSP file...")
    my_msp = MSPInterface(file_path=msp_file_path)
    print("Parsing MSP file complete.")
    metadata = {
        "fe": {"positive": None, "negative": None},
        "molecular_metadata": {},
        "fe_lr": {"positive": None, "negative": None}
    }

    # Prepare positive polarity metadata
    if polarity in ["positive", "both"]:
        # High resolution
        msp_positive, metabolite_metadata_positive = (
            my_msp.get_metabolomics_spectra_library(
                polarity="positive",
                format="flashentropy",
                normalize=True,
                fe_kwargs={
                    "normalize_intensity": True,
                    "min_ms2_difference_in_da": 0.02,  # for cleaning spectra
                    "max_ms2_tolerance_in_da": 0.01,  # for setting search space
                    "max_indexed_mz": 3000,
                    "precursor_ions_removal_da": None,
                    "noise_threshold": 0,
                },
            )
        )
        metadata["fe"]["positive"] = msp_positive
        metadata["molecular_metadata"] = metabolite_metadata_positive

    # Prepare negative polarity metadata
    if polarity in ["negative", "both"]:
        msp_negative, metabolite_metadata_negative = (
            my_msp.get_metabolomics_spectra_library(
                polarity="negative",
                format="flashentropy",
                normalize=True,
                fe_kwargs={
                    "normalize_intensity": True,
                    "min_ms2_difference_in_da": 0.02,  # for cleaning spectra
                    "max_ms2_tolerance_in_da": 0.01,  # for setting search space
                    "max_indexed_mz": 3000,
                    "precursor_ions_removal_da": None,
                    "noise_threshold": 0,
                },
            )
        )
        metadata["fe"]["negative"] = msp_negative
        metadata["molecular_metadata"].update(metabolite_metadata_negative)

    if generate_lr_metadata:
        if polarity in ["positive", "both"]:
            # Low resolution
            msp_positive, metabolite_metadata_positive = (
                my_msp.get_metabolomics_spectra_library(
                    polarity="positive",
                    format="flashentropy",
                    normalize=True,
                    fe_kwargs={
                        "normalize_intensity": True,
                        "min_ms2_difference_in_da": 0.4,  # for cleaning spectra
                        "max_ms2_tolerance_in_da": 0.2,  # for setting search space
                        "max_indexed_mz": 3000,
                        "precursor_ions_removal_da": None,
                        "noise_threshold": 0,
                    },
                )
            )
            metadata["fe_lr"]["positive"] = msp_positive

        if polarity in ["negative", "both"]:
            msp_negative, metabolite_metadata_negative = (
                my_msp.get_metabolomics_spectra_library(
                    polarity="negative",
                    format="flashentropy",
                    normalize=True,
                    fe_kwargs={
                        "normalize_intensity": True,
                        "min_ms2_difference_in_da": 0.4,  # for cleaning spectra
                        "max_ms2_tolerance_in_da": 0.2,  # for setting search space
                        "max_indexed_mz": 3000,
                        "precursor_ions_removal_da": None,
                        "noise_threshold": 0,
                    },
                )
            )
            metadata["fe_lr"]["negative"] = msp_negative

    # Save this as a pkl in the output directory
    output_path = Path("metadata.pkl")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "wb") as f:
        pickle.dump(metadata, f) 

def process_ms2(myLCMSobj, metadata, scan_translator):
    """Process ms2 spectra and perform molecular search

    Parameters
    ----------
    myLCMSobj : corems LCMS object
        LCMS object to process
    metadata : dict
        Dict with keys "mzs", "fe", and "molecular_metadata" with values of dicts of precursor mzs (negative and positive), flash entropy search databases (negative and positive), and molecular metadata, respectively

    Returns
    -------
    molecular_metadata : dict
        Dict with keys "positive" and "negative" containing the molecular metadata for each polarity
    """
    click.echo("...processing ms2 spectra")

    if metadata is None:
        # import pickled version (me)
        metadata_path = Path("metadata.pkl")
        if not metadata_path.exists():
            raise FileNotFoundError("Metadata file not found, please prepare metadata first")
        with open(metadata_path, "rb") as f:
            metadata = pickle.load(f)

    # Perform molecular search on ms2 spectra
    # Grab fe from metatdata associated with polarity (this is inherently high resolution as its from a in-silico high res library)
    fe_search = metadata["fe"][myLCMSobj.polarity]

    scan_dictionary = load_scan_translator(scan_translator)
    ms2_scan_df = myLCMSobj.scan_df[myLCMSobj.scan_df.ms_level == 2]

    # Process high resolution MS2 scans
    # Collect all high resolution MS2 scans using the scan translator
    ms2_scans_oi_hr = []
    for param_key in scan_dictionary.keys():
        if scan_dictionary[param_key]["resolution"] == "high":
            scan_filter = scan_dictionary[param_key]["scan_filter"]
            if scan_filter is not None:
                ms2_scan_df_hr = ms2_scan_df[
                    ms2_scan_df.scan_text.str.contains(scan_filter)
                ]
            else:
                ms2_scan_df_hr = ms2_scan_df
            ms2_scans_oi_hr_i = [
                x for x in ms2_scan_df_hr.scan.tolist() if x in myLCMSobj._ms.keys()
            ]
            ms2_scans_oi_hr.extend(ms2_scans_oi_hr_i)
    # Perform search on high res scans
    if len(ms2_scans_oi_hr) > 0:
        myLCMSobj.fe_search(
            scan_list=ms2_scans_oi_hr, fe_lib=fe_search, peak_sep_da=0.01
        )

    # Process low resolution MS2 scans
    # Collect all low resolution MS2 scans using the scan translator
    ms2_scans_oi_lr = []
    for param_key in scan_dictionary.keys():
        if scan_dictionary[param_key]["resolution"] == "low":
            scan_filter = scan_dictionary[param_key]["scan_filter"]
            if scan_filter is not None:
                ms2_scan_df_lr = ms2_scan_df[
                    ms2_scan_df.scan_text.str.contains(scan_filter)
                ]
            else:
                ms2_scan_df_lr = ms2_scan_df
            ms2_scans_oi_lri = [
                x for x in ms2_scan_df_lr.scan.tolist() if x in myLCMSobj._ms.keys()
            ]
            ms2_scans_oi_lr.extend(ms2_scans_oi_lri)
    # Perform search on low res scans
    if len(ms2_scans_oi_lr) > 0:
        fe_search_lr = metadata["fe_lr"][myLCMSobj.polarity]
        myLCMSobj.fe_search(
            scan_list=ms2_scans_oi_lr, fe_lib=fe_search_lr, peak_sep_da=0.3
        )
    
    return metadata["molecular_metadata"]

def process_complete_workflow(args):
    """Process a single file through the complete workflow"""
    try:
        file_in, output_path, params_toml, scan_translator, metadata = args
        
        # MS1 processing
        click.echo(f"Starting complete processing for {file_in}")
        lcms_obj = run_lcmetab_ms1(
            file_in=file_in,
            params_toml=params_toml,
            scan_translator=scan_translator,
        )
        
        # MS2 processing and export
        mol_metadata = process_ms2(lcms_obj, metadata, scan_translator)
        export_results(lcms_obj, str(output_path), mol_metadata, final=True)

        return f"Completed: {output_path}"
    except Exception as e:
        click.echo(f"Error processing {file_in}: {str(e)}")
        raise

def run_lcms_metabolomics_workflow(
    lcmsmetab_workflow_parameters_file=None,
    file_paths=None,
    output_directory=None,
    corems_toml_path=None,
    msp_file_path=None,
    scan_translator_path=None,
    cores=None,
):
    """Run the LC metabolomics workflow
    
    Parameters
    ----------
    lcmsmetab_workflow_parameters_file : str or Path
        Path to toml file with parameters
    file_paths : str
        Comma-separated string of file paths
    output_directory : str
        Path to output directory
    corems_toml_path : str
        Path to corems toml file
    msp_file_path : str
        The path to the local sqlite database used for searching ms2 spectra
    scan_translator_path : str
        Path to scan translator file
    cores : int
        Number of cores to use for processing

    Returns
    -------
    None, runs the LC metabolomics workflow        
    """

    if lcmsmetab_workflow_parameters_file is not None:
        # Set the parameters from the toml file
        with open(lcmsmetab_workflow_parameters_file, "r") as infile:
            lcmetab_workflow_params = LCMetabolomicsWorkflowParameters(**toml.load(infile))
    else:
        click.echo("Setting workflow params")
        lcmetab_workflow_params = LCMetabolomicsWorkflowParameters(
            file_paths= file_paths.split(","),
            output_directory=output_directory,
            msp_file_path=msp_file_path,
            scan_translator_path=scan_translator_path,
            corems_toml_path=corems_toml_path,
            cores=cores,
        )
        click.echo("file paths are" + file_paths)
    
    # Make output dir
    out_dir = Path(lcmetab_workflow_params.output_directory)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Check that all parameters are valid and exist
    check_lcmetab_workflow_params(lcmetab_workflow_params)

    # Organize input and output paths and determine polarities
    file_paths = [Path(file_path) for file_path in lcmetab_workflow_params.file_paths]
    files_list = list(file_paths)
    out_paths_list = [out_dir / f.stem for f in files_list]
    polarities = [determine_polarity(file_path) for file_path in file_paths]
    click.echo(f"Detected polarities: {set(polarities)}")

    # Set the workflow parameters
    cores = lcmetab_workflow_params.cores
    params_toml = lcmetab_workflow_params.corems_toml_path
    scan_translator = lcmetab_workflow_params.scan_translator_path

    # Determine if we should prepare low resolution metadata:
    # Check the scan translator, if there are only high resolution scans, then do not make low resolution metadata
    scan_trans_dict = load_scan_translator(scan_translator)
    if all(x["resolution"] == "high" for x in scan_trans_dict.values()):
        generate_lr_metadata = False
    else:
        click.echo("Low resolution scans found, generating low resolution metadata")
        generate_lr_metadata = True

    click.echo("Starting LC metabolomics workflow for " + str(len(files_list)) + " file(s), using " +  str(cores) + " core(s)")

    # RUN THE POSITIVE SAMPLES ================
    files_list_positive = [
        file for file, polarity in zip(files_list, polarities) if polarity == "positive"
    ]
    out_paths_list_positive = [
        out_path for out_path, polarity in zip(out_paths_list, polarities) if polarity == "positive"
    ]
    if len(files_list_positive) > 0:
        click.echo(f"Processing {len(files_list_positive)} positive polarity samples")
        
        # Prepare metadata for searching
        click.echo("Preparing metadata for ms2 spectral search for positive samples")
        prepare_metadata(lcmetab_workflow_params.msp_file_path, generate_lr_metadata=generate_lr_metadata, polarity="positive")
        click.echo("Metadata preparation complete for positive samples")
        
        # Run signal processing, get associated ms1, add associated ms2, do ms1 molecular search, and export intermediate results
        # for positive polarity samples
        if cores == 1 or len(files_list_positive) == 1:
            for file_in, output_path in zip(files_list_positive, out_paths_list_positive):
                args = (file_in, output_path, params_toml, scan_translator, None)
                process_complete_workflow(args)
        elif cores > 1:
            with ThreadPoolExecutor(max_workers=cores) as executor:
                args = [
                    (str(file_in), str(output_path), params_toml, scan_translator, None)
                    for file_in, output_path in zip(files_list_positive, out_paths_list_positive)
                ]
                list(executor.map(lambda arg: process_complete_workflow(arg), args))
        gc.collect()
    
    # RUN THE NEGATIVE SAMPLES ================
    files_list_negative = [
        file for file, polarity in zip(files_list, polarities) if polarity == "negative"
    ]
    out_paths_list_negative = [
        out_path for out_path, polarity in zip(out_paths_list, polarities) if polarity == "negative"
    ]
    if len(files_list_negative) > 0:
        click.echo(f"Processing {len(files_list_negative)} negative polarity samples")
        click.echo("Preparing metadata for ms2 spectral search for negative samples")
        prepare_metadata(lcmetab_workflow_params.msp_file_path, generate_lr_metadata=generate_lr_metadata, polarity="negative")
        click.echo("Metadata preparation complete for negative samples")

        # Run signal processing, get associated ms1, add associated ms2, do ms1 molecular search, and export intermediate results
        # for negative polarity samples
        if cores == 1 or len(files_list_negative) == 1:
            for file_in, output_path in zip(files_list_negative, out_paths_list_negative):
                args = (file_in, output_path, params_toml, scan_translator, None)
                process_complete_workflow(args)
        elif cores > 1:
            with ThreadPoolExecutor(max_workers=cores) as executor:
                args = [
                    (str(file_in), str(output_path), params_toml, scan_translator, None)
                    for file_in, output_path in zip(files_list_negative, out_paths_list_negative)
                ]
                list(executor.map(lambda arg: process_complete_workflow(arg), args))
        gc.collect()

    click.echo("LC metabolomics workflow complete")