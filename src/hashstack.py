import time
from typing import Dict
import collections
import copy
import decimal

import pandas
import streamlit

import src.constants as constants
import src.classes as classes
import src.compute as compute
import src.db as db


def get_hashstack_events() -> pandas.DataFrame:
    connection = db.establish_connection()
    hashstack_events = pandas.read_sql(
        sql=f"""
        SELECT
            *
        FROM
            starkscan_events
        WHERE
            from_address='{constants.Protocol.HASHSTACK.value}'
        AND
            key_name IN ('new_loan', 'loan_withdrawal', 'loan_repaid', 'loan_swap', 'collateral_added', 'collateral_withdrawal', 'loan_interest_deducted', 'liquidated')
        ORDER BY
            block_number, id ASC;
        """,
        con=connection,
    )
    connection.close()
    hashstack_events.set_index("id", inplace=True)
    # TODO: ensure we're processing loan_repaid after all other loan-altering events + other events in "logical" order
    hashstack_events["order"] = hashstack_events["key_name"].map(
        {
            "new_loan": 0,
            "loan_withdrawal": 3,
            "loan_repaid": 4,
            "loan_swap": 1,
            "collateral_added": 6,
            "collateral_withdrawal": 7,
            "loan_interest_deducted": 5,
            "liquidated": 2,
        },
    )
    hashstack_events.sort_values(
        ["block_number", "transaction_hash", "order"], inplace=True
    )
    return hashstack_events


class HashStackBorrowings:
    """
    TODO
    """

    def __init__(
        self,
        borrowings_id: int,
        market: str,
        amount: decimal.Decimal,
        current_market: str,
        current_amount: decimal.Decimal,
        debt_category: int,
    ) -> None:
        self.id: int = borrowings_id
        self.market: str = market
        self.amount: decimal.Decimal = amount
        self.current_market: str = current_market
        self.current_amount: decimal.Decimal = current_amount
        self.debt_category: int = debt_category


class HashStackCollateral:
    """
    TODO
    """

    def __init__(
        self,
        market: str,
        amount: decimal.Decimal,
        current_amount: decimal.Decimal,
    ) -> None:
        self.market: str = market
        self.amount: decimal.Decimal = amount
        self.current_amount: decimal.Decimal = current_amount


class HashStackLoan:
    """
    TODO
    """

    def __init__(
        self,
        borrowings: HashStackBorrowings,
        collateral: HashStackCollateral,
    ) -> None:
        self.borrowings: HashStackBorrowings = borrowings
        self.collateral: HashStackCollateral = collateral


class UserState:
    """
    TODO
    """

    def __init__(self) -> None:
        self.loans: Dict[int, HashStackLoan] = {}


