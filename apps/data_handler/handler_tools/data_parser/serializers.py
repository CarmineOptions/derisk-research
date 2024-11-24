""" This module contains the data models and parser class for zkLend data events. """
from decimal import Decimal
from pydantic import BaseModel, ValidationInfo, field_validator
from shared.helpers import add_leading_zeros


class LiquidationEventData(BaseModel):
    """
    Data model representing a liquidation event in the system.

    Attributes:
        liquidator: The address of the liquidator.
        user: The address of the user.
        debt_token: The address of the debt token.
        debt_raw_amount: A numeric string of the debt_raw_amount converted to decimal.
        debt_face_amount: A numeric string of the debt_face_amount converted to decimal.
        collateral_token: The address of collateral token.
        collateral_amount: A numeric string of the collateral_amount converted to decimal.
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

        Raises:
            ValueError: If the provided address is invalid.

        Returns:
            str: Formatted address with leading zeros.
        """
        if not value.startswith("0x"):
            raise ValueError(f"Invalid address provided for {info.field_name}")
        return add_leading_zeros(value)

    @field_validator("debt_raw_amount", "debt_face_amount", "collateral_amount")
    def validate_numeric_string(cls, value: str, info: ValidationInfo) -> Decimal:
        """
        Converts a hexadecimal string value to a decimal.

        Raises:
            ValueError: If value is not a valid hexadecimal.

        Returns:
            Decimal: Converted decimal value.
        """
        try:
            return Decimal(int(value, 16))
        except ValueError:
            raise ValueError(
                f"{info.field_name} field is not a valid hexadecimal number"
            )


class RepaymentEventData(BaseModel):
    """
    Data model representing a repayment event in the system.

    Attributes:
        repayer: The address of the repayer.
        beneficiary: The address of the beneficiary.
        token: The token address used for repayment.
        raw_amount: The raw amount of the repayment in hexadecimal.
        face_amount: The face amount of the repayment in hexadecimal.
    """

    repayer: str
    beneficiary: str
    token: str
    raw_amount: str
    face_amount: str

    @field_validator("repayer", "beneficiary", "token")
    def validate_address(cls, value: str, info: ValidationInfo) -> str:
        """
        Validates if the value is a valid address and formats it to have leading zeros.

        Raises:
            ValueError: If the provided address is invalid.

        Returns:
            str: Formatted address with leading zeros.
        """
        if not value.startswith("0x"):
            raise ValueError(f"Invalid address provided for {info.field_name}")
        return add_leading_zeros(value)

    @field_validator("raw_amount", "face_amount")
    def validate_numeric_string(cls, value: str, info: ValidationInfo) -> Decimal:
        """
        Converts a hexadecimal string value to a decimal.

        Raises:
            ValueError: If value is not a valid hexadecimal.

        Returns:
            Decimal: Converted decimal value.
        """
        try:
            return Decimal(int(value, 16))
        except ValueError:
            raise ValueError(
                f"{info.field_name} field is not a valid hexadecimal number"
            )


class AccumulatorsSyncEventData(BaseModel):
    """
    Data model representing an accumulators sync event in the system.

    Attributes:
        token: The token address involved in the event.
        lending_accumulator: The lending accumulator value.
        debt_accumulator: The debt accumulator value.
    """

    token: str
    lending_accumulator: str
    debt_accumulator: str

    @field_validator("token")
    def validate_address(cls, value: str, info: ValidationInfo) -> str:
        """
        Validates if the value is a valid address and formats it to 
        have leading zeros.

        Raises:
            ValueError: If the provided address is invalid.

        Returns:
            str: Formatted address with leading zeros.
        """
        if not value.startswith("0x"):
            raise ValueError(f"Invalid address provided for {info.field_name}")
        return add_leading_zeros(value)

    @field_validator("lending_accumulator", "debt_accumulator")
    def validate_numeric_string(cls, value: str, info: ValidationInfo) -> Decimal:
        """
        Converts a hexadecimal string value to a decimal.

        Raises:
            ValueError: If value is not a valid hexadecimal.

        Returns:
            Decimal: Converted decimal value.
        """
        try:
            return Decimal(int(value, 16))
        except ValueError:
            raise ValueError(
                f"{info.field_name} field is not a valid hexadecimal number"
            )


