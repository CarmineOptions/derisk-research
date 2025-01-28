"""
A module that fetches data of token prices, liquidity etc.
"""

import logging
import math
from typing import Iterator

import pandas as pd
import requests
from data_handler.handlers.loan_states.abstractions import State
from shared.amms import SwapAmm
from shared.blockchain_call import func_call
from shared.custom_types import TokenParameters, Prices

from starknet_py.cairo.felt import decode_shortstring

AMMS = ["10kSwap", "MySwap", "SithSwap", "JediSwap"]


def float_range(start: float, stop: float, step: float) -> Iterator[float]:
    """
    Generator that yields float values within the specified range.

    :param start: Start of the range.
    :param stop: End of the range.
    :param step: Step size.
    :return: Generator of float values.
    """
    while start < stop:
        yield start
        start += step


def get_collateral_token_range(
    collateral_token_underlying_address: str,
    collateral_token_price: float,
) -> list[float]:
    """
    Generates a range of prices for a collateral token and
    Returns:  A list of float values representing the range of prices for the collateral token.
    """
    target_number_of_values = 50
    start_price = 0.0
    stop_price = collateral_token_price * 1.2
    # Calculate rough step size to get about 50 (target) values
    raw_step_size = (stop_price - start_price) / target_number_of_values
    # Round the step size to the closest readable value (1, 2, or 5 times powers of 10)
    magnitude = 10 ** math.floor(math.log10(raw_step_size))  # Base scale
    step_factors = [1, 2, 2.5, 5, 10]
    difference = [
        abs(50 - stop_price / (k * magnitude)) for k in step_factors
    ]  # Stores the difference between the target value and
    # number of values generated from each step factor.
    readable_step = (
        step_factors[difference.index(min(difference))] * magnitude
    )  # Gets readable step from step factor with values closest to the target value.

    # Generate values using the calculated readable step
    return list(float_range(start=readable_step, stop=stop_price, step=readable_step))


async def get_symbol(token_address: str) -> str:
    """
    Takes the address of a token and returns the symbol of that token
    """
    # DAI V2's symbol is `DAI` but we don't want to mix it with DAI = DAI V1.
    if (
        token_address
        == "0x05574eb6b8789a91466f902c380d978e472db68170ff82a5b650b95a58ddf4ad"
    ):
        return "DAI V2"
    symbol = await func_call(
        addr=token_address,
        selector="symbol",
        calldata=[],
    )
    # For some Nostra Mainnet tokens, a list of length 3 is returned.
    if len(symbol) > 1:
        return decode_shortstring(symbol[1])
    return decode_shortstring(symbol[0])


def get_prices(token_decimals: dict[str, int]) -> dict[str, float]:
    """
    Get the prices of the tokens.
    :param token_decimals: Token decimals.
    :return: Dict with token addresses as keys and token prices as values.
    """
    url = "https://starknet.impulse.avnu.fi/v1/tokens/short"
    response = requests.get(url, timeout=10)

    if not response.ok:
        response.raise_for_status()

    tokens_info = response.json()

    # Create a map of token addresses to token information, applying add_leading_zeros conditionally
    token_info_map = {
        add_leading_zeros(token["address"]): token for token in tokens_info
    }

    prices = {}
    for token, decimals in token_decimals.items():
        token_info = token_info_map.get(token)

        if not token_info:
            logging.error("Token %s not found in response.", token)
            continue

        if decimals != token_info.get("decimals"):
            logging.error(
                "Decimal mismatch for token %s: expected %d, got %d",
                token,
                decimals,
                token_info.get("decimals"),
            )
            continue

        prices[token] = token_info.get("currentPrice")

    return prices


def add_leading_zeros(hash: str) -> str:
    """
    Converts e.g. `0x436d8d078de345c11493bd91512eae60cd2713e05bcaa0bb9f0cba90358c6e` to
    `0x00436d8d078de345c11493bd91512eae60cd2713e05bcaa0bb9f0cba90358c6e`.
    """
    return "0x" + hash[2:].zfill(64)


