from typing import Dict
import decimal

import pandas
import plotly.express
import streamlit

import src.constants
import src.helpers



def get_histogram_data(
    state: src.state.State,
    prices: Dict[str, decimal.Decimal],
    save_data: bool = False,
) -> pandas.DataFrame:
    data = [
        {
            "token": token,
            "borrowings": token_amount / src.constants.TOKEN_DECIMAL_FACTORS[token] * prices[token],
        }
        for loan_entity in state.loan_entities.values()
        for token, token_amount in loan_entity.debt.token_amounts.items()
    ]
    data = pandas.DataFrame(data)
    if save_data:
        # TODO: Save data to Google Storage.
        # TODO: Save to parquet.
        directory = src.helpers.get_directory(state=state)
        data.to_csv(f"{directory}/histogram.csv", index=False, compression='gzip')
    return data


def load_histogram_data():
    zklend = pandas.read_csv("zklend_data/histogram.csv", compression="gzip")
    hashstack = pandas.read_csv("hashstack_data/histogram.csv", compression="gzip")
    # TODO: Add Nostra and Nostra uncapped.
    return (zklend, hashstack)


# TODO: Rename borrowings -> debt_usd.
def visualization(protocols):
    (zklend, hashstack) = load_histogram_data()
    values = streamlit.slider(
        "Select a range of borrowing values:", 0.0, 16000.0, (1.0, 100.0)
    )
    streamlit.write("Borrowings Range:", values)

    if "zkLend" in protocols and "Hashstack" in protocols:
        data = pandas.concat([zklend, hashstack])
    elif "zkLend" in protocols:
        data = zklend
    elif "Hashstack" in protocols:
        data = hashstack
    else:
        data = pandas.concat([zklend, hashstack])

    token_data = data.copy()
    token_data["borrowings"] = token_data["borrowings"].astype(float)
    token_data = token_data[token_data["borrowings"] > values[0]]
    token_data = token_data[token_data["borrowings"] < values[1]]

    streamlit.plotly_chart(
        plotly.express.histogram(
            token_data,
            x="borrowings",
            color="token",
            color_discrete_map={
                "DAI": "red",
                "ETH": "blue",
                "USDT": "purple",
                "USDC": "green",
                "wBTC": "orange",
                "wstETH": "brown",
            },
            title="Distribution of all Token Borrowings",
            nbins=100,
        ),
        True,
    )

    # Comparative Token Distribution (between 0 and 1)
    token_data_small = data.copy()
    token_data_small["borrowings"] = token_data_small["borrowings"].astype(float)
    token_data_small = token_data_small[token_data_small["borrowings"] < 1]
    token_data_small = token_data_small[token_data_small["borrowings"] > 0]

    streamlit.plotly_chart(
        plotly.express.histogram(
            token_data_small,
            x="borrowings",
            color="token",
            color_discrete_map={
                "DAI": "red",
                "ETH": "blue",
                "USDT": "purple",
                "USDC": "green",
                "wBTC": "orange",
                "wstETH": "brown",
            },
            title="Distribution of all Token Borrowings (Between 0 and 1)",
            nbins=100,
        ),
        True,
    )
