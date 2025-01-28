from fastapi import APIRouter, HTTPException
from fastapi import Depends
from schemas.schemas import UserLoanByWalletParams, UserLoanByWalletResponse
from db_connector import DBConnector

loan_router = APIRouter()


@loan_router.get("/loan_data_by_wallet_id", response_model=UserLoanByWalletResponse)
async def get_loans_by_wallet_id(
    params: UserLoanByWalletParams = Depends(), db: DBConnector = Depends()
):
    """
    Retrieve loan data associated with a specific wallet ID.

    endpoint allows users to query their loan details by providing a
    wallet ID. The response includes
    information about the user's collateral, debt, and deposits across
    the specified loan protocol.

    Args:
      wallet_id (str): The wallet ID of the user
      protocol_name (str): The name of the loan protocol

    Returns:
      UserLoanByWalletResponse: User loan Information

    Raises:
      HTTPException: If address is not mapped
    """
    try:
        loan_states = db.get_loan_state(
            wallet_id=params.wallet_id,
            protocol_id=params.protocol_name,
        )
        if not loan_states:
            raise HTTPException(
                status_code=404,
                detail=f"No data found for user {params.wallet_id} in protocol {params.protocol_name}",
            )
        return UserLoanByWalletResponse(
            wallet_id=params.wallet_id,
            protocol_name=params.protocol_name,
            collateral=loan_states["collateral"],
            debt=loan_states["debt"],
            deposit=loan_states["deposit"],
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
