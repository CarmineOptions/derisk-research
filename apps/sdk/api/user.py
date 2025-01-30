from fastapi import APIRouter, HTTPException, Depends
import pandas as pd
import json
from sdk.schemas.schemas import UserCollateralResponse, UserDepositResponse
from sdk.db_connector import DBConnector

router = APIRouter(
    prefix="/user",
    tags=["user"],
    responses={404: {"description": "Not found"}},
)


mock_data = pd.DataFrame(
    columns=["user", "protocol_id", "deposit", "debt", "timestamp"]
)


@router.get("/debt", response_model=UserCollateralResponse)
async def get_user_debt(
    wallet_id: str, protocol_name: str, db: DBConnector = Depends()
) -> UserCollateralResponse:
    """
    Get user's collateral information for a specific protocol.

    Args:
        wallet_id (str): The wallet ID of the user
        protocol_name (str): The name of the protocol (e.g., 'zkLend')

    Returns:
        UserCollateralResponse: User's collateral information

    Raises:
        HTTPException: If user or protocol not found
    """
    try:
        user_data = db.get_loan_state(protocol_name, wallet_id)

        if not user_data:
            raise HTTPException(
                status_code=404,
                detail=f"No data found for wallet {wallet_id} in protocol {protocol_name}",
            )

        try:
            collateral = json.loads(
                str(user_data.get("collateral", "{}")).replace("'", '"')
            )
            if not collateral:
                collateral = {}
        except (json.JSONDecodeError, AttributeError):
            collateral = {}

        return UserCollateralResponse(
            wallet_id=wallet_id, protocol_name=protocol_name, collateral=collateral
        )

    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


def parse_deposit_data(row):
    try:
        return json.loads(row) if row.strip() else {}
    except json.JSONDecodeError:
        return {}


mock_data["deposit"] = mock_data["deposit"].apply(parse_deposit_data)


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
