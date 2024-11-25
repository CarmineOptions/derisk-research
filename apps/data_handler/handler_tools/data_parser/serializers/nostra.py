from decimal import Decimal
from pydantic import BaseModel, ValidationInfo, field_validator
from shared.helpers import add_leading_zeros


class DebtMintEventData(BaseModel):
    """
    Data model representing a debt mint event in the system.

    Attributes:
        user: The user address for whom debt is being minted.
        amount: The amount of debt being minted as a Decimal.
    """

    user: str
    amount: Decimal

    @field_validator("user")
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


class DebtBurnEventData(BaseModel):
    """
    Data model representing a debt burn event in the system.

    Attributes:
        user: The user address for whom debt is being burned.
        amount: The amount of debt being burned as a Decimal.
    """

    user: str
    amount: Decimal

    @field_validator("user")
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


class InterestRateModelEventData(BaseModel):
    """
    Data model representing an interest rate model event in the system.

    Attributes:
        debt_token: The debt token address.
        lending_index: The lending index value as a Decimal.
        borrow_index: The borrowing index value as a Decimal.
    """

    debt_token: str
    lending_index: Decimal
    borrow_index: Decimal

    @field_validator("debt_token")
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


class DebtTransferEventData(BaseModel):
    """
    Data model representing a debt transfer event in the system.

    Attributes:
        sender: The address of the sender.
        recipient: The address of the recipient.
        amount: The amount being transferred as a Decimal.
    """

    sender: str
    recipient: str
    amount: Decimal

    @field_validator("sender", "recipient")
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


class BearingCollateralMintEventData(BaseModel):
    """
    Data model representing a bearing collateral mint event in the system.

    Attributes:
        user: The user address for whom collateral is being minted.
        amount: The amount of collateral being minted as a Decimal.
    """

    user: str
    amount: Decimal

    @field_validator("user")
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


class BearingCollateralBurnEventData(BaseModel):
    """
    Data model representing a bearing collateral burn event in the system.

    Attributes:
        user: The user address for whom collateral is being burned.
        amount: The amount of collateral being burned as a Decimal.
    """

    user: str
    amount: Decimal

    @field_validator("user")
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
