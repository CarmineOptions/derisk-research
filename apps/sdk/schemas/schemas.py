from pydantic import BaseModel
from typing import Dict, Optional
from datetime import datetime

class UserLoanByWalletParams(BaseModel):
    """
    Data model representing the parameters required to query a user's loan details by wallet ID.

    Attributes:
        protocol_name: The name of the loan protocol (e.g., zkLend, Nostra).
        wallet_id: The unique identifier of the user's wallet address.
        start_block: The starting block number to filter loan data (inclusive).
        end_block: The ending block number to filter loan data (inclusive).
    """
    protocol_name: str
    wallet_id: str
    start_block: Optional[int]
    end_block: Optional[int]


class UserLoanByWalletResponse(BaseModel):
    """
    Data model representing the response for user loan details by wallet ID.

    Attributes:
        wallet_id: The unique identifier of the user's wallet address.
        collateral: A dictionary mapping token addresses to collateral values.
        debt: A dictionary mapping token addresses to debt values.
        deposit: A dictionary mapping token addresses to deposit values.
    """
    wallet_id: str
    collateral: Dict[str, str]
    debt: Dict[str, str]
    deposit: Dict[str, str]


class UserCollateralResponse(BaseModel):
    """ Base class for UserCollateralResponse

    Attributes:
        wallet_id: The unique identifier of the user's wallet address.
        protocol_name: The name of the loan protocol (e.g., zkLend, Nostra).
        collateral: A dictionary mapping token addresses to collateral values.
    """
    wallet_id: str
    protocol_name: str
    collateral: Dict[str, float]


class UserDebtResponseModel(BaseModel):
    """
    Data model representing the response for user debt details by wallet ID.
    """
    wallet_id: str
    protocol_name: str
    debt: Dict[str, float]

class Token(BaseModel):
    """
    Data model representing token response.

    Attributes:
        access_token (str): The access token string.
        expiration_date (datetime): The expiration datetime of the access token.
    """
    access_token: str
    expiration_date: datetime