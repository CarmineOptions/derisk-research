from typing import Dict, Optional, Set, Tuple
import copy
import decimal
import logging

import pandas

import src.constants
import src.helpers
import src.state



ADDRESSES_TO_TOKENS: Dict[str, str] = {
    '0x0553cea5d1dc0e0157ffcd36a51a0ced717efdadd5ef1b4644352bb45bd35453': 'ETH',
    '0x047e794d7c49c49fd2104a724cfa69a92c5a4b50a5753163802617394e973833': 'USDC',
    '0x003cd2066f3c8b4677741b39db13acebba843bbbaa73d657412102ab4fd98601': 'USDT',
    '0x04403e420521e7a4ca0dc5192af81ca0bb36de343564a9495e11c8d9ba6e9d17': 'DAI',
    '0x06b59e2a746e141f90ec8b6e88e695265567ab3bdcf27059b4a15c89b0b7bd53': 'wBTC',
    '0x070f8a4fcd75190661ca09a7300b7c93fab93971b67ea712c664d7948a8a54c6': 'ETH',
    '0x029959a546dda754dc823a7b8aa65862c5825faeaaf7938741d8ca6bfdc69e4e': 'USDC',
    '0x055ba2baf189b98c59f6951a584a3a7d7d6ff2c4ef88639794e739557e1876f0': 'USDT', 
    '0x01ac55cabf2b79cf39b17ba0b43540a64205781c4b7850e881014aea6f89be58': 'DAI',
    '0x00687b5d9e591844169bc6ad7d7256c4867a10cee6599625b9d78ea17a7caef9': 'wBTC',
    '0x040b091cb020d91f4a4b34396946b4d4e2a450dbd9410432ebdbfe10e55ee5e5': 'ETH',
    '0x03b6058a9f6029b519bc72b2cc31bcb93ca704d0ab79fec2ae5d43f79ac07f7a': 'USDC',
    '0x065c6c7119b738247583286021ea05acc6417aa86d391dcdda21843c1fc6e9c6': 'USDT',
    '0x0362b4455f5f4cc108a5a1ab1fd2cc6c4f0c70597abb541a99cf2734435ec9cb': 'DAI',
    '0x075b0d87aca8dee25df35cdc39a82b406168fa23a76fc3f03abbfdc6620bb6d7': 'wBTC',
}
ADDRESSES_TO_EVENTS: Dict[str, str] = {
    '0x0553cea5d1dc0e0157ffcd36a51a0ced717efdadd5ef1b4644352bb45bd35453': 'non_interest_bearing_collateral',
    '0x047e794d7c49c49fd2104a724cfa69a92c5a4b50a5753163802617394e973833': 'non_interest_bearing_collateral',
    '0x003cd2066f3c8b4677741b39db13acebba843bbbaa73d657412102ab4fd98601': 'non_interest_bearing_collateral',
    '0x04403e420521e7a4ca0dc5192af81ca0bb36de343564a9495e11c8d9ba6e9d17': 'non_interest_bearing_collateral',
    '0x06b59e2a746e141f90ec8b6e88e695265567ab3bdcf27059b4a15c89b0b7bd53': 'non_interest_bearing_collateral',
    '0x070f8a4fcd75190661ca09a7300b7c93fab93971b67ea712c664d7948a8a54c6': 'interest_bearing_collateral',
    '0x029959a546dda754dc823a7b8aa65862c5825faeaaf7938741d8ca6bfdc69e4e': 'interest_bearing_collateral',
    '0x055ba2baf189b98c59f6951a584a3a7d7d6ff2c4ef88639794e739557e1876f0': 'interest_bearing_collateral', 
    '0x01ac55cabf2b79cf39b17ba0b43540a64205781c4b7850e881014aea6f89be58': 'interest_bearing_collateral',
    '0x00687b5d9e591844169bc6ad7d7256c4867a10cee6599625b9d78ea17a7caef9': 'interest_bearing_collateral',
    '0x040b091cb020d91f4a4b34396946b4d4e2a450dbd9410432ebdbfe10e55ee5e5': 'debt',
    '0x03b6058a9f6029b519bc72b2cc31bcb93ca704d0ab79fec2ae5d43f79ac07f7a': 'debt',
    '0x065c6c7119b738247583286021ea05acc6417aa86d391dcdda21843c1fc6e9c6': 'debt',
    '0x0362b4455f5f4cc108a5a1ab1fd2cc6c4f0c70597abb541a99cf2734435ec9cb': 'debt',
    '0x075b0d87aca8dee25df35cdc39a82b406168fa23a76fc3f03abbfdc6620bb6d7': 'debt',
}

