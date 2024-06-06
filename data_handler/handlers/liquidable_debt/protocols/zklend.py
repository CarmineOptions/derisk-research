import simplejson as json
from db.models import LiquidableDebt

from handlers.loan_states.zklend.events import ZkLendState
from handlers.liquidable_debt.debt_handlers import GCloudLiquidableDebtDataHandler
from handlers.liquidable_debt.values import (GS_BUCKET_NAME, GS_BUCKET_URL, USER_FIELD_NAME,
                                             PROTOCOL_FIELD_NAME, LIQUIDABLE_DEBT_FIELD_NAME,
                                             HEALTH_FACTOR_FIELD_NAME, COLLATERAL_FIELD_NAME,
                                             RISK_ADJUSTED_COLLATERAL_USD_FIELD_NAME, DEBT_FIELD_NAME,
                                             DEBT_USD_FIELD_NAME, PRICE_FIELD_NAME, LendingProtocolNames)


def run():
    handler = GCloudLiquidableDebtDataHandler(
        loan_state_class=ZkLendState,
        connection_url=GS_BUCKET_URL,
        bucket_name=GS_BUCKET_NAME,
    )

    data = handler.prepare_data(
        protocol_name=LendingProtocolNames.ZKLEND.value,
    )

    for row_number, value in data.items():
        if value.get(LIQUIDABLE_DEBT_FIELD_NAME):
            db_row = LiquidableDebt(
                liquidable_debt=value[LIQUIDABLE_DEBT_FIELD_NAME],
                protocol=value[PROTOCOL_FIELD_NAME],
                price=value[PRICE_FIELD_NAME],
                collateral_token=value[COLLATERAL_FIELD_NAME],
                debt_token=value[DEBT_FIELD_NAME],
            )
            handler.CONNECTOR.write_to_db(db_row)


if __name__ == '__main__':
    run()
