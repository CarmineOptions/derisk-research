"""
Event processing for Nostra Alpha protocol, including loan and collateral management.
"""
import asyncio
import copy
import decimal
import logging
from typing import Optional

import pandas as pd
from data_handler.handler_tools.nostra_alpha_settings import (
    NOSTRA_ALPHA_ADDRESSES_TO_EVENTS,
    NOSTRA_ALPHA_CDP_MANAGER_ADDRESS,
    NOSTRA_ALPHA_DEFERRED_BATCH_CALL_ADAPTER_ADDRESS,
    NOSTRA_ALPHA_EVENTS_TO_METHODS,
    NOSTRA_ALPHA_INTEREST_RATE_MODEL_ADDRESS,
    NOSTRA_ALPHA_TOKEN_ADDRESSES,
)
from data_handler.handlers.helpers import blockchain_call, get_addresses, get_symbol
from data_handler.handlers.settings import TokenSettings
from data_handler.handlers.state import NOSTRA_ALPHA_SPECIFIC_TOKEN_SETTINGS
from data_handler.handler_tools.data_parser.nostra import NostraDataParser

from shared.constants import ProtocolIDs
from shared.helpers import add_leading_zeros
from shared.loan_entity import LoanEntity
from shared.starknet_client import StarknetClient
from shared.state import State
from shared.types import InterestRateModels, Portfolio, Prices, TokenParameters
from shared.types.nostra import (
    NostraAlphaCollateralTokenParameters,
    NostraDebtTokenParameters,
)

LIQUIDATION_HEALTH_FACTOR_THRESHOLD = decimal.Decimal("1")
TARGET_HEALTH_FACTOR = decimal.Decimal("1.25")


