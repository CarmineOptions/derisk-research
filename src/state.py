import abc
import collections

import pandas

import src.types



class State(abc.ABC):
    """
    A class that describes the state of all loan entities of the given lending protocol.
    """

    EVENTS_TO_METHODS: dict[str, str] = {}

    def __init__(
        self,
        loan_entity_class: src.types.LoanEntity,
        verbose_user: str | None = None,
    ) -> None:
        self.loan_entity_class: src.type.LoanEntity = loan_entity_class
        self.verbose_user: str | None = verbose_user
        self.loan_entities: collections.defaultdict = collections.defaultdict(self.loan_entity_class)
        self.interest_rate_models: src.types.CollateralAndDebtInterestRateModels = src.types.CollateralAndDebtInterestRateModels()
        self.token_parameters: src.types.CollateralAndDebtTokenParameters = src.types.CollateralAndDebtTokenParameters()
        self.last_block_number: int = 0

    # TODO: This method will likely differ across protocols. -> Leave undefined?
    def process_event(self, event: pandas.Series) -> None:
        # TODO: Save the timestamp of each update?
        assert event["block_number"] >= self.last_block_number
        self.last_block_number = event["block_number"]
        getattr(self, self.EVENTS_TO_METHODS[event["key_name"]])(event=event)

    @abc.abstractmethod
    def collect_token_parameters(self):
        pass

    # TODO: most of what the individual methods implement could be done within `LoanEntity`
    @abc.abstractmethod
    def compute_liquidable_debt_at_price(self):
        pass

    # TODO: This method will likely differ across protocols. -> Leave undefined?
    def compute_number_of_active_loan_entities(self) -> int:
        return sum(
            loan_entity.has_collateral() or loan_entity.has_debt()
            for loan_entity in self.loan_entities.values()
        )

    # TODO: This method will likely differ across protocols. -> Leave undefined?
    def compute_number_of_active_loan_entities_with_debt(self) -> int:
        return sum(loan_entity.has_debt() for loan_entity in self.loan_entities.values())