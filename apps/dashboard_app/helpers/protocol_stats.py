import asyncio
from collections import defaultdict
from decimal import Decimal

import pandas as pd
from data_handler.handlers import blockchain_call
from shared.constants import TOKEN_SETTINGS
from shared.state import State
from shared.types import Prices

from dashboard_app.helpers.loans_table import (
    get_protocol,
    get_supply_function_call_parameters,
)
from dashboard_app.helpers.tools import get_addresses, get_underlying_address


def get_general_stats(
    states: list[State],
    loan_stats: dict[str, pd.DataFrame],
) -> pd.DataFrame:
    """
    Get general stats for the dashboard.
    :param states: States zklend, nostra_alpha, nostra_mainnet
    :param loan_stats: Loan stats data
    :return: DataFrame with general stats
    """
    data = []
    for state in states:
        protocol = get_protocol(state=state)
        number_of_active_users = state.compute_number_of_active_loan_entities()
        number_of_active_borrowers = (
            state.compute_number_of_active_loan_entities_with_debt()
        )
        data.append(
            {
                "Protocol": protocol,
                "Number of active users": number_of_active_users,
                # At the moment, Hashstack V0 and Hashstack V1 are the only protocols for which the number of active
                # loans doesn't equal the number of active users. The reason is that Hashstack V0 and Hashstack V1
                # allow for liquidations on the loan level, whereas other protocols use user-level liquidations.
                "Number of active loans": state.compute_number_of_active_loan_entities(),
                "Number of active borrowers": number_of_active_borrowers,
                "Total debt (USD)": round(loan_stats[protocol]["Debt (USD)"].sum(), 4),
                "Total risk adjusted collateral (USD)": round(
                    loan_stats[protocol]["Risk-adjusted collateral (USD)"].sum(), 4
                ),
                "Total Collateral (USD)": round(
                    loan_stats[protocol]["Collateral (USD)"].sum(), 4
                ),
            }
        )
    data = pd.DataFrame(data)
    return data


def get_supply_stats(
    states: list[State],
    prices: Prices,
) -> pd.DataFrame:
    """
    Get supply stats for the dashboard.
    :param states: States zklend, nostra_alpha, nostra_mainnet
    :param prices: Prices dict
    :return: DataFrame with supply stats
    """
    data = []
    for state in states:
        protocol = get_protocol(state=state)
        token_supplies = {}
        for token in TOKEN_SETTINGS:
            (
                addresses,
                selector,
            ) = get_supply_function_call_parameters(
                protocol=protocol,
                token_addresses=get_addresses(
                    token_parameters=state.token_parameters.collateral,
                    underlying_symbol=token,
                ),
            )
            supply = 0
            for address in addresses:
                supply += asyncio.run(
                    blockchain_call.func_call(
                        addr=int(address, base=16),
                        selector=selector,
                        calldata=[],
                    )
                )[0]
            supply = supply / TOKEN_SETTINGS[token].decimal_factor
            token_supplies[token] = round(supply, 4)

        default_value = Decimal(0.0)
        data.append(
            {
                "Protocol": protocol,
                "ETH supply": token_supplies.get("ETH", default_value),
                "wBTC supply": token_supplies.get("wBTC", default_value),
                "USDC supply": token_supplies.get("USDC", default_value),
                # FIXME Uncomment when wBTC is added correct address
                # "DAI supply": token_supplies.get("DAI", default_value),
                "USDT supply": token_supplies.get("USDT", default_value),
                "wstETH supply": token_supplies.get("wstETH", default_value),
                "LORDS supply": token_supplies.get("LORDS", default_value),
                "STRK supply": token_supplies.get("STRK", default_value),
            }
        )
    df = pd.DataFrame(data)
    df["Total supply (USD)"] = sum(
        df[column]
        * Decimal(prices[TOKEN_SETTINGS[column.replace(" supply", "")].address])
        for column in df.columns
        if "supply" in column
    ).apply(lambda x: round(x, 4))
    return df


