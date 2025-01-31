# This script will serve as a test for the lipdomics metadata generation script.
from datetime import datetime
from metadata_generator import GCMSMetabolomicsMetadataGenerator

def main(
        metadata_file,
        database_dump_json_path,
        raw_data_url,
        process_data_url,
        minting_config_creds
):

    # Start the metadata generation setup
    generator = GCMSMetabolomicsMetadataGenerator(
        metadata_file,
        database_dump_json_path,
        raw_data_url,
        process_data_url,
        minting_config_creds
    )
    # Run the metadata generation process
    generator.run()


if __name__ == "__main__":
    # Set up output file with datetime stame
    output_file = 'metaMS/nmdc_lipidomics_metadata_generation/test_data/test_database_gcms_' + datetime.now().strftime("%Y%m%d%H%M%S") + '.json'
    main(
        metadata_file='metaMS/nmdc_lipidomics_metadata_generation/test_data/test_metadata_file_gcms.csv',
        database_dump_json_path=output_file,
        raw_data_url='https://example_raw_data_url/',
        process_data_url='https://example_processed_data_url/',
        minting_config_creds='metaMS/nmdc_lipidomics_metadata_generation/.config.yaml'
    )