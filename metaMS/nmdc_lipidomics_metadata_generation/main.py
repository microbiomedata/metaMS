import argparse
from metadata_generator import MetadataGenerator

def main():
    """
    Parse command-line arguments and run the LipidomicsMetadataGenerator.

    This function sets up argument parsing for the script, initializes a
    LipidomicsMetadataGenerator instance with the provided arguments, and
    runs the metadata generation process.

    Parameters
    ----------
    None

    Returns
    -------
    None

    Side Effects
    ------------
    Generates a JSON file with the database dump at the specified path.

    Command-line Arguments
    ----------------------
    --metadata_file : str
        Path to the input CSV metadata file. 
        Example: See example_metadata_file.csv in this directory.
    --database_dump_json_path : str
        Path where the output database dump JSON file will be saved.
    --raw_data_url : str
        URL base for the raw data files.
        Example: 'https://nmdcdemo.emsl.pnnl.gov/nom/1000soils/raw/'
    --process_data_url : str
        URL base for the processed data files.
        Example: 'https://nmdcdemo.emsl.pnnl.gov/nom/1000soils/results/'
    --minting_config_creds : str, optional
        Path to the config file with credentials for minting IDs.
        Should be a YAML file with format:
        line 1: client_id: X
        line 2: client_secret: X
        Default: 'metaMS/nmdc_lipidomics_metadata_generation/.config.yaml'

    Notes
    -----
    See example_metadata_file.csv in this directory for an example of
    the expected metadata file format.
    """
    parser = argparse.ArgumentParser(description="Generate NMDC metadata from input files")
    parser.add_argument('--metadata_file', required=True,
                        help="Path to the input CSV metadata file")
    parser.add_argument('--database_dump_json_path', required=True,
                        help="Path where the output database dump JSON file will be saved")
    parser.add_argument('--raw_data_url', required=True,
                        help="URL base for the raw data files")
    parser.add_argument('--process_data_url', required=True,
                        help="URL base for the processed data files")
    parser.add_argument('--minting_config_creds',
                        default='metaMS/nmdc_lipidomics_metadata_generation/.config.yaml',
                        help="Path to the config file with credentials for minting IDs")

    args = parser.parse_args()

    generator = MetadataGenerator(
        args.metadata_file,
        args.database_dump_json_path,
        args.raw_data_url,
        args.process_data_url,
        args.minting_config_creds
    )
    generator.run()


if __name__ == "__main__":
    main()