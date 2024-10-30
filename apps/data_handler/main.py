"""
Defines FastAPI endpoints for querying loan states, interest rates, 
user health ratios, and order book records, with a 10 requests/second rate 
limit per endpoint.
"""
import logging
from typing import List, Optional

from fastapi import Depends, FastAPI, HTTPException, Path, Query, Request, status
from slowapi import Limiter
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address
from sqlalchemy import desc
from sqlalchemy.orm import Session

from data_handler.db.database import Base, engine, get_database
from data_handler.db.models import (
    HealthRatioLevel,
    InterestRate,
    LoanState,
    OrderBookModel,
)
from data_handler.db.schemas import (
    InterestRateModel,
    LoanStateResponse,
    OrderBookResponseModel,
)
from shared.constants import ProtocolIDs

logger = logging.getLogger(__name__)

# Create the database tables
Base.metadata.create_all(bind=engine)

# Set up rate limiting
limiter = Limiter(key_func=get_remote_address)
app = FastAPI()
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)


@limiter.limit("10/second")
@app.get("/loan_states", response_model=List[LoanStateResponse])
async def read_loan_states(
    request: Request,
    protocol: Optional[str] = None,
    start_block: Optional[int] = None,
    end_block: Optional[int] = None,
    start_datetime: Optional[int] = None,
    end_datetime: Optional[int] = None,
    user: Optional[str] = None,
    db: Session = Depends(get_database),
) -> List[LoanStateResponse]:
    """
    Fetch loan states from the database with optional filtering.
    Max response size is limited to 1000 records.
    Args:
        request (Request): The request object.
        protocol (Optional[str]): The protocol ID to filter by.
        start_block (Optional[int]): The starting block number to filter by.
        end_block (Optional[int]): The ending block number to filter by.
        start_datetime (Optional[int]): The starting timestamp (in UNIX epoch format) to filter by.
        end_datetime (Optional[int]): The ending timestamp (in UNIX epoch format) to filter by.
        user (Optional[str]): The user to filter by (optional).
        db (Session): The database session.

    Returns:
        List[LoanStateResponse]: A list of loan states matching the filtering criteria.

    Raises:
        HTTPException: If no loan states are found.
    """
    query = db.query(LoanState)

    if protocol is not None:
        query = query.filter(LoanState.protocol_id == protocol)
    if start_block is not None:
        query = query.filter(LoanState.block >= start_block)
    if end_block is not None:
        query = query.filter(LoanState.block <= end_block)
    if start_datetime is not None:
        query = query.filter(LoanState.timestamp >= start_datetime)
    if end_datetime is not None:
        query = query.filter(LoanState.timestamp <= end_datetime)
    if user is not None:
        query = query.filter(LoanState.user == user)

    results = query.limit(1000).all()  # Limit the results to 1000 records
    if not results:
        raise HTTPException(status_code=404, detail="Loan states not found")

    return results


@limiter.limit("10/second")
@app.get("/interest-rate/", response_model=InterestRateModel)
def get_last_interest_rate_by_block(
    request: Request,
    protocol: Optional[str] = None,
    db: Session = Depends(get_database),
):
    """
    Fetch the last interest rate record by block number.
    :param protocol: The protocol ID to filter by.
    :param db: The database session.
    :return: The last interest rate record.
    """
    if protocol is None:
        raise HTTPException(status_code=400, detail="Protocol ID is required")

    if protocol not in ProtocolIDs.choices():
        raise HTTPException(status_code=400, detail="Invalid protocol ID")

    last_record = (
        db.query(InterestRate).filter(InterestRate.protocol_id == protocol
                                      ).order_by(InterestRate.block.desc()).first()
    )

    return last_record


@limiter.limit("10/second")
@app.get("/health-ratio-per-user/{protocol}/")
async def get_health_ratio_per_user(
    request: Request,
    protocol: str = Path(..., ),
    user_id: str = Query(..., ),
    db: Session = Depends(get_database),
):
    """
    Returns the health ratio by user id provided.
    :param request: The request object.
    :param protocol: The protocol ID to filter by.
    :param user_id: The user id.
    :param db: The database session.
    :return: The health ratio by user id.
    """
    if protocol is None:
        raise HTTPException(status_code=400, detail="Protocol ID is required")

    if protocol not in ProtocolIDs.choices():
        raise HTTPException(status_code=400, detail="Invalid protocol ID")

    if not user_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User ID is required")

    row = (
        db.query(HealthRatioLevel).filter(
            HealthRatioLevel.protocol_id == protocol,
            HealthRatioLevel.user_id == user_id,
        ).order_by(desc(HealthRatioLevel.timestamp)).first()
    )

    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Health ratio with user ID provided not found",
        )

    return row.value


@app.get("/orderbook/", response_model=OrderBookResponseModel)
def get_orderbook(
    base_token: str, quote_token: str, dex: str, db: Session = Depends(get_database)
) -> OrderBookResponseModel:
    """
    Fetch order book records from the database.
    :param base_token: The base token symbol.
    :param quote_token: The quote token symbol.
    :param dex: The DEX name.
    :return: A list of order book records.
    """
    print(f"Fetching order book records for {base_token}/{quote_token} on {dex}")
    logger.info(f"Fetching order book records for {base_token}/{quote_token} on {dex}")

    records = (
        db.query(OrderBookModel).filter(
            OrderBookModel.token_a == base_token,
            OrderBookModel.token_b == quote_token,
            OrderBookModel.dex == dex,
        ).order_by(OrderBookModel.timestamp.desc()).first()
    )
    print(f"Found {records} order book records")
    logger.info(f"Found {records} order book records")
    if not records:
        raise HTTPException(status_code=404, detail="Records not found")

    return records
