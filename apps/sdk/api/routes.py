from fastapi import APIRouter, Depends
from loan_state import LoanStateService
from schemas.schemas import UserLoanByWalletParams, UserLoanByWalletResponse

api_router = APIRouter
loan_state_service = LoanStateService()


@api_router.get("/loan_data_by_wallet_id", response_model=UserLoanByWalletResponse)
async def get_loans_by_wallet_id(params: UserLoanByWalletParams = Depends()):
    loans = loan_state_service.get_user_loans_by_wallet_id(
        protocol_name=params.protocol_name,
        wallet_id=params.wallet_id,
        start_block=params.start_block,
        end_block=params.end_block
    )
    return loans
