from typing import Dict, Set
import collections
import copy
import decimal
import time

import pandas

import src.db
import src.swap_liquidity


# TODO
NOSTRA_ETH_ADDRESSES = [
    '0x04f89253e37ca0ab7190b2e9565808f105585c9cacca6b2fa6145553fa061a41',  # ETH
    '0x0553cea5d1dc0e0157ffcd36a51a0ced717efdadd5ef1b4644352bb45bd35453',  # ETH Collateral
    '0x002f8deaebb9da2cb53771b9e2c6d67265d11a4e745ebd74a726b8859c9337b9',  # ETH Interest Bearing
    '0x040b091cb020d91f4a4b34396946b4d4e2a450dbd9410432ebdbfe10e55ee5e5',  # ETH Debt
    '0x070f8a4fcd75190661ca09a7300b7c93fab93971b67ea712c664d7948a8a54c6',  # ETH Interest Bearing Collateral
]
NOSTRA_USDC_ADDRESSES = [
    '0x05327df4c669cb9be5c1e2cf79e121edef43c1416fac884559cd94fcb7e6e232',  # USDC
    '0x047e794d7c49c49fd2104a724cfa69a92c5a4b50a5753163802617394e973833',  # USDC Collateral
    '0x06af9a313434c0987f5952277f1ac8c61dc4d50b8b009539891ed8aaee5d041d',  # USDC Interest Bearing
    '0x03b6058a9f6029b519bc72b2cc31bcb93ca704d0ab79fec2ae5d43f79ac07f7a',  # USDC Debt
    '0x029959a546dda754dc823a7b8aa65862c5825faeaaf7938741d8ca6bfdc69e4e',  # USDC Interest Bearing Collateral
]
NOSTRA_USDT_ADDRESSES = [
    '0x040375d0720245bc0d123aa35dc1c93d14a78f64456eff75f63757d99a0e6a83',  # USDT
    '0x003cd2066f3c8b4677741b39db13acebba843bbbaa73d657412102ab4fd98601',  # USDT Collateral
    '0x06404c8e886fea27590710bb0e0e8c7a3e7d74afccc60663beb82707495f8609',  # USDT Interest Bearing
    '0x065c6c7119b738247583286021ea05acc6417aa86d391dcdda21843c1fc6e9c6',  # USDT Debt
    '0x055ba2baf189b98c59f6951a584a3a7d7d6ff2c4ef88639794e739557e1876f0',  # USDT Interest Bearing Collateral 
]
NOSTRA_DAI_ADDRESSES = [
    '0x02ea39ba7a05f0c936b7468d8bc8d0e1f2116916064e7e163e7c1044d95bd135',  # DAI
    '0x04403e420521e7a4ca0dc5192af81ca0bb36de343564a9495e11c8d9ba6e9d17',  # DAI Collateral
    '0x00b9b1a4373de5b1458e598df53195ea3204aa926f46198b50b32ed843ce508b',  # DAI Interest Bearing
    '0x0362b4455f5f4cc108a5a1ab1fd2cc6c4f0c70597abb541a99cf2734435ec9cb',  # DAI Debt
    '0x01ac55cabf2b79cf39b17ba0b43540a64205781c4b7850e881014aea6f89be58',  # DAI Interest Bearing Collateral
]
NOSTRA_WBTC_ADDRESSES = [
    '0x07788bc687f203b6451f2a82e842b27f39c7cae697dace12edfb86c9b1c12f3d',  # wBTC
    '0x06b59e2a746e141f90ec8b6e88e695265567ab3bdcf27059b4a15c89b0b7bd53',  # wBTC Collateral
    '0x0061d892cccf43daf73407194da9f0ea6dbece950bb24c50be2356444313a707',  # wBTC Interest Bearing
    '0x075b0d87aca8dee25df35cdc39a82b406168fa23a76fc3f03abbfdc6620bb6d7',  # wBTC Debt
    '0x00687b5d9e591844169bc6ad7d7256c4867a10cee6599625b9d78ea17a7caef9',  # wBTC Interest Bearing Collateral
]