def get_collateral_stats(
    states: list[State],
) -> pd.DataFrame:
    data = []
    for state in states:
        protocol = get_protocol(state=state)
        token_collaterals = defaultdict(float)
        for token in TOKEN_SETTINGS:
            # TODO: save zkLend amounts under token_addresses?
            if protocol == "zkLend":
                token_addresses = [
                    get_underlying_address(
                        token_parameters=state.token_parameters.collateral,
                        underlying_symbol=token,
                    )
                ]
            elif protocol in {"Nostra Alpha", "Nostra Mainnet"}:
                token_addresses = get_addresses(
                    token_parameters=state.token_parameters.collateral,
                    underlying_symbol=token,
                )
            else:
                raise ValueError
            for token_address in token_addresses:
                try:
                    collateral = (
                        sum(
                            float(loan_entity.collateral.values.get(token_address, 0.0))
                            for loan_entity in state.loan_entities.values()
                        )
                        / TOKEN_SETTINGS[token].decimal_factor
                        * float(state.interest_rate_models.collateral[token_address])
                    )
                    token_collaterals[token] += round(collateral, 4)
                except TypeError:
                    # FIXME Remove when all tokens are added
                    token_collaterals[token] = Decimal(0.0)
        data.append(
            {
                "Protocol": protocol,
                "ETH collateral": token_collaterals["ETH"],
                "wBTC collateral": token_collaterals["wBTC"],
                "USDC collateral": token_collaterals["USDC"],
                "DAI collateral": token_collaterals["DAI"],
                "USDT collateral": token_collaterals["USDT"],
                "wstETH collateral": token_collaterals["wstETH"],
                "LORDS collateral": token_collaterals["LORDS"],
                "STRK collateral": token_collaterals["STRK"],
            }
        )
    return pd.DataFrame(data)


def get_debt_stats(
    states: list[State],
) -> pd.DataFrame:
    data = []
    for state in states:
        protocol = get_protocol(state=state)
        token_debts = defaultdict(float)
        for token in TOKEN_SETTINGS:
            # TODO: save zkLend amounts under token_addresses?
            if protocol == "zkLend":
                token_addresses = [
                    get_underlying_address(
                        token_parameters=state.token_parameters.debt,
                        underlying_symbol=token,
                    )
                ]
            elif protocol in {"Nostra Alpha", "Nostra Mainnet"}:
                token_addresses = get_addresses(
                    token_parameters=state.token_parameters.debt,
                    underlying_symbol=token,
                )
            else:
                raise ValueError
            for token_address in token_addresses:
                try:
                    debt = (
                        sum(
                            float(loan_entity.debt[token_address])
                            for loan_entity in state.loan_entities.values()
                        )
                        / TOKEN_SETTINGS[token].decimal_factor
                        * float(state.interest_rate_models.debt[token_address])
                    )
                    token_debts[token] = round(debt, 4)
                except TypeError:
                    # FIXME Remove when all tokens are added
                    token_debts[token] = Decimal(0.0)

        data.append(
            {
                "Protocol": protocol,
                "ETH debt": token_debts["ETH"],
                "WBTC debt": token_debts["WBTC"],
                "USDC debt": token_debts["USDC"],
                "DAI debt": token_debts["DAI"],
                "USDT debt": token_debts["USDT"],
                "wstETH debt": token_debts["wstETH"],
                "LORDS debt": token_debts["LORDS"],
                "STRK debt": token_debts["STRK"],
            }
        )
    data = pd.DataFrame(data)
    return data


def get_utilization_stats(
    general_stats: pd.DataFrame,
    supply_stats: pd.DataFrame,
    debt_stats: pd.DataFrame,
) -> pd.DataFrame:
    data = pd.DataFrame(
        {
            "Protocol": general_stats["Protocol"],
            "Total utilization": general_stats["Total debt (USD)"]
            / (general_stats["Total debt (USD)"] + supply_stats["Total supply (USD)"]),
            "ETH utilization": debt_stats["ETH debt"]
            / (supply_stats["ETH supply"] + debt_stats["ETH debt"]),
            "WBTC utilization": debt_stats["WBTC debt"]
            / (supply_stats.get("WBTC supply") + debt_stats.get("WBTC debt")),
            "USDC utilization": debt_stats["USDC debt"]
            / (supply_stats["USDC supply"] + debt_stats["USDC debt"]),
            "DAI utilization": debt_stats["DAI debt"]
            / (supply_stats["DAI supply"] + debt_stats["DAI debt"]),
            "USDT utilization": debt_stats["USDT debt"]
            / (supply_stats["USDT supply"] + debt_stats["USDT debt"]),
            "wstETH utilization": debt_stats["wstETH debt"]
            / (supply_stats["wstETH supply"] + debt_stats["wstETH debt"]),
            "LORDS utilization": debt_stats["LORDS debt"]
            / (supply_stats["LORDS supply"] + debt_stats["LORDS debt"]),
            "STRK utilization": debt_stats["STRK debt"]
            / (supply_stats["STRK supply"] + debt_stats["STRK debt"]),
        },
    )
    utilization_columns = [x for x in data.columns if "utilization" in x]
    data[utilization_columns] = data[utilization_columns].map(lambda x: round(x, 4))
    return data
