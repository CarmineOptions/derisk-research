"""
Pydantic models and data validation schemas for the data handler application.
Provides data validation and serialization for loan states, interest rates, and order books.

Contains:
- LoanStateBase: Base model for loan state data
- LoanStateResponse: Response model for loan state queries
- InterestRateModel: Model for interest rate data
- OrderBookResponseModel: Model for order book data with price and volume information
"""

import decimal
from decimal import Decimal
from typing import Dict, List, Optional, Tuple

from pydantic import BaseModel, field_validator


class LoanStateBase(BaseModel):
    """
    Base model for loan state data with core fields and validation.

    Attributes:
        protocol_id: Identifier for the protocol
        block: Block number when the state was recorded
        timestamp: Unix timestamp of the state
        user: Optional user address
        collateral: Optional dictionary of collateral amounts
        debt: Optional dictionary of debt amounts
        deposit: Optional dictionary of deposit amounts
    """
    protocol_id: str
    block: int
    timestamp: int
    user: Optional[str]
    collateral: Optional[Dict]
    debt: Optional[Dict]
    deposit: Optional[Dict]

    class Config:
        """Configuration for Pydantic model."""
        from_attributes = True


class LoanStateResponse(LoanStateBase):
    """
    Response model for loan state queries.
    Inherits all fields from LoanStateBase without modification.
    Used for consistent API responses.
    """
    pass


class InterestRateModel(BaseModel):
    """
    Data validation model for interest rate information.
    
    Attributes:
        block: Block number when interest rate was recorded
        timestamp: Unix timestamp of the record
        debt: Dictionary mapping token addresses to debt interest rates
        collateral: Dictionary mapping token addresses to collateral interest rates
    """
    block: int
    timestamp: int
    debt: Dict[str, float]
    collateral: Dict[str, float]


class OrderBookResponseModel(BaseModel):
    """
    Data validation model for order book responses.
    Handles price and volume data for trading pairs.
    
    Attributes:
        token_a: Address of the base token
        token_b: Address of the quote token
        block: Optional block number of the order book snapshot
        timestamp: Unix timestamp of the snapshot
        dex: Name or identifier of the DEX
        current_price: Current price in decimal format
        asks: List of (price, volume) tuples for sell orders
        bids: List of (price, volume) tuples for buy orders
    """
    token_a: str
    token_b: str
    block: Optional[int]
    timestamp: int
    dex: str
    current_price: Decimal
    asks: List[Tuple[float, float]]
    bids: List[Tuple[float, float]]

    @field_validator("asks", "bids")
    def convert_decimals_to_floats(
        cls, value: List[Tuple[decimal.Decimal, decimal.Decimal]]
    ) -> List[Tuple[float, float]]:
        """
        Convert decimal values to floats for price and volume.

        Args:
            value: List of tuples containing decimal values for price and volume

        Returns:
            List of tuples with float values for price and volume
        """
        return [(float(a), float(b)) for a, b in value]

    @field_validator("block")
    def validate_block(cls, value: Optional[int]) -> int:
        """
        Validate and normalize block number, defaulting to 0 if None.

        Args:
            value: Block number or None

        Returns:
            Normalized block number (0 if None)
        """
        if value is None:
            return 0
        return value