import unittest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock
from sdk.main import app
from sdk.db_connector import DBConnector

class TestGetLoansByWalletId(unittest.TestCase):

    def setUp(self):
        self.client = TestClient(app)
        self.mock_db = MagicMock(DBConnector)

    def test_get_loans_by_wallet_id_success(self):
        # Mock the database response
        self.mock_db.get_loan_state.return_value = {
            "collateral": 1000,
            "debt": 500,
            "deposit": 200,
        }

        # Test with valid parameters
        response = self.client.get("/loan_data_by_wallet_id?wallet_id=test_wallet&protocol_name=test_protocol")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["wallet_id"], "test_wallet")
        self.assertEqual(data["protocol_name"], "test_protocol")
        self.assertEqual(data["collateral"], 1000)
        self.assertEqual(data["debt"], 500)
        self.assertEqual(data["deposit"], 200)

    def test_get_loans_by_wallet_id_not_found(self):
        # Mock the database response when no data is found
        self.mock_db.get_loan_state.return_value = None

        # Test with invalid wallet_id
        response = self.client.get("/loan_data_by_wallet_id?wallet_id=invalid_wallet&protocol_name=test_protocol")
        self.assertEqual(response.status_code, 404)
        error_detail = response.json()["detail"]
        self.assertEqual(error_detail, "No data found for user invalid_wallet in protocol test_protocol")

    def test_get_loans_by_wallet_id_internal_server_error(self):
        # Mock an internal server error in database operation
        self.mock_db.get_loan_state.side_effect = Exception("Database connection error")

        # Test with valid parameters
        response = self.client.get("/loan_data_by_wallet_id?wallet_id=test_wallet&protocol_name=test_protocol")
        self.assertEqual(response.status_code, 500)
        error_detail = response.json()["detail"]
        self.assertEqual(error_detail, "Internal server error: Database connection error")


