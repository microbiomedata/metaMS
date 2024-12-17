import logging
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass
from typing import List, Dict

import pandas as pd
import hashlib
import json
import yaml
import oauthlib
import requests_oauthlib
import requests
from tqdm import tqdm

import nmdc_schema.nmdc as nmdc
from linkml_runtime.dumpers import json_dumper
from api_info_retriever import ApiInfoRetriever

# Configure logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s'
    )

# TODO: Update script to for Sample Processing - has_input for MassSpectrometry will have to be changed to be a processed sample id - not biosample id

@dataclass
class GroupedMetadata:
    """
    Data class for holding grouped metadata information.

    Attributes
    ----------
    biosample_id : str
        Identifier for the biosample.
    processing_type : str
        Type of processing applied to the data.
    processing_institution : str
        Institution responsible for processing the data.
    nmdc_study : float
        Identifier for the NMDC study associated with the data.
    """
    biosample_id: str
    processing_type: str
    processing_institution: str
    nmdc_study: float

@dataclass
class WorkflowMetadata:
    """
    Data class for holding workflow metadata information.

    Attributes
    ----------
    processed_data_dir : str
        Directory containing processed data files.
    raw_data_file : str
        Path or name of the raw data file.
    mass_spec_config_name : str
        Name of the mass spectrometry configuration used.
    lc_config_name : str
        Name of the liquid chromatography configuration used.
    instrument_used : str
        Name of the instrument used for analysis.
    instrument_analysis_start_date : str
        Start date of the instrument analysis.
    instrument_analysis_end_date : str
        End date of the instrument analysis.
    execution_resource : float
        Identifier for the execution resource.
    """
    processed_data_dir: str
    raw_data_file: str
    mass_spec_config_name: str
    lc_config_name: str
    instrument_used: str
    instrument_analysis_start_date: str
    instrument_analysis_end_date: str
    execution_resource: float

@dataclass
class NmdcTypes:
    """
    Data class holding NMDC type constants.

    Attributes
    ----------
    Biosample : str
        NMDC type for Biosample.
    MassSpectrometry : str
        NMDC type for Mass Spectrometry.
    MetabolomicsAnalysis : str
        NMDC type for Metabolomics Analysis.
    DataObject : str
        NMDC type for Data Object.
    """
    Biosample: str = "nmdc:Biosample"
    MassSpectrometry: str = "nmdc:MassSpectrometry"
    MetabolomicsAnalysis: str = "nmdc:MetabolomicsAnalysis"
    DataObject: str = "nmdc:DataObject"

