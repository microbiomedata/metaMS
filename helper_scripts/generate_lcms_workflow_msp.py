"""
This script generates an msp database of MS2 spectra to be used with the LCMS workflow.

Note that rdkit is required to run this script, but is not required to run the workflow and therefore not included in the requirements.txt file.

Note that this is not intended for external use, but is included in the repository for completeness.
Source databases were downloaded from here: https://gnps-external.ucsd.edu/gnpslibrary and were loaded into the minio prior to running.
To reproduce this, you will need to download the databases from GNPS and load them into a new minio location.
"""

import os

import pandas as pd
from corems.mass_spectra.output.export import LipidomicsExport, ion_type_dict
from corems.molecular_formula.factory.MolecularFormulaFactory import MolecularFormula
from minio import Minio
from rdkit import Chem
from rdkit.Chem import rdMolDescriptors

from helper_scripts.parse_msp import (
    load_lookups_from_minio,
    load_msp_files_from_minio,
    load_refmet,
    write_to_msp,
)

pd.options.display.float_format = "{:.6f}".format

# Set location of msp dbs (holds .msp files to load and curate, assuming they are in the same subfolder in
# the metabolomics minio bucket).  This assumes the lookups are in a subfolder called "lookups".
gnps_msp_dir = "databases/20250407_gnps_databases/"
output_file = "data/databases/20250407_gnps_curated.msp"

# ==================================================
# STEP 1: Read in the data from minio and add unique spectra ID column
# ==================================================

# Start up a minio client, note the access key and secret key are set in the environment variables
minio_client = Minio(
    "admin.nmdcdemo.emsl.pnl.gov",
    access_key=os.environ["MINIO_ACCESS_KEY"],
    secret_key=os.environ["MINIO_SECRET_KEY"],
    secure=True,
)
all_data = load_msp_files_from_minio(
    minio_client, bucket_name="metabolomics", prefix=gnps_msp_dir
)
og_spectra_count = all_data.shape[0]
print(f"Found {all_data['file_name'].nunique()} unique GNPS databases to compile")

# Pull out the spectra_id and check for duplicates
all_data["gnps_spectra_id"] = all_data["comment"].str.extract(r"DB#=(.+);")[0]
all_data = all_data[
    ["gnps_spectra_id"] + [col for col in all_data.columns if col != "gnps_spectra_id"]
]
assert not all_data["gnps_spectra_id"].duplicated().any(), (
    "Duplicate rows found in gnps_spectra_id"
)

# ==================================================
# STEP 2: Standardize the ionmode column and check results
# ==================================================
ionmode_mapping = {
    "positive": "positive",
    "positive-20ev": "positive",
    "negative": "negative",
}
all_data["ionmode"] = all_data["ionmode"].str.lower().map(ionmode_mapping)
assert all_data["ionmode"].isin(["positive", "negative"]).all(), (
    "Ionmode standardization failed"
)

# ==================================================
# STEP 3: Standardize inchi, smiles, molecular_formula columns using pubchem and rdkit
# ==================================================

# Remove rows with missing or empty InChIKey values
all_data = all_data[all_data["inchikey"].notna() & (all_data["inchikey"] != "")]
assert not all_data["inchikey"].isnull().any(), "Missing InChIKey values found"

# Create a DataFrame with unique InChIKeys for preparing lookups
inchikey_df = all_data[["inchikey"]].drop_duplicates(subset=["inchikey"])
# inchikey_df.to_csv(os.path.join(lookup_dir, "unique_inchikeys.csv"), index=False)
print(f"Found {inchikey_df.shape[0]} unique InChIKeys")

# Read in lookups and join to all_data
## Note that these lookups were downloaded on 2025-04-07 using the pubchem ID exchange at https://pubchem.ncbi.nlm.nih.gov/idexchange/idexchange.cgi, using the
## inchikeys from the unique_inchikeys.csv file
lookups = load_lookups_from_minio(
    minio_client, bucket_name="metabolomics", prefix=gnps_msp_dir + "lookups/"
)
for k, v in lookups.items():
    inchikey_df = inchikey_df.merge(v, on="inchikey", how="left")

# Drop rows with missing inchi values, pubchem_id values, or smiles values
inchikey_df = inchikey_df[inchikey_df["inchi"].notna() & inchikey_df["cid"].notna()]


# Get smiles from inchi using rdkit
def inchi_to_smiles(inchi: str) -> str:
    mol = Chem.MolFromInchi(inchi)
    if mol is None:
        raise ValueError(f"Invalid InChI string: {inchi}")
    smiles = Chem.MolToSmiles(mol)
    return smiles


