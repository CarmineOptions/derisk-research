import pandas
import constants
import streamlit as st
import plotly.express as px

def visualization():
    st.header('Hashstack')
    values = st.slider('Select a range of borrowing values:', 0.0, 16000.0, (1.0, 100.0))
    st.write('Borrowings Range:', values)
    
    state = st.session_state["state"]
    prices = st.session_state["prices"]

    tmp = [
        {
            "token": token,
            "borrowings": user_state.token_states[token].borrowings
            * prices.prices[token]
            / 10 ** constants.get_decimals(token),
        }
        for user_state in state.user_states.values()
        for token in constants.symbol_decimals_map.keys()
        if token[0] != "z"
    ]

    token_data = pandas.DataFrame(tmp)
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