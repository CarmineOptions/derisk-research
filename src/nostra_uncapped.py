from typing import Dict, Set
import collections
import copy
import decimal
import time

import pandas

import src.constants
import src.db
import src.swap_liquidity



NOSTRA_UNCAPPED_ETH_ADDRESSES = [
    '0x07170f54dd61tae85377f75131359e3f4a12677589bb7ec5d61f362915a5c0982',  # ETH
    '0x044debfe17e4d9a5a1e226dabaf286e72c9cc36abbe71c5b847e669da4503893',  # ETH Collateral
    '0x01fecadfe7cda2487c66291f2970a629be8eecdcb006ba4e71d1428c2b7605c7',  # ETH Interest Bearing
    '0x00ba3037d968790ac486f70acaa9a1cab10cf5843bb85c986624b4d0e5a82e74',  # ETH Debt
    '0x057146f6409deb4c9fa12866915dd952aa07c1eb2752e451d7f3b042086bdeb8',  # ETH Interest Bearing Collateral
]
NOSTRA_UNCAPPED_USDC_ADDRESSES = [
    '0x06eda767a143da12f70947192cd13ee0ccc077829002412570a88cd6539c1d85',  # USDC
    '0x05f296e1b9f4cf1ab452c218e72e02a8713cee98921dad2d3b5706235e128ee4',  # USDC Collateral
    '0x002fc2d4b41cc1f03d185e6681cbd40cced61915d4891517a042658d61cba3b1',  # USDC Interest Bearing
    '0x063d69ae657bd2f40337c39bf35a870ac27ddf91e6623c2f52529db4c1619a51',  # USDC Debt
    '0x05dcd26c25d9d8fd9fc860038dcb6e4d835e524eb8a85213a8cda5b7fff845f6',  # USDC Interest Bearing Collateral
]
NOSTRA_UNCAPPED_USDT_ADDRESSES = [
    '0x06669cb476aa7e6a29c18b59b54f30b8bfcfbb8444f09e7bbb06c10895bf5d7b',  # USDT
    '0x057717edc5b1e56743e8153be626729eb0690b882466ef0cbedc8a28bb4973b1',  # USDT Collateral
    '0x0360f9786a6595137f84f2d6931aaec09ceec476a94a98dcad2bb092c6c06701',  # USDT Interest Bearing
    '0x024e9b0d6bc79e111e6872bb1ada2a874c25712cf08dfc5bcf0de008a7cca55f',  # USDT Debt
    '0x0453c4c996f1047d9370f824d68145bd5e7ce12d00437140ad02181e1d11dc83',  # USDT Interest Bearing Collateral 
]
NOSTRA_UNCAPPED_DAI_ADDRESSES = [
    '0x02b5fd690bb9b126e3517f7abfb9db038e6a69a068303d06cf500c49c1388e20',  # DAI
    '0x005c4676bcb21454659479b3cd0129884d914df9c9b922c1c649696d2e058d70',  # DAI Collateral
    '0x022ccca3a16c9ef0df7d56cbdccd8c4a6f98356dfd11abc61a112483b242db90',  # DAI Interest Bearing
    '0x066037c083c33330a8460a65e4748ceec275bbf5f28aa71b686cbc0010e12597',  # DAI Debt
    '0x04f18ffc850cdfa223a530d7246d3c6fc12a5969e0aa5d4a88f470f5fe6c46e9',  # DAI Interest Bearing Collateral
]
NOSTRA_UNCAPPED_WBTC_ADDRESSES = [
    '0x073132577e25b06937c64787089600886ede6202d085e6340242a5a32902e23e',  # wBTC
    '0x036b68238f3a90639d062669fdec08c4d0bdd09826b1b6d24ef49de6d8141eaa',  # wBTC Collateral
    '0x0735d0f09a4e8bf8a17005fa35061b5957dcaa56889fc75df9e94530ff6991ea',  # wBTC Interest Bearing
    '0x0491480f21299223b9ce770f23a2c383437f9fbf57abc2ac952e9af8cdb12c97',  # wBTC Debt
    '0x05b7d301fa769274f20e89222169c0fad4d846c366440afc160aafadd6f88f0c',  # wBTC Interest Bearing Collateral
]

