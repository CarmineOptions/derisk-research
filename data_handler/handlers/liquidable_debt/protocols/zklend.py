from handlers.liquidable_debt.debt_handlers import (
    GCloudLiquidableDebtDataHandler
)
from handlers.liquidable_debt.values import (
    COLLATERAL_FIELD_NAME, DEBT_FIELD_NAME,
    GS_BUCKET_NAME, GS_BUCKET_URL,
    LIQUIDABLE_DEBT_FIELD_NAME, PRICE_FIELD_NAME,
    LendingProtocolNames
)
from handlers.loan_states.zklend.events import ZkLendState, ZkLendLoanEntity

from db.models import LiquidableDebt


def run():
    handler = GCloudLiquidableDebtDataHandler(
        loan_state_class=ZkLendState,
        connection_url=GS_BUCKET_URL,
        bucket_name=GS_BUCKET_NAME,
        loan_entity_class=ZkLendLoanEntity
    )

    data = handler.prepare_data(
        protocol_name=LendingProtocolNames.ZKLEND.value,
    )

    for liquidable_debt_info in data.values():
        db_row = LiquidableDebt(
            debt_token=liquidable_debt_info[DEBT_FIELD_NAME],
            liquidable_debt=liquidable_debt_info[LIQUIDABLE_DEBT_FIELD_NAME],
            protocol_name=LendingProtocolNames.ZKLEND.value,
            collateral_token_price=liquidable_debt_info[PRICE_FIELD_NAME],
            collateral_token=liquidable_debt_info[COLLATERAL_FIELD_NAME]
        )
        handler.CONNECTOR.write_to_db(db_row)
