"""
This module handles the loan state management and event processing for Hashstack V0 protocol.
It provides classes and methods for tracking loan entities, processing loan-related events,
and computing various loan metrics.
"""

import copy
import dataclasses
import decimal
import logging
from typing import Optional

import pandas
from data_handler.handlers.helpers import get_symbol
from data_handler.db.crud import InitializerDBConnector
from shared.constants import TOKEN_SETTINGS
from shared.loan_entity import LoanEntity
from shared.state import State
from shared.types import InterestRateModels, Portfolio, TokenValues, TokenSettings

ADDRESS: str = "0x03dcf5c72ba60eb7b2fe151032769d49dd3df6b04fa3141dffd6e2aa162b7a6e"


@dataclasses.dataclass
class HashstackV0SpecificTokenSettings:
    """
    Token settings specific to Hashstack V0 protocol.
    Contains neutral values for collateral and debt factors since Hashstack V0
    doesn't use these metrics.
    """
    collateral_factor: decimal.Decimal
    debt_factor: decimal.Decimal


@dataclasses.dataclass
class TokenSettings(HashstackV0SpecificTokenSettings, TokenSettings):
    """Extended token settings class that combines Hashstack V0 specific settings 
    with base settings."""
    pass


HASHSTACK_V0_SPECIFIC_TOKEN_SETTINGS: dict[str, HashstackV0SpecificTokenSettings] = {
    "ETH": HashstackV0SpecificTokenSettings(
        collateral_factor=decimal.Decimal("1"), debt_factor=decimal.Decimal("1")
    ),
    "wBTC": HashstackV0SpecificTokenSettings(
        collateral_factor=decimal.Decimal("1"), debt_factor=decimal.Decimal("1")
    ),
    "USDC": HashstackV0SpecificTokenSettings(
        collateral_factor=decimal.Decimal("1"), debt_factor=decimal.Decimal("1")
    ),
    "DAI": HashstackV0SpecificTokenSettings(
        collateral_factor=decimal.Decimal("1"), debt_factor=decimal.Decimal("1")
    ),
    "USDT": HashstackV0SpecificTokenSettings(
        collateral_factor=decimal.Decimal("1"), debt_factor=decimal.Decimal("1")
    ),
    "wstETH": HashstackV0SpecificTokenSettings(
        collateral_factor=decimal.Decimal("1"),
        debt_factor=decimal.Decimal("1"),
    ),
    "LORDS": HashstackV0SpecificTokenSettings(
        collateral_factor=decimal.Decimal("1"),
        debt_factor=decimal.Decimal("1"),
    ),
    "STRK": HashstackV0SpecificTokenSettings(
        collateral_factor=decimal.Decimal("1"),
        debt_factor=decimal.Decimal("1"),
    ),
}

TOKEN_SETTINGS: dict[str, TokenSettings] = {
    token: TokenSettings(
        symbol=TOKEN_SETTINGS[token].symbol,
        decimal_factor=TOKEN_SETTINGS[token].decimal_factor,
        address=TOKEN_SETTINGS[token].address,
        collateral_factor=HASHSTACK_V0_SPECIFIC_TOKEN_SETTINGS[token].collateral_factor,
        debt_factor=HASHSTACK_V0_SPECIFIC_TOKEN_SETTINGS[token].debt_factor,
    )
    for token in TOKEN_SETTINGS
}

# Keys are values of the "key_name" column in the database, values are the respective method names
EVENTS_METHODS_MAPPING: dict[str, str] = {
    "new_loan": "process_new_loan_event",
    "collateral_added": "process_collateral_added_event",
    "collateral_withdrawal": "process_collateral_withdrawal_event",
    "loan_withdrawal": "process_loan_withdrawal_event",
    "loan_repaid": "process_loan_repaid_event",
    "loan_swap": "process_loan_swap_event",
    "loan_interest_deducted": "process_loan_interest_deducted_event",
    "liquidated": "process_liquidated_event",
}


