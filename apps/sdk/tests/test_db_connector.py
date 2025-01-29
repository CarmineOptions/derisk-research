import pytest
from unittest.mock import MagicMock, patch
from sdk.db_connector import DBConnector

"""
This module contains the tests for the DBConnector.
"""



@pytest.fixture(scope="function")
def mock_db_connector():
    """
    Fixture to create a mock DBConnector instance.
    """
    with patch("sdk.db_connector.psycopg2.connect") as mock_connect:
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        db_connector = DBConnector()
        yield db_connector
        db_connector.close_connection()


def test_connect_to_db(mock_db_connector):
    """
    Test the connect_to_db method.
    """
    assert mock_db_connector.conn is not None
    assert mock_db_connector.cur is not None


def test_get_user_debt(mock_db_connector):
    """
    Test the get_user_debt method.
    """
    mock_db_connector.cur.fetchone.return_value = [100.0]
    result = mock_db_connector.get_user_debt("protocol_id", "wallet_id")
    assert result == 100.0
    mock_db_connector.cur.execute.assert_called_once_with(
        """
                SELECT debt FROM loan_state
                WHERE protocol_id = %s and "user" = %s;
            """,
        ("protocol_id", "wallet_id"),
    )


def test_get_user_debt_none(mock_db_connector):
    """
    Test the get_user_debt method when no debt is found.
    """
    mock_db_connector.cur.fetchone.return_value = None
    result = mock_db_connector.get_user_debt("protocol_id", "wallet_id")
    assert result is None


def test_get_user_collateral(mock_db_connector):
    """
    Test the get_user_collateral method.
    """
    mock_db_connector.cur.fetchone.return_value = [200.0]
    result = mock_db_connector.get_user_collateral("protocol_id", "wallet_id")
    assert result == 200.0
    mock_db_connector.cur.execute.assert_called_once_with(
        """
                SELECT collateral FROM loan_state
                WHERE protocol_id = %s and "user" = %s;
            """,
        ("protocol_id", "wallet_id"),
    )


def test_get_user_collateral_none(mock_db_connector):
    """
    Test the get_user_collateral method when no collateral is found.
    """
    mock_db_connector.cur.fetchone.return_value = None
    result = mock_db_connector.get_user_collateral("protocol_id", "wallet_id")
    assert result is None


def test_get_loan_state(mock_db_connector):
    """
    Test the get_loan_state method.
    """
    mock_db_connector.cur.fetchone.return_value = ["loan_state"]
    result = mock_db_connector.get_loan_state("protocol_id", "wallet_id")
    assert result == "loan_state"
    mock_db_connector.cur.execute.assert_called_once_with(
        """
                SELECT * FROM loan_state
                WHERE protocol_id = %s and "user" = %s;
            """,
        ("protocol_id", "wallet_id"),
    )


def test_get_loan_state_none(mock_db_connector):
    """
    Test the get_loan_state method when no loan state is found.
    """
    mock_db_connector.cur.fetchone.return_value = None
    result = mock_db_connector.get_loan_state("protocol_id", "wallet_id")
    assert result is None


def test_close_connection(mock_db_connector):
    """
    Test the close_connection method.
    """
    mock_db_connector.close_connection()
    mock_db_connector.cur.close.assert_called_once()
    mock_db_connector.conn.close.assert_called_once()
