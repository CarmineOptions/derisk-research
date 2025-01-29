import pytest
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
import json
import pandas as pd
from sdk.api.user import app, router
from sdk.schemas.schemas import UserCollateralResponse, UserDepositResponse
from sdk.db_connector import DBConnector

app.include_router(router)
client = TestClient(app)


@pytest.fixture
def mock_user_data():
    return {
        "user": "0x123",
        "protocol_id": "zkLend",
        "deposit": json.dumps({"USDC": "1000", "ETH": "2.5"}),
        "debt": json.dumps({"USDC": "500", "ETH": "1.0"}),
        "timestamp": "2024-01-29T00:00:00Z",
    }


@pytest.fixture
def mock_db_connector(monkeypatch):
    mock_db = Mock(spec=DBConnector)

    def mock_init(*args, **kwargs):
        return mock_db

    monkeypatch.setattr("sdk.api.user.DBConnector", mock_init)
    return mock_db


@pytest.mark.asyncio
async def test_get_user_debt(mock_db_connector):
    wallet_id = "0x123"
    protocol_id = "zkLend"

    mock_db_connector.get_loan_state.return_value = {
        "collateral": json.dumps({"USDC": "1000", "ETH": "2.5"}),
        "debt": json.dumps({"USDC": "500", "ETH": "1.0"}),
        "deposit": json.dumps({"USDC": "1000", "ETH": "2.5"}),
    }

    response = client.get(f"/user/debt?wallet_id={wallet_id}&protocol_id={protocol_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["wallet_id"] == wallet_id
    assert data["protocol_name"] == protocol_id
    assert "collateral" in data
    assert isinstance(data["collateral"], dict)
    mock_db_connector.get_loan_state.assert_called_once_with(protocol_id, wallet_id)


@pytest.mark.asyncio
async def test_get_user_debt_not_found(mock_db_connector):
    mock_db_connector.get_loan_state.return_value = None

    response = client.get("/user/debt?wallet_id=0xnonexistent&protocol_id=zkLend")

    assert response.status_code == 404
    assert "No data found" in response.json()["detail"]


@pytest.mark.asyncio
async def test_get_user_deposit(monkeypatch, mock_user_data):
    mock_df = pd.DataFrame([mock_user_data])
    monkeypatch.setattr("sdk.api.user.mock_data", mock_df)

    response = client.get(f"/user/deposit?wallet_id={mock_user_data['user']}")

    assert response.status_code == 200
    data = response.json()
    assert data["wallet_id"] == mock_user_data["user"]
    assert "deposit" in data
    assert isinstance(data["deposit"], dict)

    expected_deposit = json.loads(mock_user_data["deposit"])

    # Normalize both expected and received data
    def normalize_values(deposit_dict):
        return {
            k: (
                f"{float(v):.1f}"
                if isinstance(v, (int, float)) or v.replace(".", "", 1).isdigit()
                else v
            )
            for k, v in deposit_dict.items()
        }

    expected_deposit = normalize_values(expected_deposit)
    received_deposit = normalize_values(data["deposit"])

    assert received_deposit == expected_deposit


@pytest.mark.asyncio
async def test_get_user_deposit_not_found(monkeypatch):
    mock_df = pd.DataFrame(columns=["user", "deposit", "timestamp"])
    monkeypatch.setattr("sdk.api.user.mock_data", mock_df)

    response = client.get("/user/deposit?wallet_id=0xnonexistent")

    assert response.status_code == 404
    assert "No deposit data found" in response.json()["detail"]


@pytest.mark.asyncio
async def test_get_user_debt_invalid_json(mock_db_connector):
    mock_db_connector.get_loan_state.return_value = {
        "collateral": "invalid json",
        "debt": "{}",
        "deposit": "{}",
    }

    response = client.get("/user/debt?wallet_id=0x123&protocol_id=zkLend")

    assert response.status_code == 200
    data = response.json()
    assert data["collateral"] == {}
