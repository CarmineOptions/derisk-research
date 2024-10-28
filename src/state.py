import abc
import collections
import decimal
import json
import logging

import pandas

import src.helpers
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
        self.loan_entity_class: src.types.LoanEntity = loan_entity_class
        self.verbose_user: str | None = verbose_user
        self.loan_entities: collections.defaultdict = collections.defaultdict(
            self.loan_entity_class
        )
        self.interest_rate_models: src.types.CollateralAndDebtInterestRateModels = (
            src.types.CollateralAndDebtInterestRateModels()
        )
        self.token_parameters: src.types.CollateralAndDebtTokenParameters = (
            src.types.CollateralAndDebtTokenParameters()
        )  # TODO: move outside of State?
        self.last_block_number: int = 0

    def set_loan_entities(self, loan_entities: pandas.DataFrame) -> None:
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
                    self.loan_entities[user].collateral[collateral_token] = (
                        decimal.Decimal(str(collateral_amount))
                    )
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

    def save_loan_entities(self, path: str) -> None:
        loan_entities = []
        for user, loan_entity in self.loan_entities.items():
            # Convert each loan entity into a feasible format.
            loan_entities.append(
                {
                    "user": user,
                    "collateral": {
                        x: int(y) for x, y in loan_entity.collateral.items()
                    },
                    "debt": {x: int(y) for x, y in loan_entity.debt.items()},
                }
            )
        loan_entities = pandas.DataFrame(loan_entities)
        src.helpers.save_dataframe(data=loan_entities, path=path)
        logging.info("Saved = {} loan entities.".format(len(loan_entities)))

    def clear_loan_entities(self) -> None:
        logging.info("Clearing = {} loan entities.".format(len(self.loan_entities)))
        self.loan_entities = collections.defaultdict(self.loan_entity_class)

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
        return sum(
            loan_entity.has_debt() for loan_entity in self.loan_entities.values()
        )
