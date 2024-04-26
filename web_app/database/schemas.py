from pydantic import BaseModel, EmailStr, Field
from pydantic.networks import IPvAnyAddress

from utils.values import NotificationValidationValues


class Notification(BaseModel):
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
    health_ration_level: float = Field(
        0,
        nullable=False,
        ge=NotificationValidationValues.health_ration_level_min_value,
        le=NotificationValidationValues.health_ration_level_max_value,
    )
