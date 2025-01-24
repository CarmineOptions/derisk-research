import decimal
from decimal import Decimal
from typing import Dict, List, Optional
from pydantic import BaseModel, field_validator



class ResponseModel(BaseModel):
    wallet_id: str
    protocol_name: str
    debt: Dict[str, float]