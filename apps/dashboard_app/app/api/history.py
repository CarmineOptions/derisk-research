from fastapi import HTTPException
from typing import List
from dashboard_app.app.services.fetch_data import get_history_by_wallet_id
from dashboard_app.app.schemas.user_transaction import UserTransaction
from fastapi import APIRouter
from fastapi.templating import Jinja2Templates
from loguru import logger


router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get(
    path="/history",
    description="Get user's transaction history",
    response_model=List[UserTransaction],
)
async def get_history(wallet_id: str) -> List[UserTransaction]:
    """
    Get user's transaction history.

    Args:
            wallet_id (str): The wallet ID of the user
    Returns:
            UserTransaction: User's transaction information

    Raises:
            HTTPException: Internal Server Error
    """

    try:
        filtered_trade_open, filtered_trade_close = await get_history_by_wallet_id(
            wallet_id
        )
        return filtered_trade_open + filtered_trade_close
    except Exception as e:
        logger.error(e)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
