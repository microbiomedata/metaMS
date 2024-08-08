from metadata_generator import MetadataGenerator
from pathlib import Path
import pandas as pd

# TODO: update has_input for MassSpectrometry to not be biosample id but an analyte id when Material Processing is in place


class LipidomicsMetadataGenerator(MetadataGenerator):
    """
    A specialized metadata generator for lipidomics data, extending the MetadataGenerator class.

    This class is designed to handle metadata generation specific to lipidomics workflows,
    including the creation of various NMDC objects and updating their relationships based on
    lipidomics data files and analysis results.

    See parent MetadataGenerator for descriptions of generic attributes.

    Attributes:
    ----------
    raw_data_url : str
        URL path for accessing raw data files objects (e.g. https://nmdcdemo.emsl.pnnl.gov/nom/1000soils/raw/)
    process_data_url : str
        URL path for accessing processed data file objects (e.g. https://nmdcdemo.emsl.pnnl.gov/nom/1000soils/results/).
    no_config_process_data_category : str
        Data category for processed data files that are not workflow configuration files.
    no_config_process_data_obj_type : str
        Object type for processed data files that are not workflow configuration files.
    csv_process_data_description : str
        Description for processed data file objects that are a csv.
    hdf5_process_data_obj_type : str
        Object type for processed data files in HDF5 format.
    hdf5_process_data_description : str
        Description for processed data files in HDF5 format
    """

    def __init__(self, metadata_file, database_dump_json_path, raw_data_url, process_data_url,
                 no_config_process_data_category="processed_data", no_config_process_data_obj_type="LC-MS Lipidomics Results",
                 csv_process_data_description="Lipid annotations as a result of a lipidomics workflow activity.",
                 hdf5_process_data_obj_type="LC-MS Lipidomics Results",
                 hdf5_process_data_description="CoreMS hdf5 file representing a lipidomics data file including annotations."):
        """
        Initializes the LipidomicsMetadataGenerator with specific parameters for lipidomics data.
        """

        super().__init__(metadata_file,
                         database_dump_json_path,
                         minting_client_config_path='metaMS/nmdc_metadata_generation/.config.yaml',
                         grouped_columns=['Biosample Id', 'Associated Study', 'Processing Type',
                                          'Raw Data File', 'Raw Data Object Alt Id', 'processing institution'],
                         mass_spec_desc="Analysis of raw mass spectrometry data for the annotation of lipids.",
                         mass_spec_eluent_intro="liquid_chromatography",
                         analyte_category="lipidome",
                         raw_data_category="instrument_data",
                         raw_data_obj_type="LC-DDA-MS/MS Raw Data",
                         raw_data_obj_desc="LC-DDA-MS/MS raw data for lipidomics data acquisition.",
                         workflow_analysis_name="Lipidomics analysis",
                         workflow_description="Analysis of raw mass spectrometry data for the annotation of lipids.",
                         workflow_git_url="https://github.com/microbiomedata/metaMS",
                         workflow_version="2.2.3",
                         wf_config_process_data_category="workflow_parameter_data",
                         wf_config_process_data_obj_type="Configuration toml",
                         wf_config_process_data_description="CoreMS parameters used for Lipidomics workflow.")

        self.raw_data_url = raw_data_url
        self.process_data_url = process_data_url
        self.no_config_process_data_category = no_config_process_data_category
        self.no_config_process_data_obj_type = no_config_process_data_obj_type
        self.csv_process_data_description = csv_process_data_description
        self.hdf5_process_data_obj_type = hdf5_process_data_obj_type
        self.hdf5_process_data_description = hdf5_process_data_description

    def run(self):
        """
        Executes the metadata generation process for lipidomics data.

        This method performs the following steps:
        1. Initializes an NMDC Database instance.
        2. Loads metadata and processes it to create NMDC objects.
        3. Generates Mass Spectrometry objects, Raw Data Objects, Metabolomics Analysis objects, and Processed Data Objects.
        4. Updates the outputs for Mass Spectrometry and Metabolomics Analysis objects.
        5. Appends the generated objects to the NMDC Database.
        6. Dumps the NMDC Database to a JSON file.

        Returns:
        -------
        None
        """

        nmdc_database_inst = self.start_nmdc_database()

        for group, data in self.load_metadata():
            # Get group level metadata (e.g. 1 Biosample to many MassSpec instances 1 sample -> 2 mass spec -> 2 raw data -> 6 processed data)
            grouped_df = data[self.grouped_columns].drop_duplicates()
            group_metadata_obj = grouped_df.apply(
                lambda row: self.create_grouped_metadata(row), axis=1).iloc[0]

            # Get MassSpec and downstream metadata
            workflow_df = data.drop(columns=self.grouped_columns)
            workflow_metadata = workflow_df.apply(
                lambda row: self.create_workflow_metadata(row), axis=1)
            for workflow_metadata_obj in workflow_metadata:

                MassSpectrometry = self.generate_mass_spec_object(
                    grouped_metadata=group_metadata_obj, wf_metadata=workflow_metadata_obj)

                RawDataObject = self.generate_raw_data_object(
                    grouped_metadata=group_metadata_obj, mass_spec_obj=MassSpectrometry)

                MetabAnalysis = self.generate_metab_analysis_object(grouped_metadata=group_metadata_obj, wf_metadata=workflow_metadata_obj,
                                                                    raw_data_obj=RawDataObject, masss_spec_obj=MassSpectrometry)

                processed_data = self.generate_processed_data_objects(wf_metadata=workflow_metadata_obj, metab_analysis_obj=MetabAnalysis,
                                                                      data_obj_set=nmdc_database_inst.data_object_set)
                self.update_outputs(mass_spec_obj=MassSpectrometry,
                                    analysis_obj=MetabAnalysis,
                                    raw_data_obj=RawDataObject,
                                    processed_data_id_list=processed_data)

                nmdc_database_inst.data_generation_set.append(MassSpectrometry)
                nmdc_database_inst.data_object_set.append(RawDataObject)
                nmdc_database_inst.workflow_execution_set.append(MetabAnalysis)

        self.dump_nmdc_database(nmdc_database=nmdc_database_inst)

    def generate_mass_spec_object(self, grouped_metadata: object, wf_metadata: object) -> object:
        """"
        Generates a Mass Spectrometry object based on metadata.

        This method creates a Mass Spectrometry object with details from the provided metadata and file path.

        Parameters:
        ----------
        grouped_metadata : object
            Metadata for the grouped data (the columns in the CSV that are grouped together because they are 
            the same for each biosample).
        wf_metadata : object
            Metadata for the rest of the data that is not grouped (the columns in the CSV that are not 
             grouped together).

        Returns:
        -------
        object
            A Mass Spectrometry NMDC object.
        """
        return self.generate_mass_spectrometry(
            file_path=Path(grouped_metadata.raw_data_file),
            instrument_name=wf_metadata.instrument_used,
            sample_id=grouped_metadata.biosample_id,
            raw_data_id="nmdc:placeholder",
            study_id=grouped_metadata.nmdc_study,
            processing_institution=grouped_metadata.processing_institution,
            mass_spec_config_name=wf_metadata.mass_spec_config_name,
            lc_config_name=wf_metadata.lc_config_name,
            start_date=wf_metadata.instrument_analysis_start_date,
            end_date=wf_metadata.instrument_analysis_end_date)

    def generate_raw_data_object(self, grouped_metadata: object, mass_spec_obj: object) -> object:
        """
        Generates a Raw Data object based on metadata and a Mass Spectrometry object.

        This method creates a Raw Data object using the file path and metadata.

        Parameters:
        ----------
        grouped_metadata : object
            Metadata for the grouped data.
        mass_spec_obj : object
            The Mass Spectrometry object that generated this raw data.

        Returns:
        -------
        object
            A Raw Data NMDC object.
        """

        return self.generate_data_object(
            file_path=Path(grouped_metadata.raw_data_file),
            data_category=self.raw_data_category,
            data_object_type=self.raw_data_obj_type,
            description=self.raw_data_obj_desc,
            base_url=self.raw_data_url,
            was_generated_by=mass_spec_obj.id,
            alternative_id=grouped_metadata.raw_data_object_alt_id
        )

    def generate_metab_analysis_object(self, grouped_metadata: object, wf_metadata: object,
                                       raw_data_obj: object, masss_spec_obj: object) -> object:
        """
        Generates a Metabolomics Analysis object based on metadata and related objects.

        This method creates a Metabolomics Analysis object with details from the provided metadata and objects.

        Parameters:
        ----------
        grouped_metadata : object
            Metadata for the grouped data.
        wf_metadata : object
            Metadata for the rest of the data that is not grouped (the columns in the CSV that are not 
             grouped together).
        raw_data_obj : object
            The Raw Data object associated with this analysis.
        masss_spec_obj : object
            The Mass Spectrometry object that generated this analysis.

        Returns:
        -------
        object
            A Metabolomics Analysis NMDC object.
        """
        return self.generate_metabolomics_analysis(
            cluster_name=wf_metadata.execution_resource,
            raw_data_id=raw_data_obj.id,
            data_gen_id=masss_spec_obj.id,
            processed_data_id="nmdc:placeholder",
            processing_institution=grouped_metadata.processing_institution
        )

    def generate_processed_data_objects(self, wf_metadata: object, metab_analysis_obj: object, data_obj_set: list) -> list:
        """
        Generates Processed Data objects based on workflow metadata and a Metabolomics Analysis object.

        This method creates Processed Data objects for various file types (e.g., TOML, CSV, HDF5) found
        in the directory specified by the workflow metadata. It adds the generated objects to the data 
        object set and returns a list of IDs for the created Processed Data objects.

        Parameters:
        ----------
        wf_metadata : object
            Metadata for the rest of the data that is not grouped (the columns in the CSV that are not 
             grouped together including the processed data directories.
        metab_analysis_obj : object
            The Metabolomics Analysis object that generated these processed data files.
        data_obj_set : list
            The list to which the generated Processed Data objects will be appended.

        Returns:
        -------
        list
            A list of IDs for the generated Processed Data objects.

        Notes:
        -----
        - This method assumes that `wf_metadata.processed_data_dir` contains the directory path where processed
        data files are stored.
        - The method processes files with specific extensions ('toml', 'csv', 'hdf5') and creates appropriate
        data objects based on these extensions.
        - The `data_obj_set` list is updated with the newly created Processed Data objects.
        """

        processed_data_paths = Path(
            wf_metadata.processed_data_dir).glob('**/*')
        processed_data = []

        for file in processed_data_paths:
            file_type = file.suffixes
            if file_type:
                file_type = file_type[0].lstrip('.')

                if file_type == 'toml':
                    ProcessedDataObjectWfConfig = self.generate_data_object(
                        file_path=file,
                        data_category=self.wf_config_process_data_category,
                        data_object_type=self.wf_config_process_data_obj_type,
                        description=self.wf_config_process_data_description,
                        base_url=self.process_data_url,
                        was_generated_by=metab_analysis_obj.id
                    )

                    data_obj_set.append(ProcessedDataObjectWfConfig)
                    processed_data.append(ProcessedDataObjectWfConfig.id)

                elif file_type == 'csv':
                    ProcessedDataObjectCsv = self.generate_data_object(
                        file_path=file,
                        data_category=self.no_config_process_data_category,
                        data_object_type=self.no_config_process_data_obj_type,
                        description=self.csv_process_data_description,
                        base_url=self.process_data_url,
                        was_generated_by=metab_analysis_obj.id
                    )

                    data_obj_set.append(ProcessedDataObjectCsv)
                    processed_data.append(ProcessedDataObjectCsv.id)

                elif file_type == 'hdf5':
                    ProcessedDataObjectHdf5 = self.generate_data_object(
                        file_path=file,
                        data_category=self.no_config_process_data_category,
                        data_object_type=self.hdf5_process_data_obj_type,
                        description=self.hdf5_process_data_description,
                        base_url=self.process_data_url,
                        was_generated_by=metab_analysis_obj.id
                    )

                    data_obj_set.append(ProcessedDataObjectHdf5)
                    processed_data.append(ProcessedDataObjectHdf5.id)

        return processed_data