INTEREST_RATE_MODEL_ADDRESS: str = '0x03d39f7248fb2bfb960275746470f7fb470317350ad8656249ec66067559e892'

# Keys are values of the "key_name" column in the database, values are the respective method names.
EVENTS_METHODS_MAPPING: Dict[Tuple[str, str], str] = {
    ("non_interest_bearing_collateral", "Mint"): "process_non_interest_bearing_collateral_mint_event",
    ("non_interest_bearing_collateral", "Burn"): "process_non_interest_bearing_collateral_burn_event",
    ("interest_bearing_collateral", "Mint"): "process_interest_bearing_collateral_mint_event",
    ("interest_bearing_collateral", "Burn"): "process_interest_bearing_collateral_burn_event",
    ("debt", "Mint"): "process_debt_mint_event",
    ("debt", "Burn"): "process_debt_burn_event",
}

# Source: Starkscan, e.g. 
# https://starkscan.co/call/0x06f619127a63ddb5328807e535e56baa1e244c8923a3b50c123d41dcbed315da_1_1 for ETH.
# TODO: Load these via chain calls?
COLLATERAL_FACTORS = {
    'ETH': decimal.Decimal('0.8'),
    'USDC': decimal.Decimal('0.9'),
    'USDT': decimal.Decimal('0.9'),
    'DAI': decimal.Decimal('0'),
    'wBTC': decimal.Decimal('0'),
    # TODO: Add wstETH.
    'wstETH': decimal.Decimal('1'),
}
# TODO: Add source.
DEBT_FACTORS = {
    'ETH': decimal.Decimal('0.9'),
    'USDC': decimal.Decimal('0.95'),
    'USDT': decimal.Decimal('0.95'),
    'DAI': decimal.Decimal('0.95'),
    'wBTC': decimal.Decimal('0.8'),
    # TODO: Add wstETH.
    'wstETH': decimal.Decimal('1'),
}
# TODO: Add sources for liquidation parameters.
LIQUIDATION_HEALTH_FACTOR_THRESHOLD = decimal.Decimal('1')
TARGET_HEALTH_FACTOR = decimal.Decimal('1.25')
LIQUIDATOR_FEE_BETAS = {
    'ETH': decimal.Decimal('2.75'),
    'USDC': decimal.Decimal('1.65'),
    'USDT': decimal.Decimal('1.65'),
    'DAI': decimal.Decimal('2.2'),
    'wBTC': decimal.Decimal('2.75'),
}
LIQUIDATOR_FEE_MAXS = {
    'ETH': decimal.Decimal('0.25'),
    'USDC': decimal.Decimal('0.15'),
    'USDT': decimal.Decimal('0.15'),
    'DAI': decimal.Decimal('0.2'),
    'wBTC': decimal.Decimal('0.25'),
}
PROTOCOL_FEES = {
    'ETH': decimal.Decimal('0.02'),
    'USDC': decimal.Decimal('0.02'),
    'USDT': decimal.Decimal('0.02'),
    'DAI': decimal.Decimal('0.02'),
    'wBTC': decimal.Decimal('0.02'),
}


