from dataclasses import dataclass
from enum import Enum


@dataclass(frozen=True)
class NotificationValidationValues:
    telegram_id_min_length: int = 9
    health_ratio_level_min_value: float = 0
    health_ratio_level_max_value: float = 10
    unique_fields: tuple = tuple()
    validation_fields: tuple[str, ...] = (
        "wallet_id",
        "ip_address",
    )


@dataclass(frozen=True)
class CreateSubscriptionValues:
    health_ratio_level_validation_message: str = (
        "Your health ratio level must be between "
        f"{NotificationValidationValues.health_ratio_level_min_value} and "
        f"{NotificationValidationValues.health_ratio_level_max_value}"
    )
    create_subscription_success_message: str = "Subscription created successfully"
    create_subscription_exception_message: str = "Please provide all needed data"
    create_subscription_description_message: str = (
        "Creates a new subscription to notifications"
    )


class ProtocolIDs(Enum):
    HASHSTACK = "Hashstack"
    NOSTRA_ALPHA = "Nostra_alpha"
    NOSTRA_MAINNET = "Nostra_mainnet"
    ZKLEND = "zkLend"

HEALTH_RATIO_LEVEL_ALERT_VALUE: float = 0.1
