from handlers.liquidable_debt.debt_handlers import (
    DBLiquidableDebtDataHandler
)
from handlers.liquidable_debt.values import (
    COLLATERAL_FIELD_NAME, DEBT_FIELD_NAME,
    LIQUIDABLE_DEBT_FIELD_NAME, PRICE_FIELD_NAME,
)
from handlers.loan_states.zklend.events import ZkLendState, ZkLendLoanEntity
from handler_tools.constants import ProtocolIDs

from db.models import LiquidableDebt


def run() -> None:
    """
    Runs the liquidable debt computing script for zKlend protocol.
    :return: None
    """
    handler = DBLiquidableDebtDataHandler(
        loan_state_class=ZkLendState,
        loan_entity_class=ZkLendLoanEntity
    )

    data = handler.calculate_liquidable_debt(protocol_name=ProtocolIDs.ZKLEND.value)

    for liquidable_debt_info in data.values():
        db_row = LiquidableDebt(
            debt_token=liquidable_debt_info[DEBT_FIELD_NAME],
            liquidable_debt=liquidable_debt_info[LIQUIDABLE_DEBT_FIELD_NAME],
            protocol_name=ProtocolIDs.ZKLEND.value,
            collateral_token_price=liquidable_debt_info[PRICE_FIELD_NAME],
            collateral_token=liquidable_debt_info[COLLATERAL_FIELD_NAME]
        )
        handler.write_to_db(db_row)


if __name__ == '__main__':
    run()
