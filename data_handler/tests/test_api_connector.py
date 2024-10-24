import os
import unittest
from unittest.mock import patch, MagicMock
from requests.exceptions import RequestException
from handler_tools.api_connector import DeRiskAPIConnector

class TestDeRiskAPIConnector(unittest.TestCase):
    @patch.dict(os.environ, {"DERISK_API_URL": "https://api.derisk.io"})
    def test_api_connector_instantiates_successfully(self):
        """Test that DeRiskAPIConnector initializes correctly when the API URL is set."""
        connector = DeRiskAPIConnector()
        self.assertEqual(connector.api_url, "https://api.derisk.io")

    @patch.dict(os.environ, {}, clear=True)
    def test_api_connector_raises_value_error_exception(self):
        """Test that DeRiskAPIConnector raises a ValueError when the API URL is not set."""
        with self.assertRaises(ValueError):
            DeRiskAPIConnector()

    @patch.dict(os.environ, {"DERISK_API_URL": "https://api.derisk.io"})
    @patch('requests.get')
    def test_get_data_returns_some_data(self, mock_get):
        """Test that DeRiskAPIConnector.get_data() returns data when the response is successful."""
        # Mock positive response
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"status": "success", "data": "some_data"}
        mock_get.return_value = mock_response

        connector = DeRiskAPIConnector()
        result = connector.get_data(
            '0x04c0a5193d58f74fbace4b74dcf65481e734ed1714121bdc571da345540efa05',
            630000,
            631000
        )

        self.assertEqual(result, {"status": "success", "data": "some_data"})
        mock_get.assert_called_once_with(
            "https://api.derisk.io",
            params={
                "from_address": '0x04c0a5193d58f74fbace4b74dcf65481e734ed1714121bdc571da345540efa05',
                "min_block_number": 630000,
                "max_block_number": 631000
            }
        )

        @patch.dict(os.environ, {"DERISK_API_URL": "https://api.derisk.io"})
        @patch('requests.get')
        def test_get_data_negative(self, mock_get):
            """Test that DeRiskAPIConnector.get_data() handles request exceptions properly."""
            # Mock negative response
            mock_get.side_effect = RequestException("Network error")

            connector = DeRiskAPIConnector()
            result = connector.get_data(
                '0x04c0a5193d58f74fbace4b74dcf65481e734ed1714121bdc571da345540efa05',
                630000,
                631000
            )

            self.assertEqual(result, {"error": "Network error"})
