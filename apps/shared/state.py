import asyncio
from abc import ABC, abstractmethod
from collections import defaultdict
from typing import Optional

import pandas as pd

from shared.error_handler import BOT, MessageTemplates, TokenSettingsNotFound
from shared.loan_entity import LoanEntity
from shared.custom_types import (
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

    @property
    def get_protocol_name(self) -> str:
        """Returns the protocol name for the state"""
        if not self.PROTOCOL_NAME:
            raise NotImplementedError("PROTOCOL_NAME must be set in the implementing class")
        return self.PROTOCOL_NAME

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
