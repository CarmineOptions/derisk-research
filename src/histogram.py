import streamlit as st
import plotly.express as px
import pandas as pd


def load_histogram_data():
    zklend = pd.read_csv("data/histogram.csv")
    hashstack = pd.read_csv("hashstack_data/histogram.csv")
    return (zklend, hashstack)


def visualization(protocols):
    (zklend, hashstack) = load_histogram_data()
    values = st.slider(
        "Select a range of borrowing values:", 0.0, 16000.0, (1.0, 100.0)
    )
    st.write("Borrowings Range:", values)

    if "zkLend" in protocols and "Hashstack" in protocols:
        data = pd.concat([zklend, hashstack])
    elif "zkLend" in protocols:
        data = zklend
    elif "Hashstack" in protocols:
        data = hashstack
    else:
        data = pd.concat([zklend, hashstack])

    token_data = data
    token_data["borrowings"] = token_data["borrowings"].astype(float)
    token_data = token_data[token_data["borrowings"] > values[0]]
    token_data = token_data[token_data["borrowings"] < values[1]]

    st.plotly_chart(
        px.histogram(
            token_data,
            x="borrowings",
            color="token",
            color_discrete_map={
                "DAI": "red",
                "ETH": "blue",
                "USDT": "purple",
                "USDC": "green",
                "wBTC": "orange",
            },
            title="Distribution of all Token Borrowings",
            nbins=100,
        ),
        True,
    )
    """"
    # Comparative Token Distribution (greater than 100)
    token_data2 = pandas.DataFrame(tmp)
    token_data2["borrowings"] = token_data2["borrowings"].astype(float)
    token_data2 = token_data2[token_data2["borrowings"] > 100]
    st.write(
        px.histogram(
            token_data2,
            x="borrowings",
            color="token",
            color_discrete_map={
                "DAI": "red",
                "ETH": "blue",
                "USDT": "purple",
                "USDC": "green",
                "wBTC": "orange",
            },
            title="Distribution of all Token Borrowings (Greater than 100)",
            nbins=100,
        )
    )

    # Comparative Token Distribution (between 1 and 500)
    token_data3 = pandas.DataFrame(tmp)
    token_data3["borrowings"] = token_data3["borrowings"].astype(float)
    token_data3 = token_data3[token_data3["borrowings"] < 500]
    token_data3 = token_data3[token_data3["borrowings"] > 1]
    st.write(
        px.histogram(
            token_data3,
            x="borrowings",
            color="token",
            color_discrete_map={
                "DAI": "red",
                "ETH": "blue",
                "USDT": "purple",
                "USDC": "green",
                "wBTC": "orange",
            },
            title="Distribution of all Token Borrowings (Between 1 and 500)",
            nbins=100,
        )
    )

    # Comparative Token Distribution (between 100 and 500)
    token_data4 = pandas.DataFrame(tmp)
    token_data4["borrowings"] = token_data4["borrowings"].astype(float)
    token_data4 = token_data4[token_data4["borrowings"] < 500]
    token_data4 = token_data4[token_data4["borrowings"] > 100]
    st.write(
        px.histogram(
            token_data4,
            x="borrowings",
            color="token",
            color_discrete_map={
                "DAI": "red",
                "ETH": "blue",
                "USDT": "purple",
                "USDC": "green",
                "wBTC": "orange",
            },
            title="Distribution of all Token Borrowings (Between 100 and 500)",
            nbins=100,
        )
    )

    # Comparative Token Distribution (between 1 and 100)
    token_data5 = pandas.DataFrame(tmp)
    token_data5["borrowings"] = token_data5["borrowings"].astype(float)
    token_data5 = token_data5[token_data5["borrowings"] < 100]
    token_data5 = token_data5[token_data5["borrowings"] > 1]
    st.write(
        px.histogram(
            token_data5,
            x="borrowings",
            color="token",
            color_discrete_map={
                "DAI": "red",
                "ETH": "blue",
                "USDT": "purple",
                "USDC": "green",
                "wBTC": "orange",
            },
            title="Distribution of all Token Borrowings (Between 1 and 100)",
            nbins=100,
        )
    )
    """
    # Comparative Token Distribution (between 0 and 1)
    token_data6 = data
    token_data6["borrowings"] = token_data6["borrowings"].astype(float)
    token_data6 = token_data6[token_data6["borrowings"] < 1]
    token_data6 = token_data6[token_data6["borrowings"] > 0]

    st.plotly_chart(
        px.histogram(
            token_data6,
            x="borrowings",
            color="token",
            color_discrete_map={
                "DAI": "red",
                "ETH": "blue",
                "USDT": "purple",
                "USDC": "green",
                "wBTC": "orange",
            },
            title="Distribution of all Token Borrowings (Between 0 and 1)",
            nbins=100,
        ),
        True,
    )
