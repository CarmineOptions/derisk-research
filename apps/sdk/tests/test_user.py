import pytest
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
import json
from sdk.api.user import router, get_user_debt
from sdk.schemas.schemas import UserCollateralResponse
from sdk.db_connector import DBConnector
from fastapi import FastAPI

app = FastAPI()
app.include_router(router)
client = TestClient(app)


def normalize_values(d):
    """Ensure consistent number formatting"""
    return {
        k: str(int(float(v))) if str(v).endswith(".0") else str(v) for k, v in d.items()
    }


@pytest.fixture
def mock_db():
    with patch("sdk.db_connector.DBConnector") as mock:
        mock_instance = Mock()
        mock.return_value = mock_instance
        mock_instance.get_loan_state.return_value = {}
        mock_instance.close_connection.return_value = None
        app.dependency_overrides[DBConnector] = lambda: mock_instance
        yield mock_instance
        app.dependency_overrides = {}


@pytest.mark.asyncio
async def test_get_user_debt(mock_db):
    wallet_id = "0x123"
    protocol_name = "zkLend"

    mock_db.get_loan_state.return_value = {
        "collateral": json.dumps({"USDC": "1000", "ETH": "2.5"}),
        "debt": json.dumps({"USDC": "500", "ETH": "1.0"}),
        "deposit": json.dumps({"USDC": "1000", "ETH": "2.5"}),
    }

    response = client.get(
        f"/user/debt?wallet_id={wallet_id}&protocol_name={protocol_name}"
    )

    assert response.status_code == 200
    data = response.json()
    assert data["wallet_id"] == wallet_id
    assert data["protocol_name"] == protocol_name
    assert "collateral" in data
    assert isinstance(data["collateral"], dict)

    expected_collateral = normalize_values(
        json.loads(mock_db.get_loan_state.return_value["collateral"])
    )
    actual_collateral = normalize_values(data["collateral"])
    assert actual_collateral == expected_collateral

    mock_db.get_loan_state.assert_called_once_with(protocol_name, wallet_id)


@pytest.mark.asyncio
async def test_get_user_debt_not_found(mock_db):
    mock_db.get_loan_state.return_value = None

    response = client.get("/user/debt?wallet_id=0xnonexistent&protocol_name=zkLend")

    assert response.status_code == 404
    assert "No data found" in response.json()["detail"]


@pytest.mark.asyncio
async def test_get_user_debt_invalid_json(mock_db):
    mock_db.get_loan_state.return_value = {
        "collateral": "invalid json",
        "debt": "{}",
        "deposit": "{}",
    }

    response = client.get("/user/debt?wallet_id=0x123&protocol_name=zkLend")

    assert response.status_code == 200
    data = response.json()
    assert data["collateral"] == {}
