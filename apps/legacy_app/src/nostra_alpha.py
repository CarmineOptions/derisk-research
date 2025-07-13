import asyncio
import copy
import dataclasses
import decimal
import logging

import pandas
import src.helpers
import src.settings
import src.state
import src.types

# Source: https://docs.nostra.finance/lend/deployed-contracts/lend-alpha#core-contracts.
NOSTRA_ALPHA_INTEREST_RATE_MODEL_ADDRESS: str = (
    "0x03d39f7248fb2bfb960275746470f7fb470317350ad8656249ec66067559e892"
)

# The commented addresses are non-collateral deposits which might be useful later. Source:
# https://docs.nostra.finance/lend/deployed-contracts/lend-alpha#core-contracts.
NOSTRA_ALPHA_TOKEN_ADDRESSES: list[str] = [
    # '0x0061d892cccf43daf73407194da9f0ea6dbece950bb24c50be2356444313a707',  # iWBTC
    "0x00687b5d9e591844169bc6ad7d7256c4867a10cee6599625b9d78ea17a7caef9",  # iWBTC-c
    # '0x07788bc687f203b6451f2a82e842b27f39c7cae697dace12edfb86c9b1c12f3d',  # nWBTC
    "0x06b59e2a746e141f90ec8b6e88e695265567ab3bdcf27059b4a15c89b0b7bd53",  # nWBTC-c
    "0x075b0d87aca8dee25df35cdc39a82b406168fa23a76fc3f03abbfdc6620bb6d7",  # dWBTC
    # '0x002f8deaebb9da2cb53771b9e2c6d67265d11a4e745ebd74a726b8859c9337b9',  # iETH
    "0x070f8a4fcd75190661ca09a7300b7c93fab93971b67ea712c664d7948a8a54c6",  # iETH-c
    # '0x04f89253e37ca0ab7190b2e9565808f105585c9cacca6b2fa6145553fa061a41',  # nETH
    "0x0553cea5d1dc0e0157ffcd36a51a0ced717efdadd5ef1b4644352bb45bd35453",  # nETH-c
    "0x040b091cb020d91f4a4b34396946b4d4e2a450dbd9410432ebdbfe10e55ee5e5",  # dETH
    # '0x06af9a313434c0987f5952277f1ac8c61dc4d50b8b009539891ed8aaee5d041d',  # iUSDC
    "0x029959a546dda754dc823a7b8aa65862c5825faeaaf7938741d8ca6bfdc69e4e",  # iUSDC-c
    # '0x05327df4c669cb9be5c1e2cf79e121edef43c1416fac884559cd94fcb7e6e232',  # nUSDC
    "0x047e794d7c49c49fd2104a724cfa69a92c5a4b50a5753163802617394e973833",  # nUSDC-c
    "0x03b6058a9f6029b519bc72b2cc31bcb93ca704d0ab79fec2ae5d43f79ac07f7a",  # dUSDC
    # '0x00b9b1a4373de5b1458e598df53195ea3204aa926f46198b50b32ed843ce508b',  # iDAI
    "0x01ac55cabf2b79cf39b17ba0b43540a64205781c4b7850e881014aea6f89be58",  # iDAI-c
    # '0x02ea39ba7a05f0c936b7468d8bc8d0e1f2116916064e7e163e7c1044d95bd135',  # nDAI
    "0x04403e420521e7a4ca0dc5192af81ca0bb36de343564a9495e11c8d9ba6e9d17",  # nDAI-c
    "0x0362b4455f5f4cc108a5a1ab1fd2cc6c4f0c70597abb541a99cf2734435ec9cb",  # dDAI
    # '0x06404c8e886fea27590710bb0e0e8c7a3e7d74afccc60663beb82707495f8609',  # iUSDT
    "0x055ba2baf189b98c59f6951a584a3a7d7d6ff2c4ef88639794e739557e1876f0",  # iUSDT-c
    # '0x040375d0720245bc0d123aa35dc1c93d14a78f64456eff75f63757d99a0e6a83',  # nUSDT
    "0x003cd2066f3c8b4677741b39db13acebba843bbbaa73d657412102ab4fd98601",  # nUSDT-c
    "0x065c6c7119b738247583286021ea05acc6417aa86d391dcdda21843c1fc6e9c6",  # dUSDT
]

NOSTRA_ALPHA_CDP_MANAGER_ADDRESS: str = (
    "0x06d272e18e66289eeb874d0206a23afba148ef35f250accfdfdca085a478aec0"
)

