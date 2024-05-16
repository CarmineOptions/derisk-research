from pydantic import BaseModel
from typing import Optional, Dict


class LoanStateBase(BaseModel):
    protocol_id: str
    block: int
    timestamp: int
    user: Optional[str]
    collateral: Optional[Dict]
    debt: Optional[Dict]

    class Config:
        orm_mode = True


class LoanStateResponse(LoanStateBase):
    pass