NOSTRA_UNCAPPED_ADDRESSES = [  # TODO: We can probably ignore these
    '0x07170f54dd61ae85377f75131359e3f4a12677589bb7ec5d61f362915a5c0982',  # ETH
    '0x06eda767a143da12f70947192cd13ee0ccc077829002412570a88cd6539c1d85',  # USDC
    '0x06669cb476aa7e6a29c18b59b54f30b8bfcfbb8444f09e7bbb06c10895bf5d7b',  # USDT
    '0x02b5fd690bb9b126e3517f7abfb9db038e6a69a068303d06cf500c49c1388e20',  # DAI
    '0x073132577e25b06937c64787089600886ede6202d085e6340242a5a32902e23e',  # wBTC
]
NOSTRA_UNCAPPED_INTEREST_BEARING_ADDRESSES = [  # TODO: We can probably ignore these
    '0x01fecadfe7cda2487c66291f2970a629be8eecdcb006ba4e71d1428c2b7605c7',  # ETH Interest Bearing
    '0x002fc2d4b41cc1f03d185e6681cbd40cced61915d4891517a042658d61cba3b1',  # USDC Interest Bearing
    '0x0360f9786a6595137f84f2d6931aaec09ceec476a94a98dcad2bb092c6c06701',  # USDT Interest Bearing
    '0x022ccca3a16c9ef0df7d56cbdccd8c4a6f98356dfd11abc61a112483b242db90',  # DAI Interest Bearing
    '0x0735d0f09a4e8bf8a17005fa35061b5957dcaa56889fc75df9e94530ff6991ea',  # wBTC Interest Bearing
]
NOSTRA_UNCAPPED_COLLATERAL_ADDRESSES = [
    '0x044debfe17e4d9a5a1e226dabaf286e72c9cc36abbe71c5b847e669da4503893',  # ETH Collateral
    '0x05f296e1b9f4cf1ab452c218e72e02a8713cee98921dad2d3b5706235e128ee4',  # USDC Collateral
    '0x057717edc5b1e56743e8153be626729eb0690b882466ef0cbedc8a28bb4973b1',  # USDT Collateral
    '0x005c4676bcb21454659479b3cd0129884d914df9c9b922c1c649696d2e058d70',  # DAI Collateral
    '0x036b68238f3a90639d062669fdec08c4d0bdd09826b1b6d24ef49de6d8141eaa',  # wBTC Collateral
]
NOSTRA_UNCAPPED_INTEREST_BEARING_COLLATERAL_ADDRESSES = [
    '0x05dcd26c25d9d8fd9fc860038dcb6e4d835e524eb8a85213a8cda5b7fff845f6',  # USDC Interest Bearing Collateral
    '0x0453c4c996f1047d9370f824d68145bd5e7ce12d00437140ad02181e1d11dc83',  # USDT Interest Bearing Collateral 
    '0x04f18ffc850cdfa223a530d7246d3c6fc12a5969e0aa5d4a88f470f5fe6c46e9',  # DAI Interest Bearing Collateral
    '0x057146f6409deb4c9fa12866915dd952aa07c1eb2752e451d7f3b042086bdeb8',  # ETH Interest Bearing Collateral
    '0x05b7d301fa769274f20e89222169c0fad4d846c366440afc160aafadd6f88f0c',  # wBTC Interest Bearing Collateral
]
NOSTRA_UNCAPPED_DEBT_ADDRESSES = [
    '0x00ba3037d968790ac486f70acaa9a1cab10cf5843bb85c986624b4d0e5a82e74',  # ETH Debt
    '0x063d69ae657bd2f40337c39bf35a870ac27ddf91e6623c2f52529db4c1619a51',  # USDC Debt
    '0x024e9b0d6bc79e111e6872bb1ada2a874c25712cf08dfc5bcf0de008a7cca55f',  # USDT Debt
    '0x066037c083c33330a8460a65e4748ceec275bbf5f28aa71b686cbc0010e12597',  # DAI Debt
    '0x0491480f21299223b9ce770f23a2c383437f9fbf57abc2ac952e9af8cdb12c97',  # wBTC Debt
]