class DepositEventData(BaseModel):
    """
    Data model representing a deposit event in the system.

    Attributes:
        user: The user address making the deposit.
        token: The token address for the deposit.
        face_amount: The face amount of the deposit in hexadecimal.
    """

    user: str
    token: str
    face_amount: str

    @field_validator("user", "token")
    def validate_address(cls, value: str, info: ValidationInfo) -> str:
        """
        Validates if the value is a valid address and formats it to have leading zeros.

        Raises:
            ValueError: If the provided address is invalid.

        Returns:
            str: Formatted address with leading zeros.
        """
        if not value.startswith("0x"):
            raise ValueError(f"Invalid address provided for {info.field_name}")
        return add_leading_zeros(value)

    @field_validator("face_amount")
    def validate_numeric_string(cls, value: str, info: ValidationInfo) -> Decimal:
        """
        Converts a hexadecimal string value to a decimal.

        Raises:
            ValueError: If value is not a valid hexadecimal.

        Returns:
            Decimal: Converted decimal value.
        """
        try:
            return Decimal(int(value, 16))
        except ValueError:
            raise ValueError(
                f"{info.field_name} field is not a valid hexadecimal number"
            )


class BorrowingEventData(BaseModel):
    """
    Data model representing a borrowing event in the system.

    Attributes:
        user: The user address involved in borrowing.
        token: The token address borrowed.
        raw_amount: The raw amount of the borrowed tokens in hexadecimal.
        face_amount: The face amount of the borrowed tokens in hexadecimal.
    """

    user: str
    token: str
    raw_amount: str
    face_amount: str

    @field_validator("user", "token")
    def validate_address(cls, value: str, info: ValidationInfo) -> str:
        """
        Validates if the value is a valid address and formats 
        it to have leading zeros.

        Raises:
            ValueError: If the provided address is invalid.

        Returns:
            str: Formatted address with leading zeros.
        """
        if not value.startswith("0x"):
            raise ValueError(f"Invalid address provided for {info.field_name}")
        return add_leading_zeros(value)

    @field_validator("raw_amount", "face_amount")
    def validate_numeric_string(cls, value: str, info: ValidationInfo) -> Decimal:
        """
        Converts a hexadecimal string value to a decimal.

        Raises:
            ValueError: If value is not a valid hexadecimal.

        Returns:
            Decimal: Converted decimal value.
        """
        try:
            return Decimal(int(value, 16))
        except ValueError:
            raise ValueError(
                f"{info.field_name} field is not a valid hexadecimal number"
            )


class WithdrawalEventData(BaseModel):
    """
    Class for representing withdrawal event data.

    Attributes:
        user (str): The address of the user making the withdrawal.
        amount (Decimal): The amount withdrawn.
        token (str): The address of the token being withdrawn.
    """

    user: str
    amount: Decimal
    token: str

    @field_validator("user", "token")
    def validate_addresses(cls, value: str) -> str:
        """
        Validates that the provided address starts with '0x' and 
        formats it with leading zeros.

        Args:
            value (str): The address string to validate.

        Returns:
            str: The validated and formatted address.

        Raises:
            ValueError: If the provided address does not start with '0x'.
        """
        if not value.startswith("0x"):
            raise ValueError(f"Invalid address provided: {value}")
        return add_leading_zeros(value)

    @field_validator("amount", mode="before")
    def validate_amount(cls, value: str, info: ValidationInfo) -> Decimal:
        """
        Validates that the provided amount is numeric and converts it to a Decimal.

        Args:
            value (str): The amount string to validate.

        Returns:
            Decimal: The validated and converted amount as a Decimal.

        Raises:
            ValueError: If the provided amount is not numeric.
        """
        try:
            return Decimal(int(value, 16))
        except ValueError:
            raise ValueError(
                f"{info.field_name} field is not a valid hexadecimal number"
            )
        

