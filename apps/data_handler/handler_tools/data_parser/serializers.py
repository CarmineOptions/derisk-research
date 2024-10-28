from decimal import Decimal

from pydantic import BaseModel, ValidationInfo, field_validator
from shared.helpers import add_leading_zeros


class AccumulatorsSyncEventData(BaseModel):
    """
    Model to parse and validate data for AccumulatorsSync event.

    This model validates and converts the lending and debt accumulators from hexadecimal
    strings to `Decimal` format, scaled by `1e27`.

    Attributes:
        token (str): The token address as a hexadecimal string.
        lending_accumulator (Decimal): The lending accumulator value, converted from hex to Decimal.
        debt_accumulator (Decimal): The debt accumulator value, converted from hex to Decimal.
    """

    token: str
    lending_accumulator: Decimal
    debt_accumulator: Decimal

    @field_validator("lending_accumulator", "debt_accumulator", mode="before")
    def hex_to_decimal(cls, v: str) -> Decimal:
        """
        Converts a hexadecimal string to a Decimal value, scaled by 1e27.

        Args:
            v (str): The hexadecimal string to be converted.

        Returns:
            Decimal: The converted decimal value scaled by 1e27.
        """
        return Decimal(int(v, 16)) / Decimal("1e27")


class LiquidationEventData(BaseModel):
    """
    Class for converting liquidation event to an object model.

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

    @field_validator("debt_raw_amount", "debt_face_amount", "collateral_amount")
    def validate_valid_numbers(cls, value: str, info: ValidationInfo) -> Decimal:
        """
        Convert the hexadecimal string value to a decimal.

        Raises:
            ValueError: If value is not a valid hexadecimal.

        Returns:
            Decimal: Converted decimal value.
        """

        if not value.isdigit():
            raise ValueError("%s field is not numeric" % info.field_name)
        return Decimal(str(int(value, base=16)))


class RepaymentEventSerializer(BaseModel):
    """
    Data model representing a repayment event in the system.

    Attributes:
        repayer (str): The address or identifier of the individual or entity making the repayment.
        beneficiary (str): The address or identifier of the individual or entity receiving the repayment.
        token (str): The type or symbol of the token being used for the repayment.
        raw_amount (str): The raw amount of the repayment as provided, before any conversions or calculations.
        face_amount (str): The face amount of the repayment, representing the value after necessary conversions.
    """

    repayer: str
    beneficiary: str
    token: str
    raw_amount: str
    face_amount: str

    @field_validator("beneficiary", "token", pre=True, always=True)
    def add_leading_zeros(cls, value: str) -> str:
        """
        Ensures the `beneficiary` and `token` fields contain leading zeros if required.

        Args:
            value (str): The value of the field to validate, typically an address or identifier.

        Returns:
            str: The value with added leading zeros if necessary, maintaining a consistent format.
        """
        return add_leading_zeros(value)

    def get_raw_amount_as_decimal(self) -> Decimal:
        """
        Converts the hexadecimal `raw_amount` to a Decimal value.

        Returns:
            Decimal: The converted decimal value of `raw_amount`.
        """
        return self.convert_hex_to_decimal(self.raw_amount)

    @classmethod
    def parse_event(cls, event: pd.Series) -> "RepaymentEventSerializer":
        """
        Parses the repayment event data into a `RepaymentEventSerializer` instance.

        Args:
            event (pd.Series): A pandas Series containing repayment event data,
                               with keys "data", "block_number", and "timestamp".

        Returns:
            RepaymentEventSerializer: An instance with parsed and validated repayment event data.
        """
        return cls(
            repayer=event["data"][0],
            beneficiary=event["data"][1],
            token=event["data"][2],
            raw_amount=event["data"][3],
            face_amount=event["data"][4],
            block_number=event["block_number"],
            timestamp=event["timestamp"],
        )

    class Config:
        """
        Configuration for the RepaymentEventSerializer model.

        Attributes:
            arbitrary_types_allowed (bool): If set to True, allows fields to accept non-standard or arbitrary types
                                            that are not strictly validated, adding flexibility for custom data types.
        """

        arbitrary_types_allowed = True

    @staticmethod
    def convert_hex_to_decimal(value: str) -> Decimal:
        """
        Converts a hexadecimal string to a Decimal, or raises an error if invalid.

        Args:
            value (str): The hexadecimal string to convert.

        Returns:
            Decimal: The converted decimal value.
        """
        try:
            return Decimal(int(value, 16))
        except ValueError:
            raise ValueError(
                "%s field is not a valid hexadecimal number" % info.field_name
            )


class EventAccumulatorsSyncData(BaseModel):
    """
    A data model representing essential event data related to token transactions.

    Attributes:
        token (str): The token address involved in the event as a hexadecimal string.
        lending_accumulator (str): The lending accumulator value associated with the token, represented as a hexadecimal string.
        debt_accumulator (str): The debt accumulator value associated with the token, represented as a hexadecimal string.

    Methods:
        from_raw_data(cls, raw_data: List[str]) -> "EventAccumulatorsSyncData":
            Creates an EventAccumulatorsSyncData instance from a list of raw data, mapping each list item to the respective attribute.
    """

    token: str
    lending_accumulator: str
    debt_accumulator: str

    @field_validator("token")
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

    @field_validator("lending_accumulator", "debt_accumulator")
    def validate_valid_numbers(cls, value: str, info: ValidationInfo) -> Decimal:
        """
        Convert the hexadecimal string value to a decimal.
        Raises:
            ValueError: If value is not a valid hexadecimal.
        Returns:
            Decimal: Converted decimal value.
        """
        try:
            return Decimal(int(value, base=16))
        except ValueError:
            raise ValueError(
                "%s field is not a valid hexadecimal number" % info.field_name
            )

    @classmethod
    def from_raw_data(cls, raw_data: list[str]) -> "EventAccumulatorsSyncData":
        """
        Class method to create an EventAccumulatorsSyncData instance from raw data.

        Args:
            raw_data (List[str]): A list containing the token, lending_accumulator, and debt_accumulator as hexadecimal strings.

        Returns:
            EventAccumulatorsSync: An iDatanstance of EventAccumulatorsSync with Datafields populated from raw_data.

        Example:
            raw_data = ["0x12345", "0xabcde", "0x54321"]
            event_data = EventAccumulatorsSync.from_Dataraw_data(raw_data)
        """
        return cls(
            token=raw_data[0],
            lending_accumulator=raw_data[1],
            debt_accumulator=raw_data[2],
        )


class EventDepositData(BaseModel):
    """
    A data model representing essential deposit event data.

    Attributes:
        user (str): The user address associated with the deposit event, represented as a string.
        token (str): The token address involved in the deposit, represented as a string.
        face_amount (str): The face value of the deposit, represented as a string.

    Methods:
        from_raw_data(cls, raw_data: Dict[str, List[str]]) -> "EventDepositData":
            Creates an EventDepositData instance from a dictionary of raw data, mapping each key to the respective attribute.
    """

    user: str
    token: str
    face_amount: str

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

    @field_validator("face_amount")
    def validate_valid_numbers(cls, value: str, info: ValidationInfo) -> Decimal:
        """
        Convert the hexadecimal string value to a decimal.
        Raises:
            ValueError: If value is not a valid hexadecimal.
        Returns:
            Decimal: Converted decimal value.
        """
        try:
            return Decimal(int(value, base=16))
        except ValueError:
            raise ValueError(
                "%s field is not a valid hexadecimal number" % info.field_name
            )

    @classmethod
    def from_raw_data(cls, raw_data: dict[str, list[str]]) -> "EventDepositData":
        """
        Class method to create an EventDepositData instance from raw data.

        Args:
            raw_data (Dict[str, List[str]]): A dictionary where the keys are field names and values are lists
                                               containing the corresponding data as strings.

        Returns:
            EventDepositData: An instance of EventDepositData with fields populated from raw_data.

        Example:
            raw_data = {
                "data": ["0x67890", "0x12345", "1000.0"]
            }
            deposit_event = EventDepositData.from_raw_data(raw_data)
        """
        return cls(
            user=raw_data["data"][0],
            token=raw_data["data"][1],
            face_amount=raw_data["data"][2],
        )


class BorrowingEventData(BaseModel):
    """
    Class for converting borrowing event to an object model.

    Attributes:
        user: The address of the user.
        token: The address of the debt token.
        raw_amount: The raw amount of the borrowed tokens.
        face_amount: The face amount of the borrowed tokens.
    """

    user: str
    token: str
    raw_amount: str
    face_amount: str

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

    @field_validator("raw_amount", "face_amount")
    def validate_valid_numbers(cls, value: str, info: ValidationInfo) -> Decimal:
        """
        Convert the hexadecimal string value to a decimal.

        Raises:
            ValueError: If value is not a valid hexadecimal.

        Returns:
            Decimal: Converted decimal value.
        """
        try:
            return Decimal(int(value, base=16))
        except ValueError:
            raise ValueError(
                "%s field is not a valid hexadecimal number" % info.field_name
            )