ALL_RELEVANT_NOSTRA_UNCAPPED_ADDRESSES = (
    NOSTRA_UNCAPPED_COLLATERAL_ADDRESSES
    + NOSTRA_UNCAPPED_INTEREST_BEARING_COLLATERAL_ADDRESSES
    + NOSTRA_UNCAPPED_DEBT_ADDRESSES
)

NOSTRA_UNCAPPED_INTEREST_MODEL_UPDATES_ADDRESS = '0x059a943ca214c10234b9a3b61c558ac20c005127d183b86a99a8f3c60a08b4ff'

NOSTRA_UNCAPPED_DEBT_ADDRESSES_TO_TOKEN = {
    # TODO: remove the first `0`'s  after the `x`, e.g. `0x049...` -> `0x49...`
    '0xba3037d968790ac486f70acaa9a1cab10cf5843bb85c986624b4d0e5a82e74': 'ETH',  # ETH Debt
    '0x63d69ae657bd2f40337c39bf35a870ac27ddf91e6623c2f52529db4c1619a51': 'USDC',  # USDC Debt
    '0x24e9b0d6bc79e111e6872bb1ada2a874c25712cf08dfc5bcf0de008a7cca55f': 'USDT',  # USDT Debt
    '0x66037c083c33330a8460a65e4748ceec275bbf5f28aa71b686cbc0010e12597': 'DAI',  # DAI Debt
    '0x491480f21299223b9ce770f23a2c383437f9fbf57abc2ac952e9af8cdb12c97': 'wBTC',  # wBTC Debt
}


def get_nostra_uncapped_events() -> pandas.DataFrame:
    connection = src.db.establish_connection()
    nostra_uncapped_events = pandas.read_sql(
        sql = f"""
            SELECT
                *
            FROM
                starkscan_events
            WHERE
                (
                    from_address IN {tuple(ALL_RELEVANT_NOSTRA_UNCAPPED_ADDRESSES)}
                AND
                    key_name IN ('Burn', 'Mint')
                )
            OR 
                (
                    from_address = '{NOSTRA_UNCAPPED_INTEREST_MODEL_UPDATES_ADDRESS}'
                AND
                    key_name = 'InterestStateUpdated'
                )
            ORDER BY
                block_number, id ASC;
        """,
        con = connection,
    )
    connection.close()
    nostra_uncapped_events.set_index("id", inplace=True)
    return nostra_uncapped_events


# TODO: create a proper mapping
def get_token(address: str) -> str:
    if address in NOSTRA_UNCAPPED_ETH_ADDRESSES:
        return 'ETH'
    if address in NOSTRA_UNCAPPED_USDC_ADDRESSES:
        return 'USDC'
    if address in NOSTRA_UNCAPPED_USDT_ADDRESSES:
        return 'USDT'
    if address in NOSTRA_UNCAPPED_DAI_ADDRESSES:
        return 'DAI'
    if address in NOSTRA_UNCAPPED_WBTC_ADDRESSES:
        return 'wBTC'


class InterestModelState:
    """
    TODO
    """

    def __init__(self) -> None:
        self.lend_index: decimal.Decimal = decimal.Decimal("1e18")  # Reflects interest rate at which users lend.
        self.borrow_index: decimal.Decimal = decimal.Decimal("1e18")  # Reflects interest rate at which users borrow.

    def interest_model_update(self, lend_index: decimal.Decimal, borrow_index: decimal.Decimal):
        self.lend_index = lend_index / decimal.Decimal("1e18")
        self.borrow_index = borrow_index / decimal.Decimal("1e18")


