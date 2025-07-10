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

    @field_validator("amount", mode="before")
    def validate_numeric_string(cls, value: str, info: ValidationInfo) -> Decimal:
        """
        Validates that the provided amount is a valid hexadecimal string and converts it to a Decimal.
        Args:
            value (str): The amount string to validate.
            info (ValidationInfo): Validation context information.
        Raises:
            ValueError: If the provided amount is not a valid hexadecimal number.
        Returns:
            Decimal: The validated and converted amount as a Decimal.
        """
        try:
            return Decimal(int(value, 16))
        except ValueError:
            raise ValueError(
                f"{info.field_name} field is not a valid hexadecimal number"
            )


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

    @field_validator("amount", mode="before")
    def validate_numeric_string(cls, value: str, info: ValidationInfo) -> Decimal:
        """
        Validates that the provided amount is a valid hexadecimal string and converts it to a Decimal.
        Args:
            value (str): The amount string to validate.
            info (ValidationInfo): Validation context information.
        Raises:
            ValueError: If the provided amount is not a valid hexadecimal number.
        Returns:
            Decimal: The validated and converted amount as a Decimal.
        """
        try:
            return Decimal(int(value, 16))
        except ValueError:
            raise ValueError(
                f"{info.field_name} field is not a valid hexadecimal number"
            )


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

    @field_validator("lending_index", "borrow_index", mode="before")
    def validate_numeric_string(cls, value: str, info: ValidationInfo) -> Decimal:
        """
        Validates that the provided amount is a valid hexadecimal string and converts it to a Decimal.
        Args:
            value (str): The amount string to validate.
            info (ValidationInfo): Validation context information.
        Raises:
            ValueError: If the provided amount is not a valid hexadecimal number.
        Returns:
            Decimal: The validated and converted amount as a Decimal.
        """
        try:
            return Decimal(int(value, 16))
        except (ValueError, TypeError):
            raise ValueError(
                f"{info.field_name} field is not a valid hexadecimal number"
            )


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

    @field_validator("amount", mode="before")
    def validate_numeric_string(cls, value: str, info: ValidationInfo) -> Decimal:
        """
        Validates that the provided amount is a valid hexadecimal string and converts it to a Decimal.
        Args:
            value (str): The amount string to validate.
            info (ValidationInfo): Validation context information.
        Raises:
            ValueError: If the provided amount is not a valid hexadecimal number.
        Returns:
            Decimal: The validated and converted amount as a Decimal.
        """
        try:
            return Decimal(int(value, 16))
        except ValueError:
            raise ValueError(
                f"{info.field_name} field is not a valid hexadecimal number"
            )


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

    @field_validator("amount", mode="before")
    def validate_numeric_string(cls, value: str, info: ValidationInfo) -> Decimal:
        """
        Validates that the provided amount is a valid hexadecimal string and converts it to a Decimal.
        Args:
            value (str): The amount string to validate.
            info (ValidationInfo): Validation context information.
        Raises:
            ValueError: If the provided amount is not a valid hexadecimal number.
        Returns:
            Decimal: The validated and converted amount as a Decimal.
        """
        try:
            return Decimal(int(value, 16))
        except ValueError:
            raise ValueError(
                f"{info.field_name} field is not a valid hexadecimal number"
            )


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

    @field_validator("amount", mode="before")
    def validate_numeric_string(cls, value: str, info: ValidationInfo) -> Decimal:
        """
        Validates that the provided amount is a valid hexadecimal string and converts it to a Decimal.
        Args:
            value (str): The amount string to validate.
            info (ValidationInfo): Validation context information.
        Raises:
            ValueError: If the provided amount is not a valid hexadecimal number.
        Returns:
            Decimal: The validated and converted amount as a Decimal.
        """
        try:
            return Decimal(int(value, 16))
        except ValueError:
            raise ValueError(
                f"{info.field_name} field is not a valid hexadecimal number"
            )


