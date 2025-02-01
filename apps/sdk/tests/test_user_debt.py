import pytest
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from fastapi import FastAPI
import pandas as pd
import json
from sdk.schemas.schemas import UserDebtResponseModel


mock_df = pd.DataFrame(
    {
        "user": ["wallet123", "wallet456"],
        "protocol_id": ["zkLend", "zkLend"],
        "debt": ['{"USDC": 100.50}', '{"USDC": 200.75}'],
        "deposit": ['{"USDC": 100.0}', '{"USDC": 200.0}'],
        "timestamp": ["2023-01-01", "2023-02-01"],
    }
)


with patch("pandas.read_csv", return_value=mock_df):
    from sdk.api.user import router
    from sdk.db_connector import DBConnector


app = FastAPI()
app.include_router(router)
client = TestClient(app)


class MockDBConnector:
    def __init__(self):
        self.mock_data = {
            "wallet123": {"USDC": 100.50},
            "wallet456": {"USDC": 200.75},
        }

    def get_user_debt(self, protocol_id: str, wallet_id: str):
        if wallet_id not in self.mock_data:
            return None
        return self.mock_data.get(wallet_id)

    def close_connection(self):
        pass


@pytest.fixture(autouse=True)
def override_db():
    app.dependency_overrides[DBConnector] = lambda: MockDBConnector()
    yield
    app.dependency_overrides = {}


def test_get_user_debt_success():
    response = client.get("/user/debt?wallet_id=wallet123&protocol_name=zkLend")
    assert response.status_code == 200
    data = response.json()
    assert data["wallet_id"] == "wallet123"
    assert data["protocol_name"] == "zkLend"
    assert isinstance(data["debt"], dict)
    assert data["debt"] == {"USDC": 100.50}


def test_get_user_debt_invalid_data():
    response = client.get("/user/debt?wallet_id=wallet456&protocol_name=zkLend")
    assert response.status_code == 200
    data = response.json()
    assert data["wallet_id"] == "wallet456"
    assert data["protocol_name"] == "zkLend"
    assert isinstance(data["debt"], dict)
    assert data["debt"] == {"USDC": 200.75}