NOSTRA_COLLATERAL_ADDRESSES = [
    '0x0553cea5d1dc0e0157ffcd36a51a0ced717efdadd5ef1b4644352bb45bd35453',  # ETH Collateral
    '0x047e794d7c49c49fd2104a724cfa69a92c5a4b50a5753163802617394e973833',  # USDC Collateral
    '0x003cd2066f3c8b4677741b39db13acebba843bbbaa73d657412102ab4fd98601',  # USDT Collateral
    '0x04403e420521e7a4ca0dc5192af81ca0bb36de343564a9495e11c8d9ba6e9d17',  # DAI Collateral
    '0x06b59e2a746e141f90ec8b6e88e695265567ab3bdcf27059b4a15c89b0b7bd53',  # wBTC Collateral
]
NOSTRA_INTEREST_BEARING_COLLATERAL_ADDRESSES = [
    '0x070f8a4fcd75190661ca09a7300b7c93fab93971b67ea712c664d7948a8a54c6',  # ETH Interest Bearing Collateral
    '0x029959a546dda754dc823a7b8aa65862c5825faeaaf7938741d8ca6bfdc69e4e',  # USDC Interest Bearing Collateral
    '0x055ba2baf189b98c59f6951a584a3a7d7d6ff2c4ef88639794e739557e1876f0',  # USDT Interest Bearing Collateral 
    '0x01ac55cabf2b79cf39b17ba0b43540a64205781c4b7850e881014aea6f89be58',  # DAI Interest Bearing Collateral
    '0x00687b5d9e591844169bc6ad7d7256c4867a10cee6599625b9d78ea17a7caef9',  # wBTC Interest Bearing Collateral
]
NOSTRA_DEBT_ADDRESSES = [
    '0x040b091cb020d91f4a4b34396946b4d4e2a450dbd9410432ebdbfe10e55ee5e5',  # ETH Debt
    '0x03b6058a9f6029b519bc72b2cc31bcb93ca704d0ab79fec2ae5d43f79ac07f7a',  # USDC Debt
    '0x065c6c7119b738247583286021ea05acc6417aa86d391dcdda21843c1fc6e9c6',  # USDT Debt
    '0x0362b4455f5f4cc108a5a1ab1fd2cc6c4f0c70597abb541a99cf2734435ec9cb',  # DAI Debt
    '0x075b0d87aca8dee25df35cdc39a82b406168fa23a76fc3f03abbfdc6620bb6d7',  # wBTC Debt
]

ALL_RELEVANT_NOSTRA_ADDRESSES = NOSTRA_COLLATERAL_ADDRESSES + NOSTRA_INTEREST_BEARING_COLLATERAL_ADDRESSES + NOSTRA_DEBT_ADDRESSES


def get_nostra_events() -> pandas.DataFrame:
    connection = src.db.establish_connection()
    nostra_events = pandas.read_sql(
        sql = f"""
            SELECT
                *
            FROM
                starkscan_events
            WHERE
                from_address IN {tuple(ALL_RELEVANT_NOSTRA_ADDRESSES)}
            AND
                key_name IN ('Burn', 'Mint')
            ORDER BY
                block_number, id ASC;
        """,
        con = connection,
    )
    connection.close()
    nostra_events.set_index("id", inplace=True)
    return nostra_events


# TODO: create a proper mapping
def get_token(address: str) -> str:
    if address in NOSTRA_ETH_ADDRESSES:
        return 'ETH'
    if address in NOSTRA_USDC_ADDRESSES:
        return 'USDC'
    if address in NOSTRA_USDT_ADDRESSES:
        return 'USDT'
    if address in NOSTRA_DAI_ADDRESSES:
        return 'DAI'
    if address in NOSTRA_WBTC_ADDRESSES:
        return 'wBTC'


