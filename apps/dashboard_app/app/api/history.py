from http.client import HTTPException
from typing import List
from app.services.fetch_data import get_events_by_hash
from app.schemas.user_transaction import UserTransaction
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
        open_trades, close_trades = await get_events_by_hash()
        filter_trades = lambda trades: list(
            filter(lambda trade: trade.user_address == wallet_id, trades)
        )
        return filter_trades(open_trades) + filter_trades(close_trades)
    except Exception as e:
        logger.error(e)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
