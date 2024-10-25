import os
import unittest
from unittest.mock import patch, MagicMock
from requests.exceptions import HTTPError
from handler_tools.api_connector import DeRiskAPIConnector

class TestDeRiskAPIConnector(unittest.TestCase):
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

    def _mock_response(self, status=200,
            content="CONTENT",
            json_data=None,
            raise_for_status=None):
        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        if raise_for_status:
            mock_resp.raise_for_status.side_effect = raise_for_status
        mock_resp.status_code = status
        mock_resp.content = content
        if json_data:
            mock_resp.json = MagicMock(
                return_value=json_data
            )
        return mock_resp
    
    @patch.dict(os.environ, {"DERISK_API_URL": DERISK_API_URL})
    @patch('requests.get')
    def test_get_data_returns_some_data(self, mock_get):
        """Test that DeRiskAPIConnector.get_data() returns data when the response is successful."""
        # Mock positive response
        json_data = {"status": "success", "data": "some_data"}
        mock_response = self._mock_response(json_data=json_data)
        mock_get.return_value = mock_response

        connector = DeRiskAPIConnector()
        result = connector.get_data(
            '0x04c0a5193d58f74fbace4b74dcf65481e734ed1714121bdc571da345540efa05',
            630000,
            631000
        )

        self.assertEqual(result, json_data)
        mock_get.assert_called_once_with(
            self.DERISK_API_URL,
            params={
                "from_address": '0x04c0a5193d58f74fbace4b74dcf65481e734ed1714121bdc571da345540efa05',
                "min_block_number": 630000,
                "max_block_number": 631000
            }
        )

    @patch.dict(os.environ, {"DERISK_API_URL": DERISK_API_URL})
    @patch('requests.get')
    def test_get_data_negative(self, mock_get):
        """Test that DeRiskAPIConnector.get_data() handles request exceptions properly."""
        # Mock negative response
        mock_response = self._mock_response(raise_for_status=500)
        mock_get.return_value = mock_response

        connector = DeRiskAPIConnector()

        with self.assertRaises(HTTPError):
            connector.get_data(
                '0x04c0a5193d58f74fbace4b74dcf65481e734ed1714121bdc571da345540efa05',
                630000,
                631000
            )


    @patch.dict(os.environ, {"DERISK_API_URL": DERISK_API_URL})
    @patch('requests.get')
    def test_get_data_failure_min_block_number(self, mock_get):
        """Test that data retrieval fails when min_block_number is None or a string"""
        connector = DeRiskAPIConnector()

        with self.assertRaises(TypeError):
            connector.get_data(
                from_address='0x04c0a5193d58f74fbace4b74dcf65481e734ed1714121bdc571da345540efa05',
                min_block_number=None,
                max_block_number=631000
            )

        with self.assertRaises(TypeError):
            connector.get_data(
                from_address='0x04c0a5193d58f74fbace4b74dcf65481e734ed1714121bdc571da345540efa05',
                min_block_number="invalid",
                max_block_number=631000
            )

    @patch.dict(os.environ, {"DERISK_API_URL": DERISK_API_URL})
    @patch('requests.get')
    def test_get_data_failure_max_block_number(self, mock_get):
        """Test that data retrieval fails when max_block_number is None or a string"""
        connector = DeRiskAPIConnector()

        with self.assertRaises(TypeError):
            connector.get_data(
                from_address='0x04c0a5193d58f74fbace4b74dcf65481e734ed1714121bdc571da345540efa05',
                min_block_number=630000,
                max_block_number=None
            )

        with self.assertRaises(TypeError):
            connector.get_data(
                from_address='0x04c0a5193d58f74fbace4b74dcf65481e734ed1714121bdc571da345540efa05',
                min_block_number=630000,
                max_block_number="invalid"
            )

    @patch.dict(os.environ, {"DERISK_API_URL": DERISK_API_URL})
    @patch('requests.get')
    def test_get_data_failure_invalid_from_address(self, mock_get):
        """Test that data retrieval fails when from_address is None or an invalid format"""
        connector = DeRiskAPIConnector()

        with self.assertRaises(TypeError):
            connector.get_data(
                from_address=None,
                min_block_number=630000,
                max_block_number=631000
            )

        with self.assertRaises(ValueError):
            connector.get_data(
                from_address="invalid_address",
                min_block_number=630000,
                max_block_number=631000
            )