class CollateralEnabledDisabledEventData(BaseModel):
    """ Data model representing a collateral enabled/disabled event in the system. """
    user: str
    token: str

    @field_validator("user", "token")
    def validate_valid_addresses(cls, value: str, info: ValidationInfo) -> str:
        """
        Check if the value is an address and format it to having leading zeros.
        Raises:
            ValueError
        Returns:
            str
        """
        if not value.startswith("0x"):
            raise ValueError("Invalid address provided for %s" % info.field_name)
        return add_leading_zeros(value)


class DebtMintEventData(BaseModel):
    """
    Class for representing debt mint event data.

    Attributes:
        user (str): The address of the user associated with the debt mint event.
        amount (str): The amount minted in the debt mint event.

    Returns:
        DebtMintEventData: A Pydantic model with the parsed and validated event data in a human-readable format.
    """

    user: str
    amount: str

    @field_validator("user")
    def validate_address(cls, value: str, info: ValidationInfo) -> str:
        """
        Validates that the provided address starts with '0x' and 
        formats it with leading zeros.

        Args:
            value (str): The address string to validate.

        Returns:
            str: The validated and formatted address.

        Raises:
            ValueError: If the provided address does not start with '0x'.
        """
        if not value.startswith("0x"):
            raise ValueError(f"Invalid address provided for {info.field_name}")
        return add_leading_zeros(value)

    @field_validator("amount")
    def validate_numeric_string(cls, value: str, info: ValidationInfo) -> Decimal:
        """
        Validates that the provided amount is numeric and converts it to a Decimal.

        Args:
            value (str): The amount string to validate.

        Returns:
            Decimal: The validated and converted amount as a Decimal.

        Raises:
            ValueError: If the provided amount is not numeric.
        """
        try:
            return Decimal(int(value, 16))
        except ValueError:
            raise ValueError(
                f"{info.field_name} field is not a valid hexadecimal number"
            )


class DebtBurnEventData(BaseModel):
    """
    Class for representing debt burn event data.

    Attributes:
        user (str): The address of the user associated with the debt burn event.
        amount (str): The amount burned in the debt burn event.

    Returns:
        DebtBurnEventData: A Pydantic model with the parsed and validated event data in a human-readable format.
    """

    user: str
    amount: str

    @field_validator("user")
    def validate_address(cls, value: str, info: ValidationInfo) -> str:
        """
        Validates that the provided address starts with '0x' and 
        formats it with leading zeros.

        Args:
            value (str): The address string to validate.

        Returns:
            str: The validated and formatted address.

        Raises:
            ValueError: If the provided address does not start with '0x'.
        """
        if not value.startswith("0x"):
            raise ValueError(f"Invalid address provided for {info.field_name}")
        return add_leading_zeros(value)

    @field_validator("amount")
    def validate_numeric_string(cls, value: str, info: ValidationInfo) -> Decimal:
        """
        Validates that the provided amount is numeric and converts it to a Decimal.

        Args:
            value (str): The amount string to validate.

        Returns:
            Decimal: The validated and converted amount as a Decimal.

        Raises:
            ValueError: If the provided amount is not numeric.
        """
        try:
            return Decimal(int(value, 16))
        except ValueError:
            raise ValueError(
                f"{info.field_name} field is not a valid hexadecimal number"
            )

