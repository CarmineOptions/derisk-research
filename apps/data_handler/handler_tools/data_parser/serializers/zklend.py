from decimal import Decimal
from pydantic import BaseModel, ValidationInfo, field_validator
from shared.helpers import add_leading_zeros

class AccumulatorsSyncEventData(BaseModel):
    token: str
    lending_accumulator: str
    debt_accumulator: str

    @field_validator("token")
    def validate_address(cls, value: str, info: ValidationInfo) -> str:
        if not value.startswith("0x"):
            raise ValueError(f"Invalid address provided for {info.field_name}")
        return add_leading_zeros(value)

class LiquidationEventData(BaseModel):
    liquidator: str
    user: str
    debt_token: str
    debt_raw_amount: str
    debt_face_amount: str
    collateral_token: str
    collateral_amount: str

    @field_validator("liquidator", "user", "debt_token", "collateral_token")
    def validate_address(cls, value: str, info: ValidationInfo) -> str:
        if not value.startswith("0x"):
            raise ValueError(f"Invalid address provided for {info.field_name}")
        return add_leading_zeros(value)

class WithdrawalEventData(BaseModel):
    user: str
    token: str
    amount: str

    @field_validator("user", "token")
    def validate_address(cls, value: str, info: ValidationInfo) -> str:
        if not value.startswith("0x"):
            raise ValueError(f"Invalid address provided for {info.field_name}")
        return add_leading_zeros(value)

class BorrowingEventData(BaseModel):
    user: str
    token: str
    amount: str

class RepaymentEventData(BaseModel):
    repayer: str
    beneficiary: str
    token: str
    raw_amount: str
    face_amount: str

class DepositEventData(BaseModel):
    user: str
    token: str
    face_amount: str

class CollateralEnabledDisabledEventData(BaseModel):
    user: str
    token: str
    enabled: bool