inchikey_df["smiles"] = inchikey_df["inchi"].apply(inchi_to_smiles)


# Get molecular formula from inchi using rdkit
def inchi_to_molecular_formula(inchi: str) -> str:
    """Convert an InChI string to its molecular formula."""
    mol = Chem.MolFromInchi(inchi)
    if mol is None:
        raise ValueError(f"Invalid InChI string: {inchi}")
    formula = rdMolDescriptors.CalcMolFormula(mol)
    return formula


# Apply the function to the 'smiles' column and create a new column 'molecular_formula'
inchikey_df["molecular_formula"] = inchikey_df["inchi"].apply(
    inchi_to_molecular_formula
)

# Clean up the inchikey_df, group by inchikey, and return first value for inchi, smiles, molecular_formula
inchikey_df = inchikey_df.groupby("inchikey").first().reset_index()

# ==================================================
# STEP 4: Standardize name of the compound using RefMet
# ==================================================

# read in refmet and join to inchikey_df to get refmet_name, refmet_id, kegg_id, chebi_id
refmet_lookup = load_refmet()
inchikey_df = inchikey_df.merge(refmet_lookup, on="inchikey", how="left")

# ==================================================
# STEP 5: Add the precursor type and standardize it
# ==================================================

# Get the unique precursortype and ionmode combinations for data with inchikeys recognized by pubchem (i.e. have a molecular formula in inchikey_df)s
inchi_precursor = all_data[["inchikey", "ionmode", "precursortype"]].drop_duplicates()
inchi_precursor = inchi_precursor.merge(inchikey_df, on="inchikey", how="left")
inchi_precursor = inchi_precursor[inchi_precursor["molecular_formula"].notna()]
print(
    f"Found {inchi_precursor.shape[0]} unique molecular formula x precursortype combinations with valid InChIKeys"
)

# Standardization dictionary - key is the original value, value is the standardized value
# Note that the values in the dictionary are the same as the values in the ion_type_dict in corems
precursor_standardization = {
    "M+H": "[M+H]+",
    "M-e": "[M+H]+",
    "[M+H]": "[M+H]+",
    "M-H": "[M-H]-",
    "[M-H]": "[M-H]-",
    "M+Na": "[M+Na]+",
    "[M+Na]": "[M+Na]+",
    "M+K": "[M+K]+",
    "M+NH4": "[M+NH4]+",
    "[M+NH4]": "[M+NH4]+",
    "M-H2O+H": "[M+H-H2O]+",
    "[M-H2O+H]+": "[M+H-H2O]+",
    "M+H-H2O": "[M+H-H2O]+",
    "[M-H+2Na]+": "[M+2Na-H]+",
    "M+FA-H": "[M+HCOO]-",
    "[M-H+HCOOH]": "[M+HCOO]-",
    "M+formate": "[M+HCOO]-",
    "M+acetate": "[M+CH3COO]-",
    "[M+H+CH3OH]": "[M+CH3COO]-",
    "M+Cl": "[M+Cl]-",
    "M-H+2Na": "[M+2Na-H]+",
    "M+K-2H": "[M+K-2H]-",
}

# Change the precursortype values to the standardized values (only if they are in the mapping)
inchi_precursor["precursortype_fixed"] = inchi_precursor["precursortype"].replace(
    precursor_standardization
)
# Add flag if precursortype is in ion_type_dict.keys()
inchi_precursor["precursortype_flag"] = inchi_precursor["precursortype_fixed"].isin(
    ion_type_dict.keys()
)
inchi_precursor_summary = (
    inchi_precursor[["precursortype", "ionmode", "precursortype_flag"]]
    .groupby(["precursortype", "ionmode", "precursortype_flag"])
    .size()
    .reset_index(name="count")
)
# Print out the % of unique unique molecular formula x precursortype combinations that have precursortype_flag == True
print(
    f"Able to calculate {inchi_precursor[inchi_precursor['precursortype_flag']].shape[0] / inchi_precursor.shape[0]} precursors of molecular formula"
)
# TODO: Fix remaining precursors and deal with multiply charged species (needs to extend the ion_type_dict in corems to do this)

