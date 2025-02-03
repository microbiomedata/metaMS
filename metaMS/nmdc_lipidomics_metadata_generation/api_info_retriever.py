import requests
import json
import logging


class NMDCAPIInterface:
    """
    A generic interface for the NMDC runtime API.

    Attributes
    ----------
    base_url : str
        The base URL for the NMDC runtime API.

    Methods
    -------
    validate_json(json_path: str) -> None:
        Validates a json file using the NMDC json validate endpoint.
    """

    def __init__(self):
        self.base_url = "https://api.microbiomedata.org"

    def validate_json(self, json_path) -> None:
        """
        Validates a json file using the NMDC json validate endpoint.

        If the validation passes, the method returns without any side effects.

        Parameters
        ----------
        json_path : str
            The path to the json file to be validated.

        Raises
        ------
        Exception
            If the validation fails.
        """
        with open(json_path, "r") as f:
            data = json.load(f)

        # Check that the term "placeholder" is not present anywhere in the json
        if "placeholder" in json.dumps(data):
            raise Exception("Placeholder values found in json!")

        url = f"{self.base_url}/metadata/json:validate"
        headers = {"accept": "application/json", "Content-Type": "application/json"}
        response = requests.post(url, headers=headers, json=data)
        if response.text != '{"result":"All Okay!"}' or response.status_code != 200:
            logging.error(f"Request failed with response {response.text}")
            raise Exception("Validation failed")


class ApiInfoRetriever(NMDCAPIInterface):
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
        super().__init__()
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

        og_url = f"{self.base_url}/nmdcschema/{self.collection_name}?&filter={filter_param}&projection={field}"

        try:
            resp = requests.get(og_url)
            resp.raise_for_status()  # Raises an HTTPError for bad responses
            data = resp.json()
            identifier = data["resources"][0]["id"]
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
        for id in ids_test:
            filter_param = f'{{"id": "{id}"}}'
            field = "id"

            og_url = f"{self.base_url}/nmdcschema/{self.collection_name}?&filter={filter_param}&projection={field}"

            try:
                resp = requests.get(og_url)
                resp.raise_for_status()  # Raises an HTTPError for bad responses
                data = resp.json()
                if len(data["resources"]) == 0:
                    print(f"ID {id} not found")
                    return False
            except requests.RequestException as e:
                raise requests.RequestException(f"Error making API request: {e}")

        return True
