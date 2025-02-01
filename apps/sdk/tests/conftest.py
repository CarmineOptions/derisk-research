import pytest
from unittest.mock import MagicMock, patch
from db_connector import DBConnector


@pytest.fixture(scope="function")
def mock_db_connector():
    """
    Fixture to create a mock DBConnector instance.
    """
    with patch("db_connector.psycopg2.connect") as mock_connect:
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        db_connector = DBConnector()
        yield db_connector
        db_connector.close_connection()
