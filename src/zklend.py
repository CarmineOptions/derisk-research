from typing import Optional
import copy
import dataclasses
import decimal
import logging

import pandas

import src.helpers
import src.settings
import src.state



ADDRESS: str = "0x04c0a5193d58f74fbace4b74dcf65481e734ed1714121bdc571da345540efa05"


@dataclasses.dataclass
class ZkLendSpecificTokenSettings:
    # Source: https://zklend.gitbook.io/documentation/using-zklend/technical/asset-parameters.
    collateral_factor: decimal.Decimal
    # These are set to neutral values because zkLend doesn't use debt factors.
    debt_factor: decimal.Decimal
    # Source: https://zklend.gitbook.io/documentation/using-zklend/technical/asset-parameters.
    liquidation_bonus: decimal.Decimal
    protocol_token_address: str


@dataclasses.dataclass
class TokenSettings(ZkLendSpecificTokenSettings, src.settings.TokenSettings):
    pass


ZKLEND_SPECIFIC_TOKEN_SETTINGS: dict[str, ZkLendSpecificTokenSettings] = {
    "ETH": ZkLendSpecificTokenSettings(
        collateral_factor=decimal.Decimal("0.80"),
        debt_factor=decimal.Decimal("1"),
        liquidation_bonus=decimal.Decimal("0.10"),
        protocol_token_address='0x01b5bd713e72fdc5d63ffd83762f81297f6175a5e0a4771cdadbc1dd5fe72cb1',
    ),
    "wBTC": ZkLendSpecificTokenSettings(
        collateral_factor=decimal.Decimal("0.70"),
        debt_factor=decimal.Decimal("1"),
        liquidation_bonus=decimal.Decimal("0.15"),
        protocol_token_address='0x02b9ea3acdb23da566cee8e8beae3125a1458e720dea68c4a9a7a2d8eb5bbb4a',
    ),
    "USDC": ZkLendSpecificTokenSettings(
        collateral_factor=decimal.Decimal("0.80"),
        debt_factor=decimal.Decimal("1"),
        liquidation_bonus=decimal.Decimal("0.10"),
        protocol_token_address='0x047ad51726d891f972e74e4ad858a261b43869f7126ce7436ee0b2529a98f486',
    ),
    "DAI": ZkLendSpecificTokenSettings(
        collateral_factor=decimal.Decimal("0.70"),
        debt_factor=decimal.Decimal("1"),
        liquidation_bonus=decimal.Decimal("0.10"),
        protocol_token_address='0x062fa7afe1ca2992f8d8015385a279f49fad36299754fb1e9866f4f052289376',
    ),
    "USDT": ZkLendSpecificTokenSettings(
        collateral_factor=decimal.Decimal("0.80"),
        debt_factor=decimal.Decimal("1"),
        liquidation_bonus=decimal.Decimal("0.10"),
        protocol_token_address='0x00811d8da5dc8a2206ea7fd0b28627c2d77280a515126e62baa4d78e22714c4a',
    ),
    "wstETH": ZkLendSpecificTokenSettings(
        collateral_factor=decimal.Decimal("0.80"),
        debt_factor=decimal.Decimal("1"),
        liquidation_bonus=decimal.Decimal("0.10"),
        protocol_token_address='0x0536aa7e01ecc0235ca3e29da7b5ad5b12cb881e29034d87a4290edbb20b7c28',
    ),
    # TODO: Add LORDS.
    "LORDS": ZkLendSpecificTokenSettings(
        collateral_factor=decimal.Decimal("1"),
        debt_factor=decimal.Decimal("1"),
        liquidation_bonus=decimal.Decimal("0"),
        protocol_token_address='',
    ),
    # TODO: Update STRK settings.
    "STRK": ZkLendSpecificTokenSettings(
        collateral_factor=decimal.Decimal("0.50"),
        debt_factor=decimal.Decimal("1"),
        liquidation_bonus=decimal.Decimal("0.15"),
        protocol_token_address='0x06d8fa671ef84f791b7f601fa79fea8f6ceb70b5fa84189e3159d532162efc21',
    ),
}
TOKEN_SETTINGS: dict[str, TokenSettings] = {
    token: TokenSettings(
        symbol=src.settings.TOKEN_SETTINGS[token].symbol,
        decimal_factor=src.settings.TOKEN_SETTINGS[token].decimal_factor,
        address=src.settings.TOKEN_SETTINGS[token].address,
        collateral_factor=ZKLEND_SPECIFIC_TOKEN_SETTINGS[token].collateral_factor,
        debt_factor=ZKLEND_SPECIFIC_TOKEN_SETTINGS[token].debt_factor,
        liquidation_bonus=ZKLEND_SPECIFIC_TOKEN_SETTINGS[token].liquidation_bonus,
        protocol_token_address=ZKLEND_SPECIFIC_TOKEN_SETTINGS[token].protocol_token_address,
    )
    for token in src.settings.TOKEN_SETTINGS
}


