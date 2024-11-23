"""
zkLend Event Handlers

This module handles events for zkLend loan entities, tracking deposits, 
borrowings, repayments, collateral status, and liquidations.

Classes:
    - ZkLendLoanEntity: Manages deposit and collateral status for loans.
    - ZkLendState: Processes events and computes liquidatable debt.

Functions:
    - collect_token_parameters: Fetches token parameters.
    - process_*_event: Updates loan states based on events.
"""
import copy
import decimal
import logging
from typing import Optional

import pandas as pd

from data_handler.db.crud import InitializerDBConnector
from data_handler.handler_tools.data_parser.zklend import ZklendDataParser
from data_handler.handlers.helpers import get_async_symbol
from data_handler.handlers.settings import TokenSettings
from shared.helpers import add_leading_zeros
from shared.loan_entity import LoanEntity
from shared.state import State
from data_handler.handlers.loan_states.zklend.settings import (
    ZKLEND_SPECIFIC_TOKEN_SETTINGS,
)

logger = logging.getLogger(__name__)

from data_handler.handlers import blockchain_call

from shared.types import (
    InterestRateModels,
    Portfolio,
    Prices,
    TokenParameters,
    TokenValues,
    ZkLendCollateralEnabled,
    ZkLendCollateralTokenParameters,
    ZkLendDebtTokenParameters,
)

ZKLEND_MARKET: str = ("0x04c0a5193d58f74fbace4b74dcf65481e734ed1714121bdc571da345540efa05")
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

# ZKLEND_SPECIFIC_TOKEN_SETTINGS = asyncio.run(fetch_zklend_specific_token_settings())


class ZkLendLoanEntity(LoanEntity):
    """
    A class that describes the zkLend loan entity. On top of the abstract `LoanEntity`, 
    it implements the `deposit` and
    `collateral_enabled` attributes in order to help with accounting for the changes in 
    collateral. This is because
    under zkLend, collateral is the amount deposited that is specificaly flagged with
      `collateral_enabled` set to True
    for the given token. To properly account for the changes in collateral, we must hold the 
    information about the
    given token's deposits being enabled as collateral or not and the amount of the deposits. 
    We keep all balances in raw
    amounts.
    """

    TOKEN_SETTINGS: dict[str, TokenSettings] = ZKLEND_SPECIFIC_TOKEN_SETTINGS

    def __init__(self) -> None:
        super().__init__()
        self.deposit: Portfolio = Portfolio()
        self.collateral_enabled: ZkLendCollateralEnabled = ZkLendCollateralEnabled()

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
                risk_adjusted=True,
                collateral_interest_rate_model=collateral_interest_rate_models,
                prices=prices,
            )
        if debt_usd is None:
            debt_usd = self.compute_debt_usd(
                risk_adjusted=False,
                debt_interest_rate_model=debt_interest_rate_models,
                prices=prices,
            )

        if debt_usd == decimal.Decimal("0"):
            return decimal.Decimal("Inf")

        return risk_adjusted_collateral_usd / debt_usd

    def compute_debt_to_be_liquidated(
        self,
        collateral_token_underlying_address: str,
        debt_token_underlying_address: str,
        prices: Prices,
        collateral_token_parameters: TokenParameters,
        collateral_interest_rate_model: Optional[InterestRateModels] = None,
        debt_token_parameters: TokenParameters | None = None,
        debt_interest_rate_model: Optional[InterestRateModels] = None,
        risk_adjusted_collateral_usd: Optional[decimal.Decimal] = None,
        debt_usd: Optional[decimal.Decimal] = None,
    ) -> decimal.Decimal:
        if risk_adjusted_collateral_usd is None:
            risk_adjusted_collateral_usd = self.compute_collateral_usd(
                risk_adjusted=True,
                collateral_interest_rate_model=collateral_interest_rate_model,
                prices=prices,
            )
        if debt_usd is None:
            debt_usd = self.compute_debt_usd(
                risk_adjusted=False,
                debt_interest_rate_model=debt_interest_rate_model,
                prices=prices,
            )

        # TODO: Commit a PDF with the derivation of the formula?
        numerator = debt_usd - risk_adjusted_collateral_usd
        denominator = prices[debt_token_underlying_address] * (
            1 - collateral_token_parameters[collateral_token_underlying_address].collateral_factor *
            (
                1 +
                collateral_token_parameters[collateral_token_underlying_address].liquidation_bonus
            )
        )
        max_debt_to_be_liquidated = numerator / denominator
        # The liquidator can't liquidate more debt than what is available.
        debt_to_be_liquidated = min(
            float(self.debt[debt_token_underlying_address]), max_debt_to_be_liquidated
        )
        return debt_to_be_liquidated