class NostraAlphaLoanEntity(LoanEntity):
    """
    A class that describes the Nostra 
    Alpha loan entity. On top of the abstract `LoanEntity`, it implements the
    `non_interest_bearing_collateral` 
    and `interest_bearing_collateral` attributes in order to help with accounting for
    the changes in collateral. 
    This is because Nostra Alpha allows the user to decide the amount of collateral that
    earns interest and the amount that doesn't. We keep all balances in raw amounts.
    """

    TOKEN_SETTINGS: dict[str, TokenSettings] = NOSTRA_ALPHA_SPECIFIC_TOKEN_SETTINGS
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
        collateral_token_parameters: TokenParameters | None = None,
        collateral_interest_rate_model: InterestRateModels | None = None,
        debt_token_parameters: TokenParameters | None = None,
        debt_interest_rate_model: InterestRateModels | None = None,
        prices: Prices | None = None,
        risk_adjusted_collateral_usd: float | None = None,
        risk_adjusted_debt_usd: float | None = None,
    ) -> float:
        """
        Computes the health factor of the loan entity.
        :param standardized: If True, the health factor is standardized.
        :param collateral_token_parameters: Collateral token parameters.
        :param collateral_interest_rate_model: Collateral interest rate model.
        :param debt_token_parameters: Debt token parameters.
        :param debt_interest_rate_model: Debt interest rate model.
        :param prices: Prices of the tokens.
        :param risk_adjusted_collateral_usd: Risk-adjusted collateral in USD.
        :param risk_adjusted_debt_usd: Risk-adjusted debt in USD.
        :return: Health factor.
        """
        if risk_adjusted_collateral_usd is None:
            risk_adjusted_collateral_usd = self.compute_collateral_usd(
                risk_adjusted=True,
                collateral_token_parameters=collateral_token_parameters,
                collateral_interest_rate_model=collateral_interest_rate_model,
                prices=prices,
            )
        if risk_adjusted_debt_usd is None:
            risk_adjusted_debt_usd = self.compute_debt_usd(
                risk_adjusted=True,
                collateral_token_parameters=debt_token_parameters,
                debt_interest_rate_model=debt_interest_rate_model,
                prices=prices,
            )

        if risk_adjusted_debt_usd == 0.0:
            # TODO: Assumes collateral is positive.
            return float("inf")
        return risk_adjusted_collateral_usd / risk_adjusted_debt_usd

    def compute_debt_to_be_liquidated(
        self,
        collateral_token_addresses: list[str],
        collateral_token_parameters: TokenParameters,
        health_factor: float,
        debt_token_parameters: TokenParameters,
        debt_token_addresses: list[str],
        debt_token_debt_amount: decimal.Decimal,
        debt_token_price: float,
    ) -> float:
        """
        Computes the amount of debt to be liquidated.
        :param collateral_token_addresses: Collateral token addresses.
        :param collateral_token_parameters: Collateral token parameters.
        :param health_factor: Health factor.
        :param debt_token_parameters: Debt token parameters.
        :param debt_token_addresses: Debt token addresses.
        :param debt_token_debt_amount: Debt token debt amount.
        :param debt_token_price: Debt token price.
        :return:
        """
        # TODO: figure out what to do when there's multiple debt token addresses
        liquidator_fee_usd = 0.0
        liquidation_amount_usd = 0.0
        # TODO: do we need such a complicated way to compute this?
        # Choose the most optimal collateral_token to be liquidated.
        for collateral_token_address in collateral_token_addresses:
            # TODO: Commit a PDF with the derivation of the formula?
            # See an example of a liquidation here:
            # https://docs.nostra.finance/lend/liquidations/an-example-of-liquidation.
            liquidator_fee = min(
                collateral_token_parameters[collateral_token_address].liquidator_fee_beta *
                (self.LIQUIDATION_HEALTH_FACTOR_THRESHOLD - health_factor),
                collateral_token_parameters[collateral_token_address].liquidator_fee_max,
            )
            total_fee = (
                liquidator_fee + collateral_token_parameters[collateral_token_address].protocol_fee
            )
            max_liquidation_percentage = (self.TARGET_HEALTH_FACTOR - health_factor) / (
                self.TARGET_HEALTH_FACTOR - (
                    collateral_token_parameters[collateral_token_address].collateral_factor *
                    debt_token_parameters[debt_token_addresses[0]].debt_factor * (1.0 + total_fee)
                )
            )
            max_liquidation_percentage = min(max_liquidation_percentage, 1.0)
            max_liquidation_amount = max_liquidation_percentage * float(debt_token_debt_amount)
            max_liquidation_amount_usd = (
                debt_token_price * max_liquidation_amount /
                (10**debt_token_parameters[debt_token_addresses[0]].decimals)
            )
            max_liquidator_fee_usd = liquidator_fee * max_liquidation_amount_usd
            if max_liquidator_fee_usd > liquidator_fee_usd:
                liquidator_fee_usd = max_liquidator_fee_usd
                liquidation_amount_usd = max_liquidation_amount_usd
        return liquidation_amount_usd