SUPPLY_ADRESSES: Dict[str, str] = {
    "ETH": "0x04f89253e37ca0ab7190b2e9565808f105585c9cacca6b2fa6145553fa061a41",
    "wBTC": "0x07788bc687f203b6451f2a82e842b27f39c7cae697dace12edfb86c9b1c12f3d",
    "USDC": "0x05327df4c669cb9be5c1e2cf79e121edef43c1416fac884559cd94fcb7e6e232",
    "DAI": "0x02ea39ba7a05f0c936b7468d8bc8d0e1f2116916064e7e163e7c1044d95bd135",
    "USDT": "0x040375d0720245bc0d123aa35dc1c93d14a78f64456eff75f63757d99a0e6a83",
}



# TODO: Load and process transfers as well.
def get_events(start_block_number: int = 0) -> pandas.DataFrame:
    user_events = src.helpers.get_events(
        adresses = tuple(ADDRESSES_TO_TOKENS),
        events = ('Burn', 'Mint'),
        start_block_number = start_block_number,
    )
    interest_rate_events = src.helpers.get_events(
        adresses = (INTEREST_RATE_MODEL_ADDRESS, ''),
        events = ('InterestStateUpdated', ''),
        start_block_number = start_block_number,
    )
    events = pandas.concat([user_events, interest_rate_events])
    events.sort_values(['block_number', 'id'], inplace = True)
    return events


# TODO: Make this a dataclass?
# TODO: Explore similarities with zkLend's `Accumulators` class.`
class InterestRateModel:
    """
    A class that describes the state of the collateral and debt interest rate indices which help transform face amounts
    into raw amounts. Raw amount is the amount that would have been accumulated into the face amount if it were 
    deposited at genesis.
    """

    def __init__(self) -> None:
        # This number reflects the interest rate at which users lend/stake funds.
        self.collateral_interest_rate_index: decimal.Decimal = decimal.Decimal("1")
        # This number reflects the interest rate at which users borrow funds.
        self.debt_interest_rate_index: decimal.Decimal = decimal.Decimal("1")