# Keys are values of the "key_name" column in the database, values are the respective method names.
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



def get_events(start_block_number: int = 0) -> pandas.DataFrame:
    return src.helpers.get_events(
        addresses = (ADDRESS, ''),
        event_names = tuple(EVENTS_METHODS_MAPPING),
        start_block_number = start_block_number,
    )


class ZkLendLoanEntity(src.state.LoanEntity):
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
        self.deposit: src.helpers.Portfolio = src.helpers.Portfolio()
        self.collateral_enabled: src.helpers.TokenValues = src.helpers.TokenValues(init_value=False)

    def compute_health_factor(
        self,
        standardized: bool,
        collateral_interest_rate_models: Optional[src.state.InterestRateModels] = None,
        debt_interest_rate_models: Optional[src.state.InterestRateModels] = None,
        prices: Optional[src.helpers.TokenValues] = None,
        risk_adjusted_collateral_usd: Optional[decimal.Decimal] = None,
        debt_usd: Optional[decimal.Decimal] = None,
    ) -> decimal.Decimal:
        if risk_adjusted_collateral_usd is None:
            risk_adjusted_collateral_usd = self.compute_collateral_usd(
                collateral_interest_rate_models = collateral_interest_rate_models,
                prices = prices, 
                risk_adjusted = True,
            )
        if debt_usd is None:
            debt_usd = self.compute_debt_usd(
                debt_interest_rate_models = debt_interest_rate_models,
                prices = prices,
                risk_adjusted = False,
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
        prices: src.helpers.TokenValues,
        collateral_interest_rate_models: Optional[src.state.InterestRateModels] = None,
        debt_interest_rate_models: Optional[src.state.InterestRateModels] = None,
        risk_adjusted_collateral_usd: Optional[decimal.Decimal] = None,
        debt_usd: Optional[decimal.Decimal] = None,
    ) -> decimal.Decimal:
        if risk_adjusted_collateral_usd is None:
            risk_adjusted_collateral_usd = self.compute_collateral_usd(
                collateral_interest_rate_models = collateral_interest_rate_models,
                prices = prices, 
                risk_adjusted = True,
            )
        if debt_usd is None:
            debt_usd = self.compute_debt_usd(
                debt_interest_rate_models = debt_interest_rate_models,
                prices = prices,
                risk_adjusted = False,
            )
        # TODO: Commit a PDF with the derivation of the formula?
        numerator = debt_usd - risk_adjusted_collateral_usd
        denominator = prices.values[debt_token] * (
            1
            - self.TOKEN_SETTINGS[collateral_token].collateral_factor *
            (1 + self.TOKEN_SETTINGS[collateral_token].liquidation_bonus)
        )
        return numerator / denominator


