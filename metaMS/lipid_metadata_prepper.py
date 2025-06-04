import pandas as pd
import numpy as np
import sqlite3
import re
from ms_entropy import FlashEntropySearch
from corems.molecular_id.factory.lipid_molecular_metadata import LipidMetadata
import click

def find_closest(A, target):
    """Find the index of closest value in A to each value in target.

    Parameters
    ----------
    A : :obj:`~numpy.array`
        The array to search (blueprint). A must be sorted.
    target : :obj:`~numpy.array`
        The array of values to search for. target must be sorted.

    Returns
    -------
    :obj:`~numpy.array`
        The indices of the closest values in A to each value in target.
    """
    idx = A.searchsorted(target)
    idx = np.clip(idx, 1, len(A) - 1)
    left = A[idx - 1]
    right = A[idx]
    idx -= target - left < right - target
    return idx

def spectrum_to_array(spectrum, normalize=True):
    """
    Convert MetabRef-formatted spectrum to array.

    Parameters
    ----------
    spectrum : str
        MetabRef spectrum, i.e. list of (m/z,abundance) pairs.
    normalize : bool
        Normalize the spectrum by its magnitude.

    Returns
    -------
    :obj:`~numpy.array`
        Array of shape (N, 2), with m/z in the first column and abundance in
        the second.

    """

    # Convert parenthesis-delimited string to array
    arr = np.array(
        re.findall(r"\(([^,]+),([^)]+)\)", spectrum), dtype=float
    ).reshape(-1, 2)

    # Normalize the array
    if normalize:
        arr[:, -1] = arr[:, -1] / arr[:, -1].sum()

    return arr

def _to_flashentropy(metabref_lib, normalize=True, fe_kwargs={}):
    """
    Convert metabref-formatted library to FlashEntropy library.

    Parameters
    ----------
    metabref_lib : dict
        MetabRef MS2 library in JSON format or FlashEntropy search instance (for reformatting at different MS2 separation).
    normalize : bool
        Normalize each spectrum by its magnitude.
    fe_kwargs : dict, optional
        Keyword arguments for instantiation of FlashEntropy search and building index for FlashEntropy search;
        any keys not recognized will be ignored. By default, all parameters set to defaults.

    Returns
    -------
    :obj:`~ms_entropy.FlashEntropySearch`
        MS2 library as FlashEntropy search instance.

    Raises
    ------
    ValueError
        If "min_ms2_difference_in_da" or "max_ms2_tolerance_in_da" are present in `fe_kwargs` and they are not equal.

    """
    # If "min_ms2_difference_in_da" in fe_kwargs, check that "max_ms2_tolerance_in_da" is also present and that min_ms2_difference_in_da = 2xmax_ms2_tolerance_in_da
    if (
        "min_ms2_difference_in_da" in fe_kwargs
        or "max_ms2_tolerance_in_da" in fe_kwargs
    ):
        if (
            "min_ms2_difference_in_da" not in fe_kwargs
            or "max_ms2_tolerance_in_da" not in fe_kwargs
        ):
            raise ValueError(
                "Both 'min_ms2_difference_in_da' and 'max_ms2_tolerance_in_da' must be specified."
            )
        if (
            fe_kwargs["min_ms2_difference_in_da"]
            != 2 * fe_kwargs["max_ms2_tolerance_in_da"]
        ):
            raise ValueError(
                "The values of 'min_ms2_difference_in_da' must be exactly 2x 'max_ms2_tolerance_in_da'."
            )

    # Initialize empty library
    fe_lib = []

    # Enumerate spectra
    for i, source in enumerate(metabref_lib):
        # Reorganize source dict, if necessary
        if "spectrum_data" in source.keys():
            spectrum = source["spectrum_data"]
        else:
            spectrum = source
        click.echo(spectrum.keys())
        # Rename precursor_mz key for FlashEntropy
        if "precursor_mz" not in spectrum.keys():
            spectrum["precursor_mz"] = spectrum.pop("precursor_ion")

        # Convert CoreMS spectrum to array and clean, store as `peaks`
        spectrum["peaks"] = spectrum_to_array(
            spectrum["mz"], normalize=normalize
        )

        # Cast "fragment_types" to a list (if present and not already a list)
        if "fragment_types" in spectrum.keys():
            if not isinstance(spectrum["fragment_types"], list):
                spectrum["fragment_types"] = spectrum["fragment_types"].split(",")

        # Add spectrum to library
        fe_lib.append(spectrum)

    # Initialize FlashEntropy
    fe_init_kws = [
        "max_ms2_tolerance_in_da",
        "mz_index_step",
        "low_memory",
        "path_data",
    ]
    fe_init_kws = {k: v for k, v in fe_kwargs.items() if k in fe_init_kws}
    fes = FlashEntropySearch(**fe_init_kws)

    # Build FlashEntropy index
    fe_index_kws = [
        "max_indexed_mz",
        "precursor_ions_removal_da",
        "noise_threshold",
        "min_ms2_difference_in_da",
        "max_peak_num",
    ]
    fe_index_kws = {k: v for k, v in fe_kwargs.items() if k in fe_index_kws}
    fes.build_index(fe_lib, **fe_index_kws, clean_spectra=True)

    return fes

