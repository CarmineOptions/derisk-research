from unittest.mock import patch
from fastapi.testclient import TestClient
from fastapi import FastAPI
import pandas as pd


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
    from ..app.api.user import router


app = FastAPI()
app.include_router(router)
client = TestClient(app)


def test_get_user_debt_success():
    with patch(
        "app.dashboard_app.app.crud.base.DashboardDBConnectorAsync.get_user_debt",
        return_value={"USDC": 100.50},
    ):
        response = client.get("/user/debt?wallet_id=wallet123&protocol_name=zkLend")
        assert response.status_code == 200
        data = response.json()
        assert data["wallet_id"] == "wallet123"
        assert data["protocol_name"] == "zkLend"
        assert isinstance(data["debt"], dict)
        assert data["debt"] == {"USDC": 100.50}