class State:
    """
    TODO
    """

    # TODO: f'process_{name.lower()}_event'?
    EVENTS_FUNCTIONS_MAPPING: Dict[str, str] = {
        "new_loan": "process_new_loan_event",
        # TODO: this event shows what the user does with the loan, but it shouldn't change the amount borrowed, so let's ignore it for now
        #         "loan_withdrawal": "process_loan_withdrawal_event",
        "loan_repaid": "process_loan_repaid_event",
        "loan_swap": "process_loan_swap_event",
        "collateral_added": "process_collateral_added_event",
        "collateral_withdrawal": "process_collateral_withdrawal_event",
        "loan_interest_deducted": "process_loan_interest_deducted_event",
        "liquidated": "process_liquidated_event",
    }

    def __init__(self) -> None:
        # TODO: how to compute the interest accrued on both collateral and loan?
        self.user_loan_ids_mapping: collections.defaultdict = collections.defaultdict(
            list
        )
        self.user_states: collections.defaultdict = collections.defaultdict(UserState)

    def process_event(self, event: pandas.Series) -> None:
        # TODO: filter events in the query
        if not event["key_name"] in self.EVENTS_FUNCTIONS_MAPPING:
            return
        getattr(self, self.EVENTS_FUNCTIONS_MAPPING[event["key_name"]])(event=event)

    def process_new_loan_event(self, event: pandas.Series) -> None:
        # The order of the arguments is: `id`, `owner`, `market`, `commitment`, `amount`, `current_market`,
        # `current_amount`, `is_loan_withdrawn`, `debt_category`, `state`, `l3_integration`, `created_at`,
        # `market`, `amount`, `current_amount`, `commitment`, `timelock_validity`, `is_timelock_activated`,
        # `activation_time`, `timestamp`.
        loan_id = int(event["data"][0], base=16)
        user = event["data"][1]
        self.user_loan_ids_mapping[user].append(loan_id)
        # TODO: universal naming: use deposit, collateral and debt (instead of loan/borrowings)?
        borrowings_token = constants.get_symbol(event["data"][2])
        borrowings_amount = decimal.Decimal(str(int(event["data"][4], base=16)))
        borrowings_current_token = constants.get_symbol(event["data"][6])
        borrowings_current_amount = decimal.Decimal(str(int(event["data"][7], base=16)))
        debt_category = int(event["data"][10], base=16)
        # TODO: first ~3 loans seem to have different structure of 'data'
        try:
            collateral_token = constants.get_symbol(event["data"][14])
            collateral_amount = decimal.Decimal(str(int(event["data"][15], base=16)))
            collateral_current_amount = decimal.Decimal(
                str(int(event["data"][17], base=16))
            )
        except KeyError:
            collateral_token = constants.get_symbol(event["data"][13])
            collateral_amount = decimal.Decimal(str(int(event["data"][14], base=16)))
            collateral_current_amount = decimal.Decimal(
                str(int(event["data"][16], base=16))
            )
        self.user_states[user].loans[loan_id] = HashStackLoan(
            borrowings=HashStackBorrowings(
                borrowings_id=loan_id,
                market=borrowings_token,
                amount=borrowings_amount,
                current_market=borrowings_current_token,
                current_amount=borrowings_current_amount,
                debt_category=debt_category,
            ),
            collateral=HashStackCollateral(
                market=collateral_token,
                amount=collateral_amount,
                current_amount=collateral_current_amount,
            ),
        )

    def process_loan_repaid_event(self, event: pandas.Series) -> None:
        # The order of the arguments is: `id`, `owner`, `market`, `commitment`, `amount`, `current_market`,
        # `current_amount`, `is_loan_withdrawn`, `debt_category`, `state`, `l3_integration`, `created_at`,
        # `timestamp`.
        loan_id = int(event["data"][0], base=16)
        user = event["data"][1]
        token = constants.get_symbol(event["data"][2])
        amount = decimal.Decimal(str(int(event["data"][4], base=16)))
        current_token = constants.get_symbol(event["data"][6])
        current_amount = decimal.Decimal(str(int(event["data"][7], base=16)))
        # TODO: from the docs it seems that it's only possible to repay the whole amount
        assert current_amount == decimal.Decimal("0")
        debt_category = int(event["data"][10], base=16)
        self.user_states[user].loans[loan_id].borrowings = HashStackBorrowings(
            borrowings_id=loan_id,
            market=token,
            amount=amount,
            current_market=current_token,
            current_amount=current_amount,
            debt_category=debt_category,
        )

    def process_loan_swap_event(self, event: pandas.Series) -> None:
        # The order of the arguments is: `id`, `owner`, `market`, `commitment`, `amount`, `current_market`,
        # `current_amount`, `is_loan_withdrawn`, `debt_category`, `state`, `l3_integration`, `created_at`,
        # `id`, `owner`, `market`, `commitment`, `amount`, `current_market`, `current_amount`,
        # `is_loan_withdrawn`, `debt_category`, `state`, `l3_integration`, `created_at`, `timestamp`.
        old_loan_id = int(event["data"][0], base=16)
        old_user = event["data"][1]
        assert old_loan_id in self.user_loan_ids_mapping[old_user]
        new_loan_id = int(event["data"][14], base=16)
        new_user = event["data"][15]
        assert old_loan_id == new_loan_id
        # TODO: this doesn't always have to hold, right?
        assert old_user == new_user
        # TODO: universal naming: use deposit, collateral and debt (instead of loan/borrowings)?
        new_token = constants.get_symbol(event["data"][16])
        new_amount = decimal.Decimal(str(int(event["data"][18], base=16)))
        assert (
            self.user_states[old_user].loans[old_loan_id].borrowings.market == new_token
        )
        assert (
            self.user_states[old_user].loans[old_loan_id].borrowings.amount
            == new_amount
        )
        new_current_token = constants.get_symbol(event["data"][20])
        new_current_amount = decimal.Decimal(str(int(event["data"][21], base=16)))
        old_debt_category = int(event["data"][10], base=16)
        new_debt_category = int(event["data"][24], base=16)
        # TODO: this need to hold, right?
        assert old_debt_category == new_debt_category
        # TODO: from the docs it seems that it's only possible to swap the whole balance
        self.user_states[new_user].loans[new_loan_id].borrowings = HashStackBorrowings(
            borrowings_id=new_loan_id,
            market=new_token,
            amount=new_amount,
            current_market=new_current_token,
            current_amount=new_current_amount,
            debt_category=new_debt_category,
        )

    def process_collateral_added_event(self, event: pandas.Series) -> None:
        # The order of the arguments is: `market`, `amount`, `current_amount`, `commitment`,
        # `timelock_validity`, `is_timelock_activated`, `activation_time`, `loan_id`, `amount_added`,
        # `timestamp`.
        loan_id = int(event["data"][9], base=16)
        # TODO: create method self.find_user?
        users = [
            user
            for user, loan_ids in self.user_loan_ids_mapping.items()
            if loan_id in loan_ids
        ]
        assert len(users) == 1
        user = users[0]
        # TODO: universal naming: use deposit, collateral and debt (instead of loan/borrowings)?
        token = constants.get_symbol(event["data"][0])
        amount = decimal.Decimal(str(int(event["data"][1], base=16)))  # TODO: needed?
        current_amount = decimal.Decimal(str(int(event["data"][3], base=16)))
        # TODO: utilize `amount_added`?
        self.user_states[user].loans[loan_id].collateral = HashStackCollateral(
            market=token,
            amount=amount,
            current_amount=current_amount,
        )

    def process_collateral_withdrawal_event(self, event: pandas.Series) -> None:
        # The order of the arguments is: `market`, `amount`, `current_amount`, `commitment`,
        # `timelock_validity`, `is_timelock_activated`, `activation_time`, `loan_id`, `amount_withdrawn`,
        # `timestamp`.
        loan_id = int(event["data"][9], base=16)
        # TODO: create method self.find_user?
        users = [
            user
            for user, loan_ids in self.user_loan_ids_mapping.items()
            if loan_id in loan_ids
        ]
        assert len(users) == 1
        user = users[0]
        # TODO: universal naming: use deposit, collateral and debt (instead of loan/borrowings)?
        token = constants.get_symbol(event["data"][0])
        amount = decimal.Decimal(str(int(event["data"][1], base=16)))  # TODO: needed?
        current_amount = decimal.Decimal(str(int(event["data"][3], base=16)))
        # TODO: utilize `amount_withdrawn`?
        self.user_states[user].loans[loan_id].collateral = HashStackCollateral(
            market=token,
            amount=amount,
            current_amount=current_amount,
        )

    def process_loan_interest_deducted_event(self, event: pandas.Series) -> None:
        # The order of the arguments is: `market`, `amount`, `current_amount`, `commitment`,
        # `timelock_validity`, `is_timelock_activated`, `activation_time`, `accrued_interest`, `loan_id`,
        # `timestamp`.
        loan_id = int(event["data"][11], base=16)
        # TODO: create method self.find_user?
        users = [
            user
            for user, loan_ids in self.user_loan_ids_mapping.items()
            if loan_id in loan_ids
        ]
        assert len(users) == 1
        user = users[0]
        # TODO: universal naming: use deposit, collateral and debt (instead of loan/borrowings)?
        token = constants.get_symbol(event["data"][0])
        amount = decimal.Decimal(str(int(event["data"][1], base=16)))  # TODO: needed?
        current_amount = decimal.Decimal(str(int(event["data"][3], base=16)))
        # TODO: utilize `amount_withdrawn`?
        self.user_states[user].loans[loan_id].collateral = HashStackCollateral(
            market=token,
            amount=amount,
            current_amount=current_amount,
        )

    def process_liquidated_event(self, event: pandas.Series) -> None:
        # The order of the arguments is: `id`, `owner`, `market`, `commitment`, `amount`, `current_market`,
        # `current_amount`, `is_loan_withdrawn`, `debt_category`, `state`, `l3_integration`, `created_at`,
        # `liquidator`, `timestamp`.
        loan_id = int(event["data"][0], base=16)
        user = event["data"][1]
        token = constants.get_symbol(event["data"][2])
        amount = decimal.Decimal(str(int(event["data"][4], base=16)))
        current_token = constants.get_symbol(event["data"][6])
        current_amount = decimal.Decimal(str(int(event["data"][7], base=16)))
        # TODO: from the docs it seems that it's only possible to liquidate the whole amount
        assert current_amount == decimal.Decimal("0")
        debt_category = int(event["data"][10], base=16)
        self.user_states[user].loans[loan_id].borrowings = HashStackBorrowings(
            borrowings_id=loan_id,
            market=token,
            amount=amount,
            current_market=current_token,
            current_amount=current_amount,
            debt_category=debt_category,
        )
        # TODO: what happens to the collateral? now assuming it disappears
        self.user_states[user].loans[loan_id].collateral = HashStackCollateral(
            market=self.user_states[user].loans[loan_id].collateral.market,
            amount=self.user_states[user].loans[loan_id].collateral.amount,
            current_amount=decimal.Decimal("0"),
        )


