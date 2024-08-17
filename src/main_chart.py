import pandas
import plotly.express 
import plotly.graph_objs

import src.helpers
import src.protocol_parameters
import src.settings
import src.state
import src.swap_amm
import src.types



def get_main_chart_data(
    state: src.state.State,
    prices: src.types.Prices,
    swap_amms: src.swap_amm.SwapAmm,
    collateral_token_underlying_symbol: str,
    debt_token_underlying_symbol: str,
    save_data: bool = False,
) -> pandas.DataFrame:
    collateral_token_underlying_address = src.helpers.get_underlying_address(
        token_parameters=state.token_parameters.collateral,
        underlying_symbol=collateral_token_underlying_symbol,
    )
    if not collateral_token_underlying_address:
        return pandas.DataFrame()

    data = pandas.DataFrame(
        {
            "collateral_token_price": src.helpers.get_collateral_token_range(
                collateral_token_underlying_address=collateral_token_underlying_address,
                collateral_token_price=prices[collateral_token_underlying_address],
            ),
        }
    )

    debt_token_underlying_address = src.helpers.get_underlying_address(
        token_parameters=state.token_parameters.debt,
        underlying_symbol=debt_token_underlying_symbol,
    )
    if not debt_token_underlying_address:
        return pandas.DataFrame()

    data['liquidable_debt'] = data['collateral_token_price'].apply(
        lambda x: state.compute_liquidable_debt_at_price(
            prices=prices,
            collateral_token_underlying_address=collateral_token_underlying_address,
            collateral_token_price=x,
            debt_token_underlying_address=debt_token_underlying_address,
        )
    )

    data['liquidable_debt_at_interval'] = data['liquidable_debt'].diff().abs()
    data.dropna(inplace=True)

    for amm in src.swap_amm.AMMS:
        data[f"{amm}_debt_token_supply"] = 0

    def compute_supply_at_price(collateral_token_price: float):
        supplies = {
            amm: swap_amms.get_supply_at_price(
                collateral_token_underlying_symbol=collateral_token_underlying_symbol, 
                collateral_token_price=collateral_token_price, 
                debt_token_underlying_symbol=debt_token_underlying_symbol, 
                amm=amm,
            ) for amm in src.swap_amm.AMMS
        }
        total_supply = sum(supplies.values())
        return supplies, total_supply

    supplies_and_totals = data['collateral_token_price'].apply(compute_supply_at_price)
    for amm in src.swap_amm.AMMS:
        data[f"{amm}_debt_token_supply"] = supplies_and_totals.apply(lambda x: x[0][amm])
    data['debt_token_supply'] = supplies_and_totals.apply(lambda x: x[1])

    if save_data:
        directory = src.protocol_parameters.get_directory(state=state)
        path = f"{directory}/{collateral_token_underlying_address}-{debt_token_underlying_address}.parquet"
        src.helpers.save_dataframe(data=data, path=path)
    return data


def get_main_chart_figure(
    data: pandas.DataFrame,
    collateral_token: str,
    debt_token: str,
    collateral_token_price: float,
) -> plotly.graph_objs.Figure:
    # Define the AMMs and their color mappings
    amms = src.swap_amm.AMMS
    color_map = {"10kSwap_debt_token_supply": "#4C6DD0",
                 "MySwap_debt_token_supply": "#4CA7D0",
                 "SithSwap_debt_token_supply": "#4C99D0",
                 "JediSwap_debt_token_supply": "#4C83D0"}

    # TODO: Align colors with the rest of the app.
    color_map_protocol = {"liquidable_debt_at_interval_zkLend": "#fff7bc", # light yellow
                        "liquidable_debt_at_interval_Nostra Alpha": "#fec44f", # yellow
                        "liquidable_debt_at_interval_Nostra Mainnet": "#d95f0e"} # mustard yellow 
    color_map_liquidity = {"debt_token_supply": "#1f77b4"} # blue
    figure = plotly.graph_objs.Figure()

    # Add bars for each protocol and the total liquidable debt
    for col in color_map_protocol.keys():
        figure.add_trace(plotly.graph_objs.Bar(
            x=data["collateral_token_price"],
            y=data[col],
            name = col.replace("liquidable_debt_at_interval", f"Liquidable {debt_token} debt").replace("_", " "),
            marker_color = color_map_protocol[col],
            opacity = 0.7,
            customdata=data[["liquidable_debt", "liquidable_debt_zkLend", "liquidable_debt_at_interval_Nostra Alpha", "liquidable_debt_at_interval_Nostra Mainnet"]].values,
            hovertemplate=(
                "<b>Price:</b> %{x}<br>"
                "<b>Total Volume:</b> %{customdata[0]:,.2f}<br>"
                "<b>ZkLend Volume:</b> %{customdata[1]:,.2f}<br>"
                "<b>Nostra Alpha Volume:</b> %{customdata[2]:,.2f}<br>"
                "<b>Nostra Mainnet Volume:</b> %{customdata[3]:,.2f}<br>"
            ),
    ))
    
    # Add a separate trace for debt_token_supply with overlay mode
    figure.add_trace(plotly.graph_objs.Bar(
        x=data["collateral_token_price"],
        y=data["debt_token_supply"],
        name=f"{debt_token} available liquidity",
        marker_color=color_map_liquidity["debt_token_supply"],
        opacity=0.5,
        yaxis="y2",
        hovertemplate=(
            "<b>Price:</b> %{x}<br>"
            "<b>Volume:</b> %{y}"
        )
    ))

    # Update layout for the stacked bar plot and the separate trace
    figure.update_layout(
        barmode="stack",
        title=f"Liquidable debt and the corresponding supply of {debt_token} at various price intervals of {collateral_token}",
        xaxis_title=f"{collateral_token} Price (USD)",
        yaxis_title="Volume (USD)",
        legend_title="Legend",
        yaxis2=dict(
            overlaying='y',
            side='left',
            matches="y"
        )
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
