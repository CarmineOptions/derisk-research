import os

import pandas
import plotly.express
import streamlit

import src.helpers
import src.protocol_parameters
import src.settings



def get_histogram_data(
    state: src.state.State,
    prices: src.helpers.TokenValues,
    save_data: bool = False,
) -> pandas.DataFrame:
    data = [
        {
            "token": token,
            "debt": (
                token_amount 
                / src.settings.TOKEN_SETTINGS[token].decimal_factor 
                * state.debt_interest_rate_models.values[token] 
                * prices.values[token]
            ),
        }
        for loan_entity in state.loan_entities.values()
        for token, token_amount in loan_entity.debt.values.items()
    ]
    data = pandas.DataFrame(data)
    if save_data:
        # TODO: Save to parquet.
        directory = src.protocol_parameters.get_directory(state=state)
        path = f"{directory}/histogram.csv"
        src.helpers.save_csv(data=data, path=path)
    return data


def visualization(data: pandas.DataFrame):
    values = streamlit.slider(
        "Select a range of debt values:", 0.0, 16000.0, (1.0, 100.0)
    )
    streamlit.write("Debt Range:", values)

    token_data = data.copy()
    token_data["debt"] = token_data["debt"].astype(float)
    token_data = token_data[token_data["debt"] > values[0]]
    token_data = token_data[token_data["debt"] < values[1]]

    streamlit.plotly_chart(
        plotly.express.histogram(
            token_data,
            x="debt",
            color="token",
            color_discrete_map={
                "DAI": "red",
                "ETH": "blue",
                "USDT": "purple",
                "USDC": "green",
                "wBTC": "orange",
                "wstETH": "brown",
            },
            title="Distribution of all Token Debt",
            nbins=100,
        ),
        True,
    )

    # Comparative Token Distribution (between 0 and 1)
    token_data_small = data.copy()
    token_data_small["debt"] = token_data_small["debt"].astype(float)
    token_data_small = token_data_small[token_data_small["debt"] < 1]
    token_data_small = token_data_small[token_data_small["debt"] > 0]

    streamlit.plotly_chart(
        plotly.express.histogram(
            token_data_small,
            x="debt",
            color="token",
            color_discrete_map={
                "DAI": "red",
                "ETH": "blue",
                "USDT": "purple",
                "USDC": "green",
                "wBTC": "orange",
                "wstETH": "brown",
            },
            title="Distribution of all Token Debt (Between 0 and 1)",
            nbins=100,
        ),
        True,
    )
