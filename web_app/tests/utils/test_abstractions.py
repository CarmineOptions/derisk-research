import pytest
import requests
from unittest.mock import patch, Mock
from utils.abstractions import AbstractionAPIConnector


class TestAbstractionAPIConnector:
    @pytest.fixture(autouse=True)
    def setup_class(self):
        AbstractionAPIConnector.API_URL = "https://fakeapi.com"

    @patch('requests.get')
    def test_send_get_request_positive(self, mock_get):
        # Setup
        mock_response = Mock()
        expected_dict = {"key": "value"}
        mock_response.json.return_value = expected_dict
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        # Execute
        response = AbstractionAPIConnector.send_get_request('/test', params={'q': 'test'})

        # Verify
        mock_get.assert_called_once_with("https://fakeapi.com/test", params={'q': 'test'})
        assert response == expected_dict, "The response should match the expected JSON"

    @patch('requests.get')
    def test_send_get_request_negative(self, mock_get):
        # Setup
        mock_get.side_effect = requests.RequestException("Error occurred")

        # Execute
        response = AbstractionAPIConnector.send_get_request('/test')

        # Verify
        assert 'error' in response, "Error key should be in response"
        assert response['error'] == "Error occurred", "Error message should match the raised exception"

    @patch('requests.post')
    def test_send_post_request_positive(self, mock_post):
        # Setup
        mock_response = Mock()
        expected_dict = {"result": "success"}
        mock_response.json.return_value = expected_dict
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        # Execute
        response = AbstractionAPIConnector.send_post_request('/submit', json={'key': 'value'})

        # Verify
        mock_post.assert_called_once_with("https://fakeapi.com/submit", data=None, json={'key': 'value'})
        assert response == expected_dict, "The response should match the expected JSON"

    @patch('requests.post')
    def test_send_post_request_negative(self, mock_post):
        # Setup
        mock_post.side_effect = requests.RequestException("Posting failed")

        # Execute
        response = AbstractionAPIConnector.send_post_request('/submit', data={'form': 'data'})

        # Verify
        assert 'error' in response, "Error key should be in the response"
        assert response['error'] == "Posting failed", "Error message should match the raised exception"

