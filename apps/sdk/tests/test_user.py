import pytest
from fastapi.testclient import TestClient
from sdk.api.user import router
from sdk.db_connector import DBConnector
from fastapi import FastAPI

app = FastAPI()
app.include_router(router)
client = TestClient(app)


class MockDBConnector:
    def __init__(self):
        self.data = {"wallet123": {"debt": "100.50"}, "wallet456": {"debt": "200.75"}}

    def get_loan_state(self, protocol_name: str, wallet_id: str):
        return self.data.get(wallet_id)

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
    assert isinstance(data["collateral"]["debt"], float)
    assert data["collateral"]["debt"] == 100.50


def test_get_user_debt_not_found():
    response = client.get("/user/debt?wallet_id=unknown_wallet&protocol_name=zkLend")
    assert response.status_code == 404
    assert "No data found for wallet unknown_wallet" in response.json()["detail"]


def test_get_user_debt_invalid_data():
    response = client.get("/user/debt?wallet_id=wallet456&protocol_name=zkLend")
    assert response.status_code == 200
    data = response.json()
    assert data["wallet_id"] == "wallet456"
    assert data["protocol_name"] == "zkLend"
    assert data["collateral"]["debt"] == 200.75
    assert isinstance(data["collateral"]["debt"], float)
