"""
This module includes functions to generate financial charts using token price and liquidity data.
"""
from collections import defaultdict
import math
from decimal import Decimal
import pandas as pd
import streamlit as st  
import plotly.express
import plotly.graph_objs
from shared.amms import SwapAmm
from shared.custom_types import Prices
from shared.state import State

from .constants import CommonValues
from helpers.settings import TOKEN_SETTINGS
from helpers.tools import (
    get_collateral_token_range,
    get_custom_data,
    get_prices,
    get_underlying_address,
)

from .constants import SUPPLY_STATS_TOKEN_SYMBOLS_MAPPING

AMMS = ("10kSwap", "MySwap", "SithSwap", "JediSwap")


def get_main_chart_data(
    state: State,
    prices: Prices,
    swap_amms: SwapAmm,
    collateral_token_underlying_symbol: str,
    debt_token_underlying_symbol: str,
) -> pd.DataFrame:
    """
    Generates financial chart data based on token prices, liquidity, and debt information.
    Takes five parameters and
    Returns: A DataFrame containing calculated token prices and liquidable debt data.
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
        """
        Computes the token supply for each AMM at a given collateral token price and
        Returns: the token supplied by AMM and total supply across all AMMs.
        """
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
            lambda x, amm: x[0][amm]
        )
    data["debt_token_supply"] = supplies_and_totals.apply(lambda x: x[1])

    return data


def get_main_chart_figure(
    data: pd.DataFrame,
    collateral_token: str,
    debt_token: str,
    collateral_token_price: float,
) -> plotly.graph_objs.Figure:
    """
    Generates a plotly figure for the main chart the function takes in four parameters and
    Returns: A Plotly figure object for the chart.
    """
    color_map_protocol = {
        "liquidable_debt_at_interval_zkLend": "#fff7bc",  # light yellow
        "liquidable_debt_at_interval_Nostra Alpha": "#fec44f",  # yellow
        "liquidable_debt_at_interval_Nostra Mainnet": "#d95f0e",
    }  # mustard yellow
    color_map_liquidity = {"debt_token_supply": "#1f77b4"}  # blue
    figure = plotly.graph_objs.Figure()

    customdata = get_custom_data(data)

    # Add bars for each protocol and the total liquidable debt
    for col in color_map_protocol.keys():
        try:
            figure.add_trace(
                plotly.graph_objs.Bar(
                    x=data["collateral_token_price"],
                    y=data[col],
                    name=col.replace(
                        "liquidable_debt_at_interval", f"Liquidable {debt_token} debt"
                    ).replace("_", " "),
                    marker_color=color_map_protocol[col],
                    opacity=0.7,
                    customdata=customdata,
                    hovertemplate=(
                        "<b>Price:</b> %{x}<br>"
                        "<b>Total:</b> %{customdata[0]:,.2f}<br>"
                        "<b>ZkLend:</b> %{customdata[1]:,.2f}<br>"
                        "<b>Nostra Alpha:</b> %{customdata[2]:,.2f}<br>"
                        "<b>Nostra Mainnet:</b> %{customdata[3]:,.2f}<br>"
                    ),
                )
            )
        except KeyError:  # If `KeyError` is raised from accessing data[col]
            continue  # Skip this trace

    # Add a separate trace for debt_token_supply with overlay mode
    figure.add_trace(
        plotly.graph_objs.Bar(
            x=data["collateral_token_price"],
            y=data["debt_token_supply"],
            name=f"{debt_token} available liquidity",
            marker_color=color_map_liquidity["debt_token_supply"],
            opacity=0.5,
            yaxis="y2",
            hovertemplate=("<b>Price:</b> %{x}<br>" "<b>Volume:</b> %{y}"),
        )
    )

    # Update layout for the stacked bar plot and the separate trace
    figure.update_layout(
        barmode="stack",
        title=f"Liquidable debt and the corresponding supply of {debt_token}"
        f" at various price intervals of {collateral_token}",
        xaxis_title=f"{collateral_token} Price (USD)",
        yaxis_title="Volume (USD)",
        legend_title="Legend",
        yaxis2={"overlaying": "y", "side": "left", "matches": "y"},
    )

    # Add the vertical line and shaded region for the current price
    figure.add_vline(
        x=collateral_token_price,
        line_width=2,
        line_dash="dash",
        line_color="black",
    )
    figure.add_vrect(
        x0=0.9 * collateral_token_price,
        x1=1.1 * collateral_token_price,
        annotation_text="Current price +- 10%",
        annotation_font_size=11,
        annotation_position="top left",
        fillcolor="gray",
        opacity=0.25,
        line_width=2,
    )
    return figure


def get_bar_chart_figures(
    supply_stats: pd.DataFrame,
    collateral_stats: pd.DataFrame,
    debt_stats: pd.DataFrame,
) -> tuple[
    plotly.graph_objs.Figure, plotly.graph_objs.Figure, plotly.graph_objs.Figure
]:
    """
    Generates a bar chart figures for supply, collateral, and debt stats and then
    Returns: A tuple of three objects (supply, collateral, and debt charts).
    """
    underlying_addresses_to_decimals = {
        x.address: int(math.log10(x.decimal_factor)) for x in TOKEN_SETTINGS.values()
    }
    underlying_symbols_to_addresses = {
        x.symbol: x.address for x in TOKEN_SETTINGS.values()
    }
    prices = get_prices(token_decimals=underlying_addresses_to_decimals)
    bar_chart_supply_stats = pd.DataFrame(index=[0])
    bar_chart_collateral_stats = pd.DataFrame(index=[0])
    bar_chart_debt_stats = pd.DataFrame(index=[0])
    for column in supply_stats.columns:
        if "protocol" in column.lower():
            bar_chart_supply_stats[column] = supply_stats[column][0]
            bar_chart_collateral_stats[column] = collateral_stats[column.capitalize()][
                0
            ]
            bar_chart_debt_stats[column] = debt_stats[column][0]
            continue
        elif "total" in column.lower():
            continue
        underlying_symbol = column.split(" ")[0]
        underlying_address = underlying_symbols_to_addresses[
            SUPPLY_STATS_TOKEN_SYMBOLS_MAPPING[underlying_symbol]
        ]
        bar_chart_supply_stats[underlying_symbol] = supply_stats[column].loc[
            0
        ] * Decimal(prices[underlying_address])
        # handling the specific case with WBTC token
        if underlying_symbol == "wbtc":
            bar_chart_collateral_stats[underlying_symbol] = (
                collateral_stats["wBTC collateral"].loc[0] * prices[underlying_address]
            )
        else:
            bar_chart_collateral_stats[underlying_symbol] = (
                collateral_stats[
                    SUPPLY_STATS_TOKEN_SYMBOLS_MAPPING[underlying_symbol]
                    + " collateral"
                ].loc[0]
                * prices[underlying_address]
            )
        bar_chart_debt_stats[underlying_symbol] = (
            debt_stats[underlying_symbol + " debt"].loc[0] * prices[underlying_address]
        )

    bar_chart_supply_stats = bar_chart_supply_stats.T
    bar_chart_collateral_stats = bar_chart_collateral_stats.T
    bar_chart_debt_stats = bar_chart_debt_stats.T

    supply_figure = plotly.graph_objs.Figure(
        data=[
            plotly.graph_objs.Bar(
                name="zkLend",
                x=bar_chart_supply_stats.index,
                y=bar_chart_supply_stats[0],
                marker=plotly.graph_objs.bar.Marker(color="#fff7bc"),
            ),
            # plotly.graph_objs.Bar(
            #     name="Nostra Alpha",
            #     x=bar_chart_supply_stats.index,
            #     y=bar_chart_supply_stats["Nostra Alpha"],
            #     marker=plotly.graph_objs.bar.Marker(color="#fec44f"),
            # ),
            # plotly.graph_objs.Bar(
            #     name="Nostra Mainnet",
            #     x=bar_chart_supply_stats.index,
            #     y=bar_chart_supply_stats["Nostra Mainnet"],
            #     marker=plotly.graph_objs.bar.Marker(color="#d95f0e"),
            # ),
            # TODO: add functionality for other protocols
        ],
    )
    supply_figure.update_layout(title_text="Supply (USD) per token")
    collateral_figure = plotly.graph_objs.Figure(
        data=[
            plotly.graph_objs.Bar(
                name="zkLend",
                x=bar_chart_collateral_stats.index,
                y=bar_chart_collateral_stats[0],
                marker=plotly.graph_objs.bar.Marker(color="#fff7bc"),
            ),
            # plotly.graph_objs.Bar(
            #     name="Nostra Alpha",
            #     x=bar_chart_collateral_stats.index,
            #     y=bar_chart_collateral_stats["Nostra Alpha"],
            #     marker=plotly.graph_objs.bar.Marker(color="#fec44f"),
            # ),
            # plotly.graph_objs.Bar(
            #     name="Nostra Mainnet",
            #     x=bar_chart_collateral_stats.index,
            #     y=bar_chart_collateral_stats["Nostra Mainnet"],
            #     marker=plotly.graph_objs.bar.Marker(color="#d95f0e"),
            # ),
            # TODO: add functionality for other protocols
        ],
    )
    collateral_figure.update_layout(title_text="Collateral (USD) per token")
    debt_figure = plotly.graph_objs.Figure(
        data=[
            plotly.graph_objs.Bar(
                name="zkLend",
                x=bar_chart_debt_stats.index,
                y=bar_chart_debt_stats[0],
                marker=plotly.graph_objs.bar.Marker(color="#fff7bc"),
            ),
            # plotly.graph_objs.Bar(
            #     name="Nostra Alpha",
            #     x=bar_chart_debt_stats.index,
            #     y=bar_chart_debt_stats["Nostra Alpha"],
            #     marker=plotly.graph_objs.bar.Marker(color="#fec44f"),
            # ),
            # plotly.graph_objs.Bar(
            #     name="Nostra Mainnet",
            #     x=bar_chart_debt_stats.index,
            #     y=bar_chart_debt_stats["Nostra Mainnet"],
            #     marker=plotly.graph_objs.bar.Marker(color="#d95f0e"),
            # ),
            # TODO: add functionality for other protocols
        ],
    )
    debt_figure.update_layout(title_text="Debt (USD) per token")
    return supply_figure, collateral_figure, debt_figure


def get_specific_loan_usd_amounts(
    loan: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    This function gets the loan amount in usd and then it
    Returns: A tuple containing two DataFrames with specific loan USD amounts.
    """
    underlying_addresses_to_decimals = {
        x.address: int(math.log10(x.decimal_factor)) for x in TOKEN_SETTINGS.values()
    }
    underlying_symbols_to_addresses = {
        x.symbol: x.address for x in TOKEN_SETTINGS.values()
    }
    prices = get_prices(token_decimals=underlying_addresses_to_decimals)
    loan_collateral = loan["Collateral"].iloc[0]
    loan_debt = loan["Debt"].iloc[0]
    collateral_usd_amounts = pd.DataFrame()
    debt_usd_amounts = pd.DataFrame()
    for symbol, address in underlying_symbols_to_addresses.items():
        collateral_usd_amount_symbol = pd.DataFrame(
            {
                "token": [symbol],
                "amount_usd": [loan_collateral[address] * prices.get(address, 0)],
            },
        )
        debt_usd_amount_symbol = pd.DataFrame(
            {
                "token": [symbol],
                "amount_usd": [loan_debt[address] * prices.get(address, 0)],
            },
        )
        collateral_usd_amounts = pd.concat(
            [collateral_usd_amounts, collateral_usd_amount_symbol]
        )
        debt_usd_amounts = pd.concat([debt_usd_amounts, debt_usd_amount_symbol])
    return collateral_usd_amounts, debt_usd_amounts


