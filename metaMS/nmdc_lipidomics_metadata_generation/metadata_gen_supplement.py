import requests
from dataclasses import dataclass

# TODO: Update og_url to be regular nmdc api url when berkeley is implemented
# TODO: Update GroupedMetadata.processing_type when sample processing is added.


class ApiInfoRetriever:
    """
    A class to retrieve API information from a specified collection.

    Attributes:
    ----------
    collection_name : str
        The name of the collection from which to retrieve information.

    Methods:
    -------
    get_id_by_name_from_collection(name_field_value: str) -> str:
        Retrieves the ID of an entry from the collection based on the given name field value.
    """

    def __init__(self, collection_name: str):
        """
        Initializes the ApiInfoRetriever with the specified collection name.

        Parameters:
        ----------
        collection_name : str
            The name of the collection to be used for API queries.
        """
        self.collection_name = collection_name

    def get_id_by_name_from_collection(self, name_field_value: str):
        """
        Retrieves the ID of an entry from the collection using the name field value.

        Constructs a query to the API to filter the collection based on the given name field value,
        retrieves the response, and extracts the ID of the first entry in the response.

        Parameters:
        ----------
        name_field_value : str
            The value of the name field to filter the collection.

        Returns:
        -------
        str
            The ID of the entry retrieved from the collection.
        """
        # trim trailing white spaces
        name_field_value = name_field_value.rstrip()

        filter = f'{{"name": "{name_field_value}"}}'
        field = "id"

        og_url = f'https://api-berkeley.microbiomedata.org/nmdcschema/{self.collection_name}?&filter={filter}&projection={field}'
        resp = requests.get(og_url)
        data = resp.json()
        identifier = data['resources'][0]['id']

        return identifier


@ dataclass
class GroupedMetadata:
    """
    Data class for holding grouped metadata information.

    Attributes:
    ----------
    biosample_id : str
        Identifier for the biosample.
    processing_type : str
        Type of processing applied to the data (e.g. MPLEX).
    raw_data_file : str
        Path or name of the raw data file.
    raw_data_object_alt_id : str
        Alternative identifier for the raw data object.
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

    Attributes:
    ----------
    processed_data_dir : str
        Directory containing processed data files.
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
    raw_data_object_alt_id: str
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

    Attributes:
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
