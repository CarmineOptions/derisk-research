"""
This module handles the collection and computation of statistics related to the protocol.
"""

import asyncio
from collections import defaultdict
from decimal import Decimal

import numpy as np
import pandas as pd
from shared import blockchain_call
from shared.constants import TOKEN_SETTINGS
from shared.custom_types import Prices
from shared.state import State

from dashboard_app.helpers.loans_table import (
    get_protocol,
    get_supply_function_call_parameters,
)
from dashboard_app.helpers.tools import get_underlying_address
from shared.helpers import get_addresses, add_leading_zeros


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
        if  loan_stats[protocol].empty: continue
      
        data.append(
            {
                "Protocol": protocol,
                "Number of active users": number_of_active_users,
                # At the moment, Hashstack V0 and Hashstack V1 are the only protocols
                #  for which the number of active
                # loans doesn't equal the number of active users.
                # The reason is that Hashstack V0 and Hashstack V1
                # allow for liquidations on the loan level, whereas other
                #  protocols use user-level liquidations.
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
                "kSTRK supply": token_supplies.get("kSTRK", default_value),
            }
        )
    df = pd.DataFrame(data)
    df["Total supply (USD)"] = sum(
        df[column]
        * Decimal(
            prices[
                add_leading_zeros(TOKEN_SETTINGS[column.replace(" supply", "")].address)
            ]
        )
        for column in df.columns
        if "supply" in column
    ).apply(lambda x: round(x, 4))
    return df


def get_collateral_stats(
    states: list[State],
) -> pd.DataFrame:
    """
    Get collateral stats for the dashboard.
    :param states: States zklend, nostra_alpha, nostra_mainnet
    :return: DataFrame with collateral stats
    """
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
                        / float(TOKEN_SETTINGS[token].decimal_factor) #TODO rm! now it's Decimal in db
                        * float(
                            state.interest_rate_models.collateral.get(
                                token_address, 1.0
                            )
                        )
                    )
                    token_collaterals[token] += round(collateral, 4)
                except AttributeError:
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
                "kSTRK collateral": token_collaterals["kSTRK"],
            }
        )
    return pd.DataFrame(data)


def get_debt_stats(
    states: list[State],
) -> pd.DataFrame:
    """
    Get debts for the dashboard.
    :param states: States zklend, nostra_alpha, nostra_mainnet
    :return: DataFrame with debt stats
    """
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
                            float(loan_entity.debt.get(token_address, 0.0))
                            for loan_entity in state.loan_entities.values()
                        )
                        / float(TOKEN_SETTINGS[token].decimal_factor) #TODO rm! now it's Decimal in db
                        * float(state.interest_rate_models.debt.get(token_address, 1.0))
                    )
                    token_debts[token] = round(debt, 4)
                except AttributeError:
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
                "kSTRK debt": token_debts["kSTRK"],
            }
        )
    data = pd.DataFrame(data)
    return data


def get_utilization_stats(
    general_stats: pd.DataFrame,
    supply_stats: pd.DataFrame,
    debt_stats: pd.DataFrame,
) -> pd.DataFrame:
    """
    Get utilization stats for the dashboard.
    :param general_stats: DataFrame containing general stats.
    :param supply_stats: DataFrame containing supply stats.
    :param debt_stats: DataFrame containing debt stats.
    :return: DataFrame with utilization stats
    """

    general_stats.columns = general_stats.columns.str.lower()
    supply_stats.columns = supply_stats.columns.str.lower()
    debt_stats.columns = debt_stats.columns.str.lower()

    required_columns_general = {"protocol", "total debt (usd)"}
    required_columns_supply = {"total supply (usd)"}
    if not required_columns_general.issubset(
        general_stats.columns
    ) or not required_columns_supply.issubset(supply_stats.columns):
        return pd.DataFrame()

    data = pd.DataFrame(
        {
            "Protocol": general_stats["protocol"],
        }
    )

    total_debt = general_stats["total debt (usd)"].astype(float)
    total_supply = supply_stats["total supply (usd)"].astype(float)
    total_utilization = total_debt / (total_debt + total_supply)
    total_utilization = total_utilization.replace([np.inf, -np.inf], 0).fillna(0)
    data["Total utilization"] = total_utilization.round(4)

    tokens = ["eth", "wbtc", "usdc", "dai", "usdt", "wsteth", "lords", "strk", "kstrk"]

    for token in tokens:
        debt_col = f"{token} debt"
        supply_col = f"{token} supply"

        if debt_col in debt_stats.columns and supply_col in supply_stats.columns:
            debt = debt_stats[debt_col].astype(float)
            supply = supply_stats[supply_col].astype(float)
            utilization = debt / (debt + supply)
            utilization = utilization.replace([np.inf, -np.inf], 0).fillna(0)
            data[f"{token.upper()} utilization"] = utilization.round(4)
        else:
            data[f"{token.upper()} utilization"] = 0.0

    return data
