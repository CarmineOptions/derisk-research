from typing import Dict
import decimal

import pandas
import plotly.express
import plotly.graph_objs

import src.helpers
import src.state
import src.swap_liquidity



def get_main_chart_data(
    state: src.state.State,
    prices: Dict[str, decimal.Decimal],
    swap_amms: src.swap_liquidity.SwapAmm,
    collateral_token: str,
    debt_token: str,
    save_data: bool = False,
) -> pandas.DataFrame:
    data = pandas.DataFrame({"collateral_token_price": src.helpers.get_collateral_token_range(collateral_token)})
    data['liquidable_debt'] = \
        data['collateral_token_price'].apply(
            lambda x: state.compute_liquidable_debt_at_price(
                prices = prices,
                collateral_token = collateral_token,
                collateral_token_price = x,
                debt_token = debt_token,
            )
        )
    data['liquidable_debt_at_interval'] = data['liquidable_debt'].diff().abs()
    data.dropna(inplace = True)

    data["debt_token_supply"] = data["collateral_token_price"].apply(
        lambda x: src.swap_liquidity.get_supply_at_price(
            collateral_token=collateral_token,
            collateral_token_price=x,
            debt_token=debt_token,
            swap_amms=swap_amms,
        )
    )
    if save_data:
        # TODO: Save data to Google Storage.
        # TODO: Save to parquet.
        directory = src.helpers.get_directory(state=state)
        data.to_csv(f"{directory}/{collateral_token}-{debt_token}.csv", index=False, compression='gzip')
    return data


def get_main_chart_figure(
    data: pandas.DataFrame,
    collateral_token: str,
    debt_token: str,
) -> plotly.graph_objs.Figure:
    figure = plotly.express.bar(
        data_frame=data,
        x="collateral_token_price",
        y=["liquidable_debt_at_interval", "debt_token_supply"],
        title=f"Liquidable debt and the corresponding supply of {debt_token} at various price intervals of "
            f"{collateral_token}",
        barmode="overlay",
        opacity=0.65,
        # TODO: Align colors with the rest of the app.
        color_discrete_map={"liquidable_debt_at_interval": "#ECD662", "debt_token_supply": "#4CA7D0"},
    )
    figure.update_traces(hovertemplate=("<b>Price:</b> %{x}<br>" "<b>Volume:</b> %{y}"))
    figure.update_traces(selector={"name": "liquidable_debt_at_interval"}, name=f"Liquidable {debt_token} debt")
    figure.update_traces(selector={"name": "debt_token_supply"}, name=f"{debt_token} supply")
    figure.update_xaxes(title_text=f"{collateral_token} Price (USD)")
    figure.update_yaxes(title_text="Volume (USD)")
    collateral_token_price = src.swap_liquidity.Prices().prices[collateral_token]
    figure.add_vline(
        x=collateral_token_price,
        line_width=2,
        line_dash="dash",
        line_color="black",
    )
    figure.add_vrect(
        x0=decimal.Decimal("0.9") * collateral_token_price,
        x1=decimal.Decimal("1.1") * collateral_token_price,
        annotation_text="Current price +- 10%",
        annotation_font_size=11,
        annotation_position="top left",
        fillcolor="gray",
        opacity=0.25,
        line_width=2,
    )
    return figure