def get_user_history(user_id: str, df: pd.DataFrame) -> pd.DataFrame:
    """
    Fetches all changes in deposit, collateral, and debt for a given user.

    Args:
        user_id (str): The user ID to filter the data.
        df (pd.DataFrame): The DataFrame containing loan data.

    Returns:
        pd.DataFrame: A DataFrame showing the history of deposits, collateral, and debt.
    """
    try:
        user_df = df[df[CommonValues.user.value] == user_id][
            [CommonValues.collateral_usd.value, CommonValues.debt_usd.value]].copy()
        user_df.rename(columns={CommonValues.collateral_usd.value: "Collateral", CommonValues.debt_usd.value: "Debt"}, inplace=True)
        user_df.insert(0, "Transaction", user_df.index + 1)
        return user_df
    except KeyError:
        print(f"User ID {user_id} not found in the DataFrame.")
        return pd.DataFrame()
    
def display_user_history_chart(df: pd.DataFrame):  
    """  
    Displays a chart based on the user's wallet ID input to show their transaction history.  

    Args:  
        df (pd.DataFrame): The DataFrame containing all transactions.  
    """  
    st.subheader("Input Wallet ID to View History")  

    wallet_id = st.text_input("Enter Wallet ID:")  

    if wallet_id:  
        user_history_data = get_user_history(wallet_id, df)   
        
        if not user_history_data.empty:  
            st.dataframe(user_history_data)  

            st.subheader(f"Collateral and Debt History for Wallet ID: {wallet_id}")  
            chart_data = user_history_data.set_index("Transaction")[["Collateral", "Debt"]]  
            st.line_chart(chart_data)  
        else:  
            st.error("No data found for this wallet ID.") 

