from typing import Dict
import collections
import decimal
import pandas
import constants
import requests


class Prices:
    def __init__(self):
        self.tokens = [
            ("ethereum", "ETH"),
            ("bitcoin", "wBTC"),
            ("usd-coin", "USDC"),
            ("dai", "DAI"),
            ("tether", "USDT"),
        ]
        self.vs_currency = "usd"
        self.prices = {}
        self.get_prices()

    def get_prices(self):
        token_ids = ""
        for token in self.tokens:
            token_ids += f"{token[0]},"
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={token_ids}&vs_currencies={self.vs_currency}"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            for token in self.tokens:
                (id, symbol) = token
                self.prices[symbol] = decimal.Decimal(data[id][self.vs_currency])
        else:
            raise Exception(
                f"Failed getting prices, status code {response.status_code}"
            )

    def get_by_symbol(self, symbol):
        symbol = constants.ztoken_to_token(symbol)
        if symbol in self.prices:
            return self.prices[symbol]
        raise Exception(f"Unknown symbol {symbol}")

    def to_dollars(self, n, symbol):
        symbol = constants.ztoken_to_token(symbol)
        try:
            price = self.prices[symbol]
            decimals = constants.get_decimals(symbol)
        except:
            raise Exception(f"Unknown symbol {symbol}")
        return n / 10**decimals * price

    def to_dollars_pretty(self, n, symbol):
        v = self.to_dollars(n, symbol)
        if abs(v) < 0.00001:
            return "$0"
        return f"${v:.5f}"


# TODO: convert numbers/amounts (divide by sth)
# TODO: remove irrelevant variables (in events)
# TODO: add self.user to UserState and UserTokenState?
# TODO: add logs
class AccumulatorState:
    """
    TODO
    """

    def __init__(self) -> None:
        self.lending_accumulator: decimal.Decimal = decimal.Decimal("1e27")
        self.debt_accumulator: decimal.Decimal = decimal.Decimal("1e27")

    def accumulators_sync(
        self, lending_accumulator: decimal.Decimal, debt_accumulator: decimal.Decimal
    ):
        self.lending_accumulator = lending_accumulator / decimal.Decimal("1e27")
        self.debt_accumulator = debt_accumulator / decimal.Decimal("1e27")


class UserTokenState:
    """
    TODO

    We are making a simplifying assumption that when collateral is enabled, all
    deposits of the given token are considered as collateral.
    """

    # TODO: make it token-dependent (advanced solution: fetch token prices in $ -> round each token's
    #   balance e.g. to the nearest cent)
    MAX_ROUNDING_ERROR = decimal.Decimal("1")

    def __init__(self, token: str) -> None:
        self.token: str = token
        self.deposit: decimal.Decimal = decimal.Decimal("0")
        self.collateral_enabled: bool = False
        self.borrowings: decimal.Decimal = decimal.Decimal("0")

    def update_deposit(self, raw_amount: decimal.Decimal):
        self.deposit += raw_amount
        if -self.MAX_ROUNDING_ERROR < self.deposit < self.MAX_ROUNDING_ERROR:
            self.deposit = decimal.Decimal("0")


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
            "zETH": UserTokenState("zETH"),
            "zWBTC": UserTokenState("zWBTC"),
            "zUSDC": UserTokenState("zUSDC"),
            "zDAI": UserTokenState("zDAI"),
            "zUSDT": UserTokenState("zUSDT"),
        }
        # TODO: implement healt_factor
        # TODO: use decimal
        self.health_factor: float = 1.0  # TODO: is this a good default value??

    def deposit(self, token: str, raw_amount: decimal.Decimal):
        self.token_states[token].update_deposit(raw_amount)

    def withdrawal(self, token: str, raw_amount: decimal.Decimal):
        self.token_states[token].update_deposit(-raw_amount)

    def collateral_enabled(self, token: str):
        self.token_states[token].collateral_enabled = True

    def collateral_disabled(self, token: str):
        self.token_states[token].collateral_enabled = False

    def borrowing(
        self, token: str, raw_amount: decimal.Decimal, face_amount: decimal.Decimal
    ):
        self.token_states[token].borrowings += raw_amount

    def repayment(
        self, token: str, raw_amount: decimal.Decimal, face_amount: decimal.Decimal
    ):
        self.token_states[token].borrowings -= raw_amount

    def liquidation(
        self,
        debt_token: str,
        debt_raw_amount: decimal.Decimal,
        debt_face_amount: decimal.Decimal,
        collateral_token: decimal.Decimal,
        collateral_raw_amount: decimal.Decimal,
    ):
        self.token_states[debt_token].borrowings -= debt_raw_amount
        self.token_states[collateral_token].update_deposit(-collateral_raw_amount)


