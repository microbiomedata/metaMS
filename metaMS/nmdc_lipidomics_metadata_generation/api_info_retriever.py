import requests
from dataclasses import dataclass

class ApiInfoRetriever:
    """
    A class to retrieve API information from a specified collection.

    This class provides functionality to query an API and retrieve information
    from a specified collection based on a name field value.

    Attributes
    ----------
    collection_name : str
        The name of the collection from which to retrieve information.

    Methods
    -------
    get_id_by_name_from_collection(name_field_value: str) -> str:
        Retrieves the ID of an entry from the collection based on the given name field value.
    """

    def __init__(self, collection_name: str):
        """
        Initialize the ApiInfoRetriever with the specified collection name.

        Parameters
        ----------
        collection_name : str
            The name of the collection to be used for API queries.
        """
        self.collection_name = collection_name

    def get_id_by_name_from_collection(self, name_field_value: str) -> str:
        """
        Retrieve the ID of an entry from the collection using the name field value.

        This method constructs a query to the API to filter the collection based on the
        given name field value, retrieves the response, and extracts the ID of the first
        entry in the response.

        Parameters
        ----------
        name_field_value : str
            The value of the name field to filter the collection.

        Returns
        -------
        str
            The ID of the entry retrieved from the collection.

        Raises
        ------
        IndexError
            If no matching entry is found in the collection.
        requests.RequestException
            If there's an error in making the API request.
        """
        # Trim trailing white spaces
        name_field_value = name_field_value.strip()

        filter_param = f'{{"name": "{name_field_value}"}}'
        field = "id"

        og_url = f'https://api.microbiomedata.org/nmdcschema/{self.collection_name}?&filter={filter_param}&projection={field}'
        
        try:
            resp = requests.get(og_url)
            resp.raise_for_status()  # Raises an HTTPError for bad responses
            data = resp.json()
            identifier = data['resources'][0]['id']
            return identifier
        except requests.RequestException as e:
            raise requests.RequestException(f"Error making API request: {e}")
        except (KeyError, IndexError) as e:
            raise IndexError(f"No matching entry found for '{name_field_value}': {e}")

    def check_if_ids_exist(self, ids: list) -> bool:
        """
        Check if the IDs exist in the collection.

        This method constructs a query to the API to filter the collection based on the given IDs, and checks if all IDs exist in the collection.

        Parameters
        ----------
        ids : list
            A list of IDs to check if they exist in the collection.

        Returns
        -------
        bool
            True if all IDs exist in the collection, False otherwise.

        Raises
        ------
        requests.RequestException
            If there's an error in making the API request.
        """
        ids_test = list(set(ids))
        ids_test = [id.replace('"', "'") for id in ids_test]
        ids_test_str = ", ".join(f'"{id}"' for id in ids_test)
        match_id_field = "id"  # Replace with the actual field name if different
        filter_param = f'{{"{match_id_field}": {{"$in": [{ids_test_str}]}}}}'
        og_url = f'https://api.microbiomedata.org/nmdcschema/{self.collection_name}?&filter={filter_param}&projection={match_id_field}'
        
        try:
            resp = requests.get(og_url)
            resp.raise_for_status()  # Raises an HTTPError for bad responses
            data = resp.json()
            if not len(data['resources']) != len(ids_test):
                return False
        except requests.RequestException as e:
            raise requests.RequestException(f"Error making API request: {e}")

        return True