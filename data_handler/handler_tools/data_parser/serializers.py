from decimal import Decimal

from pydantic import BaseModel, field_validator


class DataAccumulatorsSyncEvent(BaseModel):
    token: str
    lending_accumulator: Decimal
    debt_accumulator: Decimal

    @field_validator("lending_accumulator", "debt_accumulator", pre=True)
    def hex_to_decimal(cls, v):
        return Decimal(int(v, 16)) / Decimal("1e27")