class State:
    """
    TODO
    """

    EVENTS_FUNCTIONS_MAPPING: Dict[str, str] = {
        "Deposit": "process_deposit_event",
        "Withdrawal": "process_withdrawal_event",
        "CollateralEnabled": "process_collateral_enabled_event",
        "CollateralDisabled": "process_collateral_disabled_event",
        "Borrowing": "process_borrowing_event",
        "Repayment": "process_repayment_event",
        "Liquidation": "process_liquidation_event",
        "AccumulatorsSync": "process_accumulators_sync_event",
        "Transfer": "process_transfer_event",
    }

    def __init__(self) -> None:
        self.user_states: collections.defaultdict = collections.defaultdict(UserState)
        self.accumulator_states: Dict[str, AccumulatorState] = {
            "ETH": AccumulatorState(),
            "wBTC": AccumulatorState(),
            "USDC": AccumulatorState(),
            "DAI": AccumulatorState(),
            "USDT": AccumulatorState(),
        }

    def process_event(self, event: pandas.Series) -> None:
        name = event["key_name"]
        getattr(self, self.EVENTS_FUNCTIONS_MAPPING[name])(event=event)

    def process_deposit_event(self, event: pandas.Series) -> None:
        # The order of the arguments is: `user`, `token`, `face_amount`.
        user = event["data"][0]
        token = constants.get_symbol(event["data"][1])
        # TODO: divide by something or store like this?
        # TODO: any better conversion to decimals?
        face_amount = decimal.Decimal(str(int(event["data"][2], base=16)))
        # TODO: sanity checks/asserts?
        raw_amount = face_amount / self.accumulator_states[token].lending_accumulator
        self.user_states[user].deposit(token=token, raw_amount=raw_amount)

    def process_withdrawal_event(self, event: pandas.Series) -> None:
        # The order of the arguments is: `user`, `token`, `face_amount`.
        user = event["data"][0]
        token = constants.get_symbol(event["data"][1])
        face_amount = decimal.Decimal(str(int(event["data"][2], base=16)))
        raw_amount = face_amount / self.accumulator_states[token].lending_accumulator
        self.user_states[user].withdrawal(token=token, raw_amount=raw_amount)

    def process_collateral_enabled_event(self, event: pandas.Series) -> None:
        # The order of the arguments is: `user`, `token`.
        user = event["data"][0]
        token = constants.get_symbol(event["data"][1])
        self.user_states[user].collateral_enabled(token=token)

    def process_collateral_disabled_event(self, event: pandas.Series) -> None:
        # The order of the arguments is: `user`, `token`.
        user = event["data"][0]
        token = constants.get_symbol(event["data"][1])
        self.user_states[user].collateral_disabled(token=token)

    def process_borrowing_event(self, event: pandas.Series) -> None:
        # The order of the arguments is: `user`, `token`, `raw_amount`, `face_amount`.
        user = event["data"][0]
        token = constants.get_symbol(event["data"][1])
        raw_amount = decimal.Decimal(str(int(event["data"][2], base=16)))
        face_amount = decimal.Decimal(
            str(int(event["data"][3], base=16))
        )  # TODO: relevant?
        self.user_states[user].borrowing(
            token=token,
            raw_amount=raw_amount,
            face_amount=face_amount,
        )

    def process_repayment_event(self, event: pandas.Series) -> None:
        # The order of the arguments is: `repayer`, `beneficiary`, `token`, `raw_amount`,
        # `face_amount`.
        repayer = event["data"][0]  # TODO: relevant?
        beneficiary = event["data"][1]
        token = constants.get_symbol(event["data"][2])
        raw_amount = decimal.Decimal(str(int(event["data"][3], base=16)))
        face_amount = decimal.Decimal(
            str(int(event["data"][4], base=16))
        )  # TODO: relevant?
        self.user_states[beneficiary].repayment(
            token=token,
            raw_amount=raw_amount,
            face_amount=face_amount,
        )

    def process_liquidation_event(self, event: pandas.Series) -> None:
        # The order of the arguments is: `liquidator`, `user`, `debt_token`, `debt_raw_amount`,
        # `debt_face_amount`, `collateral_token`, `collateral_amount`.
        liquidator = event["data"][0]  # TODO: relevant?
        user = event["data"][1]
        debt_token = constants.get_symbol(event["data"][2])
        debt_raw_amount = decimal.Decimal(str(int(event["data"][3], base=16)))
        debt_face_amount = decimal.Decimal(
            str(int(event["data"][4], base=16))
        )  # TODO: relevant?
        collateral_token = constants.get_symbol(event["data"][5])
        collateral_amount = decimal.Decimal(str(int(event["data"][6], base=16)))
        collateral_raw_amount = (
            collateral_amount
            / self.accumulator_states[collateral_token].lending_accumulator
        )
        self.user_states[user].liquidation(
            debt_token=debt_token,
            debt_raw_amount=debt_raw_amount,
            debt_face_amount=debt_face_amount,
            collateral_token=collateral_token,
            collateral_raw_amount=collateral_raw_amount,
        )

    def process_accumulators_sync_event(self, event: pandas.Series) -> None:
        # The order of the arguments is: `token`, `lending_accumulator`, `debt_accumulator`.
        token = constants.get_symbol(event["data"][0])
        lending_accumulator = decimal.Decimal(str(int(event["data"][1], base=16)))
        debt_accumulator = decimal.Decimal(str(int(event["data"][2], base=16)))
        self.accumulator_states[token].accumulators_sync(
            lending_accumulator=lending_accumulator,
            debt_accumulator=debt_accumulator,
        )

    def process_transfer_event(self, event: pandas.Series) -> None:
        # The order of the arguments is: `from_`, `to`, `value`.
        empty_address = "0x0"
        # token contract emitted this event
        ztoken = constants.get_symbol(event["from_address"])
        # zTokens share accumulator value with token
        token = constants.ztoken_to_token(ztoken)
        from_ = event["data"][0]
        to = event["data"][1]
        value = decimal.Decimal(str(int(event["data"][2], base=16)))
        raw_amount = value / self.accumulator_states[token].lending_accumulator

        if from_ != empty_address:
            self.user_states[from_].withdrawal(token=ztoken, raw_amount=raw_amount)
        if to != empty_address:
            self.user_states[to].deposit(token=ztoken, raw_amount=raw_amount)
