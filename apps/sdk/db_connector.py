from fastapi import APIRouter, HTTPException, FastAPI
from sdk.db_connector import DBConnector
from sdk.schemas.schemas import UserCollateralResponse, UserDebtResponseModel, UserDepositResponse

app = FastAPI()
router = APIRouter(
    prefix="/user",
    tags=["user"],
    responses={404: {"description": "Not found"}},
)

# Create a single instance of DBConnector to be used across endpoints
db = DBConnector()

@router.get("/debt", response_model=UserDebtResponseModel)
async def get_user_debt(wallet_id: str, protocol_name: str) -> UserDebtResponseModel:
    """
    Get user's debt information for a specific protocol.
    """
    try:
        debt = db.get_user_debt(protocol_name, wallet_id)
        
        if debt is None:
            raise HTTPException(
                status_code=404,
                detail=f"No debt data found for wallet {wallet_id} in protocol {protocol_name}"
            )
            
        return UserDebtResponseModel(
            wallet_id=wallet_id,
            protocol_name=protocol_name,
            debt=debt
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )

@router.get("/collateral", response_model=UserCollateralResponse)
async def get_user_collateral(wallet_id: str, protocol_name: str) -> UserCollateralResponse:
    """
    Get user's collateral information for a specific protocol.
    """
    try:
        collateral = db.get_user_collateral(protocol_name, wallet_id)
        
        if collateral is None:
            raise HTTPException(
                status_code=404,
                detail=f"No collateral data found for wallet {wallet_id} in protocol {protocol_name}"
            )
            
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

@router.get("/deposit", response_model=UserDepositResponse)
async def get_user_deposit(wallet_id: str, protocol_name: str) -> UserDepositResponse:
    """
    Get user's deposit information for a specific protocol.
    """
    try:
        deposit = db.get_user_deposit(protocol_name, wallet_id)
        
        if deposit is None:
            raise HTTPException(
                status_code=404,
                detail=f"No deposit data found for wallet {wallet_id} in protocol {protocol_name}"
            )
            
        return UserDepositResponse(
            wallet_id=wallet_id,
            protocol_name=protocol_name,
            deposit=deposit
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )

# Include the router in the app
app.include_router(router)

# If this file is run directly, start the server
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
    