# This script will serve as a test for the lipdomics metadata generation script.
from datetime import datetime
from metadata_generator import LCMSLipidomicsMetadataGenerator

def main(
        metadata_file,
        database_dump_json_path,
        raw_data_url,
        process_data_url,
        minting_config_creds
):
    # Remove 

    # Start the metadata generation setup
    generator = LCMSLipidomicsMetadataGenerator(
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
    output_file = 'metaMS/test_data/test_database_dump' + datetime.now().strftime("%Y%m%d%H%M%S") + '.json'
    main(
        metadata_file='metaMS/nmdc_lipidomics_metadata_generation/example_metadata_file.csv',
        database_dump_json_path=output_file,
        raw_data_url='https://example_raw_data_url/',
        process_data_url='https://example_processed_data_url/',
        minting_config_creds='metaMS/nmdc_lipidomics_metadata_generation/.config.yaml'
    )