def _dict_to_dataclass(metabref_lib, data_class):
    """
    Convert dictionary to dataclass.

    Notes
    -----
    This function will pull the attributes a dataclass and its parent class
    and convert the dictionary to a dataclass instance with the appropriate
    attributes.

    Parameters
    ----------
    data_class : :obj:`~dataclasses.dataclass`
        Dataclass to convert to.
    metabref_lib : dict
        Metabref dictionary object to convert to dataclass.

    Returns
    -------
    :obj:`~dataclasses.dataclass`
        Dataclass instance.

    """

    # Get list of expected attributes of data_class
    data_class_keys = list(data_class.__annotations__.keys())

    # Does the data_class inherit from another class, if so, get the attributes of the parent class as well
    if len(data_class.__mro__) > 2:
        parent_class_keys = list(data_class.__bases__[0].__annotations__.keys())
        data_class_keys = list(set(data_class_keys + parent_class_keys))

    # Remove keys that are not in the data_class from the input dictionary
    input_dict = {k: v for k, v in metabref_lib.items() if k in data_class_keys}

    # Add keys that are in the data class but not in the input dictionary as None
    for key in data_class_keys:
        if key not in input_dict.keys():
            input_dict[key] = None
    return data_class(**input_dict)

def get_lipid_library(
        db_location,
        mz_list,
        polarity,
        mz_tol_ppm,
        format='flashentropy',
        normalize=True,
        fe_kwargs={},
):
    """
    Get lipid library from database.

    Parameters
    ----------
    db_location : str
        Path to the database.
    mz_list : :obj:`~numpy.array`
        Array of observed m/z values.
    polarity : str
        Polarity of the MS2 spectra.
    mz_tol_ppm : float
        m/z tolerance in ppm for matching ms1 precursor m/z to observed m/z.
    format : str, optional
        Format of the library to return. Options are 'flashentropy' (default) or 'metabref'.
    normalize : bool, optional
        Normalize each spectrum by its magnitude. By default, True.
    fe_kwargs : dict, optional
        Keyword arguments for instantiation of FlashEntropy search and building index for FlashEntropy search;
        any keys not recognized will be ignored. By default, all parameters set to defaults.
    
    Returns
    -------
    :obj:`~ms_entropy.FlashEntropySearch`
        MS2 library as FlashEntropy search instance.
    :obj:`~dataclasses.dataclass`
        Lipid metadata as LipidMetadata dataclass.
    """
    # prepare the mz_list for searching against the database
    mz_list = pd.DataFrame(mz_list, columns=['mz_obs'])
    mz_list = mz_list.sort_values(by='mz_obs')
    mz_list = mz_list.reset_index(drop=True)
    mz_obs_arr = mz_list['mz_obs'].values

    # connect to the database
    conn = sqlite3.connect(db_location)

    # read in lipidMassSpectrumObject, get only id, polarity, and precursor_mz
    mz_all = pd.read_sql_query("SELECT id, polarity, precursor_mz FROM lipidMassSpectrumObject", conn)
    mz_all = mz_all.sort_values(by='precursor_mz')

    # filter by polarity and if there are any matches within mz_tol_ppm
    mz_subset = mz_all[mz_all['polarity'] == polarity].copy()
    mz_subset = mz_subset.sort_values(by='precursor_mz')
    mz_subset = mz_subset.reset_index(drop=True)
    mz_subset['closest_mz_obs'] = mz_obs_arr[
        find_closest(mz_obs_arr, mz_subset.precursor_mz.values)
    ]
    mz_subset['ppm_error'] = (mz_subset['precursor_mz'] - mz_subset['closest_mz_obs']) / mz_subset['precursor_mz'] * 1e6
    mz_subset = mz_subset[np.abs(mz_subset['ppm_error']) <= mz_tol_ppm]

    # get the full lipidMassSpectrumObject table for the filtered ms2 ids
    mz_subset_ids = mz_subset['id'].tolist()
    mz_subset_ids = tuple(mz_subset_ids)
    mz_subset_full = pd.read_sql_query(f"SELECT * FROM lipidMassSpectrumObject WHERE id IN {mz_subset_ids}", conn)

    # get the lipid tree for the filtered molecular ids
    mol_ids = mz_subset_full['molecular_data_id'].tolist()
    mol_ids = tuple(mol_ids)
    lipid_tree = pd.read_sql_query(f"SELECT * FROM lipidTree WHERE id IN {mol_ids}", conn)

    # convert molecular data to dictionary of LipidMetadata objects, with mol_id as key
    lipid_tree['id_index'] = lipid_tree['id']
    lipid_tree = lipid_tree.set_index('id_index')
    lipid_tree = lipid_tree.to_dict(orient='index')
    lipid_metadata = {
            k: _dict_to_dataclass(v, LipidMetadata)
            for k, v in lipid_tree.items()
        }

    # convert ms2 data to flashentropy library
    mz_subset_full_dict = mz_subset_full.to_dict(orient='records')
    fe_lib = _to_flashentropy(mz_subset_full_dict, normalize=normalize, fe_kwargs=fe_kwargs)

    # close the connection
    conn.close()

    return fe_lib, lipid_metadata