import decimal
import pandas 
import plotly.express 
import plotly.graph_objs

import src.helpers
import src.protocol_parameters
import src.state
import src.swap_amm

def get_main_chart_data(
    state: src.state.State,
    prices: src.helpers.TokenValues,
    swap_amms: src.swap_amm.SwapAmm,
    collateral_token: str,
    debt_token: str,
    save_data: bool = False,
) -> pandas.DataFrame:
    collateral_token_price = prices.values[collateral_token]
    data = pandas.DataFrame(
        {
            "collateral_token_price": src.helpers.get_collateral_token_range(
                collateral_token=collateral_token,
                collateral_token_price=collateral_token_price,
            ),
        }
    )
    data['liquidable_debt'] = data['collateral_token_price'].apply(
        lambda x: state.compute_liquidable_debt_at_price(
            prices=prices,
            collateral_token=collateral_token,
            collateral_token_price=x,
            debt_token=debt_token,
        )
    )
    data['liquidable_debt_at_interval'] = data['liquidable_debt'].diff().abs()
    data.dropna(inplace=True)

    # Initialize columns for each AMM
    for amm in ["jedi", "10k", "my", "sith"]:
        data[f"{amm}_debt_token_supply"] = 0

    for index, row in data.iterrows():
        price = row["collateral_token_price"]
        total_supply = 0
        for amm in ["jedi", "10k", "my", "sith"]:
            supply = swap_amms.get_supply_at_price(collateral_token, price, debt_token, amm)
            data.at[index, f"{amm}_debt_token_supply"] = supply
            total_supply += supply
        data.at[index, "debt_token_supply"] = total_supply

    if save_data:
        directory = src.protocol_parameters.get_directory(state=state)
        path = f"{directory}/{collateral_token}-{debt_token}.parquet"
        src.helpers.save_dataframe(data=data, path=path)
        
    return data


def get_main_chart_figure(
    data: pandas.DataFrame,
    collateral_token: str,
    debt_token: str,
) -> plotly.graph_objs.Figure:
    # Define the AMMs and their color mappings
    amms = ["jedi", "10k", "my", "sith"]
    color_map = {"jedi": "#ECD662", "10k": "#4CA7D0", "my": "#76C1FA", "sith": "#FFA07A"}

    figure = plotly.express.bar(
        data_frame=data,
        x="collateral_token_price",
        y=[f"{amm}_debt_token_supply" for amm in amms] + ["liquidable_debt_at_interval"],
        title=f"Liquidable debt and the corresponding supply of {debt_token} at various price intervals of {collateral_token}",
        barmode="overlay",
        opacity=0.65,
        color_discrete_map={**color_map, "liquidable_debt_at_interval": "#FFD700"},
    )
    figure.update_traces(hovertemplate=("<b>Price:</b> %{x}<br>" "<b>Volume:</b> %{y}"))
    for amm in amms:
        figure.update_traces(selector={"name": f"{amm}_debt_token_supply"}, name=f"{amm} {debt_token} supply")
    figure.update_traces(selector={"name": "liquidable_debt_at_interval"}, name=f"Liquidable {debt_token} debt")
    figure.update_xaxes(title_text=f"{collateral_token} Price (USD)")
    figure.update_yaxes(title_text="Volume (USD)")

    collateral_token_price = src.swap_amm.Prices().prices.values[collateral_token]
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
