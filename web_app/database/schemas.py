from fastapi import Form
from pydantic import BaseModel, Field
from pydantic.networks import IPvAnyAddress
from typing import List, Dict, Any
from datetime import datetime

from utils.values import ProtocolIDs


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

    email: str = Form(nullable=True)
    wallet_id: str = Form(..., nullable=False)
    telegram_id: str = Form(
        "",
        nullable=False,
    )
    ip_address: IPvAnyAddress = Field("", nullable=False)
    health_ratio_level: float = Field(
        0,
        nullable=False,
    )
    protocol_id: ProtocolIDs = Field("", nullable=False)

    @classmethod
    def as_form(
        cls,
        email: str = Form(""),
        wallet_id: str = Form(...),
        telegram_id: str = Form(""),
        health_ratio_level: float = Form(...),
        protocol_id: ProtocolIDs = Form(...),
    ) -> "NotificationForm":
        """
        Returns a notification form class with form fields defined in
        :param email: EmailStr = Form(...)
        :param wallet_id: str = Form(...)
        :param telegram_id: str = Form(...)
        :param health_ratio_level: float = Form(...)
        :param protocol_id: ProtocolIDs = Form(...)
        :return: NotificationForm
        """
        return cls(
            email=email,
            wallet_id=wallet_id,
            telegram_id=telegram_id,
            health_ratio_level=health_ratio_level,
            protocol_id=protocol_id,
        )


class OrderBookModel(BaseModel):
    """
    A data model class that validates data user entered
    """
    token_a: str
    token_b: str
    timestamp: datetime
    block: int
    dex: str
    asks: List[Dict[str, Any]]
    bids: List[Dict[str, Any]]
