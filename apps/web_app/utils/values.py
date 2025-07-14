import os
from dataclasses import dataclass
from enum import Enum

from dotenv import load_dotenv

load_dotenv()

DATA_HANDLER_ENDPOINT = os.environ.get("DATA_HANDLER_URL", "")
HEALTH_RATIO_URL = (
    f"{DATA_HANDLER_ENDPOINT}/health-ratio-per-user/{{protocol}}/?user_id={{user_id}}"
)
DEBT_USD_COLUMN_NAME = "Debt (USD)"
USER_COLUMN_NAME = "User"
RISK_ADJUSTED_COLLATERAL_USD_COLUMN_NAME = "Risk-adjusted collateral (USD)"


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
        f"Your health ratio level must be between {NotificationValidationValues.health_ratio_level_min_value} and {NotificationValidationValues.health_ratio_level_max_value}"
    )
    create_subscription_success_message: str = "Subscription created successfully"
    create_subscription_exception_message: str = "Please provide all needed data"
    create_subscription_description_message: str = (
        "Creates a new subscription to notifications"
    )


@dataclass(frozen=True)
class MiddlewaresValues:
    rate_limit_exceeded_message: str = "Rate limit exceeded"
    denied_access_countries: tuple[str, ...] = ("US",)
    country_access_denied_message: str = "Country access denied"
    requests_per_minute_limit: int = 5
    requests_per_hour_limit: int = 1


class ProtocolIDs(Enum):
    HASHSTACK: str = "Hashstack"
    NOSTRA_ALPHA: str = "Nostra_alpha"
    NOSTRA_MAINNET: str = "Nostra_mainnet"
    ZKLEND: str = "zkLend"
    VESU: str = "Vesu"


class ProtocolIDCodeNames(Enum):
    HASHSTACK: str = "hashstack_v1"
    NOSTRA: str = "nostra_mainnet"
    ZKLEND: str = "zklend"
    VESU: str = "Vesu"


CURRENTLY_AVAILABLE_PROTOCOLS_IDS: tuple[str, ...] = (
    "zkLend",
    "Nostra_alpha",
    "Nostra_mainnet",
    "Vesu",
)
HEALTH_RATIO_LEVEL_ALERT_VALUE: float = 0.1
