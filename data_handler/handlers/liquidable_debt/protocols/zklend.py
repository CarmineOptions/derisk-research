import simplejson as json
from db.models import LiquidableDebt

from handlers.loan_states.zklend.events import ZkLendState
from handlers.liquidable_debt.debt_handlers import GCloudLiquidableDebtDataHandler
from handlers.liquidable_debt.values import (GS_BUCKET_NAME, GS_BUCKET_URL, LendingProtocolNames,
                                             USER_FIELD_NAME, PROTOCOL_FIELD_NAME, LIQUIDABLE_DEBT_FIELD_NAME,
                                             HEALTH_FACTOR_FIELD_NAME, COLLATERAL_FIELD_NAME,
                                             RISK_ADJUSTED_COLLATERAL_USD_FIELD_NAME, DEBT_FIELD_NAME,
                                             DEBT_USD_FIELD_NAME)


def run():
    handler = GCloudLiquidableDebtDataHandler(
        loan_state_class=ZkLendState,
        connection_url=GS_BUCKET_URL,
        bucket_name=GS_BUCKET_NAME,
    )

    data = handler.prepare_data(
        protocol_name=LendingProtocolNames.ZKLEND.value,
    )

    for row in data:
        if data[row].get(LIQUIDABLE_DEBT_FIELD_NAME):
            [data[row][COLLATERAL_FIELD_NAME].update({
                token: json.dumps(data[row][COLLATERAL_FIELD_NAME][token])
            })
             for token in data[row][COLLATERAL_FIELD_NAME]]

            [data[row][DEBT_FIELD_NAME].update({
                token: json.dumps(data[row][DEBT_FIELD_NAME][token])
            })
                for token in data[row][DEBT_FIELD_NAME]]

            db_row = LiquidableDebt(
                protocol=LendingProtocolNames.ZKLEND.value,
                user=data[row][USER_FIELD_NAME],
                liquidable_debt=data[row][LIQUIDABLE_DEBT_FIELD_NAME],
                health_factor=data[row][HEALTH_FACTOR_FIELD_NAME],
                collateral=data[row][COLLATERAL_FIELD_NAME],
                risk_adjusted_collateral=data[row][RISK_ADJUSTED_COLLATERAL_USD_FIELD_NAME],
                debt=data[row][DEBT_FIELD_NAME],
                debt_usd=data[row][DEBT_USD_FIELD_NAME],
            )
            handler.CONNECTOR.write_to_db(db_row)
