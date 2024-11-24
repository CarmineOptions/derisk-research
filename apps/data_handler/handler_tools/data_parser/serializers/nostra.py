from decimal import Decimal
from pydantic import BaseModel, ValidationInfo, field_validator
from shared.helpers import add_leading_zeros

class DebtMintEventData(BaseModel):
    user: str
    amount: Decimal

    @field_validator("user")
    def validate_address(cls, value: str, info: ValidationInfo) -> str:
        if not value.startswith("0x"):
            raise ValueError(f"Invalid address provided for {info.field_name}")
        return add_leading_zeros(value)

class DebtBurnEventData(BaseModel):
    user: str
    amount: Decimal

    @field_validator("user")
    def validate_address(cls, value: str, info: ValidationInfo) -> str:
        if not value.startswith("0x"):
            raise ValueError(f"Invalid address provided for {info.field_name}")
        return add_leading_zeros(value)

class InterestRateModelEventData(BaseModel):
    debt_token: str
    lending_index: Decimal
    borrow_index: Decimal

class DebtTransferEventData(BaseModel):
    sender: str
    recipient: str
    amount: Decimal

    @field_validator("sender", "recipient")
    def validate_address(cls, value: str, info: ValidationInfo) -> str:
        if not value.startswith("0x"):
            raise ValueError(f"Invalid address provided for {info.field_name}")
        return add_leading_zeros(value)

class BearingCollateralMintEventData(BaseModel):
    user: str
    amount: Decimal

    @field_validator("user")
    def validate_address(cls, value: str, info: ValidationInfo) -> str:
        if not value.startswith("0x"):
            raise ValueError(f"Invalid address provided for {info.field_name}")
        return add_leading_zeros(value)

class BearingCollateralBurnEventData(BaseModel):
    user: str
    amount: Decimal

    @field_validator("user")
    def validate_address(cls, value: str, info: ValidationInfo) -> str:
        if not value.startswith("0x"):
            raise ValueError(f"Invalid address provided for {info.field_name}")
        return add_leading_zeros(value)