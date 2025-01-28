from fastapi import APIRouter, Depends, HTTPException

from db_connector import DBConnector
from schemas.schemas import UserLoanByWalletParams, UserLoanByWalletResponse

loan_router = APIRouter()


@loan_router.get("/loan_data_by_wallet_id", response_model=UserLoanByWalletResponse)
async def get_loans_by_wallet_id(params: UserLoanByWalletParams = Depends()):
    """
    Retrieve loan data associated with a specific wallet ID.

    Args:
      params (UserLoanByWalletParams): Query parameters containing wallet ID, protocol name, and optional block range.

    Returns:
      UserLoanByWalletResponse: User loan information.

    Raises:
      HTTPException: If no data is found or an error occurs during data fetching.
    """
    try:
        db = DBConnector()

        # Fetch collateral, debt, and loan state from the database
        collateral = db.get_user_collateral(
            protocol_id=params.protocol_name,
            wallet_id=params.wallet_id,
            start_block=params.start_block,
            end_block=params.end_block,
        )
        debt = db.get_user_debt(
            protocol_id=params.protocol_name,
            wallet_id=params.wallet_id,
            start_block=params.start_block,
            end_block=params.end_block,
        )
        loan_state = db.get_loan_state(
            protocol_id=params.protocol_name,
            wallet_id=params.wallet_id,
            start_block=params.start_block,
            end_block=params.end_block,
        )

        # Check if all retrieved data is None or empty
        if not any([collateral, debt, loan_state]):
            raise HTTPException(
                status_code=404,
                detail=f"No data found for wallet ID '{params.wallet_id}' in protocol '{params.protocol_name}'.",
            )

        # Default to empty dictionaries if data is None or not a dictionary
        collateral_data = collateral if isinstance(collateral, dict) else {}
        debt_data = debt if isinstance(debt, dict) else {}
        loan_state_data = loan_state if isinstance(loan_state, dict) else {}

        # Construct and return the response
        return UserLoanByWalletResponse(
            wallet_id=params.wallet_id,
            protocol_name=params.protocol_name,
            collateral=collateral_data,
            debt=debt_data,
            deposit=loan_state_data,  # Assuming `loan_state` represents deposit
        )

    except HTTPException as e:
        # Re-raise known HTTP exceptions
        raise e
    except Exception as e:
        # Handle unexpected errors
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
