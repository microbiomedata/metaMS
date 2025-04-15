# From https://github.com/FanzhouKong/spectral_denoising/blob/732bb5e9c48ce8edd1ae07ab9c48fa805a8ea91e/spectral_denoising/file_io.py#L11

import pandas as pd 
import os
import numpy as np
from io import StringIO
def read_msp(file_path=None, string_buffer=None):
    
    """
    Reads the MSP files into the pandas dataframe, and sort/remove zero intensity ions in MS/MS spectra.

    Args:
        file_path (str): target path path for the MSP file or a string buffer if using StringIO.
    Returns:
        pd.DataFrame: DataFrame containing the MS/MS spectra information
    """
    
    spectra = []
    spectrum = {}
    if file_path is not None:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        with open(file_path, 'r') as f:
            file_content = f.read()
    elif string_buffer is not None:
        file_content = string_buffer.getvalue()
    else:
        raise ValueError("Either file_path or string_buffer must be provided.")

    f = StringIO(file_content)
    for line in f:
        line = line.strip()
        if not line:
            continue  # Skip empty lines

        # Handle metadata
        if ":" in line:
            key, value = line.split(":", 1)
            key = key.strip().lower()
            value = value.strip()
            
            if key == 'name':
                # Save current spectrum and start a new one
                if spectrum:
                    spectra.append(spectrum)
                spectrum = {'name': value, 'peaks': []}
            else:
                spectrum[key] = value
        
        # Handle peak data (assumed to start with a number)
        elif line[0].isdigit():
            
            peaks = line.split()
            m_z = float(peaks[0])
            intensity = float(peaks[1])
            spectrum['peaks'].append((([m_z, intensity])))
    # Save the last spectrum
    if spectrum:
        spectra.append(spectrum)

    df = pd.DataFrame(spectra)
    df['peaks'] = [sort_spectrum(remove_zero_ions(np.array(peak))) for peak in df['peaks']]
    for column in df.columns:
        if column != 'peaks':  # Skip 'peaks' column
            try:
                df[column] = pd.to_numeric(df[column], errors='raise')
            except:
                pass
    return df

def sort_spectrum(msms):
    """
    Sorts the spectrum data based on m/z values.

    Parameters:
        msms (numpy.ndarray): A 2D numpy array.
    Returns:
        numpy.ndarray: A 2D numpy array with the same shape as the input, but sorted by the m/z values in ascending order.
    """
    if isinstance(msms, float) or len(msms) == 0:
        return np.nan
    msms_T = msms.T
    order = np.argsort(msms_T[0])
    msms_T[0] = msms_T[0][order]
    msms_T[1] = msms_T[1][order]

    return msms_T.T

def remove_zero_ions(msms):
    """
    Remove zero intensity ions from a mass spectrometry dataset.

    Parameters:
        msms (numpy.ndarray or float): MS/MS spectrum in 2D numpy array.
    Returns:
        numpy.ndarray: A filtered 2D numpy array with rows where the second column (ion intensities) is greater than zero, or np.nan if the input is an empty spectrum.
    """

    if isinstance(msms, float) or len(msms) == 0:
        return np.nan
    to_keep = msms.T[1] > 0
    return msms[to_keep]

def write_to_msp(df, file_path, msms_col = 'peaks'):
    
    """
    Pair function of read_msp.
    Exports a pandas DataFrame to an MSP file.

    Args:
        df (pd.DataFrame): DataFrame containing spectrum information. Should have columns for 'name', 'peaks', and other metadata.
        file_path (str): Destination path for the MSP file.
    Returns:
        None
    """
    with open(file_path, 'w') as f:
        for _, row in df.iterrows():
            # Write the name of the spectrum
            if isinstance(row[msms_col], float):
                continue
            if 'name' in df.columns:
                f.write(f"Name: {row['name']}\n")
            
            # Write other metadata if available
            for col in df.columns:
                if col not in ['name', msms_col] and 'peak' not in col:
                    if pd.notna(row[col]):
                        f.write(f"{col.capitalize()}: {row[col]}\n")
            
            # Write the peaks (assuming each peak is a tuple of (m/z, intensity))
            f.write(f"Num Peaks: {len(row[msms_col])}\n")
            for mz, intensity in row[msms_col]:
                f.write(f"{mz} {intensity}\n")
            
            # Separate spectra by an empty line
            f.write("\n")

def load_msp_files(directory):

    """
    Load all .msp files from a directory into a single pandas DataFrame.

    Args:
        directory (str): Directory containing .msp files.
    Returns:
        pd.DataFrame: DataFrame containing all spectra information.
    """
    # Get list of all files ending in .msp if the directory "tmp_data/_msps"
    files = [f for f in os.listdir(directory) if f.endswith('.msp')]

    # Read each file and store the DataFrame in a list
    dataframes = []
    for file in files:
        print(file)
        file_path = os.path.join(directory, file)
        df = read_msp(file_path)
        # Add a column for the file name
        df['file_name'] = file
        dataframes.append(df)

    # Concatenate all DataFrames into a single DataFrame
    all_data = pd.concat(dataframes, ignore_index=True)
    return all_data

def load_msp_files_from_minio(minio_client, bucket_name, prefix):
    """
    Load MSP files from a MinIO bucket subfolder.

    Args:
        minio_client (Minio): An instance of the MinIO client.
        bucket_name (str): Name of the MinIO bucket.
        prefix (str): Prefix (subfolder path) in the MinIO bucket to look for .msp files.

    Returns:
        pd.DataFrame: A concatenated DataFrame containing data from all MSP files.
    """
    objects = minio_client.list_objects(bucket_name, prefix=prefix, recursive=True)

    # Filter for .msp files
    files = [obj.object_name for obj in objects]
    files = [f for f in files if f.endswith('.msp')]

    if not files:
        raise FileNotFoundError(f"No .msp files found in MinIO bucket '{bucket_name}' with prefix '{prefix}'")

    dataframes = []
    for file_key in files:
        print(file_key)
        response = minio_client.get_object(bucket_name, file_key)
        file_content = response.read().decode('utf-8')
        df = read_msp(string_buffer=StringIO(file_content))
        # Add a column for the file name
        df['file_name'] = os.path.basename(file_key)
        dataframes.append(df)

    # Concatenate all DataFrames into a single DataFrame
    all_data = pd.concat(dataframes, ignore_index=True)
    return all_data

    