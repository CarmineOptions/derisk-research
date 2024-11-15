import asyncio
from abc import ABC, abstractmethod
from collections import defaultdict
from typing import Optional

import pandas as pd

from shared.error_handler import BOT, MessageTemplates, TokenSettingsNotFound
from shared.loan_entity import LoanEntity
from shared.types import (
    CollateralAndDebtInterestRateModels,
    CollateralAndDebtTokenParameters,
    InterestRateModels,
)


class State(ABC):
    """
    A class that describes the state of all loan entities of the given lending protocol.
    """

    PROTOCOL_NAME: str = None
    ADDRESSES_TO_TOKENS: dict[str, str] = {}
    EVENTS_METHODS_MAPPING: dict[str, str] = {}

    def __init__(
        self,
        loan_entity_class: LoanEntity,
        verbose_user: Optional[str] = None,
    ) -> None:
        self.loan_entity_class: LoanEntity = loan_entity_class
        self.verbose_user: Optional[str] = verbose_user
        self.loan_entities: defaultdict = defaultdict(self.loan_entity_class)
        # These models reflect the interest rates at which users lend/stake funds.
        self.interest_rate_models: CollateralAndDebtInterestRateModels = (
            CollateralAndDebtInterestRateModels()
        )
        # These models reflect the interest rates at which users borrow funds.
        self.debt_interest_rate_models: InterestRateModels = InterestRateModels()
        self.token_parameters: CollateralAndDebtTokenParameters = (
            CollateralAndDebtTokenParameters()
        )
        self.last_block_number: int = 0
        self.last_interest_rate_block_number: int = 0

    def set_loan_entities(self, loan_entities: pandas.DataFrame) -> None: # MB we won't need it
        # When we're processing the data for the first time, we call this method with empty `loan_entities`. In that
        # case, there's nothing to be set.
        if loan_entities.empty:
            return

        # Clear `self.loan entities` in case they were not empty.
        if len(self.loan_entities) > 0:
            self.clear_loan_entities()

        # Fill up `self.loan_entities` with `loan_entities`.
        for _, loan_entity in loan_entities.iterrows():
            user = loan_entity["user"]
            for collateral_token, collateral_amount in json.loads(
                loan_entity["collateral"].decode("utf-8")
            ).items():
                if collateral_amount:
                    self.loan_entities[user].collateral[
                        collateral_token
                    ] = decimal.Decimal(str(collateral_amount))
            for debt_token, debt_amount in json.loads(
                loan_entity["debt"].decode("utf-8")
            ).items():
                if debt_amount:
                    self.loan_entities[user].debt[debt_token] = decimal.Decimal(
                        str(debt_amount)
                    )
        logging.info(
            "Set = {} non-zero loan entities out of the former = {} loan entities.".format(
                len(self.loan_entities),
                len(loan_entities),
            )
        )

    def process_event(self, method_name: str, event: pd.Series) -> None:
        # TODO: Save the timestamp of each update?
        if event["block_number"] >= self.last_block_number:
            self.last_block_number = event["block_number"]
            method = getattr(self, method_name, "")
            if method:
                method(event)

    @abstractmethod
    def compute_liquidable_debt_at_price(self, *args, **kwargs):
        pass

    # TODO: This method will likely differ across protocols. -> Leave undefined?
    def compute_number_of_active_loan_entities(self) -> int:
        return sum(
            loan_entity.has_collateral() or loan_entity.has_debt()
            for loan_entity in self.loan_entities.values()
        )

    # TODO: This method will likely differ across protocols. -> Leave undefined?
    def compute_number_of_active_loan_entities_with_debt(self) -> int:
        return sum(
            loan_entity.has_debt() for loan_entity in self.loan_entities.values()
        )

    def get_token_name(self, address: str) -> str | None:
        """
        Get the token name from the address.
        :param address: str
        :return: str | None
        """
        # FIXME Remove Address to token mapping while doing refactoring for Nostra
        try:
            token_name = self.ADDRESSES_TO_TOKENS[address]
        except KeyError:
            asyncio.run(
                BOT.send_message(
                    message=MessageTemplates.NEW_TOKEN_MESSAGE.format(
                        protocol_name=self.PROTOCOL_NAME, address=address
                    )
                )
            )
            raise TokenSettingsNotFound(address=address, protocol=self.PROTOCOL_NAME)

        return token_name