class HashstackV0LoanEntity(LoanEntity):
    """Represents a loan entity in the Hashstack V0 protocol.

    Implements user, debt_category, original_collateral and borrowed_collateral attributes
    to help with accounting for collateral changes. Under Hashstack V0, each user can have
    multiple loans which are treated separately (including liquidations). The debt_category
    attribute determines liquidation conditions.

    Since Hashstack V0 provides leverage, we split collateral into original_collateral 
    (deposited directly by user) and borrowed_collateral (current state of borrowed funds).
    Uses face amounts as Hashstack V0 doesn't publish interest rate events.
    """

    TOKEN_SETTINGS: dict[str, TokenSettings] = TOKEN_SETTINGS

    def __init__(self, user: str, debt_category: int) -> None:
        super().__init__()
        self.user: str = user
        self.debt_category: int = debt_category
        self.original_collateral: Portfolio = Portfolio()
        self.borrowed_collateral: Portfolio = Portfolio()

    def compute_health_factor(
        self,
        standardized: bool,
        collateral_interest_rate_models: Optional[InterestRateModels] = None,
        debt_interest_rate_models: Optional[InterestRateModels] = None,
        prices: Optional[TokenValues] = None,
        collateral_usd: Optional[decimal.Decimal] = None,
        debt_usd: Optional[decimal.Decimal] = None,
    ) -> decimal.Decimal:
        """
        Calculate the health factor for this loan entity.

        Args:
            standardized: Whether to standardize the health factor calculation
            collateral_interest_rate_models: Models for collateral interest rates
            debt_interest_rate_models: Models for debt interest rates  
            prices: Token prices in USD
            collateral_usd: Pre-calculated collateral value in USD
            debt_usd: Pre-calculated debt value in USD

        Returns:
            Decimal representing the health factor
        """
        if collateral_usd is None:
            collateral_usd = self.compute_collateral_usd(
                risk_adjusted=False,
                collateral_interest_rate_models=collateral_interest_rate_models,
                prices=prices,
            )
        if debt_usd is None:
            debt_usd = self.compute_debt_usd(
                risk_adjusted=False,
                debt_interest_rate_models=debt_interest_rate_models,
                prices=prices,
            )

        if standardized:
            # Denominator is the value of (risk-adjusted) collateral at liquidation
            health_factor_liquidation_threshold = (
                decimal.Decimal("1.06")
                if self.debt_category == 1
                else decimal.Decimal("1.05")
                if self.debt_category == 2
                else decimal.Decimal("1.04")
            )
            denominator = health_factor_liquidation_threshold * debt_usd
        else:
            denominator = debt_usd

        if denominator == decimal.Decimal("0"):
            return decimal.Decimal("Inf")
        return collateral_usd / denominator

    def compute_debt_to_be_liquidated(
        self,
        debt_interest_rate_models: Optional[InterestRateModels] = None,
        prices: Optional[TokenValues] = None,
        debt_usd: Optional[decimal.Decimal] = None,
    ) -> decimal.Decimal:
        """
        Calculate the amount of debt that would be liquidated.

        Args:
            debt_interest_rate_models: Models for debt interest rates
            prices: Token prices in USD
            debt_usd: Pre-calculated debt value in USD
            
        Returns:
            Decimal representing the amount of debt to be liquidated
        """
        if debt_usd is None:
            debt_usd = self.compute_debt_usd(
                risk_adjusted=False,
                debt_interest_rate_models=debt_interest_rate_models,
                prices=prices,
            )
        return debt_usd
    
