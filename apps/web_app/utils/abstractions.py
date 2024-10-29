from abc import ABC

import requests


class AbstractionAPIConnector(ABC):
    """
    Abstract base class for making HTTP GET and POST requests using the `requests` library.
    """

    API_URL: str = None

    @classmethod
    def send_get_request(cls, endpoint: str, params=None) -> dict:
        """
        Send a GET request to the specified endpoint with optional parameters.

        :param endpoint: The endpoint URL where the GET request will be sent.
        :type endpoint: str
        :param params: Dictionary of URL parameters to append to the URL.
        :type params: dict, optional
        :return: A JSON response from the API if the request is successful; otherwise, a dictionary with an "error" key
        containing the error message.
        :rtype: dict
        """
        try:
            response = requests.get(f"{cls.API_URL}{endpoint}", params=params)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            return {"error": str(e)}

    @classmethod
    def send_post_request(cls, endpoint: str, data=None, json=None) -> dict:
        """
        Send a POST request to the specified endpoint with either form data or a JSON payload.

        :param endpoint: The endpoint URL where the POST request will be sent.
        :type endpoint: str
        :param data: Dictionary of form data to send in the request body.
        :type data: dict, optional
        :param json: Dictionary of JSON data to send in the request body.
        :type json: dict, optional
        :return: A JSON response from the API if the request is successful; otherwise, a dictionary with an "error" key
        containing the error message.
        :rtype: dict
        """
        try:
            response = requests.post(f"{cls.API_URL}{endpoint}", data=data, json=json)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            return {"error": str(e)}