class NonInterestBearingCollateralMintEventData(BaseModel):
    """
    Serializer for non-interest bearing collateral mint event data.

    Attributes:
        sender (str): The address of the sender
        recipient (str): The address of the recipient
        raw_amount (Decimal): The raw amount being transferred
    """

    sender: str
    recipient: str
    raw_amount: Decimal

    @field_validator("sender", "recipient")
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

    @field_validator("raw_amount", mode="before")
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


class NonInterestBearingCollateralBurnEventData(BaseModel):
    """
    Serializer for non-interest bearing collateral burn event data.

    Attributes:
        user (str): The address of the user
        face_amount (Decimal): The face amount being burned
    """

    user: str
    face_amount: Decimal

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

    @field_validator("face_amount", mode="before")
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

#
# """ This module contains the data models and parser class for zkLend data events. """
# from decimal import Decimal
# from pydantic import BaseModel, ValidationInfo, field_validator
# from shared.helpers import add_leading_zeros
#
#
# class DebtMintEventData(BaseModel):
#     """
#     Class for representing debt mint event data.
#
#     Attributes:
#         user (str): The address of the user associated with the debt mint event.
#         amount (str): The amount minted in the debt mint event.
#
#     Returns:
#         DebtMintEventData: A Pydantic model with the parsed and validated event data in a human-readable format.
#     """
#
#     user: str
#     amount: str
#
#     @field_validator("user")
#     def validate_address(cls, value: str, info: ValidationInfo) -> str:
#         """
#         Validates that the provided address starts with '0x' and
#         formats it with leading zeros.
#
#         Args:
#             value (str): The address string to validate.
#
#         Returns:
#             str: The validated and formatted address.
#
#         Raises:
#             ValueError: If the provided address does not start with '0x'.
#         """
#         if not value.startswith("0x"):
#             raise ValueError(f"Invalid address provided for {info.field_name}")
#         return add_leading_zeros(value)
#
#     @field_validator("amount")
#     def validate_numeric_string(cls, value: str, info: ValidationInfo) -> Decimal:
#         """
#         Validates that the provided amount is numeric and converts it to a Decimal.
#
#         Args:
#             value (str): The amount string to validate.
#
#         Returns:
#             Decimal: The validated and converted amount as a Decimal.
#
#         Raises:
#             ValueError: If the provided amount is not numeric.
#         """
#         try:
#             return Decimal(int(value, 16))
#         except ValueError:
#             raise ValueError(
#                 f"{info.field_name} field is not a valid hexadecimal number"
#             )
#
#
# class DebtBurnEventData(BaseModel):
#     """
#     Class for representing debt burn event data.
#
#     Attributes:
#         user (str): The address of the user associated with the debt burn event.
#         amount (str): The amount burned in the debt burn event.
#
#     Returns:
#         DebtBurnEventData: A Pydantic model with the parsed and validated event data in a human-readable format.
#     """
#
#     user: str
#     amount: str
#
#     @field_validator("user")
#     def validate_address(cls, value: str, info: ValidationInfo) -> str:
#         """
#         Validates that the provided address starts with '0x' and
#         formats it with leading zeros.
#
#         Args:
#             value (str): The address string to validate.
#
#         Returns:
#             str: The validated and formatted address.
#
#         Raises:
#             ValueError: If the provided address does not start with '0x'.
#         """
#         if not value.startswith("0x"):
#             raise ValueError(f"Invalid address provided for {info.field_name}")
#         return add_leading_zeros(value)
#
#     @field_validator("amount")
#     def validate_numeric_string(cls, value: str, info: ValidationInfo) -> Decimal:
#         """
#         Validates that the provided amount is numeric and converts it to a Decimal.
#
#         Args:
#             value (str): The amount string to validate.
#
#         Returns:
#             Decimal: The validated and converted amount as a Decimal.
#
#         Raises:
#             ValueError: If the provided amount is not numeric.
#         """
#         try:
#             return Decimal(int(value, 16))
#         except ValueError:
#             raise ValueError(
#                 f"{info.field_name} field is not a valid hexadecimal number"
#             )
#
#
# class NonInterestBearingCollateralMintEventData(BaseModel):
#     """
#     Serializer for non-interest bearing collateral mint event data.
#
#     Attributes:
#         sender (str): The address of the sender
#         recipient (str): The address of the recipient
#         raw_amount (str): The raw amount being transferred
#     """
#     sender: str
#     recipient: str
#     raw_amount: Decimal
#
#     @field_validator("sender", "recipient")
#     def validate_address(cls, value: str, info: ValidationInfo) -> str:
#         """
#         Validates that the provided address starts with '0x' and
#         formats it with leading zeros.
#
#         Args:
#             value (str): The address string to validate.
#
#         Returns:
#             str: The validated and formatted address.
#
#         Raises:
#             ValueError: If the provided address does not start with '0x'.
#         """
#         if not value.startswith("0x"):
#             raise ValueError(f"Invalid address provided for {info.field_name}")
#         return add_leading_zeros(value)
#
#     @field_validator("raw_amount")
#     def validate_numeric_string(cls, value: str, info: ValidationInfo) -> Decimal:
#         """
#         Validates that the provided amount is numeric and converts it to a Decimal.
#
#         Args:
#             value (str): The amount string to validate.
#
#         Returns:
#             Decimal: The validated and converted amount as a Decimal.
#
#         Raises:
#             ValueError: If the provided amount is not numeric.
#         """
#         try:
#             return Decimal(int(value, 16))
#         except ValueError:
#             raise ValueError(
#                 f"{info.field_name} field is not a valid hexadecimal number"
#             )
#
#
# class NonInterestBearingCollateralBurnEventData(BaseModel):
#     """
#     Serializer for non-interest bearing collateral burn event data.
#
#     Attributes:
#         user (str): The address of the user
#         face_amount (str): The face amount being burned
#     """
#     user: str
#     face_amount: Decimal
#
#     @field_validator("user")
#     def validate_address(cls, value: str, info: ValidationInfo) -> str:
#         """
#         Validates that the provided address starts with '0x' and
#         formats it with leading zeros.
#
#         Args:
#             value (str): The address string to validate.
#
#         Returns:
#             str: The validated and formatted address.
#
#         Raises:
#             ValueError: If the provided address does not start with '0x'.
#         """
#         if not value.startswith("0x"):
#             raise ValueError(f"Invalid address provided for {info.field_name}")
#         return add_leading_zeros(value)
#
#     @field_validator("face_amount")
#     def validate_numeric_string(cls, value: str, info: ValidationInfo) -> Decimal:
#         """
#         Validates that the provided amount is numeric and converts it to a Decimal.
#
#         Args:
#             value (str): The amount string to validate.
#
#         Returns:
#             Decimal: The validated and converted amount as a Decimal.
#
#         Raises:
#             ValueError: If the provided amount is not numeric.
#         """
#         try:
#             return Decimal(int(value, 16))
#         except ValueError:
#             raise ValueError(
#                 f"{info.field_name} field is not a valid hexadecimal number"
#             )
#
#
# class InterestRateModelEventData(BaseModel):
#     """
#     Data model representing an interest rate model event in the Nostra protocol.
#
#     Attributes:
#         debt_token (str): The address of the debt token.
#         lending_index (Decimal): The lending index in hexadecimal.
#         borrow_index (Decimal): The borrow index in hexadecimal.
#     """
#     debt_token: str
#     lending_index: Decimal
#     borrow_index: Decimal
#
#     @field_validator("debt_token")
#     def validate_address(cls, value: str, info: ValidationInfo) -> str:
#         """
#         Validates and formats the token address.
#         """
#         if not value.startswith("0x"):
#             raise ValueError(f"Invalid address provided for {info.field_name}")
#         return add_leading_zeros(value)
#
#     @field_validator("lending_index", "borrow_index")
#     def validate_numeric_string(cls, value: str, info: ValidationInfo) -> Decimal:
#         """
#         Converts a hexadecimal string to a Decimal.
#         Validates that the provided value is numeric, and converts it to a proper Decimal number.
#         """
#         try:
#             return Decimal(int(value, 16)) / Decimal("1e18")
#         except ValueError:
#             raise ValueError(
#                 f"{info.field_name} field is not a valid hexadecimal number"
#             )
#
#
# class BearingCollateralMintEventData(BaseModel):
#     user: str
#     amount: Decimal
#
#     @field_validator("user")
#     def validate_address(cls, value: str, info: ValidationInfo) -> str:
#         """
#         Validates that the provided address starts with '0x' and
#         formats it with leading zeros.
#
#         Args:
#             value (str): The address string to validate.
#
#         Returns:
#             str: The validated and formatted address.
#
#         Raises:
#             ValueError: If the provided address does not start with '0x'.
#
#         """
#         if not value.startswith("0x"):
#             raise ValueError(f"Invalid address provided for {info.field_name}")
#         return add_leading_zeros(value)
#
#     @field_validator("amount")
#     def validate_numeric_string(cls, value: str, info: ValidationInfo) -> Decimal:
#         """
#         Validates that the provided amount is numeric and converts it to a Decimal.
#
#         Args:
#             value (str): The amount string to validate.
#
#         Returns:
#             Decimal: The validated and converted amount as a Decimal.
#
#         Raises:
#             ValueError: If the provided amount is not numeric.
#         """
#         try:
#             return Decimal(int(value, 16))
#         except ValueError:
#             raise ValueError(
#                 f"{info.field_name} field is not a valid hexadecimal number"
#             )
#
#
# class DebtTransferEventData(BaseModel):
#     """
#     Data model representing a debt transfer event.
#
#     Attributes:
#         sender (str): Address of the sender.
#         recipient (str): Address of the recipient.
#         amount (str): Transfer amount in hexadecimal.
#         token (str): Address of the debt token.
#     """
#     sender: str
#     recipient: str
#     amount: Decimal
#
#     @field_validator("sender", "recipient")
#     def validate_address(cls, value: str, info: ValidationInfo) -> str:
#         """
#         Validates and formats the address.
#         """
#         if not value.startswith("0x"):
#             raise ValueError(f"Invalid address provided for {info.field_name}")
#         return add_leading_zeros(value)
#
#     @field_validator("amount")
#     def validate_numeric_string(cls, value: str, info: ValidationInfo) -> Decimal:
#         """
#         Validates that the provided amount is numeric and converts it to a Decimal.
#         """
#         try:
#             return Decimal(int(value, 16))
#         except ValueError:
#             raise ValueError(
#                 f"{info.field_name} field is not a valid hexadecimal number"
#             )
#
#
# class BearingCollateralBurnEventData(BaseModel):
#     user: str
#     amount: Decimal
#
#     @field_validator("user")
#     def validate_address(cls, value: str, info: ValidationInfo) -> str:
#         """
#         Validates that the provided address starts with '0x' and
#         formats it with leading zeros.
#
#         Args:
#             value (str): The address string to validate.
#
#         Returns:
#             str: The validated and formatted address.
#
#         Raises:
#             ValueError: If the provided address does not start with '0x'.
#
#         """
#         if not value.startswith("0x"):
#             raise ValueError(f"Invalid address provided for {info.field_name}")
#         return add_leading_zeros(value)
#
#     @field_validator("amount")
#     def validate_numeric_string(cls, value: str, info: ValidationInfo) -> Decimal:
#         """
#         Validates that the provided amount is numeric and converts it to a Decimal.
#
#         Args:
#             value (str): The amount string to validate.
#
#         Returns:
#             Decimal: The validated and converted amount as a Decimal.
#
#         Raises:
#             ValueError: If the provided amount is not numeric.
#         """
#         try:
#             return Decimal(int(value, 16))
#         except ValueError:
#             raise ValueError(
#                 f"{info.field_name} field is not a valid hexadecimal number"
#             )
