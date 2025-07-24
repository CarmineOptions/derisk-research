from fastapi import APIRouter, HTTPException
from pathlib import Path
import pandas as pd
import json
from dashboard_app.app.schemas import (
    UserDepositResponse,
    UserDebtResponseModel,
)
from dashboard_app.app.crud import db_connector

router = APIRouter(
    prefix="/user",
    tags=["user"],
    responses={404: {"description": "Not found"}},
)
file_path = Path().parent.parent / "mock_data.csv"
mock_data = pd.read_csv(file_path)


def parse_json_row(row: str):
    try:
        return json.loads(row) if row.strip() else {}
    except json.JSONDecodeError:
        return {}


mock_data["debt"] = mock_data["debt"].apply(parse_json_row)


debt_data = {}
for _, row in mock_data.iterrows():
    wallet_id = row["user"]
    protocol = row["protocol_id"]
    debt = row["debt"]
    if wallet_id not in debt_data:
        debt_data[wallet_id] = {}
    debt_data[wallet_id][protocol] = debt


@router.get("/debt", response_model=UserDebtResponseModel)
async def get_user_debt(wallet_id: str, protocol_name: str) -> UserDebtResponseModel:
    """
    Get user's debt information for a specific protocol.

    Args:
        wallet_id (str): The wallet ID of the user
        protocol_name (str): The name of the protocol (e.g., 'zkLend')
        db: The database connection
    Returns:
        UserDebtResponseModel: User's collateral information

    Raises:
        HTTPException: If user or protocol not found
    """
    try:
        user_debt_data = await db_connector.get_user_debt(protocol_name, wallet_id)
        if not user_debt_data:
            raise HTTPException(
                status_code=404,
                detail=f"No data found for wallet {wallet_id} in protocol {protocol_name}",
            )

        return UserDebtResponseModel(
            wallet_id=wallet_id,
            protocol_name=protocol_name,
            debt=user_debt_data,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


mock_data["deposit"] = mock_data["deposit"].apply(parse_json_row)


@router.get("/deposit", response_model=UserDepositResponse)
async def get_user_deposit(wallet_id: str) -> UserDepositResponse:
    """
    Get user's deposit information.

    Args:
        wallet_id (str): The wallet ID of the user.

    Returns:
        UserDepositResponse: User's deposit information.

    Raises:
        HTTPException: If user is not found or an internal error occurs.
    """
    try:
        user_data = mock_data[mock_data["user"] == wallet_id]

        if user_data.empty:
            raise HTTPException(
                status_code=404, detail=f"No deposit data found for wallet {wallet_id}"
            )

        latest_entry = user_data.sort_values("timestamp", ascending=False).iloc[0]

        try:
            deposit = json.loads(latest_entry["deposit"].replace("'", '"'))
            if not deposit:
                deposit = {}
        except (json.JSONDecodeError, AttributeError):
            deposit = {}

        return UserDepositResponse(wallet_id=wallet_id, deposit=deposit)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
