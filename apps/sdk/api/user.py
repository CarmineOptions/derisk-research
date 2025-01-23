from typing import Dict
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import pandas as pd
import json
from pathlib import Path

router = APIRouter(
    prefix="/user",
    tags=["user"],
    responses={404: {"description": "Not found"}},
)

class UserCollateralResponse(BaseModel):
    wallet_id: str
    protocol_name: str
    collateral: Dict[str, float]

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