# This seems to be a magical address, it's first event is a withdrawal. Ignore it's loan state changes.
NOSTRA_ALPHA_DEFERRED_BATCH_CALL_ADAPTER_ADDRESS: str = (
    "0x05a0042fa9bb87ed72fbee4d5a2da416528ebc84a569081ad02e9ad60b0af7d7"
)


# Keys are tuples of event types and names, values are names of the respective methods that process the given event.
NOSTRA_ALPHA_EVENTS_TO_METHODS: dict[tuple[str, str], str] = {
    ("collateral", "Transfer"): "process_collateral_transfer_event",
    (
        "collateral",
        "openzeppelin::token::erc20_v070::erc20::ERC20::Transfer",
    ): "process_collateral_transfer_event",
    ("collateral", "Mint"): "process_collateral_mint_event",
    ("collateral", "Burn"): "process_collateral_burn_event",
    ("debt", "Transfer"): "process_debt_transfer_event",
    (
        "debt",
        "openzeppelin::token::erc20_v070::erc20::ERC20::Transfer",
    ): "process_debt_transfer_event",
    ("debt", "Mint"): "process_debt_mint_event",
    ("debt", "Burn"): "process_debt_burn_event",
}

# Keys are event names, values denote the order in which the given events should be processed.
NOSTRA_ALPHA_EVENTS_TO_ORDER: dict[str, str] = {
    "InterestStateUpdated": 0,
    "Transfer": 1,
    "openzeppelin::token::erc20_v070::erc20::ERC20::Transfer": 2,
    "Burn": 3,
    "Mint": 4,
}


def nostra_alpha_get_events(start_block_number: int = 0) -> pandas.DataFrame:
    user_events = src.helpers.get_events(
        addresses=tuple(NOSTRA_ALPHA_TOKEN_ADDRESSES),
        event_names=tuple(x[1] for x in NOSTRA_ALPHA_EVENTS_TO_METHODS),
        start_block_number=start_block_number,
    )
    interest_rate_events = src.helpers.get_events(
        addresses=(NOSTRA_ALPHA_INTEREST_RATE_MODEL_ADDRESS, ""),
        event_names=("InterestStateUpdated", ""),
        start_block_number=start_block_number,
    )
    events = pandas.concat([user_events, interest_rate_events])

    # Ensure we're processing `InterestStateUpdated` before other events.
    events["order"] = events["key_name"].map(NOSTRA_ALPHA_EVENTS_TO_ORDER)
    events.sort_values(["block_number", "transaction_hash", "order"], inplace=True)
    events.drop(columns=["order"], inplace=True)
    return events


class NostraAlphaLoanEntity(src.types.LoanEntity):
    """A class that describes the Nostra Alpha loan entity."""

    # TODO: fetch from chain
    LIQUIDATION_HEALTH_FACTOR_THRESHOLD = 1.0
    TARGET_HEALTH_FACTOR = 1.25

    def __init__(self) -> None:
        super().__init__()

    def compute_health_factor(
        self,
        standardized: bool,
        collateral_token_parameters: src.types.TokenParameters | None = None,
        collateral_interest_rate_model: src.types.InterestRateModels | None = None,
        debt_token_parameters: src.types.TokenParameters | None = None,
        debt_interest_rate_model: src.types.InterestRateModels | None = None,
        prices: src.types.Prices | None = None,
        risk_adjusted_collateral_usd: float | None = None,
        risk_adjusted_debt_usd: float | None = None,
    ) -> float:
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

        if standardized:
            # Denominator is the value of (risk-adjusted) collateral at which the loan entity can be liquidated.
            # TODO: denominator = risk_adjusted_debt_usd * liquidation_threshold??
            denominator = risk_adjusted_debt_usd
        else:
            denominator = risk_adjusted_debt_usd

        if denominator == 0.0:
            # TODO: Assumes collateral is positive.
            return float("inf")
        return risk_adjusted_collateral_usd / denominator

    def compute_debt_to_be_liquidated(
        self,
        collateral_token_addresses: list[str],
        collateral_token_parameters: src.types.TokenParameters,
        health_factor: float,
        debt_token_parameters: src.types.TokenParameters,
        debt_token_addresses: list[str],
        debt_token_debt_amount: decimal.Decimal,
        debt_token_price: float,
    ) -> float:
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
                collateral_token_parameters[
                    collateral_token_address
                ].liquidator_fee_beta
                * (self.LIQUIDATION_HEALTH_FACTOR_THRESHOLD - health_factor),
                collateral_token_parameters[
                    collateral_token_address
                ].liquidator_fee_max,
            )
            total_fee = (
                liquidator_fee
                + collateral_token_parameters[collateral_token_address].protocol_fee
            )
            max_liquidation_percentage = (self.TARGET_HEALTH_FACTOR - health_factor) / (
                self.TARGET_HEALTH_FACTOR
                - (
                    collateral_token_parameters[
                        collateral_token_address
                    ].collateral_factor
                    * debt_token_parameters[debt_token_addresses[0]].debt_factor
                    * (1.0 + total_fee)
                )
            )
            max_liquidation_percentage = min(max_liquidation_percentage, 1.0)
            max_liquidation_amount = max_liquidation_percentage * float(
                debt_token_debt_amount
            )
            max_liquidation_amount_usd = (
                debt_token_price
                * max_liquidation_amount
                / (10 ** debt_token_parameters[debt_token_addresses[0]].decimals)
            )
            max_liquidator_fee_usd = liquidator_fee * max_liquidation_amount_usd
            if max_liquidator_fee_usd > liquidator_fee_usd:
                liquidator_fee_usd = max_liquidator_fee_usd
                liquidation_amount_usd = max_liquidation_amount_usd
        return liquidation_amount_usd