class NostraLoanEntity(src.state.LoanEntity):
    """
    A class that describes the Nostra loan entity. Compared to the abstract `LoanEntity`, it implements its own 
    `compute_risk_adjusted_debt_usd`, `compute_health_factor` and `compute_debt_to_be_liquidated` methods in order to 
    reflect specific features of Nostra, such as using `DEBT_FACTORS`, or its specific liquidation process.
    """

    COLLATERAL_FACTORS = COLLATERAL_FACTORS
    DEBT_FACTORS = DEBT_FACTORS
    LIQUIDATION_HEALTH_FACTOR_THRESHOLD = LIQUIDATION_HEALTH_FACTOR_THRESHOLD
    TARGET_HEALTH_FACTOR = TARGET_HEALTH_FACTOR
    LIQUIDATOR_FEE_BETAS = LIQUIDATOR_FEE_BETAS
    LIQUIDATOR_FEE_MAXS = LIQUIDATOR_FEE_MAXS
    PROTOCOL_FEES = PROTOCOL_FEES

    def __init__(self) -> None:
        super().__init__()
        self.non_interest_bearing_collateral: src.state.TokenAmounts = src.state.TokenAmounts()
        self.interest_bearing_collateral: src.state.TokenAmounts = src.state.TokenAmounts()

    def compute_risk_adjusted_debt_usd(self, prices: Dict[str, decimal.Decimal]) -> decimal.Decimal:
        return sum(
            token_amount
            / src.constants.TOKEN_DECIMAL_FACTORS[token]
            / self.DEBT_FACTORS[token]
            * prices[token]
            for token, token_amount in self.debt.token_amounts.items()
        )

    def compute_health_factor(
        self,
        prices: Optional[Dict[str, decimal.Decimal]] = None,
        risk_adjusted_collateral_usd: Optional[decimal.Decimal] = None,
        risk_adjusted_debt_usd: Optional[decimal.Decimal] = None,
    ) -> decimal.Decimal:
        if risk_adjusted_collateral_usd is None:
            risk_adjusted_collateral_usd = self.compute_risk_adjusted_collateral_usd(prices = prices)
        if risk_adjusted_debt_usd is None:
            risk_adjusted_debt_usd = self.compute_risk_adjusted_debt_usd(prices = prices)
        if risk_adjusted_debt_usd == decimal.Decimal("0"):
            # TODO: Assumes collateral is positive.
            return decimal.Decimal("Inf")
        return risk_adjusted_collateral_usd / risk_adjusted_debt_usd

    def compute_standardized_health_factor(
        self,
        prices: Optional[Dict[str, decimal.Decimal]] = None,
        risk_adjusted_collateral_usd: Optional[decimal.Decimal] = None,
        risk_adjusted_debt_usd: Optional[decimal.Decimal] = None,
    ) -> decimal.Decimal:
        if risk_adjusted_collateral_usd is None:
            risk_adjusted_collateral_usd = self.compute_risk_adjusted_collateral_usd(prices = prices)
        if risk_adjusted_debt_usd is None:
            risk_adjusted_debt_usd = self.compute_risk_adjusted_debt_usd(prices = prices)
        # Compute the value of (risk-adjusted) collateral at which the user/loan can be liquidated.
        collateral_usd_threshold = risk_adjusted_debt_usd
        if collateral_usd_threshold == decimal.Decimal("0"):
            # TODO: Assumes collateral is positive.
            return decimal.Decimal("Inf")
        return risk_adjusted_collateral_usd / collateral_usd_threshold

    def compute_debt_to_be_liquidated(
        self,
        debt_token: str,
        collateral_tokens: Set[str],
        health_factor: decimal.Decimal,
        debt_token_debt_amount: decimal.Decimal,
        debt_token_price: decimal.Decimal,
    ) -> decimal.Decimal:
        liquidator_fee_usd = decimal.Decimal('0')
        liquidation_amount_usd = decimal.Decimal('0')
        # Choose the most optimal collateral_token to be liquidated.
        for collateral_token in collateral_tokens:
            # TODO: Commit a PDF with the derivation of thetoken_states[debt_token] formula?
            # See an example of a liquidation here: 
            # https://docs.nostra.finance/lend/liquidations/an-example-of-liquidation.
            liquidator_fee = min(
                self.LIQUIDATOR_FEE_BETAS[collateral_token]
                * (self.LIQUIDATION_HEALTH_FACTOR_THRESHOLD - health_factor),
                self.LIQUIDATOR_FEE_MAXS[collateral_token],
            )
            total_fee = liquidator_fee + self.PROTOCOL_FEES[collateral_token]
            max_liquidation_percentage = (
                self.TARGET_HEALTH_FACTOR - health_factor
            ) / (
                self.TARGET_HEALTH_FACTOR - (
                    self.COLLATERAL_FACTORS[collateral_token]
                    * self.DEBT_FACTORS[debt_token]
                    * (decimal.Decimal('1') + total_fee)
                )
            )
            max_liquidation_percentage = min(max_liquidation_percentage, decimal.Decimal('1'))
            max_liquidation_amount = max_liquidation_percentage * debt_token_debt_amount
            max_liquidation_amount_usd = (
                max_liquidation_amount * debt_token_price / src.constants.TOKEN_DECIMAL_FACTORS[debt_token]
            )
            max_liquidator_fee_usd = liquidator_fee * max_liquidation_amount_usd
            if max_liquidator_fee_usd > liquidator_fee_usd:
                liquidator_fee_usd = max_liquidator_fee_usd
                liquidation_amount_usd = max_liquidation_amount_usd
        return liquidation_amount_usd


class NostraState(src.state.State):
    """
    A class that describes the state of all Nostra loan entities. It implements a method for correct processing of 
    every relevant event.
    """

    ADDRESSES_TO_TOKENS = ADDRESSES_TO_TOKENS
    ADDRESSES_TO_EVENTS = ADDRESSES_TO_EVENTS
    INTEREST_RATE_MODEL_ADDRESS = INTEREST_RATE_MODEL_ADDRESS
    EVENTS_METHODS_MAPPING = EVENTS_METHODS_MAPPING
    # TODO: This seems to be a magical address.
    IGNORE_USER: str = '0x5a0042fa9bb87ed72fbee4d5a2da416528ebc84a569081ad02e9ad60b0af7d7'

    def __init__(
        self,
        verbose_user: Optional[str] = None,
    ) -> None:
        super().__init__(
            loan_entity_class=NostraLoanEntity,
            verbose_user=verbose_user,
        )
        self.interest_rate_models: Dict[str, InterestRateModel] = {x: InterestRateModel() for x in src.constants.TOKEN_DECIMAL_FACTORS}

    def process_event(self, event: pandas.Series) -> None:
        assert event["block_number"] >= self.last_block_number
        self.last_block_number = event["block_number"]
        if event['from_address'] == self.INTEREST_RATE_MODEL_ADDRESS:
            # TODO: name of the method?
            self.process_interest_rate_model_event(event)
            return
        event_type = self.ADDRESSES_TO_EVENTS[event['from_address']]
        getattr(self, self.EVENTS_METHODS_MAPPING[(event_type, event["key_name"])])(event=event)

    def process_interest_rate_model_event(self, event: pandas.Series) -> None:
        # The order of the values in the `data` column is: `debtToken`, `lendingRate`, ``, `borrowRate`, ``, 
        # `lendIndex`, ``, `borrowIndex`, ``.
        # Example: https://starkscan.co/event/0x05e95588e281d7cab6f89aa266057c4c9bcadf3ff0bb85d4feea40a4faa94b09_4.
        token_address = event["data"][0]
        # The address is not recognized if one forgets to add `0`'s after the `x`, e.g. `0x40...` -> `0x040...`.
        while len(token_address) < 66:
            token_address = token_address[:2] + '0' + token_address[2:]
        token = self.ADDRESSES_TO_TOKENS[token_address]
        collateral_interest_rate_index = decimal.Decimal(str(int(event["data"][5], base=16))) / decimal.Decimal("1e18")
        debt_interest_rate_index = decimal.Decimal(str(int(event["data"][7], base=16))) / decimal.Decimal("1e18")
        self.interest_rate_models[token].collateral_interest_rate_index = collateral_interest_rate_index
        self.interest_rate_models[token].debt_interest_rate_index = debt_interest_rate_index

    def process_non_interest_bearing_collateral_mint_event(self, event: pandas.Series) -> None:
        # The order of the values in the `data` column is: `user`, `amount`, ``.
        # Example: https://starkscan.co/event/0x015dccf7bc9a434bcc678cf730fa92641a2f6bcbfdb61cbe7a1ef7d0a614d1ac_3.
        user = event['data'][0]
        if user == self.IGNORE_USER:
            return
        token = self.ADDRESSES_TO_TOKENS[event['from_address']]
        face_amount = decimal.Decimal(str(int(event['data'][1], base=16)))
        raw_amount = face_amount / self.interest_rate_models[token].collateral_interest_rate_index
        self.loan_entities[user].non_interest_bearing_collateral.increase_value(token=token, amount=raw_amount)
        self.loan_entities[user].collateral.token_amounts = {
            token: (
                self.loan_entities[user].non_interest_bearing_collateral.token_amounts[token]
                + self.loan_entities[user].interest_bearing_collateral.token_amounts[token]
            )
            for token in src.constants.TOKEN_DECIMAL_FACTORS
        }
        if user == self.verbose_user:
            logging.info(
                'In block number = {}, non-interest-bearing collateral of raw amount = {} of token = {} was added.'
                .format(
                    event["block_number"],
                    raw_amount,
                    token,
                )
            )

    def process_non_interest_bearing_collateral_burn_event(self, event: pandas.Series) -> None:
        # The order of the values in the `data` column is: `user`, `amount`, ``.
        # Example: https://starkscan.co/event/0x00744177ee88dd3d96dda1784e2dff50f0c989b7fd48755bc42972af2e951dd6_1.
        user = event['data'][0]
        if user == self.IGNORE_USER:
            return
        token = self.ADDRESSES_TO_TOKENS[event['from_address']]
        face_amount = decimal.Decimal(str(int(event['data'][1], base=16)))
        raw_amount = face_amount / self.interest_rate_models[token].collateral_interest_rate_index
        self.loan_entities[user].non_interest_bearing_collateral.increase_value(token=token, amount=-raw_amount)
        self.loan_entities[user].collateral.token_amounts = {
            token: (
                self.loan_entities[user].non_interest_bearing_collateral.token_amounts[token]
                + self.loan_entities[user].interest_bearing_collateral.token_amounts[token]
            )
            for token in src.constants.TOKEN_DECIMAL_FACTORS
        }
        if user == self.verbose_user:
            logging.info(
                'In block number = {}, non-interest-bearing collateral of raw amount = {} of token = {} was withdrawn.'
                .format(
                    event["block_number"],
                    raw_amount,
                    token,
                )
            )

    def process_interest_bearing_collateral_mint_event(self, event: pandas.Series) -> None:
        # The order of the values in the `data` column is: `user`, `amount`, ``.
        # Example: https://starkscan.co/event/0x07d222d9a70edbe717001ab4305a7a8cfb05116a35da24a9406209dbb07b6d0b_5.
        user = event['data'][0]
        if user == self.IGNORE_USER:
            return
        token = self.ADDRESSES_TO_TOKENS[event['from_address']]
        face_amount = decimal.Decimal(str(int(event['data'][1], base=16)))
        raw_amount = face_amount / self.interest_rate_models[token].collateral_interest_rate_index
        self.loan_entities[user].interest_bearing_collateral.increase_value(token=token, amount=raw_amount)
        self.loan_entities[user].collateral.token_amounts = {
            token: (
                self.loan_entities[user].non_interest_bearing_collateral.token_amounts[token]
                + self.loan_entities[user].interest_bearing_collateral.token_amounts[token]
            )
            for token in src.constants.TOKEN_DECIMAL_FACTORS
        }
        if user == self.verbose_user:
            logging.info(
                'In block number = {}, interest-bearing collateral of raw amount = {} of token = {} was added.'.format(
                    event["block_number"],
                    raw_amount,
                    token,
                )
            )

    def process_interest_bearing_collateral_burn_event(self, event: pandas.Series) -> None:
        # The order of the values in the `data` column is: `user`, `amount`, ``.
        # Example: https://starkscan.co/event/0x0106494005bbab6f01e7779760891eb9ae20e01b905afdb16111f7cf3a28a53e_1.
        user = event['data'][0]
        if user == self.IGNORE_USER:
            return
        token = self.ADDRESSES_TO_TOKENS[event['from_address']]
        face_amount = decimal.Decimal(str(int(event['data'][1], base=16)))
        raw_amount = face_amount / self.interest_rate_models[token].collateral_interest_rate_index
        self.loan_entities[user].interest_bearing_collateral.increase_value(token=token, amount=-raw_amount)
        self.loan_entities[user].collateral.token_amounts = {
            token: (
                self.loan_entities[user].non_interest_bearing_collateral.token_amounts[token]
                + self.loan_entities[user].interest_bearing_collateral.token_amounts[token]
            )
            for token in src.constants.TOKEN_DECIMAL_FACTORS
        }
        if user == self.verbose_user:
            logging.info(
                'In block number = {}, interest-bearing collateral of raw amount = {} of token = {} was withdrawn.'
                .format(
                    event["block_number"],
                    raw_amount,
                    token,
                )
            )
    
    def process_debt_mint_event(self, event: pandas.Series) -> None:
        # The order of the values in the `data` column is: `user`, `amount`, ``.
        # Example: https://starkscan.co/event/0x030d23c4769917bc673875e107ebdea31711e2bdc45e658125dbc2e988945f69_4.
        user = event['data'][0]
        if user == self.IGNORE_USER:
            return
        token = self.ADDRESSES_TO_TOKENS[event['from_address']]
        face_amount = decimal.Decimal(str(int(event['data'][1], base=16)))
        raw_amount = face_amount / self.interest_rate_models[token].debt_interest_rate_index
        self.loan_entities[user].debt.increase_value(token=token, amount=raw_amount)
        if user == self.verbose_user:
            logging.info(
                'In block number = {}, raw amount = {} of token = {} was borrowed.'.format(
                    event["block_number"],
                    raw_amount,
                    token,
                )
            )

    def process_debt_burn_event(self, event: pandas.Series) -> None:
        # The order of the values in the `data` column is: `user`, `amount`, ``.
        # Example: https://starkscan.co/event/0x002e4ee376785f687f32715d8bbed787b6d0fa9775dc9329ca2185155a139ca3_5.
        user = event['data'][0]
        if user == self.IGNORE_USER:
            return
        token = self.ADDRESSES_TO_TOKENS[event['from_address']]
        face_amount = decimal.Decimal(str(int(event['data'][1], base=16)))
        raw_amount = face_amount / self.interest_rate_models[token].debt_interest_rate_index
        self.loan_entities[user].debt.increase_value(token=token, amount=-raw_amount)
        if user == self.verbose_user:
            logging.info(
                'In block number = {}, raw amount = {} of token = {} was repayed.'.format(
                    event["block_number"],
                    raw_amount,
                    token,
                )
            )

    # TODO: This method looks very similar to that of the parent class.
    def compute_liquidable_debt_at_price(
        self,
        prices: Dict[str, decimal.Decimal],
        collateral_token: str,
        collateral_token_price: decimal.Decimal,
        debt_token: str,
    ) -> decimal.Decimal:
        changed_prices = copy.deepcopy(prices)
        changed_prices[collateral_token] = collateral_token_price
        max_liquidated_amount = decimal.Decimal("0")
        for _, loan_entity in self.loan_entities.items():
            # Filter out entities who borrowed the token of interest.
            debt_tokens = {
                token
                for token, token_amount in loan_entity.debt.token_amounts.items()
                if token_amount > decimal.Decimal("0")
            }
            if not debt_token in debt_tokens:
                continue

            # Filter out entities with health factor below 1.
            risk_adjusted_collateral_usd = loan_entity.compute_risk_adjusted_collateral_usd(prices=changed_prices)
            risk_adjusted_debt_usd = loan_entity.compute_risk_adjusted_debt_usd(prices=changed_prices)
            health_factor = loan_entity.compute_health_factor(
                risk_adjusted_collateral_usd=risk_adjusted_collateral_usd,
                risk_adjusted_debt_usd=risk_adjusted_debt_usd,
            )
            if health_factor >= decimal.Decimal("1"):
                continue

            # Find out how much of the `debt_token` will be liquidated.
            collateral_tokens = {
                token
                for token, token_amount in loan_entity.collateral.token_amounts.items()
                if token_amount > decimal.Decimal("0")
            }
            max_liquidated_amount += loan_entity.compute_debt_to_be_liquidated(
                debt_token=debt_token,
                collateral_tokens=collateral_tokens,
                health_factor=health_factor,
                debt_token_debt_amount=loan_entity.debt.token_amounts[debt_token],
                debt_token_price=prices[debt_token],
            )
        return max_liquidated_amount