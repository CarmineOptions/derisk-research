from db.models import HealthRatioLevel

from handler_tools.constants import ProtocolIDs
from handlers.liquidable_debt.values import TIMESTAMP_FIELD_NAME, USER_FIELD_NAME, HEALTH_FACTOR_FIELD_NAME

from health_ratio_handlers import NostrMainnetHealthRatioHandler


def run():
    handler = NostrMainnetHealthRatioHandler()

    data = handler.calculate_health_ratio()

    for id_, health_ratio in data.items():
        instance = HealthRatioLevel(
            timestamp=health_ratio[TIMESTAMP_FIELD_NAME],
            user_id=health_ratio[USER_FIELD_NAME],
            value=health_ratio[HEALTH_FACTOR_FIELD_NAME],
            protocol_id=ProtocolIDs.NOSTRA_MAINNET.value
        )
        handler.CONNECTOR.write_to_db(instance)


if __name__ == '__main__':
    run()