def get_range(start, stop, step):
    return [
        x
        for x in compute.decimal_range(
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
TOKEN_DECIMAL_FACTORS = {
    "ETH": decimal.Decimal("1e18"),
    "wBTC": decimal.Decimal("1e8"),
    "USDC": decimal.Decimal("1e6"),
    "DAI": decimal.Decimal("1e18"),
    "USDT": decimal.Decimal("1e6"),
}


def compute_collateral_current_amount_usd(
    collateral: HashStackCollateral,
    prices: Dict[str, decimal.Decimal],
) -> decimal.Decimal:
    return (
        collateral.current_amount
        * prices[collateral.market]
        # TODO: perform the conversion using TOKEN_DECIMAL_FACTORS sooner (in `UserTokenState`?)?
        / TOKEN_DECIMAL_FACTORS[collateral.market]
    )


def compute_borrowings_current_amount_usd(
    borrowings: HashStackBorrowings,
    prices: Dict[str, decimal.Decimal],
) -> decimal.Decimal:
    return (
        borrowings.current_amount
        * prices[borrowings.current_market]
        # TODO: perform the conversion using TOKEN_DECIMAL_FACTORS sooner (in `UserTokenState`?)?
        / TOKEN_DECIMAL_FACTORS[borrowings.current_market]
    )


def compute_borrowings_amount_usd(
    borrowings: HashStackBorrowings,
    prices: Dict[str, decimal.Decimal],
) -> decimal.Decimal:
    return (
        borrowings.amount
        * prices[borrowings.market]
        # TODO: perform the conversion using TOKEN_DECIMAL_FACTORS sooner (in `UserTokenState`?)?
        / TOKEN_DECIMAL_FACTORS[borrowings.market]
    )


def compute_health_factor(
    collateral: HashStackCollateral,
    borrowings: HashStackBorrowings,
    prices: Dict[str, decimal.Decimal],
    user: str,
) -> decimal.Decimal:
    collateral_current_amount_usd = compute_collateral_current_amount_usd(
        collateral=collateral, prices=prices
    )
    borrowings_current_amount_usd = compute_borrowings_current_amount_usd(
        borrowings=borrowings, prices=prices
    )
    borrowings_amount_usd = compute_borrowings_amount_usd(
        borrowings=borrowings, prices=prices
    )
    if borrowings_current_amount_usd == decimal.Decimal("0"):
        # TODO: assumes collateral is positive
        return decimal.Decimal("Inf")

    # TODO: how can this happen?
    if borrowings_amount_usd == decimal.Decimal("0"):
        # TODO: assumes collateral is positive
        return decimal.Decimal("Inf")

    health_factor = (
        collateral_current_amount_usd + borrowings_current_amount_usd
    ) / borrowings_amount_usd
    health_factor_liquidation_threshold = (
        decimal.Decimal("1.06")
        if borrowings.debt_category == 1
        else decimal.Decimal("1.05")
        if borrowings.debt_category == 2
        else decimal.Decimal("1.04")
    )
    return health_factor


def compute_max_liquidated_amount(
    state: State,
    prices: Dict[str, decimal.Decimal],
    borrowings_token: str,
) -> decimal.Decimal:
    liquidated_borrowings_amount = decimal.Decimal("0")
    for user, user_state in state.user_states.items():
        for loan_id, loan in user_state.loans.items():
            # TODO: do this?
            # Filter out users who borrowed the token of interest.
            if borrowings_token != loan.borrowings.market:
                continue

            # Filter out users with health below 1.
            borrowings_amount_usd = compute_borrowings_amount_usd(
                borrowings=loan.borrowings, prices=prices
            )
            health_factor = compute_health_factor(
                borrowings=loan.borrowings,
                collateral=loan.collateral,
                prices=prices,
                user=user,
            )
            # TODO: this should be a method of the borrowings class
            health_factor_liquidation_threshold = (
                decimal.Decimal("1.06")
                if loan.borrowings.debt_category == 1
                else decimal.Decimal("1.05")
                if loan.borrowings.debt_category == 2
                else decimal.Decimal("1.04")
            )
            if health_factor >= health_factor_liquidation_threshold:
                continue

            # TODO: find out how much of the borrowings_token will be liquidated
            liquidated_borrowings_amount += borrowings_amount_usd
    return liquidated_borrowings_amount


def simulate_liquidations_under_absolute_price_change(
    prices: classes.Prices,
    collateral_token: str,
    collateral_token_price: decimal.Decimal,
    state: State,
    borrowings_token: str,
) -> decimal.Decimal:
    changed_prices = copy.deepcopy(prices.prices)
    changed_prices[collateral_token] = collateral_token_price
    return compute_max_liquidated_amount(
        state=state, prices=changed_prices, borrowings_token=borrowings_token
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

    # TODO
    data["max_borrowings_to_be_liquidated_at_interval"] = (
        data["max_borrowings_to_be_liquidated"].diff().abs()
    )
    # TODO: drops also other NaN, if there are any
    data.dropna(inplace=True)

    data["amm_borrowings_token_supply"] = data["collateral_token_price"].apply(
        lambda x: compute.get_amm_supply_at_price(
            collateral_token=collateral_token,
            collateral_token_price=x,
            borrowings_token=borrowings_token,
            amm=swap_amm,
        )
    )
    return data


def generate_and_store_graph_data(state, prices, swap_amm, pair):
    t0 = time.time()
    print("hashstack: generating graph for", pair, flush=True)
    c = pair[0]
    b = pair[1]
    data = generate_graph_data(state, prices, swap_amm, c, b)
    filename = f"hashstack_data/{c}-{b}.csv"
    data.to_csv(filename, index=False)
    print("hashstack: ", filename, "done in", time.time() - t0, flush=True)


PAIRS = [
    # ("wBTC", "ETH"),
    # ("ETH", "wBTC"),
    ("ETH", "USDC"),
    ("ETH", "USDT"),
    ("ETH", "DAI"),
    ("wBTC", "USDC"),
    ("wBTC", "USDT"),
    ("wBTC", "DAI"),
]


def load_data():
    data = {}
    for pair in PAIRS:
        c = pair[0]
        b = pair[1]
        data[pair] = pandas.read_csv(f"hashstack_data/{c}-{b}.csv")
    #     histogram_data = pd.read_csv("data/histogram.csv")
    small_loans_sample = pandas.read_csv("hashstack_data/small_loans_sample.csv")
    large_loans_sample = pandas.read_csv("hashstack_data/large_loans_sample.csv")
    return (
        data,
        #         histogram_data,
        small_loans_sample,
        large_loans_sample,
    )
