from db.models import LiquidableDebt
from handlers.liquidable_debt.values import (COLLATERAL_FIELD_NAME,
                                             GS_BUCKET_NAME, GS_BUCKET_URL,
                                             LIQUIDABLE_DEBT_FIELD_NAME,
                                             PRICE_FIELD_NAME,
                                             LendingProtocolNames)
from handlers.loan_states.hashtack_v0.events import HashstackV0State


def run() -> None:
    """
    Runs the liquidable debt computing script for Hashstack v0 protocol.
    :return: None
    """
    handler = GCloudLiquidableDebtDataHandler(
        loan_state_class=HashstackV0State,
        connection_url=GS_BUCKET_URL,
        bucket_name=GS_BUCKET_NAME,
    )

    data = handler.prepare_data(
        protocol_name=LendingProtocolNames.HASHSTACK_V0.value,
    )

    for debt_token, liquidable_debt_info in data.items():
        db_row = LiquidableDebt(
            debt_token=debt_token,
            liquidable_debt=liquidable_debt_info[LIQUIDABLE_DEBT_FIELD_NAME],
            protocol_name=LendingProtocolNames.HASHSTACK_V0.value,
            collateral_token_price=liquidable_debt_info[PRICE_FIELD_NAME],
            collateral_token=liquidable_debt_info[COLLATERAL_FIELD_NAME]
        )
        handler.CONNECTOR.write_to_db(db_row)
