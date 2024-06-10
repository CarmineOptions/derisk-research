from typing import Optional
import copy
import decimal
import logging

import pandas as pd

from handlers.helpers import Portfolio, TokenValues, add_leading_zeros
from handlers.settings import TOKEN_SETTINGS, TokenSettings
from handlers.state import LoanEntity, InterestRateModels, State

LIQUIDATION_HEALTH_FACTOR_THRESHOLD = decimal.Decimal("1")
TARGET_HEALTH_FACTOR = decimal.Decimal("1.25")

# TODO: Move to `NostraAlphaSpecificTokenSettings`?
# Source: https://docs.nostra.finance/lend/deployed-contracts/lend-alpha#asset-contracts.
ADDRESSES_TO_TOKENS: dict[str, str] = {
    "0x0553cea5d1dc0e0157ffcd36a51a0ced717efdadd5ef1b4644352bb45bd35453": "ETH",
    "0x047e794d7c49c49fd2104a724cfa69a92c5a4b50a5753163802617394e973833": "USDC",
    "0x003cd2066f3c8b4677741b39db13acebba843bbbaa73d657412102ab4fd98601": "USDT",
    "0x04403e420521e7a4ca0dc5192af81ca0bb36de343564a9495e11c8d9ba6e9d17": "DAI",
    "0x06b59e2a746e141f90ec8b6e88e695265567ab3bdcf27059b4a15c89b0b7bd53": "wBTC",
    "0x070f8a4fcd75190661ca09a7300b7c93fab93971b67ea712c664d7948a8a54c6": "ETH",
    "0x029959a546dda754dc823a7b8aa65862c5825faeaaf7938741d8ca6bfdc69e4e": "USDC",
    "0x055ba2baf189b98c59f6951a584a3a7d7d6ff2c4ef88639794e739557e1876f0": "USDT",
    "0x01ac55cabf2b79cf39b17ba0b43540a64205781c4b7850e881014aea6f89be58": "DAI",
    "0x00687b5d9e591844169bc6ad7d7256c4867a10cee6599625b9d78ea17a7caef9": "wBTC",
    "0x040b091cb020d91f4a4b34396946b4d4e2a450dbd9410432ebdbfe10e55ee5e5": "ETH",
    "0x03b6058a9f6029b519bc72b2cc31bcb93ca704d0ab79fec2ae5d43f79ac07f7a": "USDC",
    "0x065c6c7119b738247583286021ea05acc6417aa86d391dcdda21843c1fc6e9c6": "USDT",
    "0x0362b4455f5f4cc108a5a1ab1fd2cc6c4f0c70597abb541a99cf2734435ec9cb": "DAI",
    "0x075b0d87aca8dee25df35cdc39a82b406168fa23a76fc3f03abbfdc6620bb6d7": "wBTC",
}
# TODO: Move to `NostraAlphaSpecificTokenSettings`?
# Source: https://docs.nostra.finance/lend/deployed-contracts/lend-alpha#asset-contracts.
ADDRESSES_TO_EVENTS: dict[str, str] = {
    "0x0553cea5d1dc0e0157ffcd36a51a0ced717efdadd5ef1b4644352bb45bd35453": "non_interest_bearing_collateral",
    "0x047e794d7c49c49fd2104a724cfa69a92c5a4b50a5753163802617394e973833": "non_interest_bearing_collateral",
    "0x003cd2066f3c8b4677741b39db13acebba843bbbaa73d657412102ab4fd98601": "non_interest_bearing_collateral",
    "0x04403e420521e7a4ca0dc5192af81ca0bb36de343564a9495e11c8d9ba6e9d17": "non_interest_bearing_collateral",
    "0x06b59e2a746e141f90ec8b6e88e695265567ab3bdcf27059b4a15c89b0b7bd53": "non_interest_bearing_collateral",
    "0x070f8a4fcd75190661ca09a7300b7c93fab93971b67ea712c664d7948a8a54c6": "interest_bearing_collateral",
    "0x029959a546dda754dc823a7b8aa65862c5825faeaaf7938741d8ca6bfdc69e4e": "interest_bearing_collateral",
    "0x055ba2baf189b98c59f6951a584a3a7d7d6ff2c4ef88639794e739557e1876f0": "interest_bearing_collateral",
    "0x01ac55cabf2b79cf39b17ba0b43540a64205781c4b7850e881014aea6f89be58": "interest_bearing_collateral",
    "0x00687b5d9e591844169bc6ad7d7256c4867a10cee6599625b9d78ea17a7caef9": "interest_bearing_collateral",
    "0x040b091cb020d91f4a4b34396946b4d4e2a450dbd9410432ebdbfe10e55ee5e5": "debt",
    "0x03b6058a9f6029b519bc72b2cc31bcb93ca704d0ab79fec2ae5d43f79ac07f7a": "debt",
    "0x065c6c7119b738247583286021ea05acc6417aa86d391dcdda21843c1fc6e9c6": "debt",
    "0x0362b4455f5f4cc108a5a1ab1fd2cc6c4f0c70597abb541a99cf2734435ec9cb": "debt",
    "0x075b0d87aca8dee25df35cdc39a82b406168fa23a76fc3f03abbfdc6620bb6d7": "debt",
}
# Source: https://docs.nostra.finance/lend/deployed-contracts/lend-alpha#core-contracts.
INTEREST_RATE_MODEL_ADDRESS: str = (
    "0x03d39f7248fb2bfb960275746470f7fb470317350ad8656249ec66067559e892"
)
# Keys are values of the "key_name" column in the database, values are the respective method names.
EVENTS_METHODS_MAPPING: dict[tuple[str, str], str] = {
    (
        "non_interest_bearing_collateral",
        "Mint",
    ): "process_non_interest_bearing_collateral_mint_event",
    (
        "non_interest_bearing_collateral",
        "Burn",
    ): "process_non_interest_bearing_collateral_burn_event",
    (
        "non_interest_bearing_collateral",
        "nostra::core::tokenization::lib::nostra_token::NostraTokenComponent::Mint",
    ): "process_non_interest_bearing_collateral_mint_event",
    (
        "non_interest_bearing_collateral",
        "nostra::core::tokenization::lib::nostra_token::NostraTokenComponent::Burn",
    ): "process_non_interest_bearing_collateral_burn_event",
    (
        "interest_bearing_collateral",
        "Mint",
    ): "process_interest_bearing_collateral_mint_event",
    (
        "interest_bearing_collateral",
        "Burn",
    ): "process_interest_bearing_collateral_burn_event",
    (
        "interest_bearing_collateral",
        "nostra::core::tokenization::lib::nostra_token::NostraTokenComponent::Mint",
    ): "process_interest_bearing_collateral_mint_event",
    (
        "interest_bearing_collateral",
        "nostra::core::tokenization::lib::nostra_token::NostraTokenComponent::Burn",
    ): "process_interest_bearing_collateral_burn_event",
    ("debt", "Mint"): "process_debt_mint_event",
    ("debt", "Burn"): "process_debt_burn_event",
    (
        "debt",
        "nostra::core::tokenization::lib::nostra_token::NostraTokenComponent::Mint",
    ): "process_debt_mint_event",
    (
        "debt",
        "nostra::core::tokenization::lib::nostra_token::NostraTokenComponent::Burn",
    ): "process_debt_burn_event",
}


