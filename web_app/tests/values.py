from dataclasses import dataclass
from random import choice, uniform
from uuid import uuid4

import exrex
from faker import Faker

from utils.values import NotificationValidationValues, ProtocolIDs

_FAKER = Faker()


@dataclass(frozen=True)
class CreateSubscriptionTestValues:
    valid_email: str = _FAKER.email()
    invalid_email: str = "".join(str(_FAKER.email()).split("@"))
    valid_wallet_id: str = str(uuid4())
    invalid_wallet_id: str = ""
    valid_ip_v4_address: str = str(_FAKER.ipv4())
    invalid_ip_v4_address: str = f"{str(_FAKER.ipv4())}23"
    valid_health_ratio_level: float = round(
        uniform(
            NotificationValidationValues.health_ratio_level_min_value,
            NotificationValidationValues.health_ratio_level_max_value,
        ),
        2,
    )
    invalid_health_ratio_level: float = round(
        uniform(
            NotificationValidationValues.health_ratio_level_max_value,
            NotificationValidationValues.health_ratio_level_max_value + 1,
        ),
        2,
    )
    valid_protocol_id_value: str = choice([item.value for item in ProtocolIDs])
    invalid_protocol_id_value: str = _FAKER.word()


VALID_DATA = {
    "email": CreateSubscriptionTestValues.valid_email,
    "wallet_id": CreateSubscriptionTestValues.valid_wallet_id,
    "ip_address": CreateSubscriptionTestValues.valid_ip_v4_address,
    "health_ratio_level": CreateSubscriptionTestValues.valid_health_ratio_level,
    "protocol_id": CreateSubscriptionTestValues.valid_protocol_id_value,
}

INVALID_DATA = {
    "email": CreateSubscriptionTestValues.invalid_email,
    "wallet_id": CreateSubscriptionTestValues.invalid_wallet_id,
    "ip_address": CreateSubscriptionTestValues.invalid_ip_v4_address,
    "health_ratio_level": CreateSubscriptionTestValues.invalid_health_ratio_level,
    "protocol_id": CreateSubscriptionTestValues.invalid_protocol_id_value,
}