@dataclasses.dataclass
class NostraAlphaCollateralTokenParameters(src.types.BaseTokenParameters):
    is_interest_bearing: bool  # TODO: remove if distinguished within the loan entity
    collateral_factor: float
    liquidator_fee_beta: float
    liquidator_fee_max: float
    protocol_fee: float


@dataclasses.dataclass
class NostraAlphaDebtTokenParameters(src.types.BaseTokenParameters):
    debt_factor: float


class NostraAlphaState(src.state.State):
    """
    A class that describes the state of all Nostra Alpha loan entities. It implements a method for correct processing
    of every relevant event.
    """

    TOKEN_ADDRESSES: list[str] = NOSTRA_ALPHA_TOKEN_ADDRESSES
    INTEREST_RATE_MODEL_ADDRESS: str = NOSTRA_ALPHA_INTEREST_RATE_MODEL_ADDRESS
    CDP_MANAGER_ADDRESS: str = NOSTRA_ALPHA_CDP_MANAGER_ADDRESS
    DEFERRED_BATCH_CALL_ADAPTER_ADDRESS: str = (
        NOSTRA_ALPHA_DEFERRED_BATCH_CALL_ADAPTER_ADDRESS
    )

    EVENTS_TO_METHODS: dict[str, str] = NOSTRA_ALPHA_EVENTS_TO_METHODS

    # These variables are missing the leading 0's on purpose, because they're missing in the raw event keys, too.
    INTEREST_STATE_UPDATED_KEY = (
        "0x33db1d611576200c90997bde1f948502469d333e65e87045c250e6efd2e42c7"
    )
    TRANSFER_KEY = "0x99cd8bde557814842a3121e8ddfd433a539b8c9f14bf31ebf108d12e6196e9"
    MINT_KEY = "0x34e55c1cd55f1338241b50d352f0e91c7e4ffad0e4271d64eb347589ebdfd16"
    BURN_KEY = "0x243e1de00e8a6bc1dfa3e950e6ade24c52e4a25de4dee7fb5affe918ad1e744"

    # We ignore transfers where the sender or recipient are '0x0' because these are mints and burns covered by other
    # events.
    ZERO_ADDRESS: str = src.helpers.add_leading_zeros("0x0")

    def __init__(
        self,
        loan_entity_class: NostraAlphaLoanEntity = NostraAlphaLoanEntity,
        verbose_user: str | None = None,
    ) -> None:
        super().__init__(
            loan_entity_class=loan_entity_class,
            verbose_user=verbose_user,
        )

        # These dicts' keys are the collateral/debt token addresses.
        self.token_addresses_to_events: dict[str, str] = {}
        self.debt_token_addresses_to_interest_bearing_collateral_token_addresses: dict[
            str, str
        ] = {}

        asyncio.run(self.collect_token_parameters())

    @staticmethod
    def _infer_token_type(token_symbol: str) -> tuple[str, bool]:
        if token_symbol[0] == "d" and token_symbol[-2:] != "-c":
            return "debt", True
        elif token_symbol[0] == "n" and token_symbol[-2:] == "-c":
            return "collateral", False
        elif token_symbol[0] == "i" and token_symbol[-2:] == "-c":
            return "collateral", True
        raise ValueError("Can't infer token type for token symbol = {}.", token_symbol)

    async def collect_token_parameters(self) -> None:
        for token_address in self.TOKEN_ADDRESSES:
            decimals = await src.blockchain_call.func_call(
                addr=token_address,
                selector="decimals",
                calldata=[],
            )
            decimals = int(decimals[0])

            token_symbol = await src.helpers.get_symbol(token_address=token_address)
            event, is_interest_bearing = self._infer_token_type(
                token_symbol=token_symbol
            )
            self.token_addresses_to_events[token_address] = event

            underlying_token_address = await src.blockchain_call.func_call(
                addr=token_address,
                selector="underlyingAsset",
                calldata=[],
            )
            underlying_token_address = src.helpers.add_leading_zeros(
                hex(underlying_token_address[0])
            )
            underlying_token_symbol = await src.helpers.get_symbol(
                token_address=underlying_token_address
            )

            if event == "collateral":
                # The order of the arguments is: `id`, `asset`, `collateralFactor`, ``, `priceOracle`.
                collateral_data = await src.blockchain_call.func_call(
                    addr=self.CDP_MANAGER_ADDRESS,
                    selector="getCollateralData",
                    calldata=[underlying_token_address],
                )
                collateral_factor = collateral_data[2] / 1e18

                # The order of the arguments is: `protocolFee`, ``, `protocolFeeRecipient`, `liquidatorFeeBeta`, ``,
                # `liquidatorFeeMax`, ``.
                liquidation_settings = await src.blockchain_call.func_call(
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
                # The order of the arguments is: `id`, `debtTier`, `debtToken`, `debtFactor`, ``, `priceOracle`.
                debt_data = await src.blockchain_call.func_call(
                    addr=self.CDP_MANAGER_ADDRESS,
                    selector="getDebtData",
                    calldata=[token_address],
                )
                debt_factor = debt_data[3] / 1e18

                token_parameters = NostraAlphaDebtTokenParameters(
                    address=token_address,
                    decimals=decimals,
                    symbol=token_symbol,
                    underlying_symbol=underlying_token_symbol,
                    underlying_address=underlying_token_address,
                    debt_factor=debt_factor,
                )
            getattr(self.token_parameters, event)[token_address] = token_parameters

        # Create the mapping between the debt token addresses and the respective interest bearing collateral token
        # addresses.
        for debt_token_parameters in self.token_parameters.debt.values():
            interest_bearing_collateral_token_addresses = [
                collateral_token_parameters.address
                for collateral_token_parameters in self.token_parameters.collateral.values()
                if (
                    collateral_token_parameters.is_interest_bearing
                    and collateral_token_parameters.underlying_address
                    == debt_token_parameters.underlying_address
                )
            ]
            assert len(interest_bearing_collateral_token_addresses) == 1
            self.debt_token_addresses_to_interest_bearing_collateral_token_addresses[
                debt_token_parameters.address
            ] = interest_bearing_collateral_token_addresses[0]

    def process_event(self, event: pandas.Series) -> None:
        assert event["block_number"] >= self.last_block_number
        self.last_block_number = event["block_number"]
        if event["from_address"] == self.INTEREST_RATE_MODEL_ADDRESS:
            self.process_interest_rate_model_event(event)
            return
        event_type = self.token_addresses_to_events[event["from_address"]]
        getattr(self, self.EVENTS_TO_METHODS[(event_type, event["key_name"])])(
            event=event
        )

    def process_interest_rate_model_event(self, event: pandas.Series) -> None:
        if event["keys"] == [self.INTEREST_STATE_UPDATED_KEY]:
            # The order of the values in the `data` column is: `debtToken`, `lendingRate`, ``, `borrowRate`, ``,
            # `lendIndex`, ``, `borrowIndex`, ``.
            # Example: https://starkscan.co/event/0x05e95588e281d7cab6f89aa266057c4c9bcadf3ff0bb85d4feea40a4faa94b09_4.
            debt_token = src.helpers.add_leading_zeros(event["data"][0])
            collateral_interest_rate_index = decimal.Decimal(
                str(int(event["data"][5], base=16))
            ) / decimal.Decimal("1e18")
            debt_interest_rate_index = decimal.Decimal(
                str(int(event["data"][7], base=16))
            ) / decimal.Decimal("1e18")
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

    def process_collateral_transfer_event(self, event: pandas.Series) -> None:
        if event["keys"] == [self.TRANSFER_KEY]:
            # The order of the values in the `data` column is: `sender`, `recipient`, `value`, ``. Alternatively,
            # `from_`, `to`, `value`, ``.
            # Example: https://starkscan.co/event/0x06ddd34767c8cef97d4508bcbb4e3771b1c93e160e02ca942cadbdfa29ef9ba8_2.
            sender = src.helpers.add_leading_zeros(event["data"][0])
            recipient = src.helpers.add_leading_zeros(event["data"][1])
            raw_amount = decimal.Decimal(str(int(event["data"][2], base=16)))
        else:
            raise ValueError("Event = {} has an unexpected structure.".format(event))
        if self.ZERO_ADDRESS in {sender, recipient}:
            return
        token = src.helpers.add_leading_zeros(event["from_address"])
        if sender != self.DEFERRED_BATCH_CALL_ADAPTER_ADDRESS:
            self.loan_entities[sender].collateral.increase_value(
                token=token, value=-raw_amount
            )
        if recipient != self.DEFERRED_BATCH_CALL_ADAPTER_ADDRESS:
            self.loan_entities[recipient].collateral.increase_value(
                token=token, value=raw_amount
            )
        if self.verbose_user in {sender, recipient}:
            logging.info(
                "In block number = {}, collateral of raw amount = {} of token = {} was transferred from user = {} to user = {}.".format(
                    event["block_number"],
                    raw_amount,
                    token,
                    sender,
                    recipient,
                )
            )

    def process_collateral_mint_event(self, event: pandas.Series) -> None:
        if event["keys"] == [self.MINT_KEY]:
            # The order of the values in the `data` column is: `user`, `amount`, ``.
            # Example: https://starkscan.co/event/0x015dccf7bc9a434bcc678cf730fa92641a2f6bcbfdb61cbe7a1ef7d0a614d1ac_3.
            user = src.helpers.add_leading_zeros(event["data"][0])
            face_amount = decimal.Decimal(str(int(event["data"][1], base=16)))
        else:
            raise ValueError("Event = {} has an unexpected structure.".format(event))
        if user == self.DEFERRED_BATCH_CALL_ADAPTER_ADDRESS:
            return
        token = src.helpers.add_leading_zeros(event["from_address"])
        if self.token_parameters.collateral[token].is_interest_bearing:
            raw_amount = face_amount / self.interest_rate_models.collateral[token]
        else:
            raw_amount = face_amount
        self.loan_entities[user].collateral.increase_value(
            token=token, value=raw_amount
        )
        if user == self.verbose_user:
            logging.info(
                "In block number = {}, collateral of raw amount = {} of token = {} was added.".format(
                    event["block_number"],
                    raw_amount,
                    token,
                )
            )

    def process_collateral_burn_event(self, event: pandas.Series) -> None:
        if event["keys"] == [self.BURN_KEY]:
            # The order of the values in the `data` column is: `user`, `amount`, ``.
            # Example: https://starkscan.co/event/0x00744177ee88dd3d96dda1784e2dff50f0c989b7fd48755bc42972af2e951dd6_1.
            user = src.helpers.add_leading_zeros(event["data"][0])
            face_amount = decimal.Decimal(str(int(event["data"][1], base=16)))
        else:
            raise ValueError("Event = {} has an unexpected structure.".format(event))
        if user == self.DEFERRED_BATCH_CALL_ADAPTER_ADDRESS:
            return
        token = src.helpers.add_leading_zeros(event["from_address"])
        if self.token_parameters.collateral[token].is_interest_bearing:
            raw_amount = face_amount / self.interest_rate_models.collateral[token]
        else:
            raw_amount = face_amount
        self.loan_entities[user].collateral.increase_value(
            token=token, value=-raw_amount
        )
        if user == self.verbose_user:
            logging.info(
                "In block number = {}, collateral of raw amount = {} of token = {} was withdrawn.".format(
                    event["block_number"],
                    raw_amount,
                    token,
                )
            )

    def process_debt_transfer_event(self, event: pandas.Series) -> None:
        if event["keys"] == [self.TRANSFER_KEY]:
            # The order of the values in the `data` column is: `sender`, `recipient`, `value`, ``. Alternatively,
            # `from_`, `to`, `value`, ``.
            # Example: https://starkscan.co/event/0x0786a8918c8897db760899ee35b43071bfd723fec76487207882695e4b3014a0_1.
            sender = src.helpers.add_leading_zeros(event["data"][0])
            recipient = src.helpers.add_leading_zeros(event["data"][1])
            raw_amount = decimal.Decimal(str(int(event["data"][2], base=16)))
        else:
            raise ValueError("Event = {} has an unexpected structure.".format(event))
        if self.ZERO_ADDRESS in {sender, recipient}:
            return
        token = src.helpers.add_leading_zeros(event["from_address"])
        if sender != self.DEFERRED_BATCH_CALL_ADAPTER_ADDRESS:
            self.loan_entities[sender].debt.increase_value(
                token=token, value=-raw_amount
            )
        if recipient != self.DEFERRED_BATCH_CALL_ADAPTER_ADDRESS:
            self.loan_entities[recipient].debt.increase_value(
                token=token, value=raw_amount
            )
        if self.verbose_user in {sender, recipient}:
            logging.info(
                "In block number = {}, debt of raw amount = {} of token = {} was transferred from user = {} to user = {}.".format(
                    event["block_number"],
                    raw_amount,
                    token,
                    sender,
                    recipient,
                )
            )

    def process_debt_mint_event(self, event: pandas.Series) -> None:
        if event["keys"] == [self.MINT_KEY]:
            # The order of the values in the `data` column is: `user`, `amount`, ``.
            # Example: https://starkscan.co/event/0x030d23c4769917bc673875e107ebdea31711e2bdc45e658125dbc2e988945f69_4.
            user = src.helpers.add_leading_zeros(event["data"][0])
            face_amount = decimal.Decimal(str(int(event["data"][1], base=16)))
        else:
            raise ValueError("Event = {} has an unexpected structure.".format(event))
        if user == self.DEFERRED_BATCH_CALL_ADAPTER_ADDRESS:
            return
        token = src.helpers.add_leading_zeros(event["from_address"])
        raw_amount = face_amount / self.interest_rate_models.debt[token]
        self.loan_entities[user].debt.increase_value(token=token, value=raw_amount)
        if user == self.verbose_user:
            logging.info(
                "In block number = {}, raw amount = {} of token = {} was borrowed.".format(
                    event["block_number"],
                    raw_amount,
                    token,
                )
            )

    def process_debt_burn_event(self, event: pandas.Series) -> None:
        if event["keys"] == [self.BURN_KEY]:
            # The order of the values in the `data` column is: `user`, `amount`, ``.
            # Example: https://starkscan.co/event/0x002e4ee376785f687f32715d8bbed787b6d0fa9775dc9329ca2185155a139ca3_5.
            user = src.helpers.add_leading_zeros(event["data"][0])
            face_amount = decimal.Decimal(str(int(event["data"][1], base=16)))
        else:
            raise ValueError("Event = {} has an unexpected structure.".format(event))
        if user == self.DEFERRED_BATCH_CALL_ADAPTER_ADDRESS:
            return
        token = src.helpers.add_leading_zeros(event["from_address"])
        raw_amount = face_amount / self.interest_rate_models.debt[token]
        self.loan_entities[user].debt.increase_value(token=token, value=-raw_amount)
        if user == self.verbose_user:
            logging.info(
                "In block number = {}, raw amount = {} of token = {} was repaid.".format(
                    event["block_number"],
                    raw_amount,
                    token,
                )
            )

    # TODO: This method looks very similar to that of zkLend.
    def compute_liquidable_debt_at_price(
        self,
        prices: src.types.Prices,
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
                self.token_parameters.collateral[token].underlying_address
                for token, token_amount in loan_entity.collateral.items()
                if token_amount > decimal.Decimal("0")
            }
            if (
                not collateral_token_underlying_address
                in collateral_token_underlying_addresses
            ):
                continue

            # Filter out entities where the debt token of interest is borowed.
            debt_token_underlying_addresses = {
                self.token_parameters.debt[token].underlying_address
                for token, token_amount in loan_entity.debt.items()
                if token_amount > decimal.Decimal("0")
            }
            if not debt_token_underlying_address in debt_token_underlying_addresses:
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

            # Find out how much of the `debt_token` will be liquidated. We assume that the liquidator receives the
            # collateral token of interest even though it might not be the most optimal choice for the liquidator.
            collateral_token_addresses = {
                self.token_parameters.collateral[token].address
                for token, token_amount in loan_entity.collateral.items()
                if token_amount > decimal.Decimal("0")
            }
            debt_token_addresses = src.helpers.get_addresses(
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