class NostraAlphaLoanEntity(LoanEntity):
    """
    A class that describes the Nostra Alpha loan entity. On top of the abstract `LoanEntity`, it implements the
    `non_interest_bearing_collateral` and `interest_bearing_collateral` attributes in order to help with accounting for
    the changes in collateral. This is because Nostra Alpha allows the user to decide the amount of collateral that
    earns interest and the amount that doesn't. We keep all balances in raw amounts.
    """

    TOKEN_SETTINGS: dict[str, TokenSettings] = TOKEN_SETTINGS
    # TODO: Move these to `PROTOCOL_SETTINGS` (similar to `TOKEN_SETTINGS`)? Might be useful when
    # `compute_health_factor` is generalized.
    LIQUIDATION_HEALTH_FACTOR_THRESHOLD = LIQUIDATION_HEALTH_FACTOR_THRESHOLD
    TARGET_HEALTH_FACTOR = TARGET_HEALTH_FACTOR

    def __init__(self) -> None:
        super().__init__()
        self.non_interest_bearing_collateral: Portfolio = Portfolio()
        self.interest_bearing_collateral: Portfolio = Portfolio()

    def compute_health_factor(
        self,
        standardized: bool,
        collateral_interest_rate_models: Optional[InterestRateModels] = None,
        debt_interest_rate_models: Optional[InterestRateModels] = None,
        prices: Optional[TokenValues] = None,
        risk_adjusted_collateral_usd: Optional[decimal.Decimal] = None,
        risk_adjusted_debt_usd: Optional[decimal.Decimal] = None,
    ) -> decimal.Decimal:
        if risk_adjusted_collateral_usd is None:
            risk_adjusted_collateral_usd = self.compute_collateral_usd(
                collateral_interest_rate_models=collateral_interest_rate_models,
                prices=prices,
                risk_adjusted=True,
            )
        if risk_adjusted_debt_usd is None:
            risk_adjusted_debt_usd = self.compute_debt_usd(
                debt_interest_rate_models=debt_interest_rate_models,
                prices=prices,
                risk_adjusted=True,
            )
        if standardized:
            # Denominator is the value of (risk-adjusted) collateral at which the risk_adjusted_debt_usd can be liquidated.
            # TODO: denominator = risk_adjusted_debt_usd * liquidation_threshold??
            denominator = risk_adjusted_debt_usd
        else:
            denominator = risk_adjusted_debt_usd
        if denominator == decimal.Decimal("0"):
            # TODO: Assumes collateral is positive.
            return decimal.Decimal("Inf")
        return risk_adjusted_collateral_usd / denominator

    def compute_debt_to_be_liquidated(
        self,
        debt_token: str,
        collateral_tokens: set[str],
        health_factor: decimal.Decimal,
        debt_token_debt_amount: decimal.Decimal,
        debt_token_price: decimal.Decimal,
    ) -> decimal.Decimal:
        liquidator_fee_usd = decimal.Decimal("0")
        liquidation_amount_usd = decimal.Decimal("0")
        # Choose the most optimal collateral_token to be liquidated.
        for collateral_token in collateral_tokens:
            # TODO: Commit a PDF with the derivation of thetoken_states[debt_token] formula?
            # See an example of a liquidation here:
            # https://docs.nostra.finance/lend/liquidations/an-example-of-liquidation.
            liquidator_fee = min(
                self.TOKEN_SETTINGS[collateral_token].liquidator_fee_beta
                * (self.LIQUIDATION_HEALTH_FACTOR_THRESHOLD - health_factor),
                self.TOKEN_SETTINGS[collateral_token].liquidator_fee_max,
            )
            total_fee = (
                liquidator_fee + self.TOKEN_SETTINGS[collateral_token].protocol_fee
            )
            max_liquidation_percentage = (self.TARGET_HEALTH_FACTOR - health_factor) / (
                self.TARGET_HEALTH_FACTOR
                - (
                    self.TOKEN_SETTINGS[collateral_token].collateral_factor
                    * self.TOKEN_SETTINGS[debt_token].debt_factor
                    * (decimal.Decimal("1") + total_fee)
                )
            )
            max_liquidation_percentage = min(
                max_liquidation_percentage, decimal.Decimal("1")
            )
            max_liquidation_amount = max_liquidation_percentage * debt_token_debt_amount
            max_liquidation_amount_usd = (
                max_liquidation_amount
                * debt_token_price
                / self.TOKEN_SETTINGS[debt_token].decimal_factor
            )
            max_liquidator_fee_usd = liquidator_fee * max_liquidation_amount_usd
            if max_liquidator_fee_usd > liquidator_fee_usd:
                liquidator_fee_usd = max_liquidator_fee_usd
                liquidation_amount_usd = max_liquidation_amount_usd
        return liquidation_amount_usd


