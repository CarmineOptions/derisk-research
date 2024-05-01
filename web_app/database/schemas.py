from pydantic import BaseModel, EmailStr, Field
from pydantic.networks import IPvAnyAddress

from utils.values import NotificationValidationValues, ProtocolIDs


class Notification(BaseModel):
    """
    A notification class that validates data user entered

    :Attributes:
    email (EmailStr): The email address
    wallet_id (str): The wallet id
    telegram_id (str): The telegram id
    ip_address (str): The IP address
    health_ration_level (float): The health ration level
    """

    email: EmailStr = Field("", nullable=False)
    wallet_id: str = Field("", nullable=False)
    telegram_id: str = Field(
        "",
        nullable=False,
        min_length=NotificationValidationValues.telegram_id_min_length,
        max_length=NotificationValidationValues.telegram_id_max_length,
        pattern=NotificationValidationValues.telegram_id_pattern,
    )
    ip_address: IPvAnyAddress = Field("", nullable=False)
    health_ratio_level: float = Field(
        0,
        nullable=False,
        ge=NotificationValidationValues.health_ratio_level_min_value,
        le=NotificationValidationValues.health_ratio_level_max_value,
    )
    protocol_id: ProtocolIDs = Field("", nullable=False)
