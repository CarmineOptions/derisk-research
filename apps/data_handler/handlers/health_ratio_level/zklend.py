"""
Calculates and stores health ratios for zkLend users in the database.
"""

from data_handler.handlers.liquidable_debt.values import (
    HEALTH_FACTOR_FIELD_NAME,
    TIMESTAMP_FIELD_NAME,
    USER_FIELD_NAME,
)
from health_ratio_handlers import ZkLendHealthRatioHandler
from data_handler.db.models import HealthRatioLevel
from shared.constants import ProtocolIDs


def run():
    """
    Instantiates the ZkLendHealthRatioHandler to
      calculate health ratios for zkLend
    users and writes the computed health ratio data to the database.
    """
    handler = ZkLendHealthRatioHandler()

    data = handler.calculate_health_ratio()

    for health_ratio in data:
        instance = HealthRatioLevel(
            timestamp=health_ratio[TIMESTAMP_FIELD_NAME],
            user_id=health_ratio[USER_FIELD_NAME],
            value=health_ratio[HEALTH_FACTOR_FIELD_NAME],
            protocol_id=ProtocolIDs.ZKLEND.value,
        )
        handler.db_connector.write_to_db(instance)


if __name__ == "__main__":
    run()
