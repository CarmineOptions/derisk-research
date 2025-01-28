import unittest
from fastapi import FastAPI, APIRouter, HTTPException, Depends
from fastapi.testclient import TestClient
from unittest.mock import patch
from pydantic import BaseModel
from typing import Dict


class UserLoanByWalletParams(BaseModel):
    wallet_id: str
    protocol_name: str

class UserLoanByWalletResponse(BaseModel):
    wallet_id: str
    protocol_name: str
    collateral: Dict[str, float]
    debt: Dict[str, float]
    deposit: Dict[str, float]

# Sample loan response data
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

# Endpoint parameters
endpoint_params = {
    "wallet_id": "0x042c5b7dcb2706984b2b035e76cf5b4db95667b25eebd1aa057887ef9ad5fca8",
    "protocol_name": "protocolA"
}

# Create FastAPI app and router
app = FastAPI()
loan_router = APIRouter()

# DBConnector mock class (replace with real DB logic)
class MockDBConnector:
    async def get_loan_state(self, wallet_id: str, protocol_id: str):
        return {
            "collateral": loan_response["collateral"],
            "debt": loan_response["debt"],
            "deposit": loan_response["deposit"]
        }

# Loan endpoint
@loan_router.get("/loan_data_by_wallet_id", response_model=UserLoanByWalletResponse)
async def get_loans_by_wallet_id(
    params: UserLoanByWalletParams = Depends(), db: MockDBConnector = Depends()
):
    try:
        loan_states = await db.get_loan_state(
            wallet_id=params.wallet_id,
            protocol_id=params.protocol_name,
        )
        if not loan_states:
            raise HTTPException(
                status_code=404,
                detail=f"No data found for user {params.wallet_id} in protocol {params.protocol_name}",
            )
        return UserLoanByWalletResponse(
            wallet_id=params.wallet_id,
            protocol_name=params.protocol_name,
            collateral=loan_states["collateral"],
            debt=loan_states["debt"],
            deposit=loan_states["deposit"],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

app.include_router(loan_router)

# Initialize TestClient
client = TestClient(app)

# Test case class
class TestLoanEndpoint(unittest.TestCase):
    @patch("test_loan_state.MockDBConnector", new_callable=lambda: MockDBConnector)
    def test_get_loans_complex(self, mock_db_connector):
        # Send the GET request
        response = client.get("/loan_data_by_wallet_id", params=endpoint_params)

        # Assert the response status code
        self.assertEqual(response.status_code, 200)

        # Assert the response JSON matches the expected loan_response
        self.assertDictEqual(response.json(), loan_response)


if __name__ == "__main__":
    unittest.main()
