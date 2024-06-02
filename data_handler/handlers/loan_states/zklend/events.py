import copy
import decimal
import logging
from typing import Optional

import pandas as pd

from handlers.helpers import Portfolio, TokenValues, get_symbol
from handlers.loan_states.zklend import TOKEN_SETTINGS, TokenSettings
from handlers.state import InterestRateModels, LoanEntity, State

ADDRESS: str = "0x04c0a5193d58f74fbace4b74dcf65481e734ed1714121bdc571da345540efa05"
EVENTS_METHODS_MAPPING: dict[str, str] = {
    "AccumulatorsSync": "process_accumulators_sync_event",
    "zklend::market::Market::AccumulatorsSync": "process_accumulators_sync_event",
    "Deposit": "process_deposit_event",
    "zklend::market::Market::Deposit": "process_deposit_event",
    "CollateralEnabled": "process_collateral_enabled_event",
    "zklend::market::Market::CollateralEnabled": "process_collateral_enabled_event",
    "CollateralDisabled": "process_collateral_disabled_event",
    "zklend::market::Market::CollateralDisabled": "process_collateral_disabled_event",
    "Withdrawal": "process_withdrawal_event",
    "zklend::market::Market::Withdrawal": "process_withdrawal_event",
    "Borrowing": "process_borrowing_event",
    "zklend::market::Market::Borrowing": "process_borrowing_event",
    "Repayment": "process_repayment_event",
    "zklend::market::Market::Repayment": "process_repayment_event",
    "Liquidation": "process_liquidation_event",
    "zklend::market::Market::Liquidation": "process_liquidation_event",
}


class ZkLendLoanEntity(LoanEntity):
    """
    A class that describes the zkLend loan entity. On top of the abstract `LoanEntity`, it implements the `deposit` and
    `collateral_enabled` attributes in order to help with accounting for the changes in collateral. This is because
    under zkLend, collateral is the amount deposited that is specificaly flagged with `collateral_enabled` set to True
    for the given token. To properly account for the changes in collateral, we must hold the information about the
    given token's deposits being enabled as collateral or not and the amount of the deposits. We keep all balances in raw
    amounts.
    """

    TOKEN_SETTINGS: dict[str, TokenSettings] = TOKEN_SETTINGS

    def __init__(self) -> None:
        super().__init__()
        self.deposit: Portfolio = Portfolio()
        self.collateral_enabled: TokenValues = TokenValues(init_value=False)

    def compute_health_factor(
            self,
            standardized: bool,
            collateral_interest_rate_models: Optional[InterestRateModels] = None,
            debt_interest_rate_models: Optional[InterestRateModels] = None,
            prices: Optional[TokenValues] = None,
            risk_adjusted_collateral_usd: Optional[decimal.Decimal] = None,
            debt_usd: Optional[decimal.Decimal] = None,
    ) -> decimal.Decimal:
        if risk_adjusted_collateral_usd is None:
            risk_adjusted_collateral_usd = self.compute_collateral_usd(
                collateral_interest_rate_models=collateral_interest_rate_models,
                prices=prices,
                risk_adjusted=True,
            )
        if debt_usd is None:
            debt_usd = self.compute_debt_usd(
                debt_interest_rate_models=debt_interest_rate_models,
                prices=prices,
                risk_adjusted=False,
            )
        if standardized:
            # Denominator is the value of (risk-adjusted) collateral at which the loan entity can be liquidated.
            # TODO: denominator = debt_usd * liquidation_threshold??
            denominator = debt_usd
        else:
            denominator = debt_usd
        if denominator == decimal.Decimal("0"):
            # TODO: Assumes collateral is positive.
            return decimal.Decimal("Inf")
        return risk_adjusted_collateral_usd / denominator

    def compute_debt_to_be_liquidated(
            self,
            debt_token: str,
            collateral_token: str,
            prices: TokenValues,
            collateral_interest_rate_models: Optional[InterestRateModels] = None,
            debt_interest_rate_models: Optional[InterestRateModels] = None,
            risk_adjusted_collateral_usd: Optional[decimal.Decimal] = None,
            debt_usd: Optional[decimal.Decimal] = None,
    ) -> decimal.Decimal:
        if risk_adjusted_collateral_usd is None:
            risk_adjusted_collateral_usd = self.compute_collateral_usd(
                collateral_interest_rate_models=collateral_interest_rate_models,
                prices=prices,
                risk_adjusted=True,
            )
        if debt_usd is None:
            debt_usd = self.compute_debt_usd(
                debt_interest_rate_models=debt_interest_rate_models,
                prices=prices,
                risk_adjusted=False,
            )
        # TODO: Commit a PDF with the derivation of the formula?
        numerator = debt_usd - risk_adjusted_collateral_usd
        denominator = prices.values[debt_token] * (
            1
            - self.TOKEN_SETTINGS[collateral_token].collateral_factor
            * (1 + self.TOKEN_SETTINGS[collateral_token].liquidation_bonus)
        )
        return decimal.Decimal(f"{numerator}") / denominator


