from typing import Optional

class LoanStateService:
    async def get_user_loans_by_wallet_id(
        protocol_name: str,
        wallet_id: str,
        start_block: Optional[int],
        end_block: Optional[int]
    ):
        return {
            "protocol_name": protocol_name,
            "wallet_id": wallet_id,
            "start_block": start_block,
            "end_block": end_block
        }