class NostraAlphaState(State):
    """
    A class that describes the state of all Nostra Alpha loan entities. It implements a method for correct processing
    of every relevant event.
    """

    ADDRESSES_TO_TOKENS: dict[str, str] = ADDRESSES_TO_TOKENS
    ADDRESSES_TO_EVENTS: dict[str, str] = ADDRESSES_TO_EVENTS
    INTEREST_RATE_MODEL_ADDRESS: str = INTEREST_RATE_MODEL_ADDRESS
    EVENTS_METHODS_MAPPING: dict[str, str] = EVENTS_METHODS_MAPPING
    # TODO: This seems to be a magical address.
    IGNORE_USER: str = (
        "0x5a0042fa9bb87ed72fbee4d5a2da416528ebc84a569081ad02e9ad60b0af7d7"
    )

    def __init__(
        self,
        loan_entity_class: NostraAlphaLoanEntity = NostraAlphaLoanEntity,
        verbose_user: Optional[str] = None,
    ) -> None:
        super().__init__(
            loan_entity_class=loan_entity_class,
            verbose_user=verbose_user,
        )

    def process_event(self, event: pd.Series) -> None:
        assert event["block_number"] >= self.last_block_number
        self.last_block_number = event["block_number"]
        if event["from_address"] == self.INTEREST_RATE_MODEL_ADDRESS:
            self.process_interest_rate_model_event(event)
            return
        event_type = self.ADDRESSES_TO_EVENTS[event["from_address"]]
        getattr(self, self.EVENTS_METHODS_MAPPING[(event_type, event["key_name"])])(
            event=event
        )

    def process_interest_rate_model_event(self, event: pd.Series) -> None:
        # The order of the values in the `data` column is: `debtToken`, `lendingRate`, ``, `borrowRate`, ``,
        # `lendIndex`, ``, `borrowIndex`, ``.
        # Example: https://starkscan.co/event/0x05e95588e281d7cab6f89aa266057c4c9bcadf3ff0bb85d4feea40a4faa94b09_4.
        token_address = add_leading_zeros(event["data"][0])
        # TODO: Integrate the UNO token once it's allowed to be borrowed or used as collateral.
        if (
            token_address
            == "0x04b036839a8769c04144cc47415c64b083a2b26e4a7daa53c07f6042a0d35792"
        ):
            return
        token = self.ADDRESSES_TO_TOKENS[token_address]
        collateral_interest_rate_index = decimal.Decimal(
            str(int(event["data"][5], base=16))
        ) / decimal.Decimal("1e18")
        debt_interest_rate_index = decimal.Decimal(
            str(int(event["data"][7], base=16))
        ) / decimal.Decimal("1e18")
        self.collateral_interest_rate_models.values[token] = (
            collateral_interest_rate_index
        )
        self.debt_interest_rate_models.values[token] = debt_interest_rate_index

    def process_non_interest_bearing_collateral_mint_event(
        self, event: pd.Series
    ) -> None:
        # The order of the values in the `data` column is: `user`, `amount`, ``.
        # Example: https://starkscan.co/event/0x015dccf7bc9a434bcc678cf730fa92641a2f6bcbfdb61cbe7a1ef7d0a614d1ac_3.
        user = event["data"][0]
        if user == self.IGNORE_USER:
            return
        token = self.ADDRESSES_TO_TOKENS[event["from_address"]]
        face_amount = decimal.Decimal(str(int(event["data"][1], base=16)))
        raw_amount = face_amount / self.collateral_interest_rate_models.values[token]
        # add additional info block and timestamp
        self.loan_entities[user].extra_info.block = event["block_number"]
        self.loan_entities[user].extra_info.timestamp = event["timestamp"]

        self.loan_entities[user].non_interest_bearing_collateral.increase_value(
            token=token, value=raw_amount
        )
        self.loan_entities[user].collateral.values = {
            token: (
                self.loan_entities[user].non_interest_bearing_collateral.values[token]
                + self.loan_entities[user].interest_bearing_collateral.values[token]
            )
            for token in TOKEN_SETTINGS
        }
        if user == self.verbose_user:
            logging.info(
                "In block number = {}, non-interest-bearing collateral of raw amount = {} of token = {} was added.".format(
                    event["block_number"],
                    raw_amount,
                    token,
                )
            )

    def process_non_interest_bearing_collateral_burn_event(
        self, event: pd.Series
    ) -> None:
        # The order of the values in the `data` column is: `user`, `amount`, ``.
        # Example: https://starkscan.co/event/0x00744177ee88dd3d96dda1784e2dff50f0c989b7fd48755bc42972af2e951dd6_1.
        user = event["data"][0]
        if user == self.IGNORE_USER:
            return
        token = self.ADDRESSES_TO_TOKENS[event["from_address"]]
        face_amount = decimal.Decimal(str(int(event["data"][1], base=16)))
        raw_amount = face_amount / self.collateral_interest_rate_models.values[token]
        # add additional info block and timestamp
        self.loan_entities[user].extra_info.block = event["block_number"]
        self.loan_entities[user].extra_info.timestamp = event["timestamp"]

        self.loan_entities[user].non_interest_bearing_collateral.increase_value(
            token=token, value=-raw_amount
        )
        self.loan_entities[user].collateral.values = {
            token: (
                self.loan_entities[user].non_interest_bearing_collateral.values[token]
                + self.loan_entities[user].interest_bearing_collateral.values[token]
            )
            for token in TOKEN_SETTINGS
        }
        if user == self.verbose_user:
            logging.info(
                "In block number = {}, non-interest-bearing collateral of raw amount = {} of token = {} was withdrawn.".format(
                    event["block_number"],
                    raw_amount,
                    token,
                )
            )

    def process_interest_bearing_collateral_mint_event(self, event: pd.Series) -> None:
        # The order of the values in the `data` column is: `user`, `amount`, ``.
        # Example: https://starkscan.co/event/0x07d222d9a70edbe717001ab4305a7a8cfb05116a35da24a9406209dbb07b6d0b_5.
        user = event["data"][0]
        if user == self.IGNORE_USER:
            return
        token = self.ADDRESSES_TO_TOKENS[event["from_address"]]
        face_amount = decimal.Decimal(str(int(event["data"][1], base=16)))
        raw_amount = face_amount / self.collateral_interest_rate_models.values[token]
        # add additional info block and timestamp
        self.loan_entities[user].extra_info.block = event["block_number"]
        self.loan_entities[user].extra_info.timestamp = event["timestamp"]

        self.loan_entities[user].interest_bearing_collateral.increase_value(
            token=token, value=raw_amount
        )
        self.loan_entities[user].collateral.values = {
            token: (
                self.loan_entities[user].non_interest_bearing_collateral.values[token]
                + self.loan_entities[user].interest_bearing_collateral.values[token]
            )
            for token in TOKEN_SETTINGS
        }
        if user == self.verbose_user:
            logging.info(
                "In block number = {}, interest-bearing collateral of raw amount = {} of token = {} was added.".format(
                    event["block_number"],
                    raw_amount,
                    token,
                )
            )

    def process_interest_bearing_collateral_burn_event(self, event: pd.Series) -> None:
        # The order of the values in the `data` column is: `user`, `amount`, ``.
        # Example: https://starkscan.co/event/0x0106494005bbab6f01e7779760891eb9ae20e01b905afdb16111f7cf3a28a53e_1.
        user = event["data"][0]
        if user == self.IGNORE_USER:
            return
        token = self.ADDRESSES_TO_TOKENS[event["from_address"]]
        face_amount = decimal.Decimal(str(int(event["data"][1], base=16)))
        raw_amount = face_amount / self.collateral_interest_rate_models.values[token]
        # add additional info block and timestamp
        self.loan_entities[user].extra_info.block = event["block_number"]
        self.loan_entities[user].extra_info.timestamp = event["timestamp"]

        self.loan_entities[user].interest_bearing_collateral.increase_value(
            token=token, value=-raw_amount
        )
        self.loan_entities[user].collateral.values = {
            token: (
                self.loan_entities[user].non_interest_bearing_collateral.values[token]
                + self.loan_entities[user].interest_bearing_collateral.values[token]
            )
            for token in TOKEN_SETTINGS
        }
        if user == self.verbose_user:
            logging.info(
                "In block number = {}, interest-bearing collateral of raw amount = {} of token = {} was withdrawn.".format(
                    event["block_number"],
                    raw_amount,
                    token,
                )
            )

    def process_debt_mint_event(self, event: pd.Series) -> None:
        # The order of the values in the `data` column is: `user`, `amount`, ``.
        # Example: https://starkscan.co/event/0x030d23c4769917bc673875e107ebdea31711e2bdc45e658125dbc2e988945f69_4.
        user = event["data"][0]
        if user == self.IGNORE_USER:
            return
        token = self.ADDRESSES_TO_TOKENS[event["from_address"]]
        face_amount = decimal.Decimal(str(int(event["data"][1], base=16)))
        raw_amount = face_amount / self.debt_interest_rate_models.values[token]
        # add additional info block and timestamp
        self.loan_entities[user].extra_info.block = event["block_number"]
        self.loan_entities[user].extra_info.timestamp = event["timestamp"]

        self.loan_entities[user].debt.increase_value(token=token, value=raw_amount)
        if user == self.verbose_user:
            logging.info(
                "In block number = {}, raw amount = {} of token = {} was borrowed.".format(
                    event["block_number"],
                    raw_amount,
                    token,
                )
            )

    def process_debt_burn_event(self, event: pd.Series) -> None:
        # The order of the values in the `data` column is: `user`, `amount`, ``.
        # Example: https://starkscan.co/event/0x002e4ee376785f687f32715d8bbed787b6d0fa9775dc9329ca2185155a139ca3_5.
        user = event["data"][0]
        if user == self.IGNORE_USER:
            return
        token = self.ADDRESSES_TO_TOKENS[event["from_address"]]
        face_amount = decimal.Decimal(str(int(event["data"][1], base=16)))
        raw_amount = face_amount / self.debt_interest_rate_models.values[token]
        # add additional info block and timestamp
        self.loan_entities[user].extra_info.block = event["block_number"]
        self.loan_entities[user].extra_info.timestamp = event["timestamp"]

        self.loan_entities[user].debt.increase_value(token=token, value=-raw_amount)
        if user == self.verbose_user:
            logging.info(
                "In block number = {}, raw amount = {} of token = {} was repayed.".format(
                    event["block_number"],
                    raw_amount,
                    token,
                )
            )

    # TODO: This method looks very similar to that of zkLend.
    def compute_liquidable_debt_at_price(
        self,
        prices: TokenValues,
        collateral_token: str,
        collateral_token_price: decimal.Decimal,
        debt_token: str,
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

            if health_factor >= decimal.Decimal("1"):
                continue

            # Find out how much of the `debt_token` will be liquidated.
            collateral_tokens = {
                token
                for token, token_amount in loan_entity.collateral.values.items()
                if decimal.Decimal(token_amount) > decimal.Decimal("0")
            }
            max_liquidated_amount += loan_entity.compute_debt_to_be_liquidated(
                debt_token=debt_token,
                collateral_tokens=collateral_tokens,
                health_factor=health_factor,
                debt_token_debt_amount=loan_entity.debt.values[debt_token],
                debt_token_price=prices.values[debt_token],
            )
        return max_liquidated_amount
