from fastapi import APIRouter, HTTPException, FastAPI
import pandas as pd
import json
from sdk.schemas.schemas import UserCollateralResponse, UserDebtResponseModel, UserDepositResponse

app = FastAPI()
router = APIRouter(
    prefix="/user",
    tags=["user"],
    responses={404: {"description": "Not found"}},
)

file_path = "../mock_data.csv"
mock_data = pd.read_csv(file_path)

def parse_debt_data(row):
    try:
        return json.loads(row) if row.strip() else {}
    except json.JSONDecodeError:
        return {}

mock_data["debt"] = mock_data["debt"].apply(parse_debt_data)


debt_data = {}
for _, row in mock_data.iterrows():
    wallet_id = row["user"]
    protocol = row["protocol_id"]
    debt = row["debt"]
    if wallet_id not in debt_data:
        debt_data[wallet_id] = {}
    debt_data[wallet_id][protocol] = debt


@router.get("/debt", response_model=UserCollateralResponse)
async def get_user_debt(wallet_id: str, protocol_name: str) -> UserCollateralResponse:
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
        data_path = "apps/sdk/mock_data.csv"
        df = pd.read_csv(data_path)

        user_data = df[
            (df['user'] == wallet_id) & 
            (df['protocol_id'] == protocol_name)
        ]
        
        if user_data.empty:
            raise HTTPException(
                status_code=404,
                detail=f"No data found for wallet {wallet_id} in protocol {protocol_name}"
            )
        latest_entry = user_data.sort_values('timestamp', ascending=False).iloc[0]
        
        try:
            collateral = json.loads(latest_entry['collateral'].replace("'", '"'))
            if not collateral: 
                collateral = {}
        except (json.JSONDecodeError, AttributeError):
            collateral = {}
        
        return UserCollateralResponse(
            wallet_id=wallet_id,
            protocol_name=protocol_name,
            collateral=collateral
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )



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
                status_code=404,
                detail=f"No deposit data found for wallet {wallet_id}"
            )
        
        latest_entry = user_data.sort_values("timestamp", ascending=False).iloc[0]
        
        try:
            deposit = json.loads(latest_entry["deposit"].replace("'", '"'))
            if not deposit:
                deposit = {}
        except (json.JSONDecodeError, AttributeError):
            deposit = {}
        
        return UserDepositResponse(
            wallet_id=wallet_id,
            deposit=deposit
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )