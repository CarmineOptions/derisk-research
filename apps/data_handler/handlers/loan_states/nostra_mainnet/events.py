""" This module contains the class that describes the state of all Nostra Mainnet loan entities. """
import copy
import logging
from decimal import Decimal

import pandas as pd
import starknet_py
from data_handler.handler_tools.nostra_mainnet_settings import (
    NOSTRA_MAINNET_CDP_MANAGER_ADDRESS,
    NOSTRA_MAINNET_DEFERRED_BATCH_CALL_ADAPTER_ADDRESS,
    NOSTRA_MAINNET_EVENTS_TO_METHODS,
    NOSTRA_MAINNET_INTEREST_RATE_MODEL_ADDRESS,
    NOSTRA_MAINNET_TOKEN_ADDRESSES,
)
from data_handler.handlers.helpers import blockchain_call, get_addresses, get_symbol
from data_handler.handlers.loan_states.nostra_alpha.events import (
    NostraAlphaLoanEntity,
    NostraAlphaState,
)

from shared.constants import ProtocolIDs
from shared.helpers import add_leading_zeros
from shared.starknet_client import StarknetClient
from shared.custom_types import InterestRateModels, Prices, TokenParameters
from shared.custom_types.nostra import (
    NostraDebtTokenParameters,
    NostraMainnetCollateralTokenParameters,
)

logger = logging.getLogger(__name__)


class NostraMainnetLoanEntity(NostraAlphaLoanEntity):
    """
    A class that describes the state of all Nostra Mainnet loan entities.
      All methods for correct processing of every
    relevant event are implemented in `.nostra_alpha.NostraAlphaState`.
    """

    PROTOCOL_NAME = ProtocolIDs.NOSTRA_MAINNET.value
    # TODO: fetch from chain
    TARGET_HEALTH_FACTOR = 1.25
    # TODO: confirm this
    # Source: https://docs.nostra.finance/lend/liquidations/an-example-of-liquidation.
    LIQUIDATION_BONUS = 0.2

    def compute_debt_to_be_liquidated(
        self,
        collateral_token_addresses: list[str],
        debt_token_addresses: list[str],
        prices: Prices,
        collateral_token_parameters: TokenParameters,
        debt_token_parameters: TokenParameters,
        collateral_interest_rate_model: InterestRateModels | None = None,
        debt_interest_rate_model: InterestRateModels | None = None,
        risk_adjusted_collateral_usd: float | None = None,
        risk_adjusted_debt_usd: float | None = None,
    ) -> float:
        """
        Computes the amount of debt that can be liquidated given the 
        current state of the loan entity.
        :param collateral_token_addresses: Collateral token addresses.
        :param debt_token_addresses:  Debt token addresses.
        :param prices: Prices of all tokens.
        :param collateral_token_parameters: Collateral token parameters.
        :param debt_token_parameters: Debt token parameters.
        :param collateral_interest_rate_model: Collateral interest rate model.
        :param debt_interest_rate_model: Debt interest rate model.
        :param risk_adjusted_collateral_usd: Risk-adjusted collateral value in USD.
        :param risk_adjusted_debt_usd: Risk-adjusted debt value in USD.
        :return: float
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

        # TODO: Commit a PDF with the derivation of the formula?
        # See an example of a liquidation here:
        # https://docs.nostra.finance/lend/liquidations/an-example-of-liquidation.
        numerator = (
            risk_adjusted_collateral_usd - risk_adjusted_debt_usd * self.TARGET_HEALTH_FACTOR
        )
        # TODO: figure out what to do when there's multiple collateral token addresses
        collateral_token_address = collateral_token_addresses[0]
        # TODO: figure out what to do when there's multiple collateral token addresses
        debt_token_address = debt_token_addresses[0]
        denominator = (
            collateral_token_parameters[collateral_token_address].collateral_factor *
            (1 + self.LIQUIDATION_BONUS) -
            (1 / debt_token_parameters[debt_token_address].debt_factor) * self.TARGET_HEALTH_FACTOR
        )
        max_debt_to_be_liquidated = numerator / denominator
        # The liquidator can't liquidate more debt than what is available.
        debt_to_be_liquidated = min(float(self.debt[debt_token_address]), max_debt_to_be_liquidated)
        return debt_to_be_liquidated


class NostraMainnetState(NostraAlphaState):
    """
    A class that describes the state of all Nostra Mainnet 
    loan entities. All methods for correct processing of every
    relevant event are implemented in `.nostra_alpha.NostraAlphaState`.
    """

    PROTOCOL_NAME: str = ProtocolIDs.NOSTRA_MAINNET.value
    TOKEN_ADDRESSES: list[str] = NOSTRA_MAINNET_TOKEN_ADDRESSES
    INTEREST_RATE_MODEL_ADDRESS: str = NOSTRA_MAINNET_INTEREST_RATE_MODEL_ADDRESS
    CDP_MANAGER_ADDRESS: str = NOSTRA_MAINNET_CDP_MANAGER_ADDRESS
    DEFERRED_BATCH_CALL_ADAPTER_ADDRESS: str = (NOSTRA_MAINNET_DEFERRED_BATCH_CALL_ADAPTER_ADDRESS)

    EVENTS_TO_METHODS: dict[str, str] = NOSTRA_MAINNET_EVENTS_TO_METHODS

    def __init__(
        self,
        verbose_user: str | None = None,
    ) -> None:
        super().__init__(
            loan_entity_class=NostraMainnetLoanEntity,
            verbose_user=verbose_user,
        )

    async def collect_token_parameters(self) -> None:
        """
        Collects the parameters of all tokens used in the Nostra Mainnet protocol.
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
                try:
                    # The order of the arguments is: `index`, `collateral_factor`, ``,
                    # `price_oracle`.
                    collateral_data = await stark_client.func_call(
                        addr=self.CDP_MANAGER_ADDRESS,
                        selector="collateral_data",
                        calldata=[underlying_token_address],
                    )
                    collateral_factor = collateral_data[1] / 1e18
                except starknet_py.net.client_errors.ClientError:
                    # For some tokens, the client returns `Collateral not registered`.
                    collateral_factor = 0.0

                # The order of the arguments is: `protocol_fee`, ``, `protocol_fee_recipient`.
                liquidation_settings = await stark_client.func_call(
                    addr=self.CDP_MANAGER_ADDRESS,
                    selector="liquidation_settings",
                    calldata=[underlying_token_address],
                )
                protocol_fee = liquidation_settings[0] / 1e18

                token_parameters = NostraMainnetCollateralTokenParameters(
                    address=token_address,
                    decimals=decimals,
                    symbol=token_symbol,
                    underlying_symbol=underlying_token_symbol,
                    underlying_address=underlying_token_address,
                    is_interest_bearing=is_interest_bearing,
                    collateral_factor=collateral_factor,
                    protocol_fee=protocol_fee,
                )
            else:
                # The order of the arguments is: `index`, `debt_tier`, `debt_factor`, ``,
                # `price_oracle`.
                debt_data = await stark_client.func_call(
                    addr=self.CDP_MANAGER_ADDRESS,
                    selector="debt_data",
                    calldata=[token_address],
                )
                debt_factor = debt_data[2] / 1e18

                token_parameters = NostraDebtTokenParameters(
                    address=token_address,
                    decimals=decimals,
                    symbol=token_symbol,
                    underlying_symbol=underlying_token_symbol,
                    underlying_address=underlying_token_address,
                    debt_factor=debt_factor,
                )
            getattr(self.token_parameters, event)[token_address] = token_parameters

        # Create the mapping between 
        # the debt token addresses and the respective interest bearing collateral token
        # addresses.
        for debt_token_parameters in self.token_parameters.debt.values():
            interest_bearing_collateral_token_addresses = [
                collateral_token_parameters.address
                for collateral_token_parameters in self.token_parameters.collateral.values() if (
                    collateral_token_parameters.is_interest_bearing and collateral_token_parameters.
                    underlying_address == debt_token_parameters.underlying_address
                )
            ]
            # TODO: check DAI V2
            if interest_bearing_collateral_token_addresses:
                assert len(interest_bearing_collateral_token_addresses) == 1
                self.debt_token_addresses_to_interest_bearing_collateral_token_addresses[
                    debt_token_parameters.address] = interest_bearing_collateral_token_addresses[0]

    def process_interest_rate_model_event(self, event: pd.Series) -> None:
        """
        Processes the `InterestStateUpdated` event.
        :param event: Event data.
        """
        if event["keys"] == [self.INTEREST_STATE_UPDATED_KEY]:
            # The order of the values in the `data` column is: 
            # `debtToken`, `lendingRate`, ``, `borrowRate`, ``,
            # `lendIndex`, ``, `borrowIndex`, ``.
            # Example:
            # https://starkscan.co/event/0x0735fc1d2fdd75ec049af40073a09ffc948c45467752d3123eb2b8c1d3f46edb_7.
            debt_token = add_leading_zeros(event["data"][0])
            collateral_interest_rate_index = Decimal(str(int(event["data"][5], base=16))
                                                     ) / Decimal("1e18")
            debt_interest_rate_index = Decimal(str(int(event["data"][7], base=16))
                                               ) / Decimal("1e18")
        elif (len(event["keys"]) == 2 and event["keys"][0] == self.INTEREST_STATE_UPDATED_KEY):
            # The order of the values in the `data` column is: `lendingRate`, 
            # ``, `borrowingRate`, ``, `lendingIndex`,
            # ``, `borrowingIndex`, ``.
            # Example:
            # https://starkscan.co/event/0x046d972ab22bd443534b32fdeabb1e4751ae6fa92610e9e2d4833764367d08f8_10.
            debt_token = add_leading_zeros(event["keys"][1])
            collateral_interest_rate_index = Decimal(str(int(event["data"][4], base=16))
                                                     ) / Decimal("1e18")
            debt_interest_rate_index = Decimal(str(int(event["data"][6], base=16))
                                               ) / Decimal("1e18")
        else:
            raise ValueError("Event = {} has an unexpected structure.".format(event))
        collateral_token = self.debt_token_addresses_to_interest_bearing_collateral_token_addresses.get(
            debt_token, None
        )
        # The indices are saved under the respective collateral or debt token address.
        if collateral_token:
            self.interest_rate_models.collateral[collateral_token] = (
                collateral_interest_rate_index
            )
        self.interest_rate_models.debt[debt_token] = debt_interest_rate_index

    def process_collateral_transfer_event(self, event: pd.Series) -> None:
        """
        Processes the `Transfer` event.
        :param event: Event data.
        """
        if event["keys"] == [self.TRANSFER_KEY]:
            # The order of the values in the `data` column is: `sender`, 
            # `recipient`, `value`, ``. Alternatively,
            # `from_`, `to`, `value`, ``.
            # Example:
            # https://starkscan.co/event/0x00489af46e28392d1c3e4007476328ba4ccf4bd84f4f5565fda0888d5518a70b_3.
            sender = add_leading_zeros(event["data"][0])
            recipient = add_leading_zeros(event["data"][1])
            raw_amount = Decimal(str(int(event["data"][2], base=16)))
        elif len(event["keys"]) == 3 and event["keys"][0] == self.TRANSFER_KEY:
            # The order of the values in the `data` column is: `value`, ``.
            # Example:
            # https://starkscan.co/event/0x0476bd5d00fa21ad5f4b6c02352770ec869b66659de4e784a77bf293dc1010a5_0.
            sender = add_leading_zeros(event["keys"][1])
            recipient = add_leading_zeros(event["keys"][2])
            raw_amount = Decimal(str(int(event["data"][0], base=16)))
        else:
            raise ValueError("Event = {} has an unexpected structure.".format(event))

        if self.ZERO_ADDRESS in {sender, recipient}:
            return

        token = add_leading_zeros(event["from_address"])
        if sender != self.DEFERRED_BATCH_CALL_ADAPTER_ADDRESS:
            self.loan_entities[sender].collateral.increase_value(token=token, value=-raw_amount)
        if recipient != self.DEFERRED_BATCH_CALL_ADAPTER_ADDRESS:
            self.loan_entities[recipient].collateral.increase_value(token=token, value=raw_amount)
        if self.verbose_user in {sender, recipient}:
            logger.info(
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
        """
        Processes the `Mint` event.
        :param event: Event data.
        """
        if event["keys"] == [self.MINT_KEY]:
            # The order of the values in the `data` column is: `user`, `amount`, ``.
            # Example:
            # https://starkscan.co/event/0x0477258515240a6d24c7b8b9a5d0c1c387b925186efd250c6f278245b40b442d_9.
            user = add_leading_zeros(event["data"][0])
            face_amount = Decimal(str(int(event["data"][1], base=16)))
        elif len(event["keys"]) == 2 and event["keys"][0] == self.MINT_KEY:
            # The order of the values in the `data` column is: `amount`, ``.
            # Example:
            # https://starkscan.co/event/0x01ebb29750907134804218ef5fc5f1688796a1a283e7d94aea87fa9a118f578a_4.
            user = add_leading_zeros(event["keys"][1])
            face_amount = Decimal(str(int(event["data"][0], base=16)))
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
            logger.info(
                "In block number = {}, collateral of raw amount = {} of token = {} was added.".
                format(
                    event["block_number"],
                    raw_amount,
                    token,
                )
            )

    def process_collateral_burn_event(self, event: pd.Series) -> None:
        """
        Processes the `Burn` event.
        :param event: Event data.
        """
        if event["keys"] == [self.BURN_KEY]:
            # The order of the values in the `data` column is: `user`, `amount`, ``.
            # Example:
            # https://starkscan.co/event/0x02eb8bbac79765f948cb49f91d2ffb85ffcf0e98a9292d9fdfbb426f69fd712f_1.
            user = add_leading_zeros(event["data"][0])
            face_amount = Decimal(str(int(event["data"][1], base=16)))
        elif len(event["keys"]) == 2 and event["keys"][0] == self.BURN_KEY:
            # The order of the values in the `data` column is: `amount`, ``.
            # Example:
            # https://starkscan.co/event/0x060e74cec0b2af4a0a885dd0c2019ae0af4cbc32fd36443286d03f8e1072028f_6.
            user = add_leading_zeros(event["keys"][1])
            face_amount = Decimal(str(int(event["data"][0], base=16)))
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
            logger.info(
                "In block number = {}, collateral of raw amount = {} of token = {} was withdrawn.".
                format(
                    event["block_number"],
                    raw_amount,
                    token,
                )
            )

    def process_debt_transfer_event(self, event: pd.Series) -> None:
        """
        Processes the `Transfer` event.
        :param event: Event data.
        """
        if event["keys"] == [self.TRANSFER_KEY]:
            # The order of the values in the `data` column is: `sender`, 
            # `recipient`, `value`, ``. Alternatively,
            # `from_`, `to`, `value`, ``.
            # Example:
            # https://starkscan.co/event/0x070f2c92bda051dc9f4daaef5582c7c2727b1ab07f04484c1f6a6109e1f9a0f6_2.
            sender = add_leading_zeros(event["data"][0])
            recipient = add_leading_zeros(event["data"][1])
            raw_amount = Decimal(str(int(event["data"][2], base=16)))
        elif len(event["keys"]) == 3 and event["keys"][0] == self.TRANSFER_KEY:
            # The order of the values in the `data` column is: `value`, ``.
            # Example:
            # https://starkscan.co/event/0x051aca058e0f4e6193f4bc78eabe870bfc07d477e803f89c8293fc97118d523a_4.
            sender = add_leading_zeros(event["keys"][1])
            recipient = add_leading_zeros(event["keys"][2])
            raw_amount = Decimal(str(int(event["data"][0], base=16)))
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
            logger.info(
                "In block number = {}, debt of raw amount = {} of token = {} was transferred from user = {} to user = {}."
                .format(
                    event["block_number"],
                    raw_amount,
                    token,
                    sender,
                    recipient,
                )
            )

    def process_debt_mint_event(self, event: pd.Series) -> None:
        """
        Processes the `Mint` event.
        :param event: Event data.
        """
        if event["keys"] == [self.MINT_KEY]:
            # The order of the values in the `data` column is: `user`, `amount`, ``.
            # Example:
            # https://starkscan.co/event/0x018092d8bf2b31834f6cc3dd0e00b6ebb71352c30b1c4549ac445c58cbce05fa_7.
            user = add_leading_zeros(event["data"][0])
            face_amount = Decimal(str(int(event["data"][1], base=16)))
        elif len(event["keys"]) == 2 and event["keys"][0] == self.MINT_KEY:
            # The order of the values in the `data` column is: `amount`, ``.
            # Example:
            # https://starkscan.co/event/0x02a7c2cf0263bebe38bbaace9c789ba600a1bd9ddd8f4341d618c0894048b28e_7.
            user = add_leading_zeros(event["keys"][1])
            face_amount = Decimal(str(int(event["data"][0], base=16)))
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
            logger.info(
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
            # https://starkscan.co/event/0x045561da020c693288386c92a4aaafae30ed1ddcdaa02373246d556b806662c1_7.
            user = add_leading_zeros(event["data"][0])
            face_amount = Decimal(str(int(event["data"][1], base=16)))
        elif len(event["keys"]) == 2 and event["keys"][0] == self.BURN_KEY:
            # The order of the values in the `data` column is: `amount`, ``.
            # Example:
            # https://starkscan.co/event/0x0580b701b7501058aa97a6e73670ca5530fdfe77e754a185378d85ebdac33034_5.
            user = add_leading_zeros(event["keys"][1])
            face_amount = Decimal(str(int(event["data"][0], base=16)))
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
            logger.info(
                "In block number = {}, raw amount = {} of token = {} was repaid.".format(
                    event["block_number"],
                    raw_amount,
                    token,
                )
            )

    # TODO: This method looks very similar to that of zkLend.
    def compute_liquidable_debt_at_price(
        self,
        prices: Prices,
        collateral_token_underlying_address: str,
        collateral_token_price: float,
        debt_token_underlying_address: str,
    ) -> float:
        """
        Computes the maximum amount of debt that can be 
        liquidated given the current state of the loan entities.
        :param prices: Prices of all tokens.
        :param collateral_token_underlying_address: Collateral token underlying address.
        :param collateral_token_price: Collateral token price.
        :param debt_token_underlying_address: Debt token underlying address.
        :return: float
        """
        changed_prices = copy.deepcopy(prices)
        changed_prices[collateral_token_underlying_address] = collateral_token_price
        max_liquidated_amount = 0.0
        for loan_entity in self.loan_entities.values():
            # Filter out entities where the collateral token of interest is deposited as collateral.
            collateral_token_underlying_addresses = {
                self.token_parameters.collateral[token].underlying_address
                for token, token_amount in loan_entity.collateral.items()
                if token_amount > Decimal("0")
            }
            if (not collateral_token_underlying_address in collateral_token_underlying_addresses):
                continue

            # Filter out entities where the debt token of interest is borowed.
            debt_token_underlying_addresses = {
                self.token_parameters.debt[token].underlying_address
                for token, token_amount in loan_entity.debt.items() if token_amount > Decimal("0")
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
            #  We assume that the liquidator receives the
            # collateral token of interest even though it might not be the most
            # optimal choice for the liquidator.
            collateral_token_addresses = {
                self.token_parameters.collateral[token].address
                for token, token_amount in loan_entity.collateral.items()
                if token_amount > Decimal("0")
            }
            collateral_token_addresses = get_addresses(
                token_parameters=self.token_parameters.collateral,
                underlying_address=collateral_token_underlying_address,
            )
            debt_token_addresses = get_addresses(
                token_parameters=self.token_parameters.debt,
                underlying_address=debt_token_underlying_address,
            )
            max_liquidated_amount += loan_entity.compute_debt_to_be_liquidated(
                collateral_token_addresses=collateral_token_addresses,
                debt_token_addresses=debt_token_addresses,
                prices=changed_prices,
                collateral_token_parameters=self.token_parameters.collateral,
                debt_token_parameters=self.token_parameters.debt,
                risk_adjusted_collateral_usd=risk_adjusted_collateral_usd,
                risk_adjusted_debt_usd=risk_adjusted_debt_usd,
            )
        return max_liquidated_amount
