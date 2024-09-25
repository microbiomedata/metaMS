from metadata_generator import MetadataGenerator
import argparse

# TODO: possibly combine --raw_data_url and --process_data_url to one argument that is base_url because it may be the same for raw and processed data (
# this is the base url that points to where the data objects can be downloaded. The file name is appended to the end. E.g in NOM it is https://nmdcdemo.emsl.pnnl.gov/)
def main():
    """
    Main function to parse command-line arguments and run the LipidomicsMetadataGenerator.

    This function sets up argument parsing for the script. It requires the user to provide 
    paths for the metadata csv file, database dump JSON path, raw data URL, and processed data URL. 
    It then initializes an instance of `LipidomicsMetadataGenerator` with these arguments 
    and calls its `run` method to generate metadata and process the data.

    Command-line arguments:
    -----------------------
    --metadata_file : str
        Path to the input csv metadata file. See example_metadata_file.csv in this directory for example.
    --database_dump_json_path : str
        Path where the output database dump JSON file will be saved.
    --raw_data_url : str
        URL base for the raw data files. For example: 'https://nmdcdemo.emsl.pnnl.gov/nom/1000soils/raw/'
    --process_data_url : str
        URL base for the processed data files. For example 'https://nmdcdemo.emsl.pnnl.gov/nom/1000soils/results/'
    --minting_config_creds : str
        The Path to where the config file is with credentials to mint ids. Should be a yaml file with format: line 1 is client_id: X and line 2 is client_secret: X

    Returns:
    -------
    A json file with the database dump.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('--metadata_file', required=True)
    parser.add_argument('--database_dump_json_path', required=True)
    parser.add_argument('--raw_data_url', required = True)
    parser.add_argument('--process_data_url', required = True)
    parser.add_argument('--minting_config_creds', required=True)
    args = parser.parse_args()
    generator = MetadataGenerator(args.metadata_file, args.database_dump_json_path, args.raw_data_url, args.process_data_url, args.minting_config_creds)
    generator.run()

if __name__ == "__main__":
    main()

