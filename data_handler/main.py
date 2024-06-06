from typing import List, Optional
from fastapi import FastAPI, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.middleware import SlowAPIMiddleware

from db.schemas import LoanStateResponse
from db.models import LoanState
from db.database import Base, engine, get_database

# Create the database tables
Base.metadata.create_all(bind=engine)

# Set up rate limiting
limiter = Limiter(key_func=get_remote_address)
app = FastAPI()
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)


@app.get("/loan_states", response_model=List[LoanStateResponse])
@limiter.limit("10/second")
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
