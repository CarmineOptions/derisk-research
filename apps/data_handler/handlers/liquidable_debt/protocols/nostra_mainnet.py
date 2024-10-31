""" This script is used to compute the liquidable debt for the Nostra Mainnet protocol. """
from data_handler.handlers.liquidable_debt.debt_handlers import (
    NostraMainnetDBLiquidableDebtDataHandler,
)
from data_handler.handlers.liquidable_debt.values import (
    COLLATERAL_FIELD_NAME,
    DEBT_FIELD_NAME,
    LIQUIDABLE_DEBT_FIELD_NAME,
    PRICE_FIELD_NAME,
)
from data_handler.handlers.loan_states.nostra_mainnet.events import (
    NostraMainnetLoanEntity,
    NostraMainnetState,
)

from data_handler.db.models import LiquidableDebt
from shared.constants import ProtocolIDs


def run() -> None:
    """
    Runs the liquidable debt computing script for zKlend protocol.
    :return: None
    """
    handler = NostraMainnetDBLiquidableDebtDataHandler(
        loan_state_class=NostraMainnetState, loan_entity_class=NostraMainnetLoanEntity
    )

    data = handler.calculate_liquidable_debt(protocol_name=ProtocolIDs.NOSTRA_MAINNET.value)

    for liquidable_debt_info in data:
        db_row = LiquidableDebt(
            debt_token=liquidable_debt_info[DEBT_FIELD_NAME],
            liquidable_debt=liquidable_debt_info[LIQUIDABLE_DEBT_FIELD_NAME],
            protocol_name=ProtocolIDs.NOSTRA_MAINNET.value,
            collateral_token_price=liquidable_debt_info[PRICE_FIELD_NAME],
            collateral_token=liquidable_debt_info[COLLATERAL_FIELD_NAME],
        )
        handler.db_connector.write_to_db(db_row)


if __name__ == "__main__":
    run()
