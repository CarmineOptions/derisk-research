import os

import requests


class DeRiskAPIConnector:
    """
    Class for making HTTP GET requests to the DeRisk API using the `requests` library.
    """

    def __init__(self):
        """
        Constructor for the DeRiskAPIConnector class.
        Raises an exception if the DERISK_API_URL environment variable is not set.
        """
        self.api_url = os.getenv("DERISK_API_URL", None)
        if self.api_url is None:
            raise ValueError("DERISK_API_URL environment variable is not set")

    def get_data(
        self, from_address: str, min_block_number: int, max_block_number: int
    ) -> dict:
        """
        Retrieves data from the DeRisk API for a given address and block number range.

        :param from_address: The address of the contract or account on StarkNet.
        :type from_address: str
        :param min_block_number: The minimum block number from which to retrieve events.
        :type min_block_number: int
        :param max_block_number: The maximum block number to which to retrieve events.
        :type max_block_number: int
        :return: A dictionary containing the API response data.
        :rtype: dict

        Example usage:
        DeRiskAPIConnector.get_data(
            '0x04c0a5193d58f74fbace4b74dcf65481e734ed1714121bdc571da345540efa05',
            630000,
            631000
        )
        """
        params = {
            "from_address": from_address,
            "min_block_number": min_block_number,  # start with 0 (just first time)
            "max_block_number": max_block_number,  # to endless (just first time)
        }
        try:
            response = requests.get(self.api_url, params=params)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            return {"error": str(e)}
