from pydantic import BaseModel


class UserDebtResponseModel(BaseModel):
    """
    Data model representing the response for user debt details by wallet ID.
    """

    wallet_id: str
    protocol_name: str
    debt: dict[str, float]


class UserDepositResponse(BaseModel):
    """
    Data model representing the response for user deposit details by wallet ID.

    Attributes:
        wallet_id: The unique identifier of the user's wallet address.
        deposit: A dictionary mapping token addresses to deposit values.
    """

    wallet_id: str
    deposit: dict[str, float]
