""" This module contains the script to compute liquidable debt for Hashstack V0 protocol. """
from data_handler.handlers.liquidable_debt.debt_handlers import (
    HashstackV0DBLiquidableDebtDataHandler,
)
from data_handler.handlers.liquidable_debt.values import (
    COLLATERAL_FIELD_NAME,
    DEBT_FIELD_NAME,
    LIQUIDABLE_DEBT_FIELD_NAME,
    PRICE_FIELD_NAME,
)
from data_handler.handlers.loan_states.hashtack_v0.events import (
    HashstackV0LoanEntity,
    HashstackV0State,
)

from data_handler.db.models import LiquidableDebt
from shared.constants import ProtocolIDs


def run() -> None:
    """
    Runs the liquidable debt computing script for zKlend protocol.
    :return: None
    """
    handler = HashstackV0DBLiquidableDebtDataHandler(
        loan_state_class=HashstackV0State, loan_entity_class=HashstackV0LoanEntity
    )

    data = handler.calculate_liquidable_debt(protocol_name=ProtocolIDs.HASHSTACK_V0.value)

    for liquidable_debt_info in data:
        db_row = LiquidableDebt(
            debt_token=liquidable_debt_info[DEBT_FIELD_NAME],
            liquidable_debt=liquidable_debt_info[LIQUIDABLE_DEBT_FIELD_NAME],
            protocol_name=ProtocolIDs.HASHSTACK_V0.value,
            collateral_token_price=liquidable_debt_info[PRICE_FIELD_NAME],
            collateral_token=liquidable_debt_info[COLLATERAL_FIELD_NAME],
        )
        handler.db_connector.write_to_db(db_row)


if __name__ == "__main__":
    run()
