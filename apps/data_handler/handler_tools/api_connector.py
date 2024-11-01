""" Module for making HTTP GET requests to the DeRisk API using the `requests` library. """
import os

import requests
from dotenv import load_dotenv

load_dotenv()


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

    @staticmethod
    def _validate_data(from_address: str, min_block_number: int, max_block_number: int) -> None:
        """
        Check the data for the DeRisk API.
        :param from_address: From address.
        :param min_block_number: block number.
        :param max_block_number: max block number.
        :return: None
        """
        if not isinstance(from_address, str):
            raise TypeError("from_address must be a string")
        if not isinstance(min_block_number, int):
            raise TypeError("min_block_number must be an integer")
        if not isinstance(max_block_number, int):
            raise TypeError("max_block_number must be an integer")

    def get_data(self, from_address: str, min_block_number: int, max_block_number: int) -> dict:
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
        self._validate_data(from_address, min_block_number, max_block_number)
        params = {
            "from_address": from_address,
            "min_block_number": min_block_number,
            "max_block_number": max_block_number,
        }
        try:
            response = requests.get(self.api_url, params=params)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            return {"error": str(e)}
