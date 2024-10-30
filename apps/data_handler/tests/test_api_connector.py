"""Tests for the DeRiskAPIConnector class.

Validates API connector initialization, data retrieval, and error handling functionality.
"""

import os
import unittest
from unittest.mock import MagicMock, patch

from data_handler.handler_tools.api_connector import DeRiskAPIConnector
from requests.exceptions import HTTPError, RequestException


class TestDeRiskAPIConnector(unittest.TestCase):
    """Test suite for DeRiskAPIConnector functionality.
    
    Covers initialization, data retrieval, and error handling scenarios.
    """
    DERISK_API_URL = "https://api.derisk.io"

    @patch.dict(os.environ, {"DERISK_API_URL": DERISK_API_URL})
    def test_api_connector_instantiates_successfully(self):
        """Test that DeRiskAPIConnector initializes correctly when the API URL is set."""
        connector = DeRiskAPIConnector()
        self.assertEqual(connector.api_url, self.DERISK_API_URL)

    @patch.dict(os.environ, {}, clear=True)
    def test_api_connector_raises_value_error_exception(self):
        """Test that DeRiskAPIConnector raises a ValueError when the API URL is not set."""
        with self.assertRaises(ValueError):
            DeRiskAPIConnector()

    @patch.dict(os.environ, {"DERISK_API_URL": DERISK_API_URL})
    @patch("requests.get")
    def test_get_data_success(self, mock_get):
        """Test that DeRiskAPIConnector.get_data() returns data on a successful request."""
        json_data = {"status": "success", "data": "some_data"}
        mock_get.return_value = MagicMock(
            status_code=200, json=MagicMock(return_value=json_data)
        )

        connector = DeRiskAPIConnector()
        test_addr = "0x04c0a5193d58f74fbace4b74dcf65481e734ed1714121bdc571da345540efa05"
        result = connector.get_data(test_addr, 630000, 631000)

        self.assertEqual(result, json_data)
        mock_get.assert_called_once_with(
            self.DERISK_API_URL,
            params={
                "from_address": test_addr,
                "min_block_number": 630000,
                "max_block_number": 631000,
            },
        )

    @patch.dict(os.environ, {"DERISK_API_URL": DERISK_API_URL})
    @patch("requests.get")
    def test_get_data_handles_request_exception(self, mock_get):
        """Test that get_data() returns an error dictionary on a RequestException."""
        mock_get.side_effect = RequestException("Mocked request exception")

        connector = DeRiskAPIConnector()
        test_addr = "0x04c0a5193d58f74fbace4b74dcf65481e734ed1714121bdc571da345540efa05"
        result = connector.get_data(test_addr, 630000, 631000)

        self.assertIn("error", result)
        self.assertEqual(result["error"], "Mocked request exception")

    @patch.dict(os.environ, {"DERISK_API_URL": DERISK_API_URL})
    def test_get_data_type_errors(self):
        """Test that get_data() raises TypeError for invalid types."""
        connector = DeRiskAPIConnector()
        test_addr = "0x04c0a5193d58f74fbace4b74dcf65481e734ed1714121bdc571da345540efa05"

        # Invalid from_address type
        with self.assertRaises(TypeError):
            connector.get_data(123456, 630000, 631000)

        # Invalid min_block_number type
        with self.assertRaises(TypeError):
            connector.get_data(test_addr, "invalid", 631000)

        # Invalid max_block_number type
        with self.assertRaises(TypeError):
            connector.get_data(test_addr, 630000, "invalid")