from fastapi import APIRouter, HTTPException, FastAPI
import pandas as pd
import json
from sdk.schemas.schemas import (
    UserCollateralResponse,
    UserDebtResponseModel,
    UserDepositResponse,
)
from sdk.db_connector import DBConnector

app = FastAPI()
router = APIRouter(
    prefix="/user",
    tags=["user"],
    responses={404: {"description": "Not found"}},
)

file_path = "mock_data.csv"
try:
    mock_data = pd.read_csv(file_path)
except FileNotFoundError:
    mock_data = pd.DataFrame(
        columns=["user", "protocol_id", "deposit", "debt", "timestamp"]
    )


@router.get("/debt", response_model=UserCollateralResponse)
async def get_user_debt_endpoint(
    wallet_id: str, protocol_id: str
) -> UserCollateralResponse:
    """
    Get user's collateral information for a specific protocol.
    """
    db = None
    try:
        db = DBConnector()
        user_data = db.get_loan_state(protocol_id, wallet_id)

        if user_data is None:
            raise HTTPException(
                status_code=404,
                detail=f"No data found for wallet {wallet_id} in protocol {protocol_id}",
            )

        try:
            if user_data.get("collateral"):
                collateral = json.loads(str(user_data["collateral"]).replace("'", '"'))
                
                collateral = {k: str(v) for k, v in collateral.items()}
            else:
                collateral = {}
        except (json.JSONDecodeError, AttributeError):
            collateral = {}

        return UserCollateralResponse(
            wallet_id=wallet_id, protocol_name=protocol_id, collateral=collateral
        )
    finally:
        if db:
            db.close_connection()


@router.get("/deposit", response_model=UserDepositResponse)
async def get_user_deposit(wallet_id: str) -> UserDepositResponse:
    """
    Get user's deposit information.
    """
    try:
        user_data = mock_data[mock_data["user"] == wallet_id]

        if user_data.empty:
            raise HTTPException(
                status_code=404, detail=f"No deposit data found for wallet {wallet_id}"
            )

        latest_entry = user_data.sort_values("timestamp", ascending=False).iloc[0]

        try:
            if pd.isna(latest_entry.get("deposit")):
                deposit = {}
            else:
                deposit = json.loads(str(latest_entry["deposit"]).replace("'", '"'))
                
                deposit = {
                    k: (
                        f"{float(v):.1f}"
                        if str(v).replace(".", "", 1).isdigit()
                        else str(v)
                    )
                    for k, v in deposit.items()
                }
        except (json.JSONDecodeError, AttributeError, KeyError):
            deposit = {}

        return UserDepositResponse(wallet_id=wallet_id, deposit=deposit)
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
