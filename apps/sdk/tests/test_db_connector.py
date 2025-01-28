import unittest
from unittest.mock import MagicMock, patch

from db_connector import DBConnector  # Assuming the class is saved in db_connector.py


def normalize_sql(query):
    return " ".join(query.split())


class TestDBConnector(unittest.TestCase):
    @patch("db_connector.psycopg2.connect")
    def setUp(self, mock_connect):
        """Set up the mock connection and cursor for tests."""
        # Mock connection and cursor
        self.mock_conn = MagicMock()
        self.mock_cursor = MagicMock()
        self.mock_conn.cursor.return_value = self.mock_cursor
        mock_connect.return_value = self.mock_conn

        # Initialize DBConnector
        self.db_connector = DBConnector()

    def tearDown(self):
        """Close the connection after tests."""
        self.db_connector.close_connection()

    def test_get_user_debt(self):
        """Test the get_user_debt method."""
        # Mock cursor fetchone result
        self.mock_cursor.fetchone.return_value = (100.5,)

        # Call the method
        result = self.db_connector.get_user_debt(
            protocol_id="protocol1", wallet_id="wallet1", start_block=10, end_block=20
        )

        # Assertions
        self.mock_cursor.execute.assert_called_once_with(
            normalize_sql(
                """
                SELECT debt FROM loan_state
                WHERE protocol_id = %s AND "user" = %s AND block >= %s AND block <= %s
                ORDER BY timestamp DESC LIMIT 1;
            """
            ),
            ("protocol1", "wallet1", 10, 20),
        )
        self.assertEqual(result, 100.5)

    def test_get_user_collateral(self):
        """Test the get_user_collateral method."""
        # Mock cursor fetchone result
        self.mock_cursor.fetchone.return_value = (200.75,)

        # Call the method
        result = self.db_connector.get_user_collateral(
            protocol_id="protocol2",
            wallet_id="wallet2",
            start_block=None,
            end_block=None,
        )

        # Assertions
        self.mock_cursor.execute.assert_called_once_with(
            normalize_sql(
                """
                SELECT collateral FROM loan_state
                WHERE protocol_id = %s AND "user" = %s
                ORDER BY timestamp DESC LIMIT 1;
            """
            ),
            ("protocol2", "wallet2"),
        )
        self.assertEqual(result, 200.75)

    def test_get_loan_state(self):
        """Test the get_loan_state method."""
        # Mock cursor fetchone result
        self.mock_cursor.fetchone.return_value = ("active",)

        # Call the method
        result = self.db_connector.get_loan_state(
            protocol_id="protocol3", wallet_id="wallet3", start_block=5, end_block=15
        )

        # Assertions
        self.mock_cursor.execute.assert_called_once_with(
            normalize_sql(
                """
                SELECT * FROM loan_state
                WHERE protocol_id = %s AND "user" = %s AND block >= %s AND block <= %s
                ORDER BY timestamp DESC LIMIT 1;
            """
            ),
            ("protocol3", "wallet3", 5, 15),
        )
        self.assertEqual(result, "active")

    def test_close_connection(self):
        """Test the close_connection method."""
        # Call the close_connection method
        self.db_connector.close_connection()

        # Assertions
        self.mock_cursor.close.assert_called_once()
        self.mock_conn.close.assert_called_once()


if __name__ == "__main__":
    unittest.main()
