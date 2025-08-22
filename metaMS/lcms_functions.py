from dataclasses import dataclass
import click
import toml
from pathlib import Path
import warnings
import pandas as pd

from corems.mass_spectra.input.mzml import MZMLSpectraParser
from corems.molecular_id.search.molecularFormulaSearch import SearchMolecularFormulasLC
from corems.encapsulation.input.parameter_from_json import (
    load_and_set_toml_parameters_lcms,
)

def instantiate_lcms_obj(file_in, spectra="ms1"):
    """Instantiate a corems LCMS object from a binary file.  Pull in ms1 spectra into dataframe (without storing as MassSpectrum objects to save memory)

    Parameters
    ----------
    file_in : str or Path
        Path to binary file
    spectra : str, optional
        Type of spectra to pull in, default is "ms1". Other options are "ms2" or "none".

    Returns
    -------
    myLCMSobj : corems LCMS object
        LCMS object with unprocessed ms1 spectra included as an attribute
    """
    # Instantiate parser based on binary file type
    if ".raw" in str(file_in):
        from corems.mass_spectra.input.rawFileReader import ImportMassSpectraThermoMSFileReader
        parser = ImportMassSpectraThermoMSFileReader(file_in)

    if ".mzML" in str(file_in):
        parser = MZMLSpectraParser(file_in)

    # Instantiate lc-ms data object using parser and pull in ms1 spectra into dataframe (without storing as MassSpectrum objects to save memory)
    myLCMSobj = parser.get_lcms_obj(spectra=spectra)

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
    scan_dict : dict, optional
        Dict with keys as parameter keys and values as lists of scans.
        Default is None, which will use the default scan translator
        of "{"ms2": {"scan_filter": "", "resolution": "high"}}"
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
    """Check if scan translator is provided and that it maps correctly to scans and parameters
    
    Parameters
    ----------
    myLCMSobj : corems LCMS object
        LCMS object to process
    scan_translator : str or Path
        Path to scan translator yaml file
    
    Returns
    -------
    None, raises errors if scan translator does not map correctly to scans and parameters
    """
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
    integration of mass features, annotation of C13 mass features, deconvolution of ms1 mass features,
    adding of peak shape metrics of mass features and adding associated ms2 spectra to mass features for
    DDA data to myLCMSobj.

    Parameters
    ----------
    myLCMSobj : corems LCMS object
        LCMS object to process
    scan_translator : str or Path
        Path to scan translator yaml file

    Returns
    -------
    None, but populates the mass_features attribute of myLCMSobj
    """
    # Process ms1 spectra
    click.echo("...finding mass features")
    myLCMSobj.find_mass_features()

    ms1_scan_df = myLCMSobj.scan_df[myLCMSobj.scan_df.ms_level == 1]
    
    click.echo("...adding ms1 spectra")
    if all(x == "profile" for x in ms1_scan_df.ms_format.to_list()):
        myLCMSobj.add_associated_ms1(
            auto_process=True, use_parser=False, spectrum_mode="profile"
        )
    elif all(x == "centroid" for x in ms1_scan_df.ms_format.to_list()):
        myLCMSobj.add_associated_ms1(
            auto_process=True, use_parser=True, spectrum_mode="centroid"
        )

    click.echo("...integrating mass features")
    myLCMSobj.integrate_mass_features(drop_if_fail=True)
    # Count and report how many mass features are left after integration
    print("Number of mass features after integration: ", len(myLCMSobj.mass_features))
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

def molecular_formula_search(myLCMSobj):
    """Perform molecular search on mass features within the LCMS object

    Parameters
    ----------
    myLCMSobj : corems LCMS object
        LCMS object to process

    Returns
    -------
    None, processes the LCMS object
    """
    click.echo("...performing molecular search")
    # Perform a molecular search on all of the mass features
    mol_form_search = SearchMolecularFormulasLC(myLCMSobj)
    mol_form_search.run_mass_feature_search()
    print("Finished molecular search")