class ZkLendState(src.state.State):
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

    def process_accumulators_sync_event(self, event: pandas.Series) -> None:
        # The order of the values in the `data` column is: `token`, `lending_accumulator`, `debt_accumulator`.
        # Example: https://starkscan.co/event/0x029628b89875a98c1c64ae206e7eb65669cb478a24449f3485f5e98aba6204dc_0.
        token = src.helpers.get_symbol(event["data"][0])
        collateral_interest_rate_index = decimal.Decimal(str(int(event["data"][1], base=16))) / decimal.Decimal("1e27")
        debt_interest_rate_index = decimal.Decimal(str(int(event["data"][2], base=16))) / decimal.Decimal("1e27")
        self.collateral_interest_rate_models.values[token] = collateral_interest_rate_index
        self.debt_interest_rate_models.values[token] = debt_interest_rate_index

    def process_deposit_event(self, event: pandas.Series) -> None:
        # The order of the values in the `data` column is: `user`, `token`, `face_amount`.
        # Example: https://starkscan.co/event/0x036185142bb51e2c1f5bfdb1e6cef81f8ea87fd4d777990014249bf5435fd31b_3.
        user = event["data"][0]
        token = src.helpers.get_symbol(event["data"][1])
        face_amount = decimal.Decimal(str(int(event["data"][2], base=16)))
        raw_amount = face_amount / self.collateral_interest_rate_models.values[token]
        self.loan_entities[user].deposit.increase_value(token=token, value=raw_amount)
        if self.loan_entities[user].collateral_enabled.values[token]:
            self.loan_entities[user].collateral.increase_value(token=token, value=raw_amount)
        if user == self.verbose_user:
            logging.info(
                'In block number = {}, raw amount = {} of token = {} was deposited.'.format(
                    event["block_number"],
                    raw_amount,
                    token,
                )
            )

    def process_collateral_enabled_event(self, event: pandas.Series) -> None:
        # The order of the values in the `data` column is: `user`, `token`.
        # Example: https://starkscan.co/event/0x036185142bb51e2c1f5bfdb1e6cef81f8ea87fd4d777990014249bf5435fd31b_6.
        user = event["data"][0]
        token = src.helpers.get_symbol(event["data"][1])
        self.loan_entities[user].collateral_enabled.values[token] = True
        self.loan_entities[user].collateral.set_value(
            token=token,
            value=self.loan_entities[user].deposit.values[token],
        )
        if user == self.verbose_user:
            logging.info(
                'In block number = {}, collateral was enabled for token = {}.'.format(
                    event["block_number"],
                    token,
                )
            )

    def process_collateral_disabled_event(self, event: pandas.Series) -> None:
        # The order of the values in the `data` column is: `user`, `token`.
        # Example: https://starkscan.co/event/0x0049b445bed84e0118795dbd22d76610ccac2ad626f8f04a1fc7e38113c2afe7_0.
        user = event["data"][0]
        token = src.helpers.get_symbol(event["data"][1])
        self.loan_entities[user].collateral_enabled.values[token] = False
        self.loan_entities[user].collateral.set_value(token=token, value=decimal.Decimal("0"))
        if user == self.verbose_user:
            logging.info(
                'In block number = {}, collateral was disabled for token = {}.'.format(
                    event["block_number"],
                    token,
                )
            )

    def process_withdrawal_event(self, event: pandas.Series) -> None:
        # The order of the values in the `data` column is: `user`, `token`, `face_amount`.
        # Example: https://starkscan.co/event/0x03472cf7511687a55bc7247f8765c4bbd2c18b70e09b2a10a77c61f567bfd2cb_4.
        user = event["data"][0]
        token = src.helpers.get_symbol(event["data"][1])
        face_amount = decimal.Decimal(str(int(event["data"][2], base=16)))
        raw_amount = face_amount / self.collateral_interest_rate_models.values[token]
        self.loan_entities[user].deposit.increase_value(token=token, value=-raw_amount)
        if self.loan_entities[user].collateral_enabled.values[token]:
            self.loan_entities[user].collateral.increase_value(token=token, value=-raw_amount)
        if user == self.verbose_user:
            logging.info(
                'In block number = {}, raw amount = {} of token = {} was withdrawn.'.format(
                    event["block_number"],
                    raw_amount,
                    token,
                )
            )

    def process_borrowing_event(self, event: pandas.Series) -> None:
        # The order of the values in the `data` column is: `user`, `token`, `raw_amount`, `face_amount`.
        # Example: https://starkscan.co/event/0x076b1615750528635cf0b63ca80986b185acbd20fa37f0f2b5368a4f743931f8_3.
        user = event["data"][0]
        token = src.helpers.get_symbol(event["data"][1])
        raw_amount = decimal.Decimal(str(int(event["data"][2], base=16)))
        self.loan_entities[user].debt.increase_value(token=token, value=raw_amount)
        if user == self.verbose_user:
            logging.info(
                'In block number = {}, raw amount = {} of token = {} was borrowed.'.format(
                    event["block_number"],
                    raw_amount,
                    token,
                )
            )

    def process_repayment_event(self, event: pandas.Series) -> None:
        # The order of the values in the `data` column is: `repayer`, `beneficiary`, `token`, `raw_amount`, 
        # `face_amount`.
        # Example: https://starkscan.co/event/0x06fa3dd6e12c9a66aeacd2eefa5a2ff2915dd1bb4207596de29bd0e8cdeeae66_5.
        user = event["data"][1]
        token = src.helpers.get_symbol(event["data"][2])
        raw_amount = decimal.Decimal(str(int(event["data"][3], base=16)))
        self.loan_entities[user].debt.increase_value(token=token, value=-raw_amount)
        if user == self.verbose_user:
            logging.info(
                'In block number = {}, raw amount = {} of token = {} was repayed.'.format(
                    event["block_number"],
                    raw_amount,
                    token,
                )
            )

    def process_liquidation_event(self, event: pandas.Series) -> None:
        # The order of the arguments is: `liquidator`, `user`, `debt_token`, `debt_raw_amount`, `debt_face_amount`,
        # `collateral_token`, `collateral_amount`.
        # Example: https://starkscan.co/event/0x07b8ec709df1066d9334d56b426c45440ca1f1bb841285a5d7b33f9d1008f256_5.
        user = event["data"][1]
        debt_token = src.helpers.get_symbol(event["data"][2])
        debt_raw_amount = decimal.Decimal(str(int(event["data"][3], base=16)))
        collateral_token = src.helpers.get_symbol(event["data"][5])
        collateral_face_amount = decimal.Decimal(str(int(event["data"][6], base=16)))
        collateral_raw_amount = (collateral_face_amount / self.collateral_interest_rate_models.values[collateral_token])
        self.loan_entities[user].debt.increase_value(token=debt_token, value=-debt_raw_amount)
        self.loan_entities[user].deposit.increase_value(token=collateral_token, value=-collateral_raw_amount)
        if self.loan_entities[user].collateral_enabled.values[collateral_token]:
            self.loan_entities[user].collateral.increase_value(token=collateral_token, value=-collateral_raw_amount)
        if user == self.verbose_user:
            logging.info(
                'In block number = {}, debt of raw amount = {} of token = {} and collateral of raw amount = {} of '
                'token = {} were liquidated.'.format(
                    event["block_number"],
                    debt_raw_amount,
                    debt_token,
                    collateral_raw_amount,
                    collateral_token,
                )
            )

    def compute_liquidable_debt_at_price(
        self,
        prices: src.helpers.TokenValues,
        collateral_token: str,
        collateral_token_price: decimal.Decimal,
        debt_token: str,
    ) -> decimal.Decimal:
        changed_prices = copy.deepcopy(prices)
        changed_prices.values[collateral_token] = collateral_token_price
        max_liquidated_amount = decimal.Decimal("0")
        for loan_entity in self.loan_entities.values():
            # Filter out entities who borrowed the token of interest.
            debt_tokens = {
                token
                for token, token_amount in loan_entity.debt.values.items()
                if token_amount > decimal.Decimal("0")
            }
            if not debt_token in debt_tokens:
                continue

            # Filter out entities with health factor below 1.
            risk_adjusted_collateral_usd = loan_entity.compute_collateral_usd(
                risk_adjusted=True,
                collateral_interest_rate_models=self.collateral_interest_rate_models,
                prices=changed_prices,
            )
            debt_usd = loan_entity.compute_debt_usd(
                risk_adjusted=False,
                debt_interest_rate_models=self.debt_interest_rate_models,
                prices=changed_prices,
            )
            health_factor = loan_entity.compute_health_factor(
                standardized=False,
                risk_adjusted_collateral_usd=risk_adjusted_collateral_usd,
                debt_usd=debt_usd,
            )
            # TODO: `health_factor` < 0 should not be possible if the data is right. Should we keep the filter?
            if health_factor >= decimal.Decimal("1") or health_factor <= decimal.Decimal("0"):
                continue

            # Find out how much of the `debt_token` will be liquidated.
            collateral_tokens = {
                token
                for token, token_amount in loan_entity.collateral.values.items()
                if token_amount > decimal.Decimal("0")
            }
            # Choose the most optimal collateral_token to be liquidated. In this case, the liquidator is indifferent.
            collateral_token = list(collateral_tokens)[0]
            max_liquidated_amount += loan_entity.compute_debt_to_be_liquidated(
                debt_token=debt_token,
                collateral_token=collateral_token,
                prices=changed_prices,
                risk_adjusted_collateral_usd=risk_adjusted_collateral_usd,
                debt_usd=debt_usd,
            )
        return max_liquidated_amount