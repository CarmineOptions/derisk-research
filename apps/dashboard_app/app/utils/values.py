import os
from dataclasses import dataclass
from shared.protocol_ids import ProtocolIDs

from dotenv import load_dotenv

load_dotenv()

DATA_HANDLER_ENDPOINT = os.environ.get("DATA_HANDLER_URL", "")
HEALTH_RATIO_URL = (
    f"{DATA_HANDLER_ENDPOINT}/health-ratio-per-user/{{protocol}}/?user_id={{user_id}}"
)
CURRENTLY_AVAILABLE_PROTOCOL_IDS = tuple(item.value for item in ProtocolIDs)


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


HEALTH_RATIO_LEVEL_ALERT_VALUE: float = 0.1
