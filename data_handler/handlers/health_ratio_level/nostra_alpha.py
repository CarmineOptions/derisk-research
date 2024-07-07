from db.models import HealthRatioLevel

from handler_tools.constants import ProtocolIDs
from handlers.liquidable_debt.values import TIMESTAMP_FIELD_NAME, USER_FIELD_NAME, HEALTH_FACTOR_FIELD_NAME

from health_ratio_handlers import NostrAlphaHealthRatioHandler


def run():
    handler = NostrAlphaHealthRatioHandler()

    data = handler.calculate_health_ratio()

    for health_ratio in data:
        instance = HealthRatioLevel(
            timestamp=health_ratio[TIMESTAMP_FIELD_NAME],
            user_id=health_ratio[USER_FIELD_NAME],
            value=health_ratio[HEALTH_FACTOR_FIELD_NAME],
            protocol_id=ProtocolIDs.NOSTRA_ALPHA.value
        )
        handler.db_connector.write_to_db(instance)


if __name__ == '__main__':
    run()