class UserTokenState:
    """
    TODO
    """

    MAX_ROUNDING_ERRORS = {
        "ETH": decimal.Decimal("0.5") * decimal.Decimal("1e13"),
        "wBTC": decimal.Decimal("1e2"),
        "USDC": decimal.Decimal("1e4"),
        "DAI": decimal.Decimal("1e16"),
        "USDT": decimal.Decimal("1e4"),
        "wstETH": decimal.Decimal("0.5") * decimal.Decimal("1e13"),
    }

    def __init__(self, token: str) -> None:
        self.token: str = token
        self.collateral: decimal.Decimal = decimal.Decimal("0")
        self.interest_bearing_collateral: decimal.Decimal = decimal.Decimal("0")
        self.debt: decimal.Decimal = decimal.Decimal("0")

    def update_collateral(self, raw_amount: decimal.Decimal):
        self.collateral += raw_amount
        if (
            -self.MAX_ROUNDING_ERRORS[self.token]
            < self.collateral
            < self.MAX_ROUNDING_ERRORS[self.token]
        ):
            self.collateral = decimal.Decimal("0")

    def update_interest_bearing_collateral(self, raw_amount: decimal.Decimal):
        self.interest_bearing_collateral += raw_amount
        if (
            -self.MAX_ROUNDING_ERRORS[self.token]
            < self.interest_bearing_collateral
            < self.MAX_ROUNDING_ERRORS[self.token]
        ):
            self.interest_bearing_collateral = decimal.Decimal("0")

    def update_debt(self, raw_amount: decimal.Decimal):
        self.debt += raw_amount
        if (
            -self.MAX_ROUNDING_ERRORS[self.token]
            < self.debt
            < self.MAX_ROUNDING_ERRORS[self.token]
        ):
            self.debt = decimal.Decimal("0")


class UserState:
    """
    TODO
    """

    def __init__(self) -> None:
        self.token_states: Dict[str, UserTokenState] = {
            "ETH": UserTokenState("ETH"),
            "wBTC": UserTokenState("wBTC"),
            "USDC": UserTokenState("USDC"),
            "DAI": UserTokenState("DAI"),
            "USDT": UserTokenState("USDT"),
        }


class State:
    """
    TODO
    """

    USER = "0x16e26f25bc7940de9c75347dab436f733c25e6da6e492a1eb74c218cd7d05ae"

    def __init__(self) -> None:
        self.user_states: collections.defaultdict = collections.defaultdict(UserState)
        self.interest_model_states: Dict[str, InterestModelState] = {
            "ETH": InterestModelState(),
            "wBTC": InterestModelState(),
            "USDC": InterestModelState(),
            "DAI": InterestModelState(),
            "USDT": InterestModelState(),
        }

    def process_event(self, event: pandas.Series) -> None:
        if event['from_address'] == NOSTRA_UNCAPPED_INTEREST_MODEL_UPDATES_ADDRESS:
            self.process_interest_model_update_event(event)

        is_collateral = event['from_address'] in NOSTRA_UNCAPPED_COLLATERAL_ADDRESSES
        is_interest_bearing_collateral = event['from_address'] in NOSTRA_UNCAPPED_INTEREST_BEARING_COLLATERAL_ADDRESSES
        is_debt = event['from_address'] in NOSTRA_UNCAPPED_DEBT_ADDRESSES

        # TODO: do this in a better way?
        if is_collateral:
            self.process_collateral_event(event)
        if is_interest_bearing_collateral:
            self.process_interest_bearing_collateral_event(event)
        if is_debt:
            self.process_debt_event(event)

    def process_interest_model_update_event(self, event: pandas.Series) -> None:
        # The order of the arguments is: `debtToken`, `lendingRate`, `borrowRate`, `lendIndex`, `borrowIndex`.
        token = NOSTRA_UNCAPPED_DEBT_ADDRESSES_TO_TOKEN[event["data"][0]]
        lend_index = decimal.Decimal(str(int(event["data"][5], base=16)))
        borrow_index = decimal.Decimal(str(int(event["data"][7], base=16)))
        self.interest_model_states[token].interest_model_update(
            lend_index=lend_index,
            borrow_index=borrow_index,
        )

    def process_collateral_event(self, event: pandas.Series) -> None:
        # The order of the arguments is: `user`, `amount`.
        name = event["key_name"]
        user = event['data'][0]
        # TODO: This seems to be a magical address. Let's first find out what its purpose is.
        if user == '0x5fc7053cca20fcb38550d7554c84fa6870e2b9e7ebd66398a67697ba440f12b':
            return
        token = get_token(event['from_address'])
        amount = decimal.Decimal(str(int(event['data'][1], base=16)))
        raw_amount = amount / self.interest_model_states[token].lend_index
        if name == 'Mint':  # Collateral deposited.
            self.user_states[user].token_states[token].update_collateral(raw_amount = raw_amount)
        if name == 'Burn':  # Collateral withdrawn.
            self.user_states[user].token_states[token].update_collateral(raw_amount = -raw_amount)
        # TODO
        if user == self.USER:
            print(event['block_number'], "col", name, token, amount)

    def process_interest_bearing_collateral_event(self, event: pandas.Series) -> None:
        # The order of the arguments is: `user`, `amount`.
        name = event["key_name"]
        user = event['data'][0]
        # TODO: This seems to be a magical address. Let's first find out what its purpose is.
        if user == '0x5fc7053cca20fcb38550d7554c84fa6870e2b9e7ebd66398a67697ba440f12b':
            return
        token = get_token(event['from_address'])
        amount = decimal.Decimal(str(int(event['data'][1], base=16)))
        raw_amount = amount / self.interest_model_states[token].lend_index
        if name == 'Mint':  # Collateral deposited.
            self.user_states[user].token_states[token].update_interest_bearing_collateral(raw_amount = raw_amount)
        if name == 'Burn':  # Collateral withdrawn.
            self.user_states[user].token_states[token].update_interest_bearing_collateral(raw_amount = -raw_amount)
        # TODO
        if user == self.USER:
            print(event['block_number'], "ib col", name, token, amount)

    def process_debt_event(self, event: pandas.Series) -> None:
        # The order of the arguments is: `user`, `amount`.
        name = event["key_name"]
        user = event['data'][0]
        token = get_token(event['from_address'])
        amount = decimal.Decimal(str(int(event['data'][1], base=16)))
        raw_amount = amount / self.interest_model_states[token].borrow_index
        if name == 'Mint':  # Debt borrowed.
            self.user_states[user].token_states[token].update_debt(raw_amount = raw_amount)
        if name == 'Burn':  # Debt repayed.
            self.user_states[user].token_states[token].update_debt(raw_amount = -raw_amount)
        # TODO
        if user == self.USER:
            print(event['block_number'], "deb", name, token, amount)


# TODO: find collateral factors
COLLATERAL_FACTORS = {
    'ETH': decimal.Decimal('0.8'),  # https://starkscan.co/call/0x06f619127a63ddb5328807e535e56baa1e244c8923a3b50c123d41dcbed315da_1_1
    'USDC': decimal.Decimal('0.9'),  # https://starkscan.co/call/0x0540d0c76da67ed0e4d6c466c75f14f9b34a7db743b546a3556125a8dbd4b013_1_1
    'USDT': decimal.Decimal('0.9'),  # https://starkscan.co/call/0x020feb60fb3360e9dcbe9ddb8157334d3b95c0758c9df141d6398c72ffd4aa56_1_1
    # TODO: verify via chain call?
    'DAI': decimal.Decimal('0'),  # https://starkscan.co/call/0x057c4cdc434e83d68f4fd004d9cd34cb73f4cc2ca6721b88da488cfbf2d33ec9_1_1
    # TODO: verify via chain call?
    'wBTC': decimal.Decimal('0'),  # https://starkscan.co/call/0x06d02f87f6d5673ea414bebb58dbe24bfbc7abd385b45710b12562f79f0b602c_1_1
}
DEBT_FACTORS = {
    'ETH': decimal.Decimal('0.9'),
    'USDC': decimal.Decimal('0.95'),
    'USDT': decimal.Decimal('0.95'),
    'DAI': decimal.Decimal('0.95'),
    'wBTC': decimal.Decimal('0.8'),
}

LIQUIDATION_HEALTH_FACTOR_THRESHOLD = decimal.Decimal('1')
TARGET_HEALTH_FACTOR = decimal.Decimal('1.25')  # TODO
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

TOKEN_DECIMAL_FACTORS = {
    "ETH": decimal.Decimal('1e18'),
    "wBTC": decimal.Decimal('1e8'),
    "USDC": decimal.Decimal('1e6'),
    "DAI": decimal.Decimal('1e18'),
    "USDT": decimal.Decimal('1e6'),
}


def compute_risk_adjusted_collateral_usd(
    user_state: UserState,
    prices: Dict[str, decimal.Decimal],
) -> decimal.Decimal:
    return sum(
        (token_state.collateral + token_state.interest_bearing_collateral)
        * COLLATERAL_FACTORS[token]
        * prices[token]
        # TODO: perform the conversion using TOKEN_DECIMAL_FACTORS sooner (in `UserTokenState`?)?
        / TOKEN_DECIMAL_FACTORS[token]
        for token, token_state in user_state.token_states.items()
    )


def compute_borrowings_amount_usd(
    user_state: UserState,
    prices: Dict[str, decimal.Decimal],
) -> decimal.Decimal:
    return sum(
        token_state.debt
        * prices[token]
        # TODO: perform the conversion using TOKEN_DECIMAL_FACTORS sooner (in `UserTokenState`?)?
        / TOKEN_DECIMAL_FACTORS[token]
        for token, token_state in user_state.token_states.items()
    )


def compute_risk_adjusted_debt_usd(
    user_state: UserState,
    prices: Dict[str, decimal.Decimal],
) -> decimal.Decimal:
    return sum(
        token_state.debt
        / DEBT_FACTORS[token]
        * prices[token]
        # TODO: perform the conversion using TOKEN_DECIMAL_FACTORS sooner (in `UserTokenState`?)?
        / TOKEN_DECIMAL_FACTORS[token]
        for token, token_state in user_state.token_states.items()
    )


def compute_health_factor(
    risk_adjusted_collateral_usd: decimal.Decimal,
    risk_adjusted_debt_usd: decimal.Decimal,
) -> decimal.Decimal:
    if risk_adjusted_debt_usd == decimal.Decimal("0"):
        # TODO: assumes collateral is positive
        return decimal.Decimal("Inf")

    health_factor = risk_adjusted_collateral_usd / risk_adjusted_debt_usd
    # TODO: enable?
    #     if health_factor < decimal.Decimal('0.9'):
    #         print(f'Suspiciously low health factor = {health_factor} of user = {user}, investigate.')
    # TODO: too many loans eligible for liquidation?
    #     elif health_factor < decimal.Decimal('1'):
    #         print(f'Health factor = {health_factor} of user = {user} eligible for liquidation.')
    return health_factor


