import requests
from dataclasses import dataclass

# TODO: Update og_url to be regular nmdc api url when berkeley is implemented

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