<<<<<<< HEAD
def get_total_debt_amount(debt_df: pd.DataFrame) -> pd.DataFrame:
    """
    Computes the total debt amount per token from the provided DataFrame.
    
    The function assumes that the DataFrame contains (according to the data.csv):
    - A column representing token identifiers (e.g., 'Token' or 'Asset').
    - A 'Debt (USD)' column containing numerical debt values.
    
    It groups the data by token and sums the debt amounts accordingly.
    
    Args:
        debt_df (pd.DataFrame): DataFrame containing debt data with at least:
            - A column for token identifiers.
            - A 'Debt (USD)' column for debt values.
    """
    total_debt = {}

    for _, row in debt_df.iterrows():
        debt_entry = row.get("Debt")
        if isinstance(debt_entry, dict):
            for token, amount in debt_entry.items():
                total_debt[token] = total_debt.get(token, 0) + amount
        else:
            # If the 'Debt' field is not a dict, skip this row or handle accordingly.
            continue

    result_df = pd.DataFrame(list(total_debt.items()), columns=["token", "total_debt"])
    return result_df
=======
                
def get_total_deposit_amount(df: pd.DataFrame) -> dict:
    """
    A dataframe with a "Collateral" column containing deposit amount in the format:
    "TOKEN: amount, TOKEN: amount, ...".
    This function sums up the deposit amounts per token across all rows.
    Args: Pandas DataFrame with a "Collateral" column.
    Returns: A dictionary containing the total deposit amount per token.
    """
    totals = defaultdict(float)

    #Iterate over each row in the DataFrame
    for _, row in df.iterrows():
        collateral = row.get("Collateral", "")
        # Skip empty or missing collateral entries
        if pd.isna(collateral) or not collateral.strip():
            continue

        # Split the collateral string by comma to separate token entries
        tokens = collateral.split(',')
        for token_entry in tokens:
            token_entry = token_entry.strip()
            if not token_entry or ":" not in token_entry:
                continue

            # Split token and its amount
            token, amount_str = token_entry.split(":", 1)
            token = token.strip()
            try:
                amount = float(amount_str.strip())
            except ValueError:
                # Skip or handle the case where conversion fails
                continue

            totals[token] += amount
    
    return dict(totals)
>>>>>>> 1756c94 (token_amount function)