# TODO: compute_health_factor, etc. should be methods of class UserState
def compute_debt_to_be_liquidated(
    debt_token: str,
    collateral_tokens: Set[str],
    health_factor: decimal.Decimal,
    debt_token_debt_amount: decimal.Decimal,
    debt_token_price: decimal.Decimal,
) -> decimal.Decimal:
    liquidator_fee_usd = decimal.Decimal('0')
    liquidation_amount_usd = decimal.Decimal('0')
    for collateral_token in collateral_tokens:
        # TODO: commit the derivation of the formula in a document?
        # See an example of a liquidation here: https://docs.nostra.finance/lend/liquidations/an-example-of-liquidation.
        liquidator_fee = min(
            LIQUIDATOR_FEE_BETAS[collateral_token] * (LIQUIDATION_HEALTH_FACTOR_THRESHOLD - health_factor),
            LIQUIDATOR_FEE_MAXS[collateral_token],
        )
        total_fee = liquidator_fee + PROTOCOL_FEES[collateral_token]
        max_liquidation_percentage = (
            TARGET_HEALTH_FACTOR - health_factor
        ) / (
            TARGET_HEALTH_FACTOR - COLLATERAL_FACTORS[collateral_token] * DEBT_FACTORS[debt_token] * (decimal.Decimal('1') + total_fee)
        )
        max_liquidation_percentage = min(max_liquidation_percentage, decimal.Decimal('1'))
        max_liquidation_amount = max_liquidation_percentage * debt_token_debt_amount
        max_liquidation_amount_usd = max_liquidation_amount * debt_token_price / TOKEN_DECIMAL_FACTORS[debt_token]
        max_liquidator_fee_usd = liquidator_fee * max_liquidation_amount_usd
        if max_liquidator_fee_usd > liquidator_fee_usd:
            liquidator_fee_usd = max_liquidator_fee_usd
            liquidation_amount_usd = max_liquidation_amount_usd
    return liquidation_amount_usd


def compute_max_liquidated_amount(
    state: State,
    prices: Dict[str, decimal.Decimal],
    debt_token: str,
) -> decimal.Decimal:
    liquidated_debt_amount = decimal.Decimal("0")
    for user, user_state in state.user_states.items():
        # TODO: do this?
        # Filter out users who borrowed the token of interest.
        debt_tokens = {
            token_state.token
            for token_state in user_state.token_states.values()
            if token_state.debt > decimal.Decimal("0")
        }
        if not debt_token in debt_tokens:
            continue

        # Filter out users with health below 1.
        risk_adjusted_collateral_usd = compute_risk_adjusted_collateral_usd(
            user_state=user_state,
            prices=prices,
        )
        risk_adjusted_debt_usd = compute_risk_adjusted_debt_usd(
            user_state=user_state,
            prices=prices,
        )
        health_factor = compute_health_factor(
            risk_adjusted_collateral_usd=risk_adjusted_collateral_usd,
            risk_adjusted_debt_usd=risk_adjusted_debt_usd,
        )
        if health_factor >= decimal.Decimal('1'):
            continue

        # TODO: find out how much of the debt_token will be liquidated
        collateral_tokens = {
            token_state.token
            for token_state in user_state.token_states.values()
            if token_state.collateral
            != decimal.Decimal("0")
            or token_state.interest_bearing_collateral
            != decimal.Decimal("0")
        }
        liquidated_debt_amount += compute_debt_to_be_liquidated(
            debt_token=debt_token,
            collateral_tokens=collateral_tokens,
            health_factor=health_factor,
            debt_token_debt_amount=user_state.token_states[debt_token].debt,
            debt_token_price=prices[debt_token],
        )
    return liquidated_debt_amount


def simulate_liquidations_under_absolute_price_change(
    prices: src.swap_liquidity.Prices,
    collateral_token: str,
    collateral_token_price: decimal.Decimal,
    state: State,
    debt_token: str,
) -> decimal.Decimal:
    changed_prices = copy.deepcopy(prices.prices)
    changed_prices[collateral_token] = collateral_token_price
    return compute_max_liquidated_amount(
        state=state, prices=changed_prices, debt_token=debt_token
    )


def get_range(start, stop, step):
    return [
        x
        for x in src.zklend.decimal_range(
            # TODO: make it dependent on the collateral token .. use prices.prices[COLLATERAL_TOKEN]
            start=decimal.Decimal(start),
            stop=decimal.Decimal(stop),
            # TODO: make it dependent on the collateral token
            step=decimal.Decimal(step),
        )
    ]


