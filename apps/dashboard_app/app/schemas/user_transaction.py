from pydantic import BaseModel


class UserTransaction(BaseModel):
    """Model representing details of a user's token transaction."""

    user_address: str
    token: str
    price: str
    amount: float
    timestamp: str
    is_sold: bool
