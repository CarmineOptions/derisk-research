from fastapi import APIRouter, HTTPException, FastAPI
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
    db = None
    try:
        db = DBConnector()
        user_data = db.get_loan_state(
            None, wallet_id
        )  # or pass appropriate protocol_id if needed

        if user_data is None:
            raise HTTPException(
                status_code=404, detail=f"No deposit data found for wallet {wallet_id}"
            )

        try:
            if user_data.get("deposit"):
                deposit = json.loads(str(user_data["deposit"]).replace("'", '"'))
                deposit = {k: str(v) for k, v in deposit.items()}
            else:
                deposit = {}
        except (json.JSONDecodeError, AttributeError):
            deposit = {}

        return UserDepositResponse(wallet_id=wallet_id, deposit=deposit)
    finally:
        if db:
            db.close_connection()
