""" This script is used to compute the liquidable debt for the zKlend protocol. """
import logging

from data_handler.handlers.liquidable_debt.debt_handlers import (
    ZkLendDBLiquidableDebtDataHandler,
)
from data_handler.handlers.liquidable_debt.values import (
    COLLATERAL_FIELD_NAME,
    DEBT_FIELD_NAME,
    LIQUIDABLE_DEBT_FIELD_NAME,
    PRICE_FIELD_NAME,
)
from data_handler.handlers.loan_states.zklend.events import (
    ZkLendLoanEntity,
    ZkLendState,
)

from data_handler.db.models import LiquidableDebt
from shared.constants import ProtocolIDs

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def run() -> None:
    """
    Runs the liquidable debt computing script for zKlend protocol.
    :return: None
    """
    logger.info("Running liquidable debt computation for zKlend protocol")
    handler = ZkLendDBLiquidableDebtDataHandler(
        loan_state_class=ZkLendState, loan_entity_class=ZkLendLoanEntity
    )

    data = handler.calculate_liquidable_debt(protocol_name=ProtocolIDs.ZKLEND.value)
    logger.info(f"Data for zKlend protocol: {len(data)})")
    for liquidable_debt_info in data:
        db_row = LiquidableDebt(
            debt_token=liquidable_debt_info[DEBT_FIELD_NAME],
            liquidable_debt=liquidable_debt_info[LIQUIDABLE_DEBT_FIELD_NAME],
            protocol_name=ProtocolIDs.ZKLEND.value,
            collateral_token_price=liquidable_debt_info[PRICE_FIELD_NAME],
            collateral_token=liquidable_debt_info[COLLATERAL_FIELD_NAME],
        )
        handler.db_connector.write_to_db(db_row)
    logger.info("Successfully computed liquidable debt for zKlend protocol")


if __name__ == "__main__":
    run()
