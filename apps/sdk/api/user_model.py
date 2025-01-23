from typing import Dict
from pydantic import BaseModel

class UserCollateralResponse(BaseModel):
    wallet_id: str
    protocol_name: str
    collateral: Dict[str, float]