class ZkLendState(State):
    """
    A class that describes the state 
    of all zkLend loan entities. It implements methods for correct processing of every
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
        self.db_connector = InitializerDBConnector()

    def process_accumulators_sync_event(self, event: pd.Series) -> None:
        """Processes an accumulators sync event, updating collateral and 
        debt interest rate models based on the latest data."""
        # The order of the values in the `data` column is: `token`, 
        # `lending_accumulator`, `debt_accumulator`.
        # Example: 
        # https://starkscan.co/event/0x029628b89875a98c1c64ae206e7eb65669cb478a24449f3485f5e98aba6204dc_0.
        # TODO: Integrate the ZEND token once it's allowed to be borrowed or used as collateral.
        parsed_event_data = ZklendDataParser.parse_accumulators_sync_event(event["data"])

        token = add_leading_zeros(parsed_event_data.token)
        collateral_interest_rate_index = parsed_event_data.lending_accumulator
        debt_interest_rate_index = parsed_event_data.debt_accumulator

        self.interest_rate_models.collateral[token] = collateral_interest_rate_index
        self.interest_rate_models.debt[token] = debt_interest_rate_index

    def process_deposit_event(self, event: pd.Series) -> None:
        """Handles a deposit event, increasing the user's
          deposit and optionally setting it as collateral."""
        # The order of the values in the `data` column is: `user`, `token`, `face_amount`.
        # Example:
        # https://starkscan.co/event/0x036185142bb51e2c1f5bfdb1e6cef81f8ea87fd4d777990014249bf5435fd31b_3.

        data = ZklendDataParser.parse_deposit_event(event["data"])
        user, token = data.user, data.token

        raw_amount = data.face_amount / self.interest_rate_models.collateral[token]

        # add additional info block and timestamp
        self.loan_entities[user].extra_info.block = event["block_number"]
        self.loan_entities[user].extra_info.timestamp = event["timestamp"]

        self.loan_entities[user].deposit.increase_value(token=token, value=raw_amount)
        if self.loan_entities[user].collateral_enabled[token]:
            self.loan_entities[user].collateral.increase_value(token=token, value=raw_amount)
        if user == self.verbose_user:
            logging.info(
                "In block number = {}, raw amount = {} of token = {} was deposited.".format(
                    event["block_number"],
                    raw_amount,
                    token,
                )
            )

    def process_collateral_enabled_event(self, event: pd.Series) -> None:
        """Processes a collateral enablement event, 
        activating the specified token as collateral for the user."""
        # The order of the values in the `data` column is: `user`, `token`.
        # Example:
        # https://starkscan.co/event/0x036185142bb51e2c1f5bfdb1e6cef81f8ea87fd4d777990014249bf5435fd31b_6.
        user = add_leading_zeros(event["data"][0])
        token = add_leading_zeros(event["data"][1])

        # add additional info block and timestamp
        self.loan_entities[user].extra_info.block = event["block_number"]
        self.loan_entities[user].extra_info.timestamp = event["timestamp"]

        self.loan_entities[user].collateral_enabled[token] = True
        self.loan_entities[user].collateral.set_value(
            token=token,
            value=self.loan_entities[user].deposit[token],
        )
        # save last loan collateral_enabled state to db
        self.db_connector.save_collateral_enabled_by_user(
            user,
            self.loan_entities[user].collateral_enabled,
            self.loan_entities[user].collateral,
            self.loan_entities[user].debt,
        )
        if user == self.verbose_user:
            logging.info(
                "In block number = {}, collateral was enabled for token = {}.".format(
                    event["block_number"],
                    token,
                )
            )

    def process_collateral_disabled_event(self, event: pd.Series) -> None:
        """Processes a collateral disablement event, 
        setting collateral for the specified token to zero for the user."""
        # The order of the values in the `data` column is: `user`, `token`.
        # Example:
        # https://starkscan.co/event/0x0049b445bed84e0118795dbd22d76610ccac2ad626f8f04a1fc7e38113c2afe7_0.
        user = add_leading_zeros(event["data"][0])
        token = add_leading_zeros(event["data"][1])

        # add additional info block and timestamp
        self.loan_entities[user].extra_info.block = event["block_number"]
        self.loan_entities[user].extra_info.timestamp = event["timestamp"]

        self.loan_entities[user].collateral_enabled[token] = False
        self.loan_entities[user].collateral.set_value(token=token, value=decimal.Decimal("0"))
        if user == self.verbose_user:
            logging.info(
                "In block number = {}, collateral was disabled for token = {}.".format(
                    event["block_number"],
                    token,
                )
            )

    def process_withdrawal_event(self, event: pd.Series) -> None:
        """Handles a withdrawal event by reducing 
        the user's deposit and collateral, adjusting based on the raw amount withdrawn."""
        # The order of the values in the `data` column is: `user`, `token`, `face_amount`.
        # Example:
        # https://starkscan.co/event/0x03472cf7511687a55bc7247f8765c4bbd2c18b70e09b2a10a77c61f567bfd2cb_4.

        data = ZklendDataParser.parse_withdrawal_event(event["data"])
        user, token = data.user, data.token

        # Calculate the raw amount from face amount
        raw_amount = (
            decimal.Decimal(str(data.face_amount)) / self.interest_rate_models.collateral[token]
        )

        # Add additional info: block number and timestamp
        self.loan_entities[user].extra_info.block = event["block_number"]
        self.loan_entities[user].extra_info.timestamp = event["timestamp"]

        # Update the user's deposit and collateral values
        self.loan_entities[user].deposit.increase_value(token=token, value=-raw_amount)
        self.loan_entities[user].deposit.increase_value(token=token, value=-raw_amount)

        if self.loan_entities[user].collateral_enabled[token]:
            self.loan_entities[user].collateral.increase_value(token=token, value=-raw_amount)

        # Log the information if the user matches the verbose user
        if user == self.verbose_user:
            logging.info(
                "In block number = {}, raw amount = {} of token = {} was withdrawn.".format(
                    event["block_number"],
                    raw_amount,
                    token,
                )
            )

    def process_borrowing_event(self, event: pd.Series) -> None:
        """Processes a borrowing event, increasing the user's debt by the 
        raw amount borrowed for the specified token."""
        # The order of the values in the `data` column is: `user`,
        #  `token`, `raw_amount`, `face_amount`.
        # Example:
        # https://starkscan.co/event/0x076b1615750528635cf0b63ca80986b185acbd20fa37f0f2b5368a4f743931f8_3.
        data = ZklendDataParser.parse_borrowing_event(event["data"])
        user, token = data.user, data.token
        raw_amount = data.raw_amount

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
        """Processes a repayment event, updating the user’s debt by 
        reducing it according to the raw amount repaid."""
        data = ZklendDataParser.parse_repayment_event(event["data"])

        user = data.beneficiary
        token = data.token
        raw_amount = data.raw_amount

        self.loan_entities[user].debt.increase_value(token=token, value=-raw_amount)

        self.loan_entities[user].extra_info.block = event.block_number
        self.loan_entities[user].extra_info.timestamp = event.timestamp

        if user == self.verbose_user:
            logging.info(
                "In block number = {}, raw amount = {} of token = {} was repayed.".format(
                    data.block_number,
                    raw_amount,
                    token,
                )
            )

    def process_liquidation_event(self, event: pd.Series) -> None:
        """Processes a liquidation event, adjusting the user's debt and collateral 
        values based on liquidation amounts."""
        # The order of the arguments is: `liquidator`, `user`, `debt_token`,
        #  `debt_raw_amount`, `debt_face_amount`,
        # `collateral_token`, `collateral_amount`.
        # Example:
        # https://starkscan.co/event/0x07b8ec709df1066d9334d56b426c45440ca1f1bb841285a5d7b33f9d1008f256_5.

        data = ZklendDataParser.parse_liquidation_event(event["data"])
        user = data.user

        collateral_raw_amount = (
            data.collateral_amount / self.interest_rate_models.collateral[data.collateral_token]
        )
        # add additional info block and timestamp
        self.loan_entities[user].extra_info.block = event["block_number"]
        self.loan_entities[user].extra_info.timestamp = event["timestamp"]

        self.loan_entities[user].debt.increase_value(
            token=data.debt_token, value=-data.debt_raw_amount
        )
        self.loan_entities[user].deposit.increase_value(
            token=data.collateral_token, value=-collateral_raw_amount
        )
        if self.loan_entities[user].collateral_enabled[data.collateral_token]:
            self.loan_entities[user].collateral.increase_value(
                token=data.collateral_token, value=-collateral_raw_amount
            )
        if user == self.verbose_user:
            logging.info(
                "In block number = {}, debt of raw amount = {} of token = {} and collateral of raw amount = {} of "
                "token = {} were liquidated.".format(
                    event["block_number"],
                    data.debt_raw_amount,
                    data.debt_token,
                    collateral_raw_amount,
                    data.collateral_token,
                )
            )

    def compute_liquidable_debt_at_price(
        self,
        prices: Prices,
        collateral_token_underlying_address: str,
        collateral_token_price: float,
        debt_token_underlying_address: str,
    ) -> float:
        changed_prices = copy.deepcopy(prices)
        changed_prices[collateral_token_underlying_address] = collateral_token_price
        max_liquidated_amount = 0.0
        for loan_entity in self.loan_entities.values():
            # Filter out entities where the collateral token of interest is deposited as collateral.
            collateral_token_underlying_addresses = {
                token  # TODO: this assumes that `token` is the underlying address
                for token, token_amount in loan_entity.collateral.items()
                if token_amount > decimal.Decimal("0")
            }
            if (not collateral_token_underlying_address in collateral_token_underlying_addresses):
                continue

            # Filter out entities where the debt token of interest is borrowed.
            debt_token_underlying_addresses = {
                token  # TODO: this assumes that `token` is the underlying address
                for token, token_amount in loan_entity.debt.items()
                if token_amount > decimal.Decimal("0")
            }
            if debt_token_underlying_address not in debt_token_underlying_addresses:
                continue

            # Filter out entities with health factor below 1.
            risk_adjusted_collateral_usd = loan_entity.compute_collateral_usd(
                risk_adjusted=True,
                collateral_token_parameters=self.token_parameters.collateral,
                collateral_interest_rate_model=self.interest_rate_models.collateral,
                prices=changed_prices,
            )
            debt_usd = loan_entity.compute_debt_usd(
                risk_adjusted=False,
                debt_token_parameters=self.token_parameters.debt,
                debt_interest_rate_model=self.interest_rate_models.debt,
                prices=changed_prices,
            )
            health_factor = loan_entity.compute_health_factor(
                standardized=False,
                risk_adjusted_collateral_usd=risk_adjusted_collateral_usd,
                debt_usd=debt_usd,
            )
            # TODO: `health_factor` < 0 should not be possible if the data is right.
            # Should we keep the filter?
            if health_factor >= 1.0 or health_factor <= 0.0:
                continue

            # Find out how much of the `debt_token` will be liquidated. 
            # We assume that the liquidator receives the
            # collateral token of interest even though it might not be the most
            # optimal choice for the liquidator.
            max_liquidated_amount += loan_entity.compute_debt_to_be_liquidated(
                debt_token_underlying_address=debt_token_underlying_address,
                collateral_token_underlying_address=collateral_token_underlying_address,
                prices=changed_prices,
                collateral_token_parameters=self.token_parameters.collateral,
                risk_adjusted_collateral_usd=risk_adjusted_collateral_usd,
                debt_usd=debt_usd,
            )
        return max_liquidated_amount

    async def collect_token_parameters(self) -> None:
        """Collects and sets token parameters for collateral and debt 
        tokens under zkLend, including collateral factors, liquidation bonuses, and debt factors."""
        # Get the sets of unique collateral and debt tokens.
        collateral_tokens = {y for x in self.loan_entities.values() for y in x.collateral.values.keys()}
        debt_tokens = {y for x in self.loan_entities.values() for y in x.debt.values.keys()}
        logging.info(f"Collecting token parameters for collateral tokens: {collateral_tokens}")
        logging.info(f"Collecting token parameters for debt tokens: {debt_tokens}")
        # Get parameters for each collateral and debt token. Under zkLend,
        # the collateral token in the events data is
        # the underlying token directly.
        for underlying_collateral_token_address in collateral_tokens:
            underlying_collateral_token_symbol = await get_async_symbol(
                token_address=underlying_collateral_token_address
            )
            # The order of the arguments is: 
            # `enabled`, `decimals`, `z_token_address`, `interest_rate_model`,
            # `collateral_factor`, `borrow_factor`, 
            # `reserve_factor`, `last_update_timestamp`, `lending_accumulator`,
            # `debt_accumulator`, `current_lending_rate`, `current_borrowing_rate`, 
            # `raw_total_debt`, `flash_loan_fee`,
            # `liquidation_bonus`, `debt_limit`.
            reserve_data = await blockchain_call.func_call(
                addr=ZKLEND_MARKET,
                selector="get_reserve_data",
                calldata=[underlying_collateral_token_address],
            )
            collateral_token_address = add_leading_zeros(hex(reserve_data[2]))
            collateral_token_symbol = await get_async_symbol(token_address=collateral_token_address)
            self.token_parameters.collateral[underlying_collateral_token_address] = (
                ZkLendCollateralTokenParameters(
                    address=collateral_token_address,
                    decimals=int(reserve_data[1]),
                    symbol=collateral_token_symbol,
                    underlying_symbol=underlying_collateral_token_symbol,
                    underlying_address=underlying_collateral_token_address,
                    collateral_factor=reserve_data[4] / 1e27,
                    liquidation_bonus=reserve_data[14] / 1e27,
                )
            )
        for underlying_debt_token_address in debt_tokens:
            underlying_debt_token_symbol = await get_async_symbol(
                token_address=underlying_debt_token_address
            )
            # The order of the arguments is: `enabled`, `decimals`, 
            # `z_token_address`, `interest_rate_model`,
            # `collateral_factor`, `borrow_factor`, `reserve_factor`, 
            # `last_update_timestamp`, `lending_accumulator`,
            # `debt_accumulator`, `current_lending_rate`, `current_borrowing_rate`, 
            # `raw_total_debt`, `flash_loan_fee`,
            # `liquidation_bonus`, `debt_limit`.
            reserve_data = await blockchain_call.func_call(
                addr=ZKLEND_MARKET,
                selector="get_reserve_data",
                calldata=[underlying_debt_token_address],
            )
            debt_token_address = add_leading_zeros(hex(reserve_data[2]))
            debt_token_symbol = await get_async_symbol(token_address=debt_token_address)
            self.token_parameters.debt[underlying_debt_token_address] = (
                ZkLendDebtTokenParameters(
                    address=debt_token_address,
                    decimals=int(reserve_data[1]),
                    symbol=debt_token_symbol,
                    underlying_symbol=underlying_debt_token_symbol,
                    underlying_address=underlying_debt_token_address,
                    debt_factor=reserve_data[5] / 1e27,
                )
            )
