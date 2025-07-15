from pydantic import BaseModel


class UserLoanByWalletParams(BaseModel):
    """
    Data model representing the parameters required to query a user's loan details by wallet ID.

    Attributes:
        protocol_name: The name of the loan protocol (e.g., zkLend, Nostra).
        wallet_id: The unique identifier of the user's wallet address.
    """

    protocol_name: str
    wallet_id: str


class UserLoanByWalletResponse(BaseModel):
    """
    Data model representing the response for user loan details by wallet ID.

    Attributes:
        wallet_id: The unique identifier of the user's wallet address.
        protocol_name: The name of the loan protocol (e.g., zkLend, Nostra).
        collateral: A dictionary mapping token addresses to collateral values.
        debt: A dictionary mapping token addresses to debt values.
        deposit: A dictionary mapping token addresses to deposit values.
    """

    wallet_id: str
    protocol_name: str
    collateral: dict[str, float]
    debt: dict[str, float]
    deposit: dict[str, float]
