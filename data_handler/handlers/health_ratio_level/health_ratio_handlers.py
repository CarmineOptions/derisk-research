import uuid
import asyncio
from datetime import datetime

from db.crud import DBConnector
from db.models import HealthRatioLevel, LoanState

from handlers.helpers import TokenValues
from handlers.state import State, LoanEntity
from handlers.loan_states.zklend.events import ZkLendState, ZkLendLoanEntity
from handler_tools.constants import ProtocolIDs
from handlers.liquidable_debt.utils import Prices
from handlers.liquidable_debt.values import USER_FIELD_NAME, HEALTH_FACTOR_FIELD_NAME, TIMESTAMP_FIELD_NAME


class ZkLendHealthRatioHandler:
    """
    A handler that collects data from DB,
    computes health_ratio level and stores it in the database.

    :cvar AVAILABLE_PROTOCOLS: A list of all available protocols.
    :cvar CONNECTOR: A DB connection object.
    """
    CONNECTOR = DBConnector()

    def __init__(self):
        self.state_class = ZkLendState
        self.loan_entity_class = ZkLendLoanEntity

    def fetch_data(self, protocol_name: str) -> tuple:
        """
        Prepares the data for the given protocol.
        :param protocol_name: Protocol name.
        :return: tuple
        """
        fetched_data = self.get_data_from_db(
            protocol_name=protocol_name
        )
        interest_rate_models = self.get_interest_rate_models_from_db(
            protocol_id=protocol_name
        )

        return fetched_data, interest_rate_models

    def calculate_health_ratio(self) -> dict:
        """
        Calculates health ratio based on provided data.
        :return: A dictionary of the ready health ratio data.
        """
        data, interest_rate_models = self.fetch_data(protocol_name=ProtocolIDs.ZKLEND.value)
        state = self.state_class()

        for instance in data:
            loan_entity = self.loan_entity_class()

            loan_entity.debt = TokenValues(values=instance.debt.items())
            loan_entity.collateral = TokenValues(values=instance.collateral.items())

            state.loan_entities.update(
                {
                    instance.user: loan_entity,
                }
            )

        # Set up collateral and debt interest rate models
        state.collateral_interest_rate_models = TokenValues(
            values=interest_rate_models.collateral
        )
        state.debt_interest_rate_models = TokenValues(
            values=interest_rate_models.debt
        )

        current_prices = Prices()
        asyncio.run(current_prices.get_lp_token_prices())

        result_data = dict()
        prices = TokenValues(values=current_prices.prices.values)

        for user_id, loan_entity in state.loan_entities.items():
            risk_adjusted_collateral_usd = loan_entity.compute_collateral_usd(
                risk_adjusted=True,
                collateral_interest_rate_models=state.collateral_interest_rate_models,
                prices=prices,
            )
            debt_usd = loan_entity.compute_debt_usd(
                risk_adjusted=False,
                debt_interest_rate_models=state.debt_interest_rate_models,
                prices=prices,
            )
            health_ratio_level = loan_entity.compute_health_factor(
                standardized=False,
                risk_adjusted_collateral_usd=risk_adjusted_collateral_usd,
                debt_usd=debt_usd,
            )

            if health_ratio_level > Decimal("0"):
                result_data.update({
                        f"{uuid.uuid4()}": {
                            USER_FIELD_NAME: user_id,
                            HEALTH_FACTOR_FIELD_NAME: health_ratio_level,
                            TIMESTAMP_FIELD_NAME: datetime.now().timestamp(),
                        }
                    })

        return result_data

    @classmethod
    def get_interest_rate_models_from_db(cls, protocol_id: str) -> dict:
        """
        Returns interest rate models data from DB.
        :param protocol_id: str
        :return: dict
        """
        return cls.CONNECTOR.get_last_interest_rate_record_by_protocol_id(protocol_id=protocol_id)

    @classmethod
    def get_data_from_db(cls, protocol_name: str) -> dict:
        """
        Gets the data from the database based on the protocol name.
        :param protocol_name: The protocol name.
        :return: The data from the database.
        """
        return cls.CONNECTOR.get_loans(
            model=LoanState,
            protocol=protocol_name
        )

    @classmethod
    def write_to_db(cls, data: HealthRatioLevel = None) -> None:
        """
        Writes the data into the database.
        :param data: A dictionary of the parsed data.
        :return: None
        """
        cls.CONNECTOR.write_to_db(data)


if __name__ == "__main__":
    handler = ZkLendHealthRatioHandler()

    data = handler.calculate_health_ratio()

    for id_, health_ratio in data.items():
        instance = HealthRatioLevel(
            timestamp=health_ratio[TIMESTAMP_FIELD_NAME],
            user_id=health_ratio[USER_FIELD_NAME],
            value=health_ratio[HEALTH_FACTOR_FIELD_NAME]
        )
        handler.write_to_db(instance)
