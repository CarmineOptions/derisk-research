from decimal import Decimal

from pydantic import BaseModel, ValidationInfo, field_validator

from shared.helpers import add_leading_zeros


class LiquidationEventData(BaseModel):
    liquidator: str
    user: str
    debt_token: str
    debt_raw_amount: str
    debt_face_amount: str
    collateral_token: str
    collateral_amount: str

    @field_validator("liquidator", "user", "debt_token", "collateral_token")
    def validate_valid_addresses(cls, value: str, info: ValidationInfo):
        if not value.startswith("0x"):
            raise ValueError("Invalid address provided for %s" % info.field_name)
        return add_leading_zeros(value)

    @field_validator("debt_raw_amount", "debt_face_amount", "collateral_amount")
    def validate_valid_numbers(cls, value: str, info: ValidationInfo):
        if not value.isdigit():
            raise ValueError("%s field is not numeric" % info.field_name)
        return Decimal(str(int(value, base=16)))
