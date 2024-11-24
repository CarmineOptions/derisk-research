from decimal import Decimal
from pydantic import BaseModel, ValidationInfo, field_validator
from shared.helpers import add_leading_zeros


class AccumulatorsSyncEventData(BaseModel):
    """
    Data model representing an accumulators sync event in the system.

    Attributes:
        token: The token address involved in the sync.
        lending_accumulator: The lending accumulator value as a string.
        debt_accumulator: The debt accumulator value as a string.
    """

    token: str
    lending_accumulator: str
    debt_accumulator: str

    @field_validator("token")
    def validate_address(cls, value: str, info: ValidationInfo) -> str:
        """
        Validates if the value is a valid address and formats it to have leading zeros.

        Args:
            value (str): The address string to validate.
            info (ValidationInfo): Validation context information.

        Raises:
            ValueError: If the provided address is invalid.

        Returns:
            str: Formatted address with leading zeros.
        """


class LiquidationEventData(BaseModel):
    """
    Data model representing a liquidation event in the system.

    Attributes:
        liquidator: The address of the liquidator.
        user: The address of the user being liquidated.
        debt_token: The address of the debt token.
        debt_raw_amount: The raw amount of debt as a string.
        debt_face_amount: The face amount of debt as a string.
        collateral_token: The address of the collateral token.
        collateral_amount: The amount of collateral as a string.
    """

    liquidator: str
    user: str
    debt_token: str
    debt_raw_amount: str
    debt_face_amount: str
    collateral_token: str
    collateral_amount: str

    @field_validator("liquidator", "user", "debt_token", "collateral_token")
    def validate_address(cls, value: str, info: ValidationInfo) -> str:
        """
        Validates if the value is a valid address and formats it to have leading zeros.

        Args:
            value (str): The address string to validate.
            info (ValidationInfo): Validation context information.

        Raises:
            ValueError: If the provided address is invalid.

        Returns:
            str: Formatted address with leading zeros.
        """


class WithdrawalEventData(BaseModel):
    """
    Data model representing a withdrawal event in the system.

    Attributes:
        user: The user address making the withdrawal.
        token: The token address being withdrawn.
        amount: The amount being withdrawn as a string.
    """

    user: str
    token: str
    amount: str

    @field_validator("user", "token")
    def validate_address(cls, value: str, info: ValidationInfo) -> str:
        """
        Validates if the value is a valid address and formats it to have leading zeros.

        Args:
            value (str): The address string to validate.
            info (ValidationInfo): Validation context information.

        Raises:
            ValueError: If the provided address is invalid.

        Returns:
            str: Formatted address with leading zeros.
        """


class BorrowingEventData(BaseModel):
    """
    Data model representing a borrowing event in the system.

    Attributes:
        user: The user address making the borrowing.
        token: The token address being borrowed.
        raw_amount: The raw amount being borrowed as a string.
        face_amount: The face amount being borrowed as a string.
    """

    user: str
    token: str
    raw_amount: str
    face_amount: str

    @field_validator("user", "token")
    def validate_address(cls, value: str, info: ValidationInfo) -> str:
        """
        Validates if the value is a valid address and formats it to have leading zeros.

        Args:
            value (str): The address string to validate.
            info (ValidationInfo): Validation context information.

        Raises:
            ValueError: If the provided address is invalid.

        Returns:
            str: Formatted address with leading zeros.
        """
        if not value.startswith("0x"):
            raise ValueError(f"Invalid address provided for {info.field_name}")
        return add_leading_zeros(value)


class RepaymentEventData(BaseModel):
    """
    Data model representing a repayment event in the system.

    Attributes:
        repayer: The address of the repayer.
        beneficiary: The address of the beneficiary.
        token: The token address being repaid.
        raw_amount: The raw amount being repaid as a string.
        face_amount: The face amount being repaid as a string.
    """

    repayer: str
    beneficiary: str
    token: str
    raw_amount: str
    face_amount: str


class DepositEventData(BaseModel):
    """
    Data model representing a deposit event in the system.

    Attributes:
        user: The user address making the deposit.
        token: The token address being deposited.
        face_amount: The face amount being deposited as a string.
    """

    user: str
    token: str
    face_amount: str


class CollateralEnabledDisabledEventData(BaseModel):
    """
    Data model representing a collateral enabled/disabled event in the system.

    Attributes:
        user: The user address for whom collateral is being enabled/disabled.
        token: The token address being enabled/disabled as collateral.
        enabled: Boolean indicating if collateral is being enabled (True) or disabled (False).
    """

    user: str
    token: str
    enabled: bool