class InterestRateModelEventData(BaseModel):
    """
    Data model representing an interest rate model event in the Nostra protocol.

    Attributes:
        debt_token (str): The address of the debt token.
        lending_index (Decimal): The lending index in hexadecimal.
        borrow_index (Decimal): The borrow index in hexadecimal.
    """
    debt_token: str
    lending_index: Decimal
    borrow_index: Decimal

    @field_validator("debt_token")
    def validate_address(cls, value: str, info: ValidationInfo) -> str:
        """
        Validates and formats the token address.
        """
        if not value.startswith("0x"):
            raise ValueError(f"Invalid address provided for {info.field_name}")
        return add_leading_zeros(value)

    @field_validator("lending_index", "borrow_index")
    def validate_numeric_string(cls, value: str, info: ValidationInfo) -> Decimal:
        """
        Converts a hexadecimal string to a Decimal.
        Validates that the provided value is numeric, and converts it to a proper Decimal number.
        """
        try:
            return Decimal(int(value, 16)) / Decimal("1e18")
        except ValueError:
            raise ValueError(
                f"{info.field_name} field is not a valid hexadecimal number"
            )


class BearingCollateralMintEventData(BaseModel):
    user: str
    amount: Decimal

    @field_validator("user")
    def validate_address(cls, value: str, info: ValidationInfo) -> str:
        """
        Validates that the provided address starts with '0x' and 
        formats it with leading zeros.

        Args:
            value (str): The address string to validate.

        Returns:
            str: The validated and formatted address.

        Raises:
            ValueError: If the provided address does not start with '0x'.

        """
        if not value.startswith("0x"):
            raise ValueError(f"Invalid address provided for {info.field_name}")
        return add_leading_zeros(value)

    @field_validator("amount")
    def validate_numeric_string(cls, value: str, info: ValidationInfo) -> Decimal:
        """
        Validates that the provided amount is numeric and converts it to a Decimal.

        Args:
            value (str): The amount string to validate.

        Returns:
            Decimal: The validated and converted amount as a Decimal.

        Raises:
            ValueError: If the provided amount is not numeric.
        """
        try:
            return Decimal(int(value, 16))
        except ValueError:
            raise ValueError(
                f"{info.field_name} field is not a valid hexadecimal number"
            )


class DebtTransferEventData(BaseModel):
    """
    Data model representing a debt transfer event.

    Attributes:
        sender (str): Address of the sender.
        recipient (str): Address of the recipient.
        amount (str): Transfer amount in hexadecimal.
        token (str): Address of the debt token.
    """
    sender: str
    recipient: str
    amount: Decimal

    @field_validator("sender", "recipient")
    def validate_address(cls, value: str, info: ValidationInfo) -> str:
        """
        Validates and formats the address.
        """
        if not value.startswith("0x"):
            raise ValueError(f"Invalid address provided for {info.field_name}")
        return add_leading_zeros(value)

    @field_validator("amount")
    def validate_numeric_string(cls, value: str, info: ValidationInfo) -> Decimal:
        """
        Validates that the provided amount is numeric and converts it to a Decimal.
        """
        try:
            return Decimal(int(value, 16))
        except ValueError:
            raise ValueError(
                f"{info.field_name} field is not a valid hexadecimal number"
            )
            

class BearingCollateralBurnEventData(BaseModel):
    user: str
    amount: Decimal

    @field_validator("user")
    def validate_address(cls, value: str, info: ValidationInfo) -> str:
        """
        Validates that the provided address starts with '0x' and 
        formats it with leading zeros.

        Args:
            value (str): The address string to validate.

        Returns:
            str: The validated and formatted address.

        Raises:
            ValueError: If the provided address does not start with '0x'.

        """
        if not value.startswith("0x"):
            raise ValueError(f"Invalid address provided for {info.field_name}")
        return add_leading_zeros(value)

    @field_validator("amount")
    def validate_numeric_string(cls, value: str, info: ValidationInfo) -> Decimal:
        """
        Validates that the provided amount is numeric and converts it to a Decimal.

        Args:
            value (str): The amount string to validate.

        Returns:
            Decimal: The validated and converted amount as a Decimal.

        Raises:
            ValueError: If the provided amount is not numeric.
        """
        try:
            return Decimal(int(value, 16))
        except ValueError:
            raise ValueError(
                f"{info.field_name} field is not a valid hexadecimal number"
            )
