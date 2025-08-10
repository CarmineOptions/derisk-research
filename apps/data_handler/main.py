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
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from shared.db.connector import db_connector
from data_handler.db.models import (
    InterestRate,
    LoanState,
    OrderBookModel,
)
from data_handler.db.schemas import (
    InterestRateModel,
    LoanStateResponse,
    OrderBookResponseModel,
)
from shared.protocol_ids import ProtocolIDs

logger = logging.getLogger(__name__)

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
    db: Session = Depends(db_connector.get_db),
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
    query = select(LoanState)

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

    results = await db.execute(query.limit(1000))
    loan_states = results.scalars().all()
    if not loan_states:
        raise HTTPException(status_code=404, detail="Loan states not found")

    return loan_states


@limiter.limit("10/second")
@app.get("/interest-rate/", response_model=InterestRateModel)
async def get_last_interest_rate_by_block(
    request: Request,
    protocol: Optional[str] = None,
    db: Session = Depends(db_connector.get_db),
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

    query = (
        select(InterestRate)
        .filter(InterestRate.protocol_id == protocol)
        .order_by(InterestRate.block.desc())
        .limit(1)
    )
    res = await db.execute(query)
    last_record = res.scalar_one_or_none()
    return last_record


@app.get("/orderbook/", response_model=OrderBookResponseModel)
async def get_orderbook(
    base_token: str,
    quote_token: str,
    dex: str,
    db: Session = Depends(db_connector.get_db),
) -> OrderBookResponseModel:
    """
    Fetch order book records from the database.
    :param base_token: The base token symbol.
    :param quote_token: The quote token symbol.
    :param dex: The DEX name.
    :return: A latest order book record.
    """
    print(f"Fetching order book records for {base_token}/{quote_token} on {dex}")
    logger.info(f"Fetching order book records for {base_token}/{quote_token} on {dex}")

    query = (
        select(OrderBookModel)
        .filter(
            OrderBookModel.token_a == base_token,
            OrderBookModel.token_b == quote_token,
            OrderBookModel.dex == dex,
        )
        .order_by(OrderBookModel.timestamp.desc())
        .limit(1)
    )
    res = await db.execute(query)
    order_book = res.scalar_one_or_none()
    if not order_book:
        raise HTTPException(status_code=404, detail="Order book not found")

    return order_book
