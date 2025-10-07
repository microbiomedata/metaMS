from dataclasses import dataclass
import toml
from pathlib import Path
from multiprocessing import Pool
import click
import warnings
import pandas as pd
import gc

from corems.mass_spectra.input.corems_hdf5 import ReadCoreMSHDFMassSpectra
from corems.mass_spectra.output.export import LipidomicsExport


from metaMS.lipid_metadata_prepper import get_lipid_library, _to_flashentropy
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
    db_location : str
        The path to the local sqlite database used for searching lipid ms2 spectra
    scan_translator_path : str
        The path to the scan translator file, optional
    cores : int
        The number of cores to use for processing, optional

    """
    file_paths: tuple = ('data/...', 'data/...')
    output_directory: str = "output"
    corems_toml_path: str = None
    db_location: str = None
    scan_translator_path: str = None
    cores: int = 1

def check_lipidomics_workflow_params(lipid_workflow_params):
    """Check that all parameters are valid and exist

    Parameters
    ----------
    lipid_workflow_params : LipidomicsWorkflowParameters
        Parameters for the lipidomics workflow

    Returns
    -------
    None, raises errors if parameters are not valid or do not exist
    """
    # Check that corems_toml_path exists
    if not Path(lipid_workflow_params.corems_toml_path).exists():
        raise FileNotFoundError("Corems toml file not found, exiting workflow")
    
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
    
    # Check that db_location exists
    if lipid_workflow_params.db_location is not None:
        if not Path(lipid_workflow_params.db_location).exists():
            raise FileNotFoundError("Database location not found, exiting workflow")

def export_results(myLCMSobj, out_path, molecular_metadata=None, final=False):
    """Export results to hdf5 and csv as a lipid report

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
    None, exports results to hdf5 and csv as a lipid report
    """
    exporter = LipidomicsExport(out_path, myLCMSobj)
    exporter.to_hdf(overwrite=True)
    if final:
        exporter.report_to_csv(molecular_metadata=molecular_metadata)

def run_lipid_sp_ms1(file_in, out_path, params_toml, scan_translator):
    """Run signal processing and associated mass feature generation for a lipidomics LCMS file
    
    Run signal processing, get associated ms1, add associated ms2, do ms1 molecular search, 
    and export intermediate results from an input LCMS file

    Parameters
    ----------
    file_in : str or Path
        Path to input file (raw or mzML)
    out_path : str or Path
        Path to output file
    params_toml : str or Path
        Path to toml file with parameters
    scan_translator : str or Path
        Path to scan translator file

    Returns
    -------
    mz_dict : dict
        Dict with keys "positive" and "negative" and values of lists of precursor mzs
    """  
    myLCMSobj = instantiate_lcms_obj(file_in)   
    set_params_on_lcms_obj(myLCMSobj, params_toml)
    check_scan_translator(myLCMSobj, scan_translator)
    add_mass_features(myLCMSobj, scan_translator)
    myLCMSobj.remove_unprocessed_data()
    # Finally, perform molecular formula search on all ms1 spectra associated with mass features
    molecular_formula_search(myLCMSobj)
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
    mz_dict = {myLCMSobj.polarity: precursor_mz_list.copy()}
    del myLCMSobj
    gc.collect()

    return mz_dict

def prep_metadata(mz_dicts, out_dir, db_location):
    """Prepare metadata for ms2 spectral search

    Parameters
    ----------
    mz_dicts : list of dicts
        List of dicts with keys "positive" and "negative" and values of lists of precursor mzs
    out_dir : Path
        Path to output directory
    db_location : str
        Path to lipid database

    Returns
    -------
    metadata : dict
        Dict with keys "mzs", "fe", and "molecular_metadata" with values of dicts of precursor mzs (negative and positive), flash entropy search databases (negative and positive), and molecular metadata, respectively

    Notes
    -------
    Also writes out files for the flash entropy search databases and molecular metadata
    """
    metadata = {
        "mzs": {"positive": None, "negative": None},
        "fe": {"positive": None, "negative": None},
        "molecular_metadata": {},
    }
    for d in mz_dicts:
        metadata["mzs"].update(d)

    print("Preparing negative lipid library")

    if metadata["mzs"]["negative"] is not None:
        metabref_negative, lipidmetadata_negative = get_lipid_library(
            db_location=db_location,
            mz_list=metadata["mzs"]["negative"],
            polarity="negative",
            mz_tol_ppm=5,
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
        metadata["fe"]["negative"] = metabref_negative
        metadata["molecular_metadata"].update(lipidmetadata_negative)
        fe_negative_df = pd.DataFrame.from_dict(
            {k: v for k, v in enumerate(metadata["fe"]["negative"])}, orient="index"
        )
        fe_negative_df.to_csv(out_dir / "ms2_db_negative.csv")
    
    print("Preparing positive lipid library")
    if metadata["mzs"]["positive"] is not None:
        metabref_positive, lipidmetadata_positive = get_lipid_library(
            db_location=db_location,
            mz_list=metadata["mzs"]["positive"],
            polarity="positive",
            mz_tol_ppm=5,
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
        metadata["fe"]["positive"] = metabref_positive
        metadata["molecular_metadata"].update(lipidmetadata_positive)
        fe_positive_df = pd.DataFrame.from_dict(
            {k: v for k, v in enumerate(metadata["fe"]["positive"])}, orient="index"
        )
        fe_positive_df.to_csv(out_dir / "ms2_db_positive.csv")

    mol_metadata_df = pd.concat(
        [
            pd.DataFrame.from_dict(v.__dict__, orient="index").transpose()
            for k, v in metadata["molecular_metadata"].items()
        ],
        ignore_index=True,
    )
    mol_metadata_df.to_csv(out_dir / "molecular_metadata.csv")

    return metadata

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
    None, processes the LCMS object
    """
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
        # Recast the flashentropy search database to low resolution
        fe_search_lr = _to_flashentropy(
            metabref_lib=fe_search,
            normalize=True,
            fe_kwargs={
                "normalize_intensity": True,
                "min_ms2_difference_in_da": 0.4,
                "max_ms2_tolerance_in_da": 0.2,
                "max_indexed_mz": 3000,
                "precursor_ions_removal_da": None,
                "noise_threshold": 0,
            },
        )
        myLCMSobj.fe_search(
            scan_list=ms2_scans_oi_lr, fe_lib=fe_search_lr, peak_sep_da=0.3
        )

