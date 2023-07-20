# Imports
import decimal
import copy
from typing import Dict
import collections

import numpy as np
import matplotlib.pyplot as plt 
import seaborn as sns
import pandas
import plotly.express as px
import streamlit as st

import db
import classes
import constants

from compute import (
    decimal_range,
    update_graph_data,
)
from get_data import get_events
from persistent_state import load_persistent_state

# SESSION STATE
if "parameters" not in st.session_state:
    st.session_state["parameters"] = {
        "COLLATERAL_TOKEN": "ETH",
        "BORROWINGS_TOKEN": "USDC",
        "COLLATERAL_TOKEN_PRICE": decimal.Decimal("1500"),
        "X_AXIS_DESC": "collateral_token_price_multiplier",
        "Y_AXIS_DESC": "max_borrowings_to_be_liquidated",
    }

if "prices" not in st.session_state:
    st.session_state["prices"] = classes.Prices()

if "data" not in st.session_state:
    st.session_state["data"] = pandas.DataFrame(
        {
            st.session_state.parameters["X_AXIS_DESC"]: [
                x
                for x in decimal_range(
                    # TODO: make it dependent on the collateral token .. use prices.prices[COLLATERAL_TOKEN]
                    start=decimal.Decimal("1000"),
                    stop=decimal.Decimal("3000"),
                    # TODO: make it dependent on the collateral token
                    step=decimal.Decimal("50"),
                )
            ]
        },
    )

load_persistent_state()

if "latest_block" not in st.session_state:
    st.session_state["latest_block"] = 0
if "state" not in st.session_state:
    st.session_state["state"] = classes.State()


def bench(msg, start):
    print(f"{msg} {round(time.time() - start, 2)}s")


async def hide_message(msg):
    await asyncio.sleep(10)
    msg.empty()


def main():
    st.title("DeRisk")

    def update_state():
        print("Updating...")
        t0 = time.time()
        # get new events
        events = get_events()
        bench("got events in", t0)
        t1 = time.time()
        for _, event in events.iterrows():
            st.session_state.state.process_event(event=event)
        bench("updated state in", t1)
        t2 = time.time()
        update_graph_data()
        bench("updated graph data in", t2)
        bench("entire update took", t0)

    if st.button("Update"):
        with st.spinner("Processing..."):
            update_state()
        msg = st.success("Updated!")
        asyncio.run(hide_message(msg))

    if "max_borrowings_to_be_liquidated_at_interval" in st.session_state.data:
        figure = plotly.express.bar(
            st.session_state.data.astype(float),
            x = 'collateral_token_price',
            y = {'max_borrowings_to_be_liquidated_at_interval': 'New Liquidatable Amount', 
                'amm_borrowings_token_supply': 'Borrowing Token Supply'
                },
            title = f'Projected Liquidatable Amounts of {st.session_state["parameters"]["BORROWINGS_TOKEN"]} and the Corresponding Supply',
            barmode = 'overlay',
            opacity = 0.65,
        )
        st.plotly_chart(figure)


if __name__ == "__main__":
    st.set_page_config(
        layout="wide",
        page_title="DeRisk by Carmine Finance",
        page_icon="https://carmine.finance/assets/logo.svg",
    )

    main()


# ZKLend Events Data 
connection = db.establish_connection()

# Load all Zklend events.
zklend_events = pandas.read_sql(
    sql = 
    f"""
    SELECT
        *
    FROM
        starkscan_events
    WHERE
        from_address='{constants.Protocol.ZKLEND.value}'
    AND
        key_name IN ('Deposit', 'Withdrawal', 'CollateralEnabled', 'CollateralDisabled', 'Borrowing', 'Repayment', 'Liquidation', 'AccumulatorsSync')
    ORDER BY
        block_number ASC, id;
    """,
    con = connection,
)

# Close the connection.
connection.close()

zklend_events.set_index('id', inplace = True)

from classes import State, Prices #just importing classes didn't work for some reason 

state = State() 
prices = Prices()
for _, event in zklend_events.iterrows():
    state.process_event(event = event)
    