class ZkLendState(State):
    """
    A class that describes the state of all zkLend loan entities. It implements methods for correct processing of every
    relevant event.
    """

    EVENTS_METHODS_MAPPING: dict[str, str] = EVENTS_METHODS_MAPPING

    def __init__(
            self,
            verbose_user: Optional[str] = None,
    ) -> None:
        super().__init__(
            loan_entity_class=ZkLendLoanEntity,
            verbose_user=verbose_user,
        )

    def process_accumulators_sync_event(self, event: pd.Series) -> None:
        # The order of the values in the `data` column is: `token`, `lending_accumulator`, `debt_accumulator`.
        # Example: https://starkscan.co/event/0x029628b89875a98c1c64ae206e7eb65669cb478a24449f3485f5e98aba6204dc_0.
        # TODO: Integrate the ZEND token once it's allowed to be borrowed or used as collateral.
        if (
                event["data"][0]
                == "0x585c32b625999e6e5e78645ff8df7a9001cf5cf3eb6b80ccdd16cb64bd3a34"
        ):
            return
        token = get_symbol(event["data"][0])
        collateral_interest_rate_index = decimal.Decimal(
            str(int(event["data"][1], base=16))
        ) / decimal.Decimal("1e27")
        debt_interest_rate_index = decimal.Decimal(
            str(int(event["data"][2], base=16))
        ) / decimal.Decimal("1e27")
        self.collateral_interest_rate_models.values[token] = (
            collateral_interest_rate_index
        )

        self.debt_interest_rate_models.values[token] = debt_interest_rate_index

    def process_deposit_event(self, event: pd.Series) -> None:
        # The order of the values in the `data` column is: `user`, `token`, `face_amount`.
        # Example: https://starkscan.co/event/0x036185142bb51e2c1f5bfdb1e6cef81f8ea87fd4d777990014249bf5435fd31b_3.
        user = event["data"][0]
        # TODO: Integrate the ZEND token once it's allowed to be borrowed or used as collateral.
        if (
                event["data"][1]
                == "0x585c32b625999e6e5e78645ff8df7a9001cf5cf3eb6b80ccdd16cb64bd3a34"
        ):
            return
        token = get_symbol(event["data"][1])
        face_amount = decimal.Decimal(str(int(event["data"][2], base=16)))
        raw_amount = face_amount / self.collateral_interest_rate_models.values[token]

        # add additional info block and timestamp
        self.loan_entities[user].extra_info.block = event["block_number"]
        self.loan_entities[user].extra_info.timestamp = event["timestamp"]

        self.loan_entities[user].deposit.increase_value(token=token, value=raw_amount)
        if self.loan_entities[user].collateral_enabled.values[token]:
            self.loan_entities[user].collateral.increase_value(
                token=token, value=raw_amount
            )
        if user == self.verbose_user:
            logging.info(
                "In block number = {}, raw amount = {} of token = {} was deposited.".format(
                    event["block_number"],
                    raw_amount,
                    token,
                )
            )

    def process_collateral_enabled_event(self, event: pd.Series) -> None:
        # The order of the values in the `data` column is: `user`, `token`.
        # Example: https://starkscan.co/event/0x036185142bb51e2c1f5bfdb1e6cef81f8ea87fd4d777990014249bf5435fd31b_6.
        user = event["data"][0]
        token = get_symbol(event["data"][1])

        # add additional info block and timestamp
        self.loan_entities[user].extra_info.block = event["block_number"]
        self.loan_entities[user].extra_info.timestamp = event["timestamp"]

        self.loan_entities[user].collateral_enabled.values[token] = True
        self.loan_entities[user].collateral.set_value(
            token=token,
            value=self.loan_entities[user].deposit.values[token],
        )
        if user == self.verbose_user:
            logging.info(
                "In block number = {}, collateral was enabled for token = {}.".format(
                    event["block_number"],
                    token,
                )
            )

    def process_collateral_disabled_event(self, event: pd.Series) -> None:
        # The order of the values in the `data` column is: `user`, `token`.
        # Example: https://starkscan.co/event/0x0049b445bed84e0118795dbd22d76610ccac2ad626f8f04a1fc7e38113c2afe7_0.
        user = event["data"][0]
        token = get_symbol(event["data"][1])

        # add additional info block and timestamp
        self.loan_entities[user].extra_info.block = event["block_number"]
        self.loan_entities[user].extra_info.timestamp = event["timestamp"]

        self.loan_entities[user].collateral_enabled.values[token] = False
        self.loan_entities[user].collateral.set_value(
            token=token, value=decimal.Decimal("0")
        )
        if user == self.verbose_user:
            logging.info(
                "In block number = {}, collateral was disabled for token = {}.".format(
                    event["block_number"],
                    token,
                )
            )

    def process_withdrawal_event(self, event: pd.Series) -> None:
        # The order of the values in the `data` column is: `user`, `token`, `face_amount`.
        # Example: https://starkscan.co/event/0x03472cf7511687a55bc7247f8765c4bbd2c18b70e09b2a10a77c61f567bfd2cb_4.
        user = event["data"][0]
        # TODO: Integrate the ZEND token once it's allowed to be borrowed or used as collateral.
        if (
                event["data"][1]
                == "0x585c32b625999e6e5e78645ff8df7a9001cf5cf3eb6b80ccdd16cb64bd3a34"
        ):
            return
        token = get_symbol(event["data"][1])
        face_amount = decimal.Decimal(str(int(event["data"][2], base=16)))
        raw_amount = face_amount / self.collateral_interest_rate_models.values[token]

        # add additional info block and timestamp
        self.loan_entities[user].extra_info.block = event["block_number"]
        self.loan_entities[user].extra_info.timestamp = event["timestamp"]

        self.loan_entities[user].deposit.increase_value(token=token, value=-raw_amount)
        if self.loan_entities[user].collateral_enabled.values[token]:
            self.loan_entities[user].collateral.increase_value(
                token=token, value=-raw_amount
            )
        if user == self.verbose_user:
            logging.info(
                "In block number = {}, raw amount = {} of token = {} was withdrawn.".format(
                    event["block_number"],
                    raw_amount,
                    token,
                )
            )

    def process_borrowing_event(self, event: pd.Series) -> None:
        # The order of the values in the `data` column is: `user`, `token`, `raw_amount`, `face_amount`.
        # Example: https://starkscan.co/event/0x076b1615750528635cf0b63ca80986b185acbd20fa37f0f2b5368a4f743931f8_3.
        user = event["data"][0]
        token = get_symbol(event["data"][1])
        raw_amount = decimal.Decimal(str(int(event["data"][2], base=16)))

        self.loan_entities[user].debt.increase_value(token=token, value=raw_amount)
        # add additional info block and timestamp
        self.loan_entities[user].extra_info.block = event["block_number"]
        self.loan_entities[user].extra_info.timestamp = event["timestamp"]
        if user == self.verbose_user:
            logging.info(
                "In block number = {}, raw amount = {} of token = {} was borrowed.".format(
                    event["block_number"],
                    raw_amount,
                    token,
                )
            )

    def process_repayment_event(self, event: pd.Series) -> None:
        # The order of the values in the `data` column is: `repayer`, `beneficiary`, `token`, `raw_amount`,
        # `face_amount`.
        # Example: https://starkscan.co/event/0x06fa3dd6e12c9a66aeacd2eefa5a2ff2915dd1bb4207596de29bd0e8cdeeae66_5.
        user = event["data"][1]
        token = get_symbol(event["data"][2])
        raw_amount = decimal.Decimal(str(int(event["data"][3], base=16)))

        self.loan_entities[user].debt.increase_value(token=token, value=-raw_amount)
        # add additional info block and timestamp
        self.loan_entities[user].extra_info.block = event["block_number"]
        self.loan_entities[user].extra_info.timestamp = event["timestamp"]
        if user == self.verbose_user:
            logging.info(
                "In block number = {}, raw amount = {} of token = {} was repayed.".format(
                    event["block_number"],
                    raw_amount,
                    token,
                )
            )

    def process_liquidation_event(self, event: pd.Series) -> None:
        # The order of the arguments is: `liquidator`, `user`, `debt_token`, `debt_raw_amount`, `debt_face_amount`,
        # `collateral_token`, `collateral_amount`.
        # Example: https://starkscan.co/event/0x07b8ec709df1066d9334d56b426c45440ca1f1bb841285a5d7b33f9d1008f256_5.
        user = event["data"][1]
        debt_token = get_symbol(event["data"][2])
        debt_raw_amount = decimal.Decimal(str(int(event["data"][3], base=16)))
        collateral_token = get_symbol(event["data"][5])
        collateral_face_amount = decimal.Decimal(str(int(event["data"][6], base=16)))
        collateral_raw_amount = (
                collateral_face_amount
                / self.collateral_interest_rate_models.values[collateral_token]
        )
        # add additional info block and timestamp
        self.loan_entities[user].extra_info.block = event["block_number"]
        self.loan_entities[user].extra_info.timestamp = event["timestamp"]

        self.loan_entities[user].debt.increase_value(
            token=debt_token, value=-debt_raw_amount
        )
        self.loan_entities[user].deposit.increase_value(
            token=collateral_token, value=-collateral_raw_amount
        )
        if self.loan_entities[user].collateral_enabled.values[collateral_token]:
            self.loan_entities[user].collateral.increase_value(
                token=collateral_token, value=-collateral_raw_amount
            )
        if user == self.verbose_user:
            logging.info(
                "In block number = {}, debt of raw amount = {} of token = {} and collateral of raw amount = {} of "
                "token = {} were liquidated.".format(
                    event["block_number"],
                    debt_raw_amount,
                    debt_token,
                    collateral_raw_amount,
                    collateral_token,
                )
            )

    def compute_liquidable_debt_at_price(
        self,
        prices: TokenValues,
        collateral_token: str,
        collateral_token_price: decimal.Decimal,
        debt_token: str,
        risk_adjusted_collateral_usd: decimal.Decimal,
        debt_usd: decimal.Decimal,
        health_factor: decimal.Decimal
    ) -> decimal.Decimal:
        changed_prices = copy.deepcopy(prices)
        changed_prices.values[collateral_token] = collateral_token_price
        max_liquidated_amount = decimal.Decimal("0")
        for loan_entity in self.loan_entities.values():
            # Filter out entities who borrowed the token of interest.
            debt_tokens = {
                token
                for token, token_amount in loan_entity.debt.values.items()
                if decimal.Decimal(token_amount) > decimal.Decimal("0")
            }
            if not debt_token in debt_tokens:
                continue

            if health_factor >= decimal.Decimal(
                "1"
            ) or health_factor <= decimal.Decimal("0"):
                continue

            # Find out how much of the `debt_token` will be liquidated.
            collateral_tokens = {
                token
                for token, token_amount in loan_entity.collateral.values.items()
                if decimal.Decimal(token_amount) > decimal.Decimal("0")
            }
            # Choose the most optimal collateral_token to be liquidated. In this case, the liquidator is indifferent.
            collateral_token = next(iter(list(collateral_tokens)))
            max_liquidated_amount += loan_entity.compute_debt_to_be_liquidated(
                debt_token=debt_token,
                collateral_token=collateral_token,
                prices=changed_prices,
                risk_adjusted_collateral_usd=risk_adjusted_collateral_usd,
                debt_usd=debt_usd,
            )
        return max_liquidated_amount