def run_lipid_ms2(out_path, metadata, scan_translator=None):
    """Run ms2 spectral search and export final results

    Parameters
    ----------
    out_path : str or Path
        Path to output file
    metadata : dict
        Dict with keys "mzs", "fe", and "molecular_metadata" with values of dicts of precursor mzs (negative and positive), flash entropy search databases (negative and positive), and molecular metadata, respectively

    Returns
    -------
    None, runs ms2 spectral search and exports final results
    """
    # Read in the intermediate results
    out_path_hdf5 = str(out_path) + ".corems/" + out_path.stem + ".hdf5"
    # Catch known UserWarning from corems and ignore it
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        parser = ReadCoreMSHDFMassSpectra(out_path_hdf5)
        myLCMSobj = parser.get_lcms_obj(load_raw=False)

    # Process ms2 spectra, perform spectral search, and export final results
    process_ms2(myLCMSobj, metadata, scan_translator=scan_translator)
    export_results(myLCMSobj, str(out_path), metadata["molecular_metadata"], final=True)

def run_lcms_lipidomics_workflow(
    lipidomics_workflow_paramaters_file=None,
    file_paths=None,
    output_directory=None,
    corems_toml_path=None,
    db_location=None,
    scan_translator_path=None,
    cores=None,
):
    """Run the lipidomics workflow
    
    Parameters
    ----------
    lipidomics_workflow_paramaters_file : str or Path
        Path to toml file with parameters
    file_paths : str
        Comma-separated string of file paths
    output_directory : str
        Path to output directory
    corems_toml_path : str
        Path to corems toml file
    db_location : str
        Path to lipid database
    scan_translator_path : str
        Path to scan translator file
    cores : int
        Number of cores to use for processing

    Returns
    -------
    None, runs the lipidomics workflow        
    """

    if lipidomics_workflow_paramaters_file is not None:
        # Set the parameters from the toml file
        with open(lipidomics_workflow_paramaters_file, "r") as infile:
            lipid_workflow_params = LipidomicsWorkflowParameters(**toml.load(infile))
    else:
        lipid_workflow_params = LipidomicsWorkflowParameters(
            file_paths= file_paths.split(","),
            output_directory=output_directory,
            db_location=db_location,
            scan_translator_path=scan_translator_path,
            corems_toml_path=corems_toml_path,
            cores=cores,
        )
    
    # Make output dir
    out_dir = Path(lipid_workflow_params.output_directory)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Check that all parameters are valid and exist
    check_lipidomics_workflow_params(lipid_workflow_params)

    # Organize input and output paths
    file_paths = [Path(file_path) for file_path in lipid_workflow_params.file_paths]
    files_list = list(file_paths)
    out_paths_list = [out_dir / f.stem for f in files_list]
    
    # Set the workflow parameters
    cores = lipid_workflow_params.cores
    params_toml = lipid_workflow_params.corems_toml_path
    scan_translator = lipid_workflow_params.scan_translator_path
    # check if any files are raw - they will not be able to run on multiprocesses - they need threading. 
    cores = 1 if any(".raw" in file.name for file in files_list) else cores
    
    click.echo("Starting lipidomics workflow for " + str(len(files_list)) + " file(s), using " +  str(cores) + " core(s)")
    
    # Run signal processing, get associated ms1, add associated ms2, do ms1 molecular search, and export intermediate results
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
        click.echo("Entering multiple cores if condition....")
        click.echo("Using ThreadPoolExecutor...")
        with Pool(cores) as pool:
            args = [
                (
                    str(file_in),
                    str(file_out),
                    params_toml,
                    scan_translator,
                )
                for file_in, file_out in zip(files_list, out_paths_list)
            ]
            mz_dicts = pool.starmap(run_lipid_sp_ms1, args)
            click.echo("Out with executor...")

    # Prepare metadata for searching
    click.echo("Preparing metadata for ms2 spectral search")
    metadata = prep_metadata(mz_dicts, out_dir, lipid_workflow_params.db_location)
    del mz_dicts
    
    # Run ms2 spectral search and export final results
    click.echo("Starting ms2 spectral search and exporting final results")
    if cores == 1 or len(files_list) == 1:
        for file_out in out_paths_list:
            run_lipid_ms2(
                file_out, metadata, scan_translator=scan_translator
            )
    elif cores > 1:
        with Pool(cores) as pool:
            args = [(file_out, metadata, scan_translator) for file_out in out_paths_list]
            pool.starmap(run_lipid_ms2, args)

    click.echo("Lipidomics workflow complete")
