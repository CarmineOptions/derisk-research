""" This script is used to calculate the liquidable debt for Nostra Alpha protocol. """
from data_handler.handlers.liquidable_debt.debt_handlers import (
    NostraAlphaDBLiquidableDebtDataHandler,
)
from data_handler.handlers.liquidable_debt.values import (
    COLLATERAL_FIELD_NAME,
    DEBT_FIELD_NAME,
    LIQUIDABLE_DEBT_FIELD_NAME,
    PRICE_FIELD_NAME,
)
from data_handler.handlers.loan_states.nostra_alpha.events import (
    NostraAlphaLoanEntity,
    NostraAlphaState,
)

from data_handler.db.models import LiquidableDebt
from shared.constants import ProtocolIDs


def run() -> None:
    """
    Runs the liquidable debt computing script for zKlend protocol.
    :return: None
    """
    handler = NostraAlphaDBLiquidableDebtDataHandler(
        loan_state_class=NostraAlphaState, loan_entity_class=NostraAlphaLoanEntity
    )

    data = handler.calculate_liquidable_debt(protocol_name=ProtocolIDs.NOSTRA_ALPHA.value)

    for liquidable_debt_info in data:
        db_row = LiquidableDebt(
            debt_token=liquidable_debt_info[DEBT_FIELD_NAME],
            liquidable_debt=liquidable_debt_info[LIQUIDABLE_DEBT_FIELD_NAME],
            protocol_name=ProtocolIDs.NOSTRA_ALPHA.value,
            collateral_token_price=liquidable_debt_info[PRICE_FIELD_NAME],
            collateral_token=liquidable_debt_info[COLLATERAL_FIELD_NAME],
        )
        handler.db_connector.write_to_db(db_row)


if __name__ == "__main__":
    run()