class UserTokenState:
    """
    TODO
    """

    def __init__(self, token: str) -> None:
        self.token: str = token
        self.collateral: decimal.Decimal = decimal.Decimal("0")
        self.interest_bearing_collateral: decimal.Decimal = decimal.Decimal("0")
        self.debt: decimal.Decimal = decimal.Decimal("0")


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

    USER = "0x5a0042fa9bb87ed72fbee4d5a2da416528ebc84a569081ad02e9ad60b0af7d7"

    def __init__(self) -> None:
        self.user_states: collections.defaultdict = collections.defaultdict(UserState)

    def process_event(self, event: pandas.Series) -> None:
        is_collateral = event['from_address'] in NOSTRA_COLLATERAL_ADDRESSES
        is_interest_bearing_collateral = event['from_address'] in NOSTRA_INTEREST_BEARING_COLLATERAL_ADDRESSES
        is_debt = event['from_address'] in NOSTRA_DEBT_ADDRESSES

        # TODO: do this in a better way?
        if is_collateral:
            self.process_collateral_event(event)
        if is_interest_bearing_collateral:
            self.process_interest_bearing_collateral_event(event)
        if is_debt:
            self.process_debt_event(event)

    def process_collateral_event(self, event: pandas.Series) -> None:
        # The order of the arguments is: `user`, `amount`.
        name = event["key_name"]
        user = event['data'][0]
        # TODO: This seems to be a magical address. Let's first find out what its purpose is.
        if user == '0x5a0042fa9bb87ed72fbee4d5a2da416528ebc84a569081ad02e9ad60b0af7d7':
            return
        token = get_token(event['from_address'])
        amount = decimal.Decimal(str(int(event['data'][1], base=16)))
        if name == 'Mint':
            self.user_states[user].token_states[token].collateral += amount
        if name == 'Burn':
            self.user_states[user].token_states[token].collateral -= amount
        # TODO
        if user == self.USER:
            print(event['block_number'], "col", token, amount)

    def process_interest_bearing_collateral_event(self, event: pandas.Series) -> None:
        # The order of the arguments is: `user`, `amount`.
        name = event["key_name"]
        user = event['data'][0]
        # TODO: This seems to be a magical address. Let's first find out what its purpose is.
        if user == '0x5a0042fa9bb87ed72fbee4d5a2da416528ebc84a569081ad02e9ad60b0af7d7':
            return
        token = get_token(event['from_address'])
        amount = decimal.Decimal(str(int(event['data'][1], base=16)))
        if name == 'Mint':
            self.user_states[user].token_states[token].interest_bearing_collateral += amount
        if name == 'Burn':
            self.user_states[user].token_states[token].interest_bearing_collateral -= amount
        # TODO
        if user == self.USER:
            print(event['block_number'], "ib col", token, amount)

    def process_debt_event(self, event: pandas.Series) -> None:
        # The order of the arguments is: `user`, `amount`.
        name = event["key_name"]
        user = event['data'][0]
        token = get_token(event['from_address'])
        amount = decimal.Decimal(str(int(event['data'][1], base=16)))
        if name == 'Mint':
            self.user_states[user].token_states[token].debt += amount
        if name == 'Burn':
            self.user_states[user].token_states[token].debt -= amount
        # TODO
        if user == self.USER:
            print(event['block_number'], "deb", token, amount)


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


# Source: Starkscan, e.g. 
# https://starkscan.co/token/0x049d36570d4e46f48e99674bd3fcc84644ddd6b96f7c741b1562b82f9e004dc7 for ETH.
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


# Source: Starkscan, e.g.
# https://starkscan.co/token/0x049d36570d4e46f48e99674bd3fcc84644ddd6b96f7c741b1562b82f9e004dc7 for ETH.
TOKEN_DECIMAL_FACTORS = {
    "ETH": decimal.Decimal("1e18"),
    "wBTC": decimal.Decimal("1e8"),
    "USDC": decimal.Decimal("1e6"),
    "DAI": decimal.Decimal("1e18"),
    "USDT": decimal.Decimal("1e6"),
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
    borrowings_token: str,
) -> decimal.Decimal:
    changed_prices = copy.deepcopy(prices.prices)
    changed_prices[collateral_token] = collateral_token_price
    return compute_max_liquidated_amount(
        state=state, prices=changed_prices, debt_token=borrowings_token
    )


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
            borrowings_token=borrowings_token,
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
    print("nostra: generating graph for", pair, flush=True)
    c = pair[0]
    b = pair[1]
    data = generate_graph_data(state, prices, swap_amm, c, b)
    filename = f"nostra_data/{c}-{b}.csv"
    data.to_csv(filename, index=False)
    print("nostra: ", filename, "done in", time.time() - t0, flush=True)


PAIRS = [
    "ETH-USDC",
    "ETH-USDT",
    "ETH-DAI",
    "wBTC-USDC",
    "wBTC-USDT",
    "wBTC-DAI",
    # "ETH-wBTC",
    # "wBTC-ETH",
]


def load_data():
    data = {}
    for pair in PAIRS:
        data[pair] = pandas.read_csv(f"nostra_data/{pair}.csv")
    histogram_data = pandas.read_csv("nostra_data/histogram.csv")
    small_loans_sample = pandas.read_csv("nostra_data/small_loans_sample.csv")
    large_loans_sample = pandas.read_csv("nostra_data/large_loans_sample.csv")
    return (
        data,
        histogram_data,
        small_loans_sample,
        large_loans_sample,
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
