from fastapi import Form
from pydantic import BaseModel, EmailStr, Field
from pydantic.networks import IPvAnyAddress

from utils.values import NotificationValidationValues


class NotificationForm(BaseModel):
    """
    A notification form class that validates data user entered

    :Attributes:
        email (EmailStr): The email address
        wallet_id (str): The wallet id
        telegram_id (str): The telegram id
        health_ration_level (float): The health ration level

    :Methods:
        as_form(): NotificationForm
    """

    email: EmailStr = Form(..., nullable=False)
    wallet_id: str = Form(..., nullable=False)
    telegram_id: str = Form(
        ...,
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

    @classmethod
    def as_form(
        cls,
        email: EmailStr = Form(...),
        wallet_id: str = Form(...),
        telegram_id: str = Form(...),
        health_ration_level: float = Form(...),
    ) -> "NotificationForm":
        """
        Returns a notification form class with form fields defined in
        :param email: EmailStr = Form(...)
        :param wallet_id: str = Form(...)
        :param telegram_id: str = Form(...)
        :param health_ration_level: float = Form(...)
        :return: NotificationForm
        """
        return cls(
            email=email,
            wallet_id=wallet_id,
            telegram_id=telegram_id,
            health_ration_level=health_ration_level,
        )
