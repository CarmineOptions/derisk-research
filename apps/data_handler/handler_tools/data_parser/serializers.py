from decimal import Decimal
from pydantic import BaseModel, ValidationInfo, field_validator
from shared.helpers import add_leading_zeros
from typing import List, Any
from decimal import Decimal
from pydantic import BaseModel, ValidationInfo, field_validator


class CollateralEventData(BaseModel):
    """
    Data model representing collateral enable/disable events in the system.
    Used for both CollateralEnabled and CollateralDisabled events.

    Attributes:
        user: The address of the user whose collateral status is being modified.
        token: The address of the token being enabled/disabled as collateral.
    """

    user: str
    token: str

    @field_validator("user", "token")
    def validate_address(cls, value: str, info: ValidationInfo) -> str:
        """
        Validates if the value is a valid address and formats it to have leading zeros.

        Args:
            value (str): The address string to validate.
            info (ValidationInfo): Information about the field being validated.

        Raises:
            ValueError: If the provided address is invalid.

        Returns:
            str: Formatted address with leading zeros.
        """
        if not value.startswith("0x"):
            raise ValueError(f"Invalid address provided for {info.field_name}")
        return add_leading_zeros(value)


# Update ZkLendDataParser class with new methods
class ZkLendDataParser:
    """
    Parser class to convert zkLend data events to human-readable formats.
    """
    # ... (existing methods remain the same)

    @classmethod
    def parse_collateral_event(cls, event_data: List[Any]) -> CollateralEventData:
        """
        Parses both CollateralEnabled and CollateralDisabled event data using 
        the CollateralEventData model.

        Args:
            event_data (List[Any]): A list containing the raw event data.

        Returns:
            CollateralEventData: Parsed collateral event data.
        """
        return CollateralEventData(
            user=event_data[0],
            token=event_data[1]
        )


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
        Validates if the value is a valid address and formats it to have leading zeros.

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
        Validates that the provided address starts with '0x' and formats it with leading zeros.

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
    def validate_amount(cls, value: str) -> Decimal:
        """
        Validates that the provided amount is numeric and converts it to a Decimal.

        Args:
            value (str): The amount string to validate.

        Returns:
            Decimal: The validated and converted amount as a Decimal.

        Raises:
            ValueError: If the provided amount is not numeric.
        """
        if not value.isdigit():
            raise ValueError("Amount field is not numeric")
        return Decimal(value)


class ZkLendDataParser:
    """
    Parser class to convert zkLend data events to human-readable formats.
    """

    @classmethod
    def parse_accumulators_sync_event(
        cls, event_data: List[Any]
    ) -> AccumulatorsSyncEventData:
        """
        Parses the AccumulatorsSync event data using the AccumulatorsSyncEventData model.

        Args:
            event_data (List[Any]): A list containing the raw event data.

        Returns:
            AccumulatorsSyncEventData: Parsed event data in a human-readable format.
        """
        return AccumulatorsSyncEventData(
            token=event_data[0],
            lending_accumulator=event_data[1],
            debt_accumulator=event_data[2],
        )

    @classmethod
    def parse_deposit_event(cls, event_data: List[Any]) -> DepositEventData:
        """
        Parses the Deposit event data using the DepositEventData model.

        Args:
            event_data (List[Any]): A list containing the raw event data.

        Returns:
            DepositEventData: Parsed deposit event data.
        """
        return DepositEventData(
            user=event_data[0],
            token=event_data[1],
            face_amount=event_data[2],
        )

    @classmethod
    def parse_borrowing_event(cls, event_data: List[Any]) -> BorrowingEventData:
        """
        Parses the Borrowing event data using the BorrowingEventData model.

        Args:
            event_data (List[Any]): A list containing the raw event data.

        Returns:
            BorrowingEventData: Parsed borrowing event data.
        """
        return BorrowingEventData(
            user=event_data[0],
            token=event_data[1],
            raw_amount=event_data[2],
            face_amount=event_data[3],
        )

    @classmethod
    def parse_repayment_event(cls, event_data: List[Any]) -> RepaymentEventData:
        """
        Parses the Repayment event data using the RepaymentEventData model.

        Args:
            event_data (List[Any]): A list containing the raw repayment event data.

        Returns:
            RepaymentEventData: Parsed repayment event data.
        """
        return RepaymentEventData(
            repayer=event_data[0],
            beneficiary=event_data[1],
            token=event_data[2],
            raw_amount=event_data[3],
            face_amount=event_data[4],
        )

    @classmethod
    def parse_liquidation_event(cls, event_data: List[Any]) -> LiquidationEventData:
        """
        Parses the Liquidation event data using the LiquidationEventData model.

        Args:
            event_data (List[Any]): A list containing the raw liquidation event data.

        Returns:
            LiquidationEventData: Parsed liquidation event data.
        """
        return LiquidationEventData(
            liquidator=event_data[0],
            user=event_data[1],
            debt_token=event_data[2],
            debt_raw_amount=event_data[3],
            debt_face_amount=event_data[4],
            collateral_token=event_data[5],
            collateral_amount=event_data[6],
        )