class NostraAlphaState(State):
    """
    A class that describes the state of all
      Nostra Alpha loan entities. It implements a method for correct processing
    of every relevant event.
    """

    PROTOCOL_NAME = ProtocolIDs.NOSTRA_ALPHA.value

    IGNORE_USER: str = ("0x5a0042fa9bb87ed72fbee4d5a2da416528ebc84a569081ad02e9ad60b0af7d7")
    TOKEN_ADDRESSES: list[str] = NOSTRA_ALPHA_TOKEN_ADDRESSES
    INTEREST_RATE_MODEL_ADDRESS: str = NOSTRA_ALPHA_INTEREST_RATE_MODEL_ADDRESS
    CDP_MANAGER_ADDRESS: str = NOSTRA_ALPHA_CDP_MANAGER_ADDRESS
    DEFERRED_BATCH_CALL_ADAPTER_ADDRESS: str = (NOSTRA_ALPHA_DEFERRED_BATCH_CALL_ADAPTER_ADDRESS)

    EVENTS_TO_METHODS: dict[str, str] = NOSTRA_ALPHA_EVENTS_TO_METHODS

    # These variables are missing the leading 0's on purpose, because they're
    # missing in the raw event keys, too.
    INTEREST_STATE_UPDATED_KEY = (
        "0x33db1d611576200c90997bde1f948502469d333e65e87045c250e6efd2e42c7"
    )
    TRANSFER_KEY = "0x99cd8bde557814842a3121e8ddfd433a539b8c9f14bf31ebf108d12e6196e9"
    MINT_KEY = "0x34e55c1cd55f1338241b50d352f0e91c7e4ffad0e4271d64eb347589ebdfd16"
    BURN_KEY = "0x243e1de00e8a6bc1dfa3e950e6ade24c52e4a25de4dee7fb5affe918ad1e744"

    # We ignore transfers where the 
    # sender or recipient are '0x0' because these are mints and burns covered by other
    # events.
    ZERO_ADDRESS: str = add_leading_zeros("0x0")

    def __init__(
        self,
        loan_entity_class: NostraAlphaLoanEntity = NostraAlphaLoanEntity,
        verbose_user: Optional[str] = None,
    ) -> None:
        super().__init__(
            loan_entity_class=loan_entity_class,
            verbose_user=verbose_user,
        )
        # These dicts' keys are the collateral/debt token addresses.
        self.token_addresses_to_events: dict[str, str] = {}
        self.debt_token_addresses_to_interest_bearing_collateral_token_addresses: dict[str,
                                                                                       str] = {}

        asyncio.run(self.collect_token_parameters())

    @staticmethod
    def _infer_token_type(token_symbol: str) -> tuple[str, bool]:
        """
        Infers the token type based on the token symbol.
        :param token_symbol: the token symbol.
        :return: the token type and whether the token is interest bearing.
        """
        if token_symbol[0] == "d" and token_symbol[-2:] != "-c":
            return "debt", True
        elif token_symbol[0] == "n" and token_symbol[-2:] == "-c":
            return "collateral", False
        elif token_symbol[0] == "i" and token_symbol[-2:] == "-c":
            return "collateral", True
        raise ValueError("Can't infer token type for token symbol = {}.", token_symbol)

    async def collect_token_parameters(self) -> None:
        """
        Collects the token parameters for all the tokens in the protocol.
        """
        stark_client = StarknetClient()
        for token_address in self.TOKEN_ADDRESSES:
            decimals = await stark_client.func_call(
                addr=token_address,
                selector="decimals",
                calldata=[],
            )
            decimals = int(decimals[0])

            token_symbol = await get_symbol(token_address=token_address)
            event, is_interest_bearing = self._infer_token_type(token_symbol=token_symbol)
            self.token_addresses_to_events[token_address] = event

            underlying_token_address = await stark_client.func_call(
                addr=token_address,
                selector="underlyingAsset",
                calldata=[],
            )
            underlying_token_address = add_leading_zeros(hex(underlying_token_address[0]))
            underlying_token_symbol = await get_symbol(token_address=underlying_token_address)

            if event == "collateral":
                # The order of the arguments is: `id`, `asset`, `collateralFactor`, ``,
                # `priceOracle`.
                collateral_data = await stark_client.func_call(
                    addr=self.CDP_MANAGER_ADDRESS,
                    selector="getCollateralData",
                    calldata=[underlying_token_address],
                )
                collateral_factor = collateral_data[2] / 1e18

                # The order of the arguments is: 
                # `protocolFee`, ``, `protocolFeeRecipient`, `liquidatorFeeBeta`, ``,
                # `liquidatorFeeMax`, ``.
                liquidation_settings = await stark_client.func_call(
                    addr=self.CDP_MANAGER_ADDRESS,
                    selector="getLiquidationSettings",
                    calldata=[underlying_token_address],
                )
                liquidator_fee_beta = liquidation_settings[0] / 1e18
                liquidator_fee_max = liquidation_settings[3] / 1e18
                protocol_fee = liquidation_settings[5] / 1e18

                token_parameters = NostraAlphaCollateralTokenParameters(
                    address=token_address,
                    decimals=decimals,
                    symbol=token_symbol,
                    underlying_symbol=underlying_token_symbol,
                    underlying_address=underlying_token_address,
                    is_interest_bearing=is_interest_bearing,
                    collateral_factor=collateral_factor,
                    liquidator_fee_beta=liquidator_fee_beta,
                    liquidator_fee_max=liquidator_fee_max,
                    protocol_fee=protocol_fee,
                )
            else:
                # The order of the arguments is: `id`, `debtTier`, `debtToken`,
                # `debtFactor`, ``, `priceOracle`.
                debt_data = await stark_client.func_call(
                    addr=self.CDP_MANAGER_ADDRESS,
                    selector="getDebtData",
                    calldata=[token_address],
                )
                debt_factor = debt_data[3] / 1e18

                token_parameters = NostraDebtTokenParameters(
                    address=token_address,
                    decimals=decimals,
                    symbol=token_symbol,
                    underlying_symbol=underlying_token_symbol,
                    underlying_address=underlying_token_address,
                    debt_factor=debt_factor,
                )
            getattr(self.token_parameters, event)[token_address] = token_parameters

        # Create the mapping between the debt 
        # token addresses and the respective interest bearing collateral token
        # addresses.
        for debt_token_parameters in self.token_parameters.debt.values():
            interest_bearing_collateral_token_addresses = [
                collateral_token_parameters.address
                for collateral_token_parameters in self.token_parameters.collateral.values() if (
                    collateral_token_parameters.is_interest_bearing and collateral_token_parameters.
                    underlying_address == debt_token_parameters.underlying_address
                )
            ]
            assert len(interest_bearing_collateral_token_addresses) == 1
            self.debt_token_addresses_to_interest_bearing_collateral_token_addresses[
                debt_token_parameters.address] = interest_bearing_collateral_token_addresses[0]

    def process_event(self, event: pd.Series) -> None:
        """
        Processes an event based on the method name and the event data.
        :param event: Event data.
        """
        assert event["block_number"] >= self.last_block_number
        self.last_block_number = event["block_number"]
        if event["from_address"] == self.INTEREST_RATE_MODEL_ADDRESS:
            self.process_interest_rate_model_event(event)
            return
        event_type = NOSTRA_ALPHA_ADDRESSES_TO_EVENTS[event["from_address"]]
        getattr(self, self.EVENTS_METHODS_MAPPING[(event_type, event["key_name"])])(event=event)

    def process_interest_rate_model_event(self, event: pd.Series) -> None:
        """Processes an interest rate model event, 
        updating collateral and debt interest rate indices."""
        # The order of the values in the `data` column is: 
        # `debtToken`, `lendingRate`, ``, `borrowRate`, ``,
        # `lendIndex`, ``, `borrowIndex`, ``.
        # Example:
        # https://starkscan.co/event/0x05e95588e281d7cab6f89aa266057c4c9bcadf3ff0bb85d4feea40a4faa94b09_4.
        if event["keys"] == [self.INTEREST_STATE_UPDATED_KEY]:
            # The order of the values in the `data` column is: `debtToken`, `lendingRate`, ``, `borrowRate`, ``,
            # `lendIndex`, ``, `borrowIndex`, ``.
            # Example:
            # https://starkscan.co/event/0x05e95588e281d7cab6f89aa266057c4c9bcadf3ff0bb85d4feea40a4faa94b09_4.
            # Parse the event using the new serializer
            data = NostraDataParser.parse_interest_rate_model_event(event["data"])
            debt_token = parsed_event_data.debt_token
            collateral_interest_rate_index = parsed_event_data.lending_index
            debt_interest_rate_index = parsed_event_data.borrow_index
        else:
            raise ValueError("Event = {} has an unexpected structure.".format(event))
            
        collateral_token = self.debt_token_addresses_to_interest_bearing_collateral_token_addresses.get(
            debt_token, None)  
        # The indices are saved under the respective collateral or debt token address.
        if collateral_token:
            self.interest_rate_models.collateral[collateral_token] = (
                collateral_interest_rate_index
            )
        self.interest_rate_models.debt[debt_token] = debt_interest_rate_index

    def process_non_interest_bearing_collateral_mint_event(self, event: pd.Series) -> None:
        """Processes non-interest-bearing collateral mint event, 
        adjusting collateral values for the sender and recipient."""
        # The order of the values in the `data` column is: `user`, `amount`, ``.
        # Example:
        # https://starkscan.co/event/0x015dccf7bc9a434bcc678cf730fa92641a2f6bcbfdb61cbe7a1ef7d0a614d1ac_3.
        if event["keys"] == [self.TRANSFER_KEY]:
            # The order of the values in the `data` column is: `sender`, 
            # `recipient`, `value`, ``. Alternatively,
            # `from_`, `to`, `value`, ``.
            # Example:
            # https://starkscan.co/event/0x06ddd34767c8cef97d4508bcbb4e3771b1c93e160e02ca942cadbdfa29ef9ba8_2.
            sender = add_leading_zeros(event["data"][0])
            recipient = add_leading_zeros(event["data"][1])
            raw_amount = decimal.Decimal(str(int(event["data"][2], base=16)))
        else:
            raise ValueError("Event = {} has an unexpected structure.".format(event))
        if self.ZERO_ADDRESS in {sender, recipient}:
            return

        token = add_leading_zeros(event["from_address"])
        if sender != self.DEFERRED_BATCH_CALL_ADAPTER_ADDRESS:
            self.loan_entities[sender].collateral.increase_value(token=token, value=-raw_amount)
            self.loan_entities[sender].extra_info.block = event["block_number"]
            self.loan_entities[sender].extra_info.timestamp = event["timestamp"]
        if recipient != self.DEFERRED_BATCH_CALL_ADAPTER_ADDRESS:
            self.loan_entities[recipient].collateral.increase_value(token=token, value=raw_amount)
            self.loan_entities[recipient].extra_info.block = event["block_number"]
            self.loan_entities[recipient].extra_info.timestamp = event["timestamp"]
        if self.verbose_user in {sender, recipient}:
            logging.info(
                "In block number = {}, collateral of raw amount = {} of token = {} was transferred from user = {} to user = {}."
                .format(
                    event["block_number"],
                    raw_amount,
                    token,
                    sender,
                    recipient,
                )
            )

    def process_collateral_mint_event(self, event: pd.Series) -> None:
        """Process collateral addition event for a loan."""
        if event["keys"] == [self.MINT_KEY]:
            # The order of the values in the `data` column is: `user`, `amount`, ``.
            # Example:
            # https://starkscan.co/event/0x015dccf7bc9a434bcc678cf730fa92641a2f6bcbfdb61cbe7a1ef7d0a614d1ac_3.
            user = add_leading_zeros(event["data"][0])
            face_amount = decimal.Decimal(str(int(event["data"][1], base=16)))
        else:
            raise ValueError("Event = {} has an unexpected structure.".format(event))
        if user == self.DEFERRED_BATCH_CALL_ADAPTER_ADDRESS:
            return
        token = add_leading_zeros(event["from_address"])
        if self.token_parameters.collateral[token].is_interest_bearing:
            raw_amount = face_amount / self.interest_rate_models.collateral[token]
        else:
            raw_amount = face_amount
        self.loan_entities[user].collateral.increase_value(token=token, value=raw_amount)
        if user == self.verbose_user:
            logging.info(
                "In block number = {}, collateral of raw amount = {} of token = {} was added.".
                format(
                    event["block_number"],
                    raw_amount,
                    token,
                )
            )

    def process_collateral_burn_event(self, event: pd.Series) -> None:
        """Handles collateral withdrawal event by 
        decreasing the collateral value for a specified user."""
        if event["keys"] == [self.BURN_KEY]:
            # The order of the values in the `data` column is: `user`, `amount`, ``.
            # Example:
            # https://starkscan.co/event/0x00744177ee88dd3d96dda1784e2dff50f0c989b7fd48755bc42972af2e951dd6_1.
            user = add_leading_zeros(event["data"][0])
            face_amount = decimal.Decimal(str(int(event["data"][1], base=16)))
        else:
            raise ValueError("Event = {} has an unexpected structure.".format(event))
        if user == self.DEFERRED_BATCH_CALL_ADAPTER_ADDRESS:
            return
        token = add_leading_zeros(event["from_address"])
        if self.token_parameters.collateral[token].is_interest_bearing:
            raw_amount = face_amount / self.interest_rate_models.collateral[token]
        else:
            raw_amount = face_amount
        self.loan_entities[user].collateral.increase_value(token=token, value=-raw_amount)
        if user == self.verbose_user:
            logging.info(
                "In block number = {}, collateral of raw amount = {} of token = {} was withdrawn.".
                format(
                    event["block_number"],
                    raw_amount,
                    token,
                )
            )

    def process_debt_transfer_event(self, event: pd.Series) -> None:
        """Process debt transfer event, adjusting loan debt for sender and recipient."""
        if event["keys"] == [self.TRANSFER_KEY]:
            # The order of the values in the `data` column is: 
            # `sender`, `recipient`, `value`, ``. Alternatively,
            # `from_`, `to`, `value`, ``.
            # Example:
            # https://starkscan.co/event/0x0786a8918c8897db760899ee35b43071bfd723fec76487207882695e4b3014a0_1.
            event_data = NostraDataParser.parse_debt_transfer_event(event["data"])
            sender = event_data.sender 
            recipient = event_data.recipient
            raw_amount = event_data.amount
        else:
            raise ValueError("Event = {} has an unexpected structure.".format(event))
        if self.ZERO_ADDRESS in {sender, recipient}:
            return

        token = add_leading_zeros(event["from_address"])
        if sender != self.DEFERRED_BATCH_CALL_ADAPTER_ADDRESS:
            self.loan_entities[sender].debt.increase_value(token=token, value=-raw_amount)

        if recipient != self.DEFERRED_BATCH_CALL_ADAPTER_ADDRESS:
            self.loan_entities[recipient].debt.increase_value(token=token, value=raw_amount)

        if self.verbose_user in {sender, recipient}:
            logging.info(
                "In block number = {}, debt of raw amount = {} of token = {} was transferred from user = {} to user = {}."
                .format(
                    event["block_number"],
                    raw_amount,
                    token,
                    sender,
                    recipient,
                )
            )

    def process_non_interest_bearing_collateral_burn_event(self, event: pd.Series) -> None:
        """
        Processes the non-interest-bearing collateral burn event.
        :param event: Event data.
        """
        # The order of the values in the `data` column is: `user`, `amount`, ``.
        # Example:
        # https://starkscan.co/event/0x00744177ee88dd3d96dda1784e2dff50f0c989b7fd48755bc42972af2e951dd6_1.
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
                self.loan_entities[user].non_interest_bearing_collateral.values[token] +
                self.loan_entities[user].interest_bearing_collateral.values[token]
            )
            for token in NOSTRA_ALPHA_SPECIFIC_TOKEN_SETTINGS
        }
        if user == self.verbose_user:
            logging.info(
                "In block number = {}, non-interest-bearing collateral of raw amount = {} of token = {} was withdrawn."
                .format(
                    event["block_number"],
                    raw_amount,
                    token,
                )
            )

    def process_interest_bearing_collateral_mint_event(self, event: pd.Series) -> None:
        """Process event adding interest-bearing collateral to a loan."""
        # The order of the values in the `data` column is: `user`, `amount`, ``.
        # Example:
        # https://starkscan.co/event/0x07d222d9a70edbe717001ab4305a7a8cfb05116a35da24a9406209dbb07b6d0b_5.
        data = NostraDataParser.parse_interest_bearing_collateral_mint_event(event["data"])
        user, face_amount = data.user, data.amount
         
        if user == self.IGNORE_USER:
            return
        
        token = self.ADDRESSES_TO_TOKENS[event["from_address"]]

        raw_amount = face_amount / self.collateral_interest_rate_models.values[token]
        # add additional info block and timestamp
        self.loan_entities[user].extra_info.block = event["block_number"]
        self.loan_entities[user].extra_info.timestamp = event["timestamp"]

        self.loan_entities[user].interest_bearing_collateral.increase_value(
            token=token, value=raw_amount
        )
        self.loan_entities[user].collateral.values = {
            token: (
                self.loan_entities[user].non_interest_bearing_collateral.values[token] +
                self.loan_entities[user].interest_bearing_collateral.values[token]
            )
            for token in NOSTRA_ALPHA_SPECIFIC_TOKEN_SETTINGS
        }
        if user == self.verbose_user:
            logging.info(
                "In block number = {}, interest-bearing collateral of raw amount = {} of token = {} was added."
                .format(
                    event["block_number"],
                    raw_amount,
                    token,
                )
            )

    def process_interest_bearing_collateral_burn_event(self, event: pd.Series) -> None:
        """Handle withdrawal of interest-bearing collateral from a loan."""
        # The order of the values in the `data` column is: `user`, `amount`, ``.
        # Example:
        # https://starkscan.co/event/0x0106494005bbab6f01e7779760891eb9ae20e01b905afdb16111f7cf3a28a53e_1.
         
        data = NostraDataParser.parse_interest_bearing_collateral_mint_event(event["data"])
        user, face_amount = data.user, data.amount
        
        if user == self.IGNORE_USER:
            return
        
        token = self.ADDRESSES_TO_TOKENS[event["from_address"]]
        raw_amount = face_amount / self.collateral_interest_rate_models.values[token]
        # add additional info block and timestamp
        self.loan_entities[user].extra_info.block = event["block_number"]
        self.loan_entities[user].extra_info.timestamp = event["timestamp"]

        self.loan_entities[user].interest_bearing_collateral.increase_value(
            token=token, value=-raw_amount
        )
        self.loan_entities[user].collateral.values = {
            token: (
                self.loan_entities[user].non_interest_bearing_collateral.values[token] +
                self.loan_entities[user].interest_bearing_collateral.values[token]
            )
            for token in NOSTRA_ALPHA_SPECIFIC_TOKEN_SETTINGS
        }
        if user == self.verbose_user:
            logging.info(
                "In block number = {}, interest-bearing collateral of raw amount = {} of token = {} was withdrawn."
                .format(
                    event["block_number"],
                    raw_amount,
                    token,
                )
            )

    def process_debt_mint_event(self, event: pd.Series) -> None:
        """
        Processes the `Burn` event.
        :param event: Event data.
        """
        if event["keys"] == [self.MINT_KEY]:
            # The order of the values in the `data` column is: `user`, `amount`, ``.
            # Example:
            # https://starkscan.co/event/0x030d23c4769917bc673875e107ebdea31711e2bdc45e658125dbc2e988945f69_4.
            data = NostraDataParser.parse_debt_mint_event(event["data"])
            user, face_amount = data.user, data.amount
        else:
            raise ValueError("Event = {} has an unexpected structure.".format(event))
        if user == self.DEFERRED_BATCH_CALL_ADAPTER_ADDRESS:
            return

        token = add_leading_zeros(event["from_address"])
        raw_amount = face_amount / self.interest_rate_models.debt[token]
        self.loan_entities[user].debt.increase_value(token=token, value=raw_amount)
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

    def process_debt_burn_event(self, event: pd.Series) -> None:
        """
        Processes the `Burn` event.
        :param event: Event data.
        """
        if event["keys"] == [self.BURN_KEY]:
            # The order of the values in the `data` column is: `user`, `amount`, ``.
            # Example:
            # https://starkscan.co/event/0x002e4ee376785f687f32715d8bbed787b6d0fa9775dc9329ca2185155a139ca3_5.
            data = NostraDataParser.parse_debt_mint_event(event["data"])
            user, face_amount = data.user, data.amount
        else:
            raise ValueError("Event = {} has an unexpected structure.".format(event))
        if user == self.DEFERRED_BATCH_CALL_ADAPTER_ADDRESS:
            return
        token = add_leading_zeros(event["from_address"])
        raw_amount = face_amount / self.interest_rate_models.debt[token]
        self.loan_entities[user].debt.increase_value(token=token, value=-raw_amount)
        self.loan_entities[user].extra_info.block = event["block_number"]
        self.loan_entities[user].extra_info.timestamp = event["timestamp"]
        if user == self.verbose_user:
            logging.info(
                "In block number = {}, raw amount = {} of token = {} was repaid.".format(
                    event["block_number"],
                    raw_amount,
                    token,
                )
            )

    def compute_liquidable_debt_at_price(
        self,
        prices: Prices,
        collateral_token_underlying_address: str,
        collateral_token_price: float,
        debt_token_underlying_address: str,
    ) -> decimal.Decimal:
        changed_prices = copy.deepcopy(prices)
        changed_prices[collateral_token_underlying_address] = collateral_token_price
        max_liquidated_amount = 0.0
        for loan_entity in self.loan_entities.values():
            # Filter out entities where the collateral token of interest is deposited as collateral.
            collateral_token_underlying_addresses = {
                self.token_parameters.collateral[token].underlying_address
                for token, token_amount in loan_entity.collateral.items()
                if token_amount > decimal.Decimal("0")
            }
            if (not collateral_token_underlying_address in collateral_token_underlying_addresses):
                continue

            # Filter out entities where the debt token of interest is borowed.
            debt_token_underlying_addresses = {
                self.token_parameters.debt[token].underlying_address
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
            risk_adjusted_debt_usd = loan_entity.compute_debt_usd(
                risk_adjusted=True,
                debt_token_parameters=self.token_parameters.debt,
                debt_interest_rate_model=self.interest_rate_models.debt,
                prices=changed_prices,
            )
            health_factor = loan_entity.compute_health_factor(
                standardized=False,
                risk_adjusted_collateral_usd=risk_adjusted_collateral_usd,
                risk_adjusted_debt_usd=risk_adjusted_debt_usd,
            )
            if health_factor >= 1.0:
                continue

            # Find out how much of the `debt_token` will be liquidated. 
            # We assume that the liquidator receives the
            # collateral token of interest even though it might not be the most
            # optimal choice for the liquidator.
            collateral_token_addresses = {
                self.token_parameters.collateral[token].address
                for token, token_amount in loan_entity.collateral.items()
                if token_amount > decimal.Decimal("0")
            }
            debt_token_addresses = get_addresses(
                token_parameters=self.token_parameters.debt,
                underlying_address=debt_token_underlying_address,
            )
            max_liquidated_amount += loan_entity.compute_debt_to_be_liquidated(
                collateral_token_addresses=collateral_token_addresses,
                collateral_token_parameters=self.token_parameters.collateral,
                health_factor=health_factor,
                debt_token_parameters=self.token_parameters.debt,
                debt_token_addresses=debt_token_addresses,
                # TODO: figure out what to do when there's multiple debt token addresses
                debt_token_debt_amount=loan_entity.debt[debt_token_addresses[0]],
                debt_token_price=prices[debt_token_underlying_address],
            )
        return max_liquidated_amount
