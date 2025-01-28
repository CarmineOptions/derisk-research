import unittest
from fastapi import FastAPI, APIRouter
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
from db_connector import DBConnector


loan_router = APIRouter()

# Setup a test FastAPI app and include the loan router
app = FastAPI()
app.include_router(loan_router)

# Initialize TestClient
client = TestClient(app)

# Endpoint parameters and expected response
endpoint_params = {
    "wallet_id": "0x042c5b7dcb2706984b2b035e76cf5b4db95667b25eebd1aa057887ef9ad5fca8",
    "protocol_name": "protocolA"
}

loan_response = {
    "wallet_id": "0x042c5b7dcb2706984b2b035e76cf5b4db95667b25eebd1aa057887ef9ad5fca8",
    "protocol_name": "protocolA",
    "collateral": {
        "0x049d36570d4e46f48e99674bd3fcc84644ddd6b96f7c741b1562b82f9e004dc7": 5.59987142124803e16
    },
    "debt": {
        "0x053c91253bc9682c04929ca02ed00b3e423f6710d2ee7e0d5ebb06f3ecf368a8": 0.0
    },
    "deposit": {
        "0x049d36570d4e46f48e99674bd3fcc84644ddd6b96f7c741b1562b82f9e004dc7": 5.59987142124803e16,
        "0x00000000000000000000000000000000000000000000000000c4f1656259e56a": -4.17404284944524e75
    },
}

class TestLoanEndpoint(unittest.TestCase):
    @patch("apps.sdk.api.loan_state.DBConnector")
    def test_get_loans_complex(self, mock_db_connector):
        # Mocking the database response with complex data
        mock_db_connector.return_value.get_loan_state = AsyncMock(return_value={
            "collateral": loan_response["collateral"],
            "debt": loan_response["debt"],
            "deposit": loan_response["deposit"],
        })
    
        # Sending the GET request
        response = client.get("/loan_data_by_wallet_id", params=endpoint_params)
    
        # Asserting the response status code
        self.assertEqual(response.status_code, 200)
    
        # Asserting the response JSON matches the expected response
        self.assertDictEqual(response.json(), loan_response)
    


if __name__ == "__main__":
    unittest.main()