# TODO: move this somewhere
def get_pair_range(c, b):
    if c == "ETH" and b == "wBTC":
        return get_range("0", "0.2", "0.0015")
    if c == "wBTC" and b == "ETH":
        return get_range("0", "25", "0.375")
    if c == "ETH":
        return get_range("50", "2500", "50")
    if c == "wBTC":
        return get_range("250", "32000", "250")
    raise ValueError(f"Wrong pair {c}-{b}")


def generate_graph_data(state, prices, swap_amm, collateral_token, borrowings_token):
    data = pandas.DataFrame(
        {"collateral_token_price": get_pair_range(collateral_token, borrowings_token)},
    )
    data["max_borrowings_to_be_liquidated"] = data["collateral_token_price"].apply(
        lambda x: simulate_liquidations_under_absolute_price_change(
            prices=prices,
            collateral_token=collateral_token,
            collateral_token_price=x,
            state=state,
            debt_token=borrowings_token,
        )
    )
    data["max_borrowings_to_be_liquidated_at_interval"] = (
        data["max_borrowings_to_be_liquidated"].diff().abs()
    )
    # TODO: drops also other NaN, if there are any
    data.dropna(inplace=True)

    data["amm_borrowings_token_supply"] = data["collateral_token_price"].apply(
        lambda x: src.zklend.get_amm_supply_at_price(
            collateral_token=collateral_token,
            collateral_token_price=x,
            borrowings_token=borrowings_token,
            amm=swap_amm,
        )
    )
    return data


def generate_and_store_graph_data(state, prices, swap_amm, pair):
    t0 = time.time()
    print("nostra_uncapped: generating graph for", pair, flush=True)
    c, b = pair.split("-")
    data = generate_graph_data(state, prices, swap_amm, c, b)
    filename = f"nostra_uncapped_data/{c}-{b}.csv"
    data.to_csv(filename, index=False, compression='gzip')
    print("nostra_uncapped: ", filename, "done in", time.time() - t0, flush=True)


def load_data():
    data = {}
    for pair in src.constants.PAIRS:
        data[pair] = pandas.read_csv(f"nostra_uncapped_data/{pair}.csv", compression="gzip")
    histogram_data = pandas.read_csv("nostra_uncapped_data/histogram.csv", compression="gzip")
    loans = pandas.read_csv("nostra_uncapped_data/loans.csv", compression="gzip")
    return (
        data,
        histogram_data,
        loans,
    )


def compute_number_of_users(
    state: State,
) -> int:
    return sum(
        any(
            (token_state.collateral + token_state.interest_bearing_collateral) > decimal.Decimal('0')
            or token_state.debt > decimal.Decimal('0')
            for token_state in user_state.token_states.values()
        )
        for user_state in state.user_states.values()
    )


def compute_number_of_stakers(
    state: State,
) -> int:
    return sum(
        any((token_state.collateral + token_state.interest_bearing_collateral) > decimal.Decimal('0') for token_state in user_state.token_states.values())
        for user_state in state.user_states.values()
    )


def compute_number_of_borrowers(
    state: State,
) -> int:
    return sum(
        any(token_state.debt > decimal.Decimal('0') for token_state in user_state.token_states.values())
        for user_state in state.user_states.values()
    )


def compute_standardized_health_factor(
    risk_adjusted_collateral_usd: decimal.Decimal,
    borrowings_usd: decimal.Decimal,
) -> decimal.Decimal:
    # Compute the value of collateral at which the user/loan can be liquidated.
    collateral_usd_threshold = borrowings_usd
    if collateral_usd_threshold == decimal.Decimal("0"):
        # TODO: assumes collateral is positive
        return decimal.Decimal("Inf")
    return risk_adjusted_collateral_usd / collateral_usd_threshold