tmp = [
    {'token': token, 'borrowings': user_state.token_states[token].borrowings * prices.prices[token] / 10**constants.get_decimals(token)}
    for user_state in state.user_states.values()
    for token in constants.symbol_decimals_map.keys()
]

#token_dataa = pandas.DataFrame(tmp)
#token_dataa['borrowings'] = token_dataa['borrowings'].astype(float)


token_data = pandas.DataFrame(tmp)
token_data['borrowings'] = token_data['borrowings'].astype(float)
token_data = token_data[token_data['borrowings'] > 500]
st.write(px.histogram(token_data, x='borrowings', color='token', color_discrete_map= {
    "DAI": "red",
    "ETH": "blue", 
    "USDT": "purple",
    "USDC": "green",
    "wBTC": "orange",
    }, title='Distribution of all Token Borrowings (Greater than 500)', nbins= 100))

# Comparative Token Distribution (greater than 100)
token_data2 = pandas.DataFrame(tmp)
token_data2['borrowings'] = token_data2['borrowings'].astype(float)
token_data2 = token_data2[token_data2['borrowings'] > 100]
st.write(px.histogram(token_data2, x='borrowings', color='token', color_discrete_map= {
    "DAI": "red",
    "ETH": "blue", 
    "USDT": "purple",
    "USDC": "green",
    "wBTC": "orange",
    }, title='Distribution of all Token Borrowings (Greater than 100)', nbins= 100))
#st.write(fig.update_xaxes(range = [100, 12000]))


# Comparative Token Distribution (between 1 and 500)
token_data3 = pandas.DataFrame(tmp)
token_data3['borrowings'] = token_data3['borrowings'].astype(float)
token_data3 = token_data3[token_data3['borrowings'] < 500]
token_data3= token_data3[token_data3['borrowings'] > 1]
st.write(px.histogram(token_data3, x='borrowings', color='token', color_discrete_map= {
    "DAI": "red",
    "ETH": "blue", 
    "USDT": "purple",
    "USDC": "green",
    "wBTC": "orange",
    }, title='Distribution of all Token Borrowings (Between 1 and 500)', nbins = 100))



# Comparative Token Distribution (between 100 and 500)
token_data4 = pandas.DataFrame(tmp)
token_data4['borrowings'] = token_data4['borrowings'].astype(float)
token_data4 = token_data4[token_data4['borrowings'] < 500] 
token_data4 = token_data4[token_data4['borrowings'] > 100]
st.write(px.histogram(token_data4, x='borrowings', color='token', color_discrete_map= {
    "DAI": "red",
    "ETH": "blue", 
    "USDT": "purple",
    "USDC": "green",
    "wBTC": "orange",
    }, title='Distribution of all Token Borrowings (Between 100 and 500)', nbins =100))


# Comparative Token Distribution (between 1 and 100) 
token_data5 = pandas.DataFrame(tmp)
token_data5['borrowings'] = token_data5['borrowings'].astype(float)
token_data5 = token_data5[token_data5['borrowings'] < 100] 
token_data5 = token_data5[token_data5['borrowings'] > 1] 
st.write(px.histogram(token_data5, x='borrowings', color='token', color_discrete_map= {
    "DAI": "red",
    "ETH": "blue", 
    "USDT": "purple",
    "USDC": "green",
    "wBTC": "orange",
    }, title='Distribution of all Token Borrowings (Between 1 and 100)', nbins = 100))


# Comparative Token Distribution (between 0 and 1)
token_data6 = pandas.DataFrame(tmp)
token_data6['borrowings'] = token_data6['borrowings'].astype(float)
token_data6 = token_data6[token_data6['borrowings'] < 1] 
token_data6 = token_data6[token_data6['borrowings'] > 0] 
st.write(px.histogram(token_data6, x='borrowings', color='token', color_discrete_map= {
    "DAI": "red",
    "ETH": "blue", 
    "USDT": "purple",
    "USDC": "green",
    "wBTC": "orange",
    }, title='Distribution of all Token Borrowings (Between 0 and 1)', nbins = 100))


