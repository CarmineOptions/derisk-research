import pandas
import plotly.express
import streamlit


def load_histogram_data():
    zklend = pandas.read_csv("data/histogram.csv", compression="gzip")
    hashstack = pandas.read_csv("hashstack_data/histogram.csv", compression="gzip")
    return (zklend, hashstack)


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
