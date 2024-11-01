""" This module contains the data models for the database schema """

import decimal
from decimal import Decimal
from typing import Dict, List, Optional

from pydantic import BaseModel, field_validator


class LoanStateBase(BaseModel):
    """ Base class for LoanStateResponse """
    protocol_id: str
    block: int
    timestamp: int
    user: Optional[str]
    collateral: Optional[Dict]
    debt: Optional[Dict]
    deposit: Optional[Dict]

    class Config:
        """ Pydantic configuration """
        from_attributes = True


class LoanStateResponse(LoanStateBase):
    """ Pydantic model for LoanStateResponse """
    pass


class InterestRateModel(BaseModel):
    """
    A data model class that validates data user entered
    """

    block: int
    timestamp: int
    debt: Dict[str, float]
    collateral: Dict[str, float]


class OrderBookResponseModel(BaseModel):
    """
    A data model class that validates data user entered
    """

    token_a: str
    token_b: str
    block: Optional[int]
    timestamp: int
    dex: str
    current_price: Decimal
    asks: List[tuple[float, float]]
    bids: List[tuple[float, float]]

    @field_validator("asks", "bids")
    def convert_decimals_to_floats(
        cls, value: List[tuple[decimal.Decimal, decimal.Decimal]]
    ) -> List[tuple[float, float]]:
        """
        Convert decimal values to floats
        :param value: list of tuples of decimal values
        :return: list of tuples of float values
        """
        return [(float(a), float(b)) for a, b in value]

    @field_validator("block")
    def validate_block(cls, value: int | None) -> int:
        """
        Validate block number
        :param value: block number
        :return: block number
        """
        if value is None:
            return 0
        return value