def get_addresses(
    token_parameters: TokenParameters,
    underlying_address: str | None = None,
    underlying_symbol: str | None = None,
) -> list[str]:
    """
    get the token address based on underlying address or symbol and
    Returns it.
    """
    # Up to 2 addresses can match the given `underlying_address` or `underlying_symbol`.
    if underlying_address:
        addresses = [
            x.address
            for x in token_parameters.values()
            if x.underlying_address == underlying_address
        ]
    elif underlying_symbol:
        addresses = [
            x.address
            for x in token_parameters.values()
            if x.underlying_symbol == underlying_symbol
        ]
    else:
        raise ValueError(
            f"Both `underlying_address` =  {underlying_symbol} "
            f"or `underlying_symbol` = {underlying_symbol} are not specified."
        )
    assert len(addresses) <= 2
    return addresses


def get_underlying_address(
    token_parameters: TokenParameters,
    underlying_symbol: str,
) -> str:
    """
    Retrieves the underlying address for a given underlying symbol.
    """
    # One underlying address at maximum can match the given `underlying_symbol`.
    underlying_addresses = {
        x.underlying_address
        for x in token_parameters.values()
        if x.underlying_symbol == underlying_symbol
    }
    if not underlying_addresses:
        return ""
    assert len(underlying_addresses) == 1
    return list(underlying_addresses)[0]


def get_custom_data(data: pd.DataFrame) -> list:
    """
    Returns custom data for Plotly charts.
    :param data: dataframe
    :return: list
    """
    custom_columns = [
        "liquidable_debt_at_interval",
        "liquidable_debt_at_interval_zkLend",
        "liquidable_debt_at_interval_Nostra Alpha",
        "liquidable_debt_at_interval_Nostra Mainnet",
    ]
    customdata = []
    data_length = len(data)
    for col in custom_columns:
        if col in data.columns:
            customdata.append(data[col].values)
        else:
            customdata.append([0] * data_length)  # Use 0 if the column is missing

    # Transpose customdata to match rows to records
    customdata = list(zip(*customdata))

    return customdata


def get_main_chart_data(
    state: State,
    prices: Prices,
    swap_amms: SwapAmm,
    collateral_token_underlying_symbol: str,
    debt_token_underlying_symbol: str,
) -> pd.DataFrame:
    """
    Returns the main chart data for the given state and prices.
    Args:
        state:
        prices:
        swap_amms:
        collateral_token_underlying_symbol:
        debt_token_underlying_symbol:

    Returns: DataFrame

    """
    collateral_token_underlying_address = get_underlying_address(
        token_parameters=state.token_parameters.collateral,
        underlying_symbol=collateral_token_underlying_symbol,
    )
    if not collateral_token_underlying_address:
        return pd.DataFrame()

    data = pd.DataFrame(
        {
            "collateral_token_price": get_collateral_token_range(
                collateral_token_underlying_address=collateral_token_underlying_address,
                collateral_token_price=prices[collateral_token_underlying_address],
            ),
        }
    )

    debt_token_underlying_address = get_underlying_address(
        token_parameters=state.token_parameters.debt,
        underlying_symbol=debt_token_underlying_symbol,
    )
    if not debt_token_underlying_address:
        return pd.DataFrame()

    data["liquidable_debt"] = data["collateral_token_price"].apply(
        lambda x: state.compute_liquidable_debt_at_price(
            prices=prices,
            collateral_token_underlying_address=collateral_token_underlying_address,
            collateral_token_price=x,
            debt_token_underlying_address=debt_token_underlying_address,
        )
    )

    data["liquidable_debt_at_interval"] = data["liquidable_debt"].diff().abs()
    data.dropna(inplace=True)

    for amm in AMMS:
        data[f"{amm}_debt_token_supply"] = 0

    def compute_supply_at_price(collateral_token_price: float):
        supplies = {
            amm: swap_amms.get_supply_at_price(
                collateral_token_underlying_symbol=collateral_token_underlying_symbol,
                collateral_token_price=collateral_token_price,
                debt_token_underlying_symbol=debt_token_underlying_symbol,
                amm=amm,
            )
            for amm in AMMS
        }
        total_supply = sum(supplies.values())
        return supplies, total_supply

    supplies_and_totals = data["collateral_token_price"].apply(compute_supply_at_price)
    for amm in AMMS:
        data[f"{amm}_debt_token_supply"] = supplies_and_totals.apply(
            lambda x: x[0][amm]
        )
    data["debt_token_supply"] = supplies_and_totals.apply(lambda x: x[1])

    return data