class MetadataGenerator:
    """
    A class for generating NMDC metadata objects using provided metadata files and configuration.

    This class processes input metadata files, generates various NMDC objects, and produces
    a database dump in JSON format.

    Attributes
    ----------
    metadata_file : str
        Path to the CSV file containing the metadata about a sample data lifecycle.
    database_dump_json_path : str
        Path to the output JSON file for dumping the NMDC database results.
    raw_data_url : str
        Base URL for raw data files.
    process_data_url : str
        Base URL for processed data files.
    minting_client_config_path : str
        Path to the YAML configuration file for the NMDC ID minting client.
    grouped_columns : List[str]
        List of columns used for grouping metadata.
    mass_spec_desc : str
        Description of the mass spectrometry analysis.
    mass_spec_eluent_intro : str
        Eluent introduction category for mass spectrometry.
    analyte_category : str
        Category of the analyte.
    raw_data_category : str
        Category of the raw data.
    raw_data_obj_type : str
        Type of the raw data object.
    raw_data_obj_desc : str
        Description of the raw data object.
    workflow_analysis_name : str
        Name of the workflow analysis.
    workflow_description : str
        Description of the workflow.
    workflow_git_url : str
        URL of the workflow's Git repository.
    workflow_version : str
        Version of the workflow.
    wf_config_process_data_category : str
        Category of the workflow configuration process data.
    wf_config_process_data_obj_type : str
        Type of the workflow configuration process data object.
    wf_config_process_data_description : str
        Description of the workflow configuration process data.
    no_config_process_data_category : str
        Category for processed data without configuration.
    no_config_process_data_obj_type : str
        Type of processed data object without configuration.
    csv_process_data_description : str
        Description of CSV processed data.
    hdf5_process_data_obj_type : str
        Type of HDF5 processed data object.
    hdf5_process_data_description : str
        Description of HDF5 processed data.
    """

    
    def __init__(
        self,
        metadata_file: str,
        database_dump_json_path: str,
        raw_data_url: str,
        process_data_url: str,
        minting_config_creds: str
        ):
        """
        Initialize the MetadataGenerator with required file paths and configuration.

        Parameters
        ----------
        metadata_file : str
            Path to the input CSV metadata file.
        database_dump_json_path : str
            Path where the output database dump JSON file will be saved.
        raw_data_url : str
            Base URL for the raw data files.
        process_data_url : str
            Base URL for the processed data files.
        minting_config_creds : str
            Path to the config file with credentials for minting IDs.

        Returns
        -------
        None

        Notes
        -----
        This method sets up various attributes used throughout the class,
        including file paths, URLs, and predefined values for different
        data categories and descriptions.
        """
        self.metadata_file = metadata_file
        self.database_dump_json_path = database_dump_json_path
        self.raw_data_url = raw_data_url
        self.process_data_url = process_data_url
        self.minting_client_config_path = minting_config_creds
        self.grouped_columns = [
            'Biosample Id',
            'Associated Study',
            'Processing Type',
            'processing institution'
        ]
        self.mass_spec_desc = (
            "Generation of mass spectrometry data for the analysis of lipids."
        )
        self.mass_spec_eluent_intro = "liquid_chromatography"
        self.analyte_category = "lipidome"
        self.raw_data_category = "instrument_data"
        self.raw_data_obj_type = "LC-DDA-MS/MS Raw Data"
        self.raw_data_obj_desc = (
            "LC-DDA-MS/MS raw data for lipidomics data acquisition."
        )
        self.workflow_analysis_name = "Lipidomics analysis"
        self.workflow_description = (
            "Analysis of raw mass spectrometry data for the annotation of lipids."
        )
        self.workflow_git_url = "https://github.com/microbiomedata/metaMS/wdl/metaMS_lipidomics.wdl"
        self.workflow_version = "1.0.0"
        self.wf_config_process_data_category = "workflow_parameter_data"
        self.wf_config_process_data_obj_type = "Configuration toml"
        self.wf_config_process_data_description = (
            "CoreMS parameters used for Lipidomics workflow."
        )
        self.no_config_process_data_category = "processed_data"
        self.no_config_process_data_obj_type = "LC-MS Lipidomics Results"
        self.csv_process_data_description = (
            "Lipid annotations as a result of a lipidomics workflow activity."
        )
        self.hdf5_process_data_obj_type = "LC-MS Lipidomics Results"
        self.hdf5_process_data_description = (
            "CoreMS hdf5 file representing a lipidomics data file including annotations."
        )

    def run(self):
        """
        Execute the metadata generation process for lipidomics data.

        This method performs the following steps:
        1. Initialize an NMDC Database instance.
        2. Load and process metadata to create NMDC objects.
        3. Generate Mass Spectrometry, Raw Data, Metabolomics Analysis, and
        Processed Data objects.
        4. Update outputs for Mass Spectrometry and Metabolomics Analysis objects.
        5. Append generated objects to the NMDC Database.
        6. Dump the NMDC Database to a JSON file.

        Returns
        -------
        None

        Notes
        -----
        This method uses tqdm to display progress bars for the processing of
        biosamples and mass spectrometry metadata.
        """

        nmdc_database_inst = self.start_nmdc_database()
        grouped_data = self.load_metadata()
        total_groups = len(grouped_data)

        for group, data in tqdm(grouped_data, total=total_groups,
                                desc="Processing biosamples"):
            grouped_df = data[self.grouped_columns].drop_duplicates()
            group_metadata_obj = grouped_df.apply(
                lambda row: self.create_grouped_metadata(row), axis=1).iloc[0]

            workflow_df = data.drop(columns=self.grouped_columns)
            workflow_metadata = workflow_df.apply(
                lambda row: self.create_workflow_metadata(row), axis=1)
            
            for workflow_metadata_obj in tqdm(
                workflow_metadata, 
                desc=f"Processing mass spec metadata for biosample "
                    f"{group_metadata_obj.biosample_id}",
                leave=False
            ):
                mass_spec = self.generate_mass_spectrometry(
                    file_path=Path(workflow_metadata_obj.raw_data_file),
                    instrument_name=workflow_metadata_obj.instrument_used,
                    sample_id=group_metadata_obj.biosample_id,
                    raw_data_id="nmdc:placeholder",
                    study_id=group_metadata_obj.nmdc_study,
                    processing_institution=group_metadata_obj.processing_institution,
                    mass_spec_config_name=workflow_metadata_obj.mass_spec_config_name,
                    lc_config_name=workflow_metadata_obj.lc_config_name,
                    start_date=workflow_metadata_obj.instrument_analysis_start_date,
                    end_date=workflow_metadata_obj.instrument_analysis_end_date
                )

                raw_data_object = self.generate_data_object(
                    file_path=Path(workflow_metadata_obj.raw_data_file),
                    data_category=self.raw_data_category,
                    data_object_type=self.raw_data_obj_type,
                    description=self.raw_data_obj_desc,
                    base_url=self.raw_data_url,
                    was_generated_by=mass_spec.id,
                )

                metab_analysis = self.generate_metabolomics_analysis(
                    cluster_name=workflow_metadata_obj.execution_resource,
                    raw_data_name=Path(workflow_metadata_obj.raw_data_file).name,
                    raw_data_id=raw_data_object.id,
                    data_gen_id=mass_spec.id,
                    processed_data_id="nmdc:placeholder",
                    processing_institution=group_metadata_obj.processing_institution
                )
            
                processed_data_paths = Path(
                    workflow_metadata_obj.processed_data_dir).glob('**/*')
                processed_data = []

                for file in processed_data_paths:
                    file_type = file.suffixes
                    if file_type:
                        file_type = file_type[0].lstrip('.')

                        if file_type == 'toml':
                            processed_data_object = self.generate_data_object(
                                file_path=file,
                                data_category=self.wf_config_process_data_category,
                                data_object_type=self.wf_config_process_data_obj_type,
                                description=self.wf_config_process_data_description,
                                base_url=self.process_data_url,
                                was_generated_by=metab_analysis.id
                            )
                            nmdc_database_inst.data_object_set.append(processed_data_object)
                            processed_data.append(processed_data_object.id)

                        elif file_type == 'csv':
                            processed_data_object = self.generate_data_object(
                                file_path=file,
                                data_category=self.no_config_process_data_category,
                                data_object_type=self.no_config_process_data_obj_type,
                                description=self.csv_process_data_description,
                                base_url=self.process_data_url,
                                was_generated_by=metab_analysis.id
                            )
                            nmdc_database_inst.data_object_set.append(processed_data_object)
                            processed_data.append(processed_data_object.id)

                        elif file_type == 'hdf5':
                            processed_data_object = self.generate_data_object(
                                file_path=file,
                                data_category=self.no_config_process_data_category,
                                data_object_type=self.hdf5_process_data_obj_type,
                                description=self.hdf5_process_data_description,
                                base_url=self.process_data_url,
                                was_generated_by=metab_analysis.id
                            )
                            
                            nmdc_database_inst.data_object_set.append(processed_data_object)
                            processed_data.append(processed_data_object.id)

                            # Update MetabolomicsAnalysis times based on HDF5 file
                            metab_analysis.started_at_time = datetime.fromtimestamp(
                                file.stat().st_ctime).strftime("%Y-%m-%d %H:%M:%S")
                            metab_analysis.ended_at_time = datetime.fromtimestamp(
                                file.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")

                self.update_outputs(
                    mass_spec_obj=mass_spec,
                    analysis_obj=metab_analysis,
                    raw_data_obj=raw_data_object,
                    processed_data_id_list=processed_data
                )

                nmdc_database_inst.data_generation_set.append(mass_spec)
                nmdc_database_inst.data_object_set.append(raw_data_object)
                nmdc_database_inst.workflow_execution_set.append(metab_analysis)
        
        self.dump_nmdc_database(nmdc_database=nmdc_database_inst)
        self.validate_json()
        logging.info("Metadata processing completed.")

    def load_metadata(self) -> pd.core.groupby.DataFrameGroupBy:
        """
        Load and group workflow metadata from a CSV file.

        This method reads the metadata CSV file, checks for uniqueness in
        specified columns, checks that biosamples exist, and groups the data by biosample ID.

        Returns
        -------
        pd.core.groupby.DataFrameGroupBy
            DataFrame grouped by biosample ID.

        Raises
        ------
        FileNotFoundError
            If the `metadata_file` does not exist.
        ValueError
            If values in columns 'Raw Data File',
            and 'Processed Data Directory' are not unique.

        Notes
        -----
        See example_metadata_file.csv in this directory for an example of
        the expected input file format.
        """
        try:
            metadata_df = pd.read_csv(self.metadata_file)
        except FileNotFoundError:
            raise FileNotFoundError(f"Metadata file not found: {self.metadata_file}")

        # Check for uniqueness in specified columns
        columns_to_check = [
            'Raw Data File',
            'Processed Data Directory'
        ]
        for column in columns_to_check:
            if not metadata_df[column].is_unique:
                raise ValueError(f"Duplicate values found in column '{column}'.")
            
        # Check that all biosamples exist
        biosample_ids = metadata_df['Biosample Id'].unique()
        api_biosample_getter = ApiInfoRetriever(collection_name="biosample_set")

        if not api_biosample_getter.check_if_ids_exist(biosample_ids):
            raise ValueError("Biosample IDs do not exist in the collection.")

        # Group by Biosample
        grouped = metadata_df.groupby('Biosample Id')

        return grouped

    def create_grouped_metadata(self, row: pd.Series) -> GroupedMetadata:
        """
        Construct a GroupedMetadata object from a DataFrame row.

        Parameters
        ----------
        row : pd.Series
            A row from the grouped metadata DataFrame.

        Returns
        -------
        GroupedMetadata
            A GroupedMetadata object populated with data from the input row.

        Notes
        -----
        This method assumes that the `self.grouped_columns` list contains
        exactly four elements in the following order:
        [biosample_id, nmdc_study, processing_type, processing_institution]
        """
        return GroupedMetadata(
            biosample_id=row[self.grouped_columns[0]],
            nmdc_study=row[self.grouped_columns[1]],
            processing_type=row[self.grouped_columns[2]],
            processing_institution=row[self.grouped_columns[3]]
        )

    def create_workflow_metadata(
        self, 
        row: 
        dict[str, str]
        ) -> WorkflowMetadata:
        """
        Create a WorkflowMetadata object from a dictionary of workflow metadata.

        Parameters
        ----------
        row : dict[str, str]
            Dictionary containing metadata for a workflow. This is typically
            a row from the input metadata CSV file.

        Returns
        -------
        WorkflowMetadata
            A WorkflowMetadata object populated with data from the input dictionary.

        Notes
        -----
        The input dictionary is expected to contain the following keys:
        'Processed Data Directory', 'Raw Data File', 'Raw Data Object Alt Id',
        'mass spec configuration name', 'lc config name', 'instrument used',
        'instrument analysis start date', 'instrument analysis end date',
        'execution resource'.
        """
        return WorkflowMetadata(
            processed_data_dir=row['Processed Data Directory'],
            raw_data_file=row['Raw Data File'],
            mass_spec_config_name=row['mass spec configuration name'],
            lc_config_name=row['lc config name'],
            instrument_used=row['instrument used'],
            instrument_analysis_start_date=row['instrument analysis start date'],
            instrument_analysis_end_date=row['instrument analysis end date'],
            execution_resource=row['execution resource']
        )

    def mint_nmdc_id(self, nmdc_type: str) -> list[str]:
        """
        Mint new NMDC IDs of the specified type using the NMDC ID minting API.

        Parameters
        ----------
        nmdc_type : str
            The type of NMDC ID to mint (e.g., 'nmdc:MassSpectrometry',
            'nmdc:DataObject').

        Returns
        -------
        list[str]
            A list containing one newly minted NMDC ID.

        Raises
        ------
        requests.exceptions.RequestException
            If there is an error during the API request.

        Notes
        -----
        This method relies on a YAML configuration file for authentication
        details. The file should contain 'client_id' and 'client_secret' keys.

        """
        config = yaml.safe_load(open(self.minting_client_config_path))
        client = oauthlib.oauth2.BackendApplicationClient(
            client_id=config['client_id']
        )
        oauth = requests_oauthlib.OAuth2Session(client=client)

        api_base_url = 'https://api.microbiomedata.org'

        token = oauth.fetch_token(
            token_url=f'{api_base_url}/token',
            client_id=config['client_id'],
            client_secret=config['client_secret']
        )

        nmdc_mint_url = f'{api_base_url}/pids/mint'

        payload = {
            "schema_class": {"id": nmdc_type},
            "how_many": 1
        }

        response = oauth.post(nmdc_mint_url, data=json.dumps(payload))
        list_ids = response.json()

        return list_ids

    def generate_mass_spectrometry(
        self,
        file_path: Path,
        instrument_name: str,
        sample_id: str,
        raw_data_id: str,
        study_id: str,
        processing_institution: str,
        mass_spec_config_name: str,
        lc_config_name: str,
        start_date: str,
        end_date: str
        ) -> nmdc.DataGeneration:
        """
        Create an NMDC DataGeneration object for mass spectrometry and mint an NMDC ID.

        Parameters
        ----------
        file_path : Path
            File path of the mass spectrometry data.
        instrument_name : str
            Name of the instrument used for data generation.
        sample_id : str
            ID of the input sample associated with the data generation.
        raw_data_id : str
            ID of the raw data object associated with the data generation.
        study_id : str
            ID of the study associated with the data generation.
        processing_institution : str
            Name of the processing institution.
        mass_spec_config_name : str
            Name of the mass spectrometry configuration.
        lc_config_name : str
            Name of the liquid chromatography configuration.
        start_date : str
            Start date of the data generation.
        end_date : str
            End date of the data generation.

        Returns
        -------
        nmdc.DataGeneration
            An NMDC DataGeneration object with the provided metadata.

        Notes
        -----
        This method uses the ApiInfoRetriever to fetch IDs for the instrument
        and configurations. It also mints a new NMDC ID for the DataGeneration object.

        TODO: Update docstring with new variables (e.g. analyte_category).
        """
        nmdc_id = self.mint_nmdc_id(nmdc_type=NmdcTypes.MassSpectrometry)[0]

        # Look up instrument, lc_config, and mass_spec_config id by name slot using API
        api_instrument_getter = ApiInfoRetriever(collection_name="instrument_set")
        instrument_id = api_instrument_getter.get_id_by_name_from_collection(
            name_field_value=instrument_name
        )

        api_config_getter = ApiInfoRetriever(collection_name="configuration_set")
        lc_config_id = api_config_getter.get_id_by_name_from_collection(
            name_field_value=lc_config_name
        )
        mass_spec_id = api_config_getter.get_id_by_name_from_collection(
            name_field_value=mass_spec_config_name
        )

        data_dict = {
            "id": nmdc_id,
            "name": file_path.stem,
            "description": self.mass_spec_desc,
            "add_date": datetime.now().strftime('%Y-%m-%d'),
            "eluent_introduction_category": self.mass_spec_eluent_intro,
            "has_mass_spectrometry_configuration": mass_spec_id,
            "has_chromatography_configuration": lc_config_id,
            "analyte_category": self.analyte_category,
            "instrument_used": instrument_id,
            "has_input": [sample_id],
            "has_output": [raw_data_id],
            "associated_studies": study_id,
            "processing_institution": processing_institution,
            "start_date": start_date,
            "end_date": end_date,
            "type": NmdcTypes.MassSpectrometry
        }

        mass_spectrometry = nmdc.DataGeneration(**data_dict)

        return mass_spectrometry

    def generate_data_object(
        self,
        file_path: Path,
        data_category: str,
        data_object_type: str,
        description: str,
        base_url: str,
        was_generated_by: str,
        alternative_id: str = None
        ) -> nmdc.DataObject:
        """
        Create an NMDC DataObject with metadata from the specified file and details.

        This method generates an NMDC DataObject and assigns it a unique NMDC ID.
        The DataObject is populated with metadata derived from the provided file
        and input parameters.

        Parameters
        ----------
        file_path : Path
            Path to the file representing the data object. The file's name is
            used as the `name` attribute.
        data_category : str
            Category of the data object (e.g., 'instrument_data').
        data_object_type : str
            Type of the data object (e.g., 'LC-DDA-MS/MS Raw Data').
        description : str
            Description of the data object.
        base_url : str
            Base URL for accessing the data object, to which the file name is
            appended to form the complete URL.
        was_generated_by : str
            ID of the process or entity that generated the data object
            (e.g., the DataGeneration id or the MetabolomicsAnalysis id).
        alternative_id : str, optional
            An optional alternative identifier for the data object.

        Returns
        -------
        nmdc.DataObject
            An NMDC DataObject instance with the specified metadata.

        Notes
        -----
        This method calculates the MD5 checksum of the file, which may be
        time-consuming for large files.
        """
        nmdc_id = self.mint_nmdc_id(nmdc_type=NmdcTypes.DataObject)[0]
        data_dict = {
            'id': nmdc_id,
            'data_category': data_category,
            'data_object_type': data_object_type,
            'name': file_path.name,
            'description': description,
            'file_size_bytes': file_path.stat().st_size,
            'md5_checksum': hashlib.md5(file_path.open('rb').read()).hexdigest(),
            'url': base_url + str(file_path.name),
            'was_generated_by': was_generated_by,
            'type': NmdcTypes.DataObject
        }

        if alternative_id is not None and isinstance(alternative_id, str):
            data_dict['alternative_identifiers'] = [alternative_id]

        data_object = nmdc.DataObject(**data_dict)

        return data_object

    def generate_metabolomics_analysis(
        self,
        cluster_name: str,
        raw_data_name: str,
        raw_data_id: str,
        data_gen_id: str,
        processed_data_id: str,
        processing_institution: str
        ) -> nmdc.MetabolomicsAnalysis:
        """
        Create an NMDC MetabolomicsAnalysis object with metadata for a workflow analysis.

        This method generates an NMDC MetabolomicsAnalysis object, including details
        about the analysis, the processing institution, and relevant workflow information.

        Parameters
        ----------
        cluster_name : str
            Name of the cluster or computing resource used for the analysis.
        raw_data_name : str
            Name of the raw data file that was analyzed.
        raw_data_id : str
            ID of the raw data object that was analyzed.
        data_gen_id : str
            ID of the DataGeneration object that generated the raw data.
        processed_data_id : str
            ID of the processed data resulting from the analysis.
        processing_institution : str
            Name of the institution where the analysis was performed.

        Returns
        -------
        nmdc.MetabolomicsAnalysis
            An NMDC MetabolomicsAnalysis instance with the provided metadata.

        Notes
        -----
        The 'started_at_time' and 'ended_at_time' fields are initialized with
        placeholder values and should be updated with actual timestamps later
        when the processed files are iterated over in the run method.
        """
        nmdc_id = self.mint_nmdc_id(nmdc_type=NmdcTypes.MetabolomicsAnalysis)[0]+".1"
        #TODO: Update the minting to handle versioning in the future

        data_dict = {
            'id': nmdc_id,
            'name': f'{self.workflow_analysis_name} for {raw_data_name}',
            'description': self.workflow_description,
            'processing_institution': processing_institution,
            'execution_resource': cluster_name,
            'git_url': self.workflow_git_url,
            'version': self.workflow_version,
            'was_informed_by': data_gen_id,
            'has_input': [raw_data_id],
            'has_output': [processed_data_id],
            'started_at_time': 'placeholder',
            'ended_at_time': 'placeholder',
            'type': NmdcTypes.MetabolomicsAnalysis,
        }

        metab_analysis = nmdc.MetabolomicsAnalysis(**data_dict)

        return metab_analysis

    def update_outputs(
        self,
        mass_spec_obj: object,
        analysis_obj: object,
        raw_data_obj: object,
        processed_data_id_list: list
        ) -> None:
        """
        Update output references for Mass Spectrometry and Workflow Analysis objects.

        This method assigns the output references for a Mass Spectrometry object
        and a Workflow Execution Analysis object. It sets `mass_spec_obj.has_output`
        to the ID of `raw_data_obj` and `analysis_obj.has_output` to a list of
        processed data IDs.

        Parameters
        ----------
        mass_spec_obj : object
            The Mass Spectrometry object to update.
        analysis_obj : object
            The Workflow Execution Analysis object to update
            (e.g., MetabolomicsAnalysis).
        raw_data_obj : object
            The Raw Data Object associated with the Mass Spectrometry.
        processed_data_id_list : list
            List of IDs representing processed data objects associated with
            the Workflow Execution.

        Returns
        -------
        None

        Side Effects
        ------------
        - Sets `mass_spec_obj.has_output` to [raw_data_obj.id].
        - Sets `analysis_obj.has_output` to `processed_data_id_list`.
        """
        mass_spec_obj.has_output = [raw_data_obj.id]
        analysis_obj.has_output = processed_data_id_list

    def start_nmdc_database(self) -> nmdc.Database:
        """
        Initialize and return a new NMDC Database instance.

        Returns
        -------
        nmdc.Database
            A new instance of an NMDC Database.

        Notes
        -----
        This method simply creates and returns a new instance of the NMDC
        Database. It does not perform any additional initialization or
        configuration.
        """
        return nmdc.Database()

    def dump_nmdc_database(self, nmdc_database: nmdc.Database) -> None:
        """
        Dump the NMDC database to a JSON file.

        This method serializes the NMDC Database instance to a JSON file
        at the specified path.

        Parameters
        ----------
        nmdc_database : nmdc.Database
            The NMDC Database instance to dump.

        Returns
        -------
        None

        Side Effects
        ------------
        Writes the database content to the file specified by
        `self.database_dump_json_path`.
        """
        json_dumper.dump(nmdc_database, self.database_dump_json_path)
        logging.info(
            "Database successfully dumped in %s",
            self.database_dump_json_path
        )
    
    def validate_json(self) -> None:
        """
        Validates the json file generated by the MetadataGenerator class.

        This method reads the JSON file generated by the MetadataGenerator class
        and validates it against the NMDC schema.

        If the validation passes, the method returns without any side effects.

        Raises
        ------
        Exception
            If the validation fails.
        """
        with open(self.database_dump_json_path, 'r') as f:
            data = json.load(f)

        url = 'https://api-dev.microbiomedata.org/metadata/json:validate'
        headers = {
            'accept': 'application/json',
            'Content-Type': 'application/json'
        }
        response = requests.post(url, headers=headers, json=data)
        if response.status_code != 200:
            logging.error(f"Request failed with status code {response.status_code}")
            logging.error(response.text)
            raise Exception("Validation failed")