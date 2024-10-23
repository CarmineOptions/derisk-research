from decimal import Decimal

from pydantic import BaseModel


class AccumulatorsSyncEvent(BaseModel):
    token: str
    lending_accumulator: Decimal
    debt_accumulator: Decimal