class HashstackV0State(State):
    """
    Describes the state of all Hashstack V0 loan entities.
    
    Implements methods for correct processing of every relevant event. Hashstack V0 events 
    contain the final state of the loan entity's collateral and debt, thus balances are 
    rewritten whenever updated.
    """

    EVENTS_METHODS_MAPPING: dict[str, str] = EVENTS_METHODS_MAPPING

    def __init__(
        self,
        verbose_user: Optional[str] = None,
    ) -> None:
        """Initialize HashstackV0State with optional verbose user for logging."""
        self.db_connector = InitializerDBConnector()
        super().__init__(
            loan_entity_class=HashstackV0LoanEntity,
            verbose_user=verbose_user,
        )

    def process_new_loan_event(self, event: pandas.Series) -> None:
        """
        Process a new loan creation event from the provided event data.
        
        The data column order is:
        [loan_record] id, owner, market, commitment, amount, empty, current_market, 
        current_amount, empty, is_loan_withdrawn, debt_category, state, l3_integration,
        created_at, [collateral] market, amount, empty, current_amount, empty, commitment,
        timelock_validity, is_timelock_activated, activation_time, [timestamp] timestamp.
        """
        # The order of the values in the `data` column is: 
        # [`loan_record`] `id`, `owner`, `market`, `commitment`,
        # `amount`, ``, `current_market`, `current_amount`, ``, 
        # `is_loan_withdrawn`, `debt_category`, `state`,
        # `l3_integration`, `created_at`, [`collateral`] `market`, `amount`, ``, 
        # `current_amount`, ``, `commitment`,
        # `timelock_validity`, `is_timelock_activated`, `activation_time`,
        #  [`timestamp`] `timestamp`.
        # Example: https://starkscan.co/event/0x04ff9acb9154603f1fc14df328a3ea53a6c\
        # 58087aaac0bfbe9cc7f2565777db8_2.
        loan_id = int(event["data"][0], base=16)
        user = event["data"][1]
        debt_token = get_symbol(event["data"][2])
        debt_face_amount = decimal.Decimal(str(int(event["data"][4], base=16)))
        borrowed_collateral_token = get_symbol(event["data"][6])
        borrowed_collateral_face_amount = decimal.Decimal(
            str(int(event["data"][7], base=16))
        )
        debt_category = int(event["data"][10], base=16)
        # Several initial loans have different structure of 'data'.
        try:
            original_collateral_token = get_symbol(event["data"][14])
            original_collateral_face_amount = decimal.Decimal(
                str(int(event["data"][17], base=16))
            )
        except KeyError:
            original_collateral_token = get_symbol(event["data"][13])
            original_collateral_face_amount = decimal.Decimal(
                str(int(event["data"][16], base=16))
            )

        self.loan_entities[loan_id] = HashstackV0LoanEntity(
            user=user, debt_category=debt_category
        )
        # TODO: Make it possible to initialize Portfolio with some token amount directly.
        original_collateral = Portfolio()
        original_collateral.values[original_collateral_token] = (
            original_collateral_face_amount
        )
        self.loan_entities[loan_id].original_collateral = original_collateral
        borrowed_collateral = Portfolio()
        borrowed_collateral.values[borrowed_collateral_token] = (
            borrowed_collateral_face_amount
        )
        self.loan_entities[loan_id].borrowed_collateral = borrowed_collateral
        # TODO: Make it easier to sum 2 Portfolio instances.
        self.loan_entities[loan_id].collateral.values = {
            token: (
                self.loan_entities[loan_id].original_collateral.values[token]
                + self.loan_entities[loan_id].borrowed_collateral.values[token]
            )
            for token in TOKEN_SETTINGS
        }
        debt = Portfolio()
        debt.values[debt_token] = debt_face_amount
        loan_entity = self.loan_entities[loan_id]
        loan_entity.debt = debt
        # add additional info block and timestamp
        loan_entity.extra_info.block = event["block_number"]
        loan_entity.extra_info.timestamp = event["timestamp"]

        self.db_connector.save_debt_category(
            user_id=user,
            loan_id=loan_id,
            debt_category=loan_entity.debt_category,
            collateral=loan_entity.collateral.values,
            debt=loan_entity.debt.values,
            original_collateral=loan_entity.original_collateral.values,
            borrowed_collateral=loan_entity.borrowed_collateral.values,
            version=0,
        )
        if self.loan_entities[loan_id].user == self.verbose_user:
            logging.info(
                "In block number = {}, face amount = {} of token = {} "
                "was borrowed against original collateral face amount = {} "
                "of token = {} and borrowed collateral face amount = {} "
                "of token = {}.".format(
                    event["block_number"],
                    debt_face_amount,
                    debt_token,
                    original_collateral_face_amount,
                    original_collateral_token,
                    original_collateral_token,
                    borrowed_collateral_face_amount,
                    borrowed_collateral_token,
                )
            )

    def process_collateral_added_event(self, event: pandas.Series) -> None:
            """
            Process an event where collateral is added to a loan.

            The data column contains: [collateral_record] market, amount, current_amount,
            commitment, timelock_validity, is_timelock_activated, activation_time,
            [loan_id], [amount_added], [timestamp].
            """
            # The order of the values in the `data` column is: [`collateral_record`] 
            # `market`, `amount`, ``,
            # `current_amount`, ``, `commitment`, `timelock_validity`, 
            # `is_timelock_activated`, `activation_time`,
            # [`loan_id`] `loan_id`, [`amount_added`] `amount_added`, ``, 
            # [`timestamp`] `timestamp`.
            # Example:
            # https://starkscan.co/event/0x02df71b02fce15f2770533328d1e645b957ac347d96bd730466a2e087f24ee07_2

            loan_id = int(event["data"][9], base=16)
            original_collateral_token = get_symbol(event["data"][0])
            original_collateral_face_amount = decimal.Decimal(
                str(int(event["data"][3], base=16))
            )
            original_collateral = Portfolio()
            original_collateral.values[original_collateral_token] = (
                original_collateral_face_amount
            )
            self.loan_entities[loan_id].original_collateral = original_collateral
            self.loan_entities[loan_id].collateral.values = {
                token: (
                    self.loan_entities[loan_id].original_collateral.values[token]
                    + self.loan_entities[loan_id].borrowed_collateral.values[token]
                )
                for token in TOKEN_SETTINGS
            }
            # add additional info block and timestamp
            self.loan_entities[loan_id].extra_info.block = event["block_number"]
            self.loan_entities[loan_id].extra_info.timestamp = event["timestamp"]
            if self.loan_entities[loan_id].user == self.verbose_user:
                logging.info(
                    "In block number = {}, collateral was added, resulting in "
                    "collateral of face amount = {} of token = {}.".format(
                        event["block_number"],
                        original_collateral_face_amount,
                        original_collateral_token,
                    )
                )

    def process_collateral_withdrawal_event(self, event: pandas.Series) -> None:
        """
        Process an event where collateral is withdrawn from a loan.

        The data column contains: [collateral_record] market, amount, current_amount,
        commitment, timelock_validity, is_timelock_activated, activation_time,
        [loan_id], [amount_withdrawn], [timestamp].
        """
        # The order of the values in the `data` column is: [`collateral_record`] 
        # `market`, `amount`, ``,
        # `current_amount`, ``, `commitment`, `timelock_validity`, 
        # `is_timelock_activated`, `activation_time`,
        # [`loan_id`] `loan_id`, [`amount_withdrawn`] `amount_withdrawn`, ``, 
        # [`timestamp`] `timestamp`.
        # Example: 
        # https://starkscan.co/event/0x03809ebcaad1647f2c6d5294706e0dc619317c240b5554848c454683a18b75ba_5.
        loan_id = int(event["data"][9], base=16)
        original_collateral_token = get_symbol(event["data"][0])
        original_collateral_face_amount = decimal.Decimal(
            str(int(event["data"][3], base=16))
        )
        original_collateral = Portfolio()
        original_collateral.values[original_collateral_token] = (
            original_collateral_face_amount
        )
        #  add additional info block and timestamp
        self.loan_entities[loan_id].extra_info.block = event["block_number"]
        self.loan_entities[loan_id].extra_info.timestamp = event["timestamp"]
        self.loan_entities[loan_id].original_collateral = original_collateral
        self.loan_entities[loan_id].collateral.values = {
            token: (
                self.loan_entities[loan_id].original_collateral.values[token]
                + self.loan_entities[loan_id].borrowed_collateral.values[token]
            )
            for token in TOKEN_SETTINGS
        }
        if self.loan_entities[loan_id].user == self.verbose_user:
            logging.info(
                "In block number = {}, collateral was withdrawn, resulting in "
                "collateral of face amount = {} of token = {}.".format(
                    event["block_number"],
                    original_collateral_face_amount,
                    original_collateral_token,
                )
            )

    def process_loan_withdrawal_event(self, event: pandas.Series) -> None:
        """
        Process an event where a loan is withdrawn.

        The data column contains: [loan_record] id, owner, market, commitment, amount,
        current_market, current_amount, is_loan_withdrawn, debt_category, state,
        l3_integration, created_at, [amount_withdrawn], [timestamp].
        """
        # The order of the values in the `data` column is: 
        # [`loan_record`] `id`, `owner`, `market`, `commitment`,
        # `amount`, ``, `current_market`, `current_amount`, ``,
        #  `is_loan_withdrawn`, `debt_category`, `state`,
        # `l3_integration`, `created_at`, [`amount_withdrawn`] 
        # `amount_withdrawn`, ``, [`timestamp`] `timestamp`.
        # Example:
        #  https://starkscan.co/event/0x05bb8614095fac1ac9b405c27e7ce870804e85 \
        # aa5924ef2494fec46792b6b8dc_2.
        loan_id = int(event["data"][0], base=16)
        user = event["data"][1]
        # TODO: Is this assert needed?
        try:
            if (
                self.loan_entities.get(loan_id)
                and self.loan_entities[loan_id].user != user
            ):
                logging.error(
                    "In block number = {}, loan was withdrawn, but the user is "
                    "different from the one in the loan entity.".format(
                        event["block_number"]
                    )
                )
                return
        except TypeError:
            print()

        # add additional info block and timestamp
        self.loan_entities[loan_id].extra_info.block = event["block_number"]
        self.loan_entities[loan_id].extra_info.timestamp = event["timestamp"]
        debt_token = get_symbol(event["data"][2])
        debt_face_amount = decimal.Decimal(str(int(event["data"][4], base=16)))
        borrowed_collateral_token = get_symbol(event["data"][6])
        borrowed_collateral_face_amount = decimal.Decimal(
            str(int(event["data"][7], base=16))
        )
        debt_category = int(event["data"][10], base=16)

        borrowed_collateral = Portfolio()
        borrowed_collateral.values[borrowed_collateral_token] = (
            borrowed_collateral_face_amount
        )
        self.loan_entities[loan_id].borrowed_collateral = borrowed_collateral
        self.loan_entities[loan_id].collateral.values = {
            token: (
                self.loan_entities[loan_id].original_collateral.values[token]
                + self.loan_entities[loan_id].borrowed_collateral.values[token]
            )
            for token in TOKEN_SETTINGS
        }
        debt = Portfolio()
        debt.values[debt_token] = debt_face_amount
        self.loan_entities[loan_id].debt = debt
        self.loan_entities[loan_id].debt_category = debt_category
        if self.loan_entities[loan_id].user == self.verbose_user:
            logging.info(
                "In block number = {}, loan was withdrawn, resulting in debt of "
                "face amount = {} of token = {} and borrowed collateral face "
                "amount = {} of token = {}.".format(
                    event["block_number"],
                    debt_face_amount,
                    debt_token,
                    borrowed_collateral_face_amount,
                    borrowed_collateral_token,
                )
            )


    def process_loan_repaid_event(self, event: pandas.Series) -> None:
            """
            Process an event where a loan is repaid.

            The data column contains: [loan_record] id, owner, market, commitment, amount,
            current_market, current_amount, is_loan_withdrawn, debt_category, state,
            l3_integration, created_at, [timestamp].
            """
            # The order of the values in the `data`
            #  column is: [`loan_record`] `id`, `owner`, `market`, `commitment`,
            # `amount`, ``, `current_market`, `current_amount`, `
            # `, `is_loan_withdrawn`, `debt_category`, `state`,
            # `l3_integration`, `created_at`, [`timestamp`] `timestamp`.
            # Example: 
            # https://starkscan.co/event/0x07731e48d33f6b916f4e4e81e9cee1d282e2 \
            # 0e970717e11ad440f73cc1a73484_1.
            loan_id = int(event["data"][0], base=16)
            user = event["data"][1]
            assert self.loan_entities[loan_id].user == user
            debt_token = get_symbol(event["data"][2])
            # This prevents repaid loans to appear as not repaid.
            debt_face_amount = decimal.Decimal("0")
            borrowed_collateral_token = get_symbol(event["data"][6])
            borrowed_collateral_face_amount = decimal.Decimal(
                str(int(event["data"][7], base=16))
            )
            # Based on the documentation, it seems that it's only possible to 
            # repay the whole amount.
            assert borrowed_collateral_face_amount == decimal.Decimal("0")
            debt_category = int(event["data"][10], base=16)

            borrowed_collateral = Portfolio()
            borrowed_collateral.values[borrowed_collateral_token] = (
                borrowed_collateral_face_amount
            )
            # add additional info block and timestamp
            self.loan_entities[loan_id].extra_info.block = event["block_number"]
            self.loan_entities[loan_id].extra_info.timestamp = event["timestamp"]

            self.loan_entities[loan_id].borrowed_collateral = borrowed_collateral
            self.loan_entities[loan_id].collateral.values = {
                token: (
                    self.loan_entities[loan_id].original_collateral.values[token]
                    + self.loan_entities[loan_id].borrowed_collateral.values[token]
                )
                for token in TOKEN_SETTINGS
            }
            debt = Portfolio()
            debt.values[debt_token] = debt_face_amount
            self.loan_entities[loan_id].debt = debt
            self.loan_entities[loan_id].debt_category = debt_category
            if self.loan_entities[loan_id].user == self.verbose_user:
                logging.info(
                    "In block number = {}, loan was repaid, resulting in debt of face "
                    "amount = {} of token = {} and borrowed collateral face amount = {} "
                    "of token = {}.".format(
                        event["block_number"],
                        debt_face_amount,
                        debt_token,
                        borrowed_collateral_face_amount,
                        borrowed_collateral_token,
                    )
                )

    def process_loan_swap_event(self, event: pandas.Series) -> None:
        """
        Process an event where a loan is swapped.

        The data column contains: [old_loan_record] id, owner, market, commitment,
        is_loan_withdrawn, debt_category, state, l3_integration, created_at,
        [new_loan_record], amount, current_market, current_amount, debt_category,
        [timestamp].
        """
        # The order of the values in the `data` column is: 
        # [`old_loan_record`] `id`, `owner`, `market`, `commit
        # , `is_loan_withdrawn`, `debt_category`, `state`,
        # `l3_integration`, `created_at`, [`new_loan_record`] `id`, `owner`, 
        # `market`, `commitment`, `amount`, ``,
        # `current_market`, `current_amount`, ``, `is_loan_withdrawn`,
        #  `debt_category`, `state`, `l3_integration`,
        # `created_at`, [`timestamp`] `timestamp`.
        # 
        # Example: https://starkscan.co/event/0x00ad0b6b00ce68a1d7f5b79cd550d7f4a15b1708b632b88985a4f6faeb42d5b1_7.
        old_loan_id = int(event["data"][0], base=16)
        old_user = event["data"][1]
        if (
            self.loan_entities.get(old_loan_id)
            and self.loan_entities[old_loan_id].user != old_user
        ):
            logging.error(
                "In block number = {}, loan was swapped, but the user is "
                "different from the one in the loan entity.".format(
                    event["block_number"]
                )
            )
            return

        new_loan_id = int(event["data"][14], base=16)
        new_user = event["data"][15]
        # TODO: Does this always have to hold?
        assert new_loan_id == old_loan_id
        # TODO: Does this always have to hold?
        assert new_user == old_user
        new_debt_token = get_symbol(event["data"][16])
        new_debt_face_amount = decimal.Decimal(str(int(event["data"][18], base=16)))
        new_borrowed_collateral_token = get_symbol(event["data"][20])
        new_borrowed_collateral_face_amount = decimal.Decimal(
            str(int(event["data"][21], base=16))
        )
        new_debt_category = int(event["data"][24], base=16)

        new_borrowed_collateral = Portfolio()
        new_borrowed_collateral.values[new_borrowed_collateral_token] = (
            new_borrowed_collateral_face_amount
        )
        # add additional info block and timestamp
        self.loan_entities[new_loan_id].extra_info.block = event["block_number"]
        self.loan_entities[new_loan_id].extra_info.timestamp = event["timestamp"]

        self.loan_entities[new_loan_id].borrowed_collateral = new_borrowed_collateral
        self.loan_entities[new_loan_id].collateral.values = {
            token: (
                self.loan_entities[new_loan_id].original_collateral.values[token]
                + self.loan_entities[new_loan_id].borrowed_collateral.values[token]
            )
            for token in TOKEN_SETTINGS
        }
        new_debt = Portfolio()
        new_debt.values[new_debt_token] = new_debt_face_amount
        # Based on the documentation, it seems that it's only possible to swap the whole amount.
        if self.loan_entities[old_loan_id].debt.values == new_debt.values:
            logging.error(
                "In block number = {}, loan was swapped, but the debt stayed "
                "the same.".format(event["block_number"])
            )
            return
        self.loan_entities[new_loan_id].debt = new_debt
        self.loan_entities[new_loan_id].debt_category = new_debt_category
        if self.loan_entities[new_loan_id].user == self.verbose_user:
            logging.info(
                "In block number = {}, loan was swapped, resulting in debt of face "
                "amount = {} of token = {} and borrowed collateral face amount = {} "
                "of token = {}.".format(
                    event["block_number"],
                    new_debt_face_amount,
                    new_debt_token,
                    new_borrowed_collateral_face_amount,
                    new_borrowed_collateral_token,
                )
            )

    def process_loan_interest_deducted_event(self, event: pandas.Series) -> None:
        """
        Process an event where loan interest is deducted.

        The data column contains: [collateral_record] market, amount, current_amount,
        commitment, timelock_validity, is_timelock_activated, activation_time,
        [accrued_interest], [loan_id], [amount_withdrawn], [timestamp].
        """
        # The order of the values in the 
        # `data` column is: [`collateral_record`] `market`, `amount`, ``,
        # `current_amount`, ``, `commitment`, `timelock_validity`, 
        # `is_timelock_activated`, `activation_time`,
        # [`accrued_interest`] `accrued_interest`, ``, 
        # [`loan_id`] `loan_id`, [`amount_withdrawn`] `amount_withdrawn`,
        # ``, [`timestamp`] `timestamp`.
        # Example: 
        # https://starkscan.co/event/0x050db0ed93d7abbfb152e16608d4cf4dbe0b686b134f890dd0ad8418b203c580_2.
        loan_id = int(event["data"][11], base=16)
        original_collateral_token = get_symbol(event["data"][0])
        original_collateral_face_amount = decimal.Decimal(
            str(int(event["data"][3], base=16))
        )
        original_collateral = Portfolio()
        original_collateral.values[original_collateral_token] = (
            original_collateral_face_amount
        )
        try:
            self.loan_entities[loan_id].original_collateral = original_collateral
            self.loan_entities[loan_id].collateral.values = {
                token: (
                    self.loan_entities[loan_id].original_collateral.values[token]
                    + self.loan_entities[loan_id].borrowed_collateral.values[token]
                )
                for token in TOKEN_SETTINGS
            }
        except TypeError as exc:
            logging.getLogger("ErrorHandler").info(
                f"TypeErrorHandler: {exc}: {loan_id=}"
            )
            return
        # add additional info block and timestamp
        self.loan_entities[loan_id].extra_info.block = event["block_number"]
        self.loan_entities[loan_id].extra_info.timestamp = event["timestamp"]
        if self.loan_entities[loan_id].user == self.verbose_user:
            logging.info(
                "In block number = {}, loan interest was deducted, resulting in "
                "collateral of face amount = {} of token = {}.".format(
                    event["block_number"],
                    original_collateral_face_amount,
                    original_collateral_token,
                )
            )

    def process_liquidated_event(self, event: pandas.Series) -> None:
        """
        Process an event where a loan is liquidated.

        The data column contains: [loan_record] id, owner, market, commitment, amount,
        current_market, current_amount, is_loan_withdrawn, debt_category, state,
        l3_integration, created_at, [liquidator], [timestamp].
        """
        # The order of the values in the `data` column is: 
        # [`loan_record`] `id`, `owner`, `market`, `commitment`,
        # `amount`, ``, `current_market`, `current_amount`, ``
        # , `is_loan_withdrawn`, `debt_category`, `state`,
        # `l3_integration`, `created_at`, [`liquidator`]
        #  `liquidator`, [`timestamp`] `timestamp`.
        # Example:
        #  https://starkscan.co/event/0x0774bebd15505d3f950c362d813dc81c6320ae9 \
        # 2cb396b6469fd1ac5d8ff62dc_8.
        loan_id = int(event["data"][0], base=16)
        user = event["data"][1]
        assert self.loan_entities[loan_id].user == user
        debt_token = get_symbol(event["data"][2])
        # This prevents liquidated loans to appear as not repaid.
        debt_face_amount = decimal.Decimal("0")
        borrowed_collateral_token = get_symbol(event["data"][6])
        borrowed_collateral_face_amount = decimal.Decimal(
            str(int(event["data"][7], base=16))
        )
        # Based on the documentation, it seems that it's only
        #  possible to liquidate the whole amount.
        assert borrowed_collateral_face_amount == decimal.Decimal("0")
        debt_category = int(event["data"][10], base=16)

        borrowed_collateral = Portfolio()
        borrowed_collateral.values[borrowed_collateral_token] = (
            borrowed_collateral_face_amount
        )
        # add additional info block and timestamp
        self.loan_entities[loan_id].extra_info.block = event["block_number"]
        self.loan_entities[loan_id].extra_info.timestamp = event["timestamp"]

        self.loan_entities[loan_id].borrowed_collateral = borrowed_collateral
        # TODO: What happens to original collateral? For now, let's assume it disappears.
        original_collateral = Portfolio()
        self.loan_entities[loan_id].original_collateral = original_collateral
        self.loan_entities[loan_id].collateral.values = {
            token: (
                self.loan_entities[loan_id].original_collateral.values[token]
                + self.loan_entities[loan_id].borrowed_collateral.values[token]
            )
            for token in TOKEN_SETTINGS
        }
        debt = Portfolio()
        debt.values[debt_token] = debt_face_amount
        self.loan_entities[loan_id].debt = debt
        self.loan_entities[loan_id].debt_category = debt_category
        if self.loan_entities[loan_id].user == self.verbose_user:
            logging.info(
                "In block number = {}, loan was liquidated, resulting in debt of "
                "face amount = {} of token = {}, borrowed collateral face amount = {} "
                "of token = {} and no original collateral.".format(
                    event["block_number"],
                    debt_face_amount,
                    debt_token,
                    borrowed_collateral_face_amount,
                    borrowed_collateral_token,
                )
            )

    def compute_liquidable_debt_at_price(
        self,
        prices: TokenValues,
        collateral_token: str,
        collateral_token_price: decimal.Decimal,
        debt_token: str,
    ) -> decimal.Decimal:
        changed_prices = copy.deepcopy(prices)
        changed_prices.values[collateral_token] = collateral_token_price
        max_liquidated_amount = decimal.Decimal("0")
        for loan_entity in self.loan_entities.values():
            # Filter out users who borrowed the token of interest.
            debt_tokens = {
                token
                for token, token_amount in loan_entity.debt.values.items()
                if token_amount > decimal.Decimal("0")
            }
            if not debt_token in debt_tokens:
                continue

            # Filter out users with health factor below 1.
            debt_usd = loan_entity.compute_debt_usd(
                risk_adjusted=False,
                debt_interest_rate_models=self.debt_interest_rate_models,
                prices=changed_prices,
            )
            health_factor = loan_entity.compute_health_factor(
                standardized=False,
                collateral_interest_rate_models=self.collateral_interest_rate_models,
                prices=changed_prices,
                debt_usd=debt_usd,
            )
            health_factor_liquidation_threshold = (
                decimal.Decimal("1.06")
                if loan_entity.debt_category == 1
                else (
                    decimal.Decimal("1.05")
                    if loan_entity.debt_category == 2
                    else decimal.Decimal("1.04")
                )
            )
            if health_factor >= health_factor_liquidation_threshold:
                continue

            # Find out how much of the `debt_token` will be liquidated.
            max_liquidated_amount += loan_entity.compute_debt_to_be_liquidated(
                debt_usd=debt_usd
            )
        return max_liquidated_amount

    def compute_number_of_active_users(self) -> int:
        """
        Count the number of unique users who have either collateral or debt.
        
        Returns:
            int: Number of unique users with active positions (collateral or debt)
        """
        unique_active_users = {
            loan_entity.user
            for loan_entity in self.loan_entities.values()
            if loan_entity.has_collateral() or loan_entity.has_debt()
        }
        return len(unique_active_users)

    def compute_number_of_active_borrowers(self) -> int:
        """
        Count the number of unique users who currently have outstanding debt.

        Returns:
            int: Number of unique users with active loans
        """
        unique_active_borrowers = {
            loan_entity.user
            for loan_entity in self.loan_entities.values()
            if loan_entity.has_debt()
        }
        return len(unique_active_borrowers)