# ==================================================
# STEP 6: Calculate m/z based on molecular formula and the precursortype
# ==================================================
inchi_precursor = inchi_precursor[inchi_precursor["precursortype_flag"]]
calculated_mz = []
for row in inchi_precursor.itertuples():
    precursor_type = row.precursortype_fixed
    molecular_formula = row.molecular_formula
    # make ionmode 1 or -1 based on row.polarity
    if row.ionmode == "positive":
        ion_mode = 1
    else:
        ion_mode = -1
    # Calculate the precursor m/z from the molecular formula and the ion type
    try:
        ion_formula = LipidomicsExport.get_ion_formula(
            molecular_formula, precursor_type
        )
        mol = MolecularFormula(
            molecular_formula=ion_formula, ion_type="RADICAL", ion_charge=ion_mode
        )
        calculated_mz.append(mol.mz_calc)
    except:
        calculated_mz.append(None)
inchi_precursor["calculated_precursor_mz"] = calculated_mz
inchi_precursor = inchi_precursor[inchi_precursor["calculated_precursor_mz"].notna()]

# ==================================================
# STEP 7: Merge the calculated m/z back to the all_data to compare m/z calculated to original
# ==================================================
curated_data = all_data[
    [
        "gnps_spectra_id",
        "file_name",
        "name",
        "peaks",
        "precursortype",
        "precursormz",
        "inchikey",
        "ionmode",
        "instrumenttype",
        "instrument",
    ]
]
# 59k
curated_data_merged = curated_data.merge(
    inchi_precursor, on=["inchikey", "precursortype", "ionmode"], how="left"
)
assert len(curated_data_merged) == len(curated_data), (
    "Merge failed, number of rows do not match"
)

curated_data_merged["precursor_mz_diff"] = (
    curated_data_merged["precursormz"] - curated_data_merged["calculated_precursor_mz"]
)
bad_mz_rows = curated_data_merged[abs(curated_data_merged["precursor_mz_diff"]) > 0.1]
print(
    f"{bad_mz_rows.shape[0] / len(curated_data_merged) * 100:.3f}% of rows have bad m/z values for precursor based on the newly calculated m/z values"
)
curated_data_merged = curated_data_merged[
    abs(curated_data_merged["precursor_mz_diff"]) <= 0.1
]
print(
    f"{curated_data_merged['file_name'].nunique()} remaining file names in the dataset"
)
# Replace the precursormz with the calculated precursor m/z and drop the calculated_precursor_mz column
curated_data_merged["precursor_mz"] = curated_data_merged["calculated_precursor_mz"]
curated_data_merged = curated_data_merged.drop(
    columns=[
        "calculated_precursor_mz",
        "precursor_mz_diff",
        "precursor_mz",
        "precursortype_flag",
    ]
)

# Replace precursortype with the standardized precursortype and keep precursortype as precursortype_original
curated_data_merged["precursortype"] = curated_data_merged["precursortype_fixed"]
curated_data_merged = curated_data_merged.drop(columns=["precursortype_fixed"])

# ==================================================
# STEP 8: Investigate the instruments and remove low-resolution instruments
# ==================================================
instrument_df = curated_data_merged[["instrumenttype", "instrument"]].drop_duplicates()
bad_instruments = ["Ion Trap", "QQQ"]
curated_data_instremove = curated_data_merged[
    ~curated_data_merged["instrument"].isin(bad_instruments)
]
print(
    f"Removed {round((1 - curated_data_instremove.shape[0] / curated_data_merged.shape[0]) * 100, ndigits=1)}% spectra due to low-resolution instruments"
)
print(
    f"{curated_data_instremove['file_name'].nunique()} unique file names remain in the dataset after instrument filtering"
)
print(f"Remaining instruments: {curated_data_instremove['instrumenttype'].unique()}")

# ==================================================
# STEP 9: Write out a msp file of the curated data
# ==================================================

# rename columns for interpretability
final_curated_data = curated_data_instremove.rename(
    columns={
        "file_name": "database_name",
        "name": "name_in_original_database",
        "gnps_spectra_id": "gnps_spectra_id",
        "cid": "pubchem_id",
        "pubchemtitle": "name",
    }
)
# cast pubchem_id and chebi_id to int
final_curated_data["pubchem_id"] = pd.to_numeric(
    final_curated_data["pubchem_id"], errors="coerce"
).astype("Int64")
final_curated_data["chebi_id"] = pd.to_numeric(
    final_curated_data["chebi_id"], errors="coerce"
).astype("Int64")

print(
    f"Writing out curated MSP file...with {curated_data_instremove.shape[0] / og_spectra_count} of original spectra"
)
write_to_msp(final_curated_data, output_file, msms_col="peaks")
print("Done.")
