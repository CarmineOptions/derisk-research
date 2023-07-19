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

token_data = pandas.DataFrame(tmp)
token_data['borrowings'] = token_data['borrowings'].astype(float)
token_data = token_data[token_data['borrowings'] > 500]
fig = st.write(px.histogram(token_data, x='borrowings', color='token', color_discrete_map= {
    "DAI": "red",
    "ETH": "blue", 
    "USDT": "purple",
    "USDC": "green",
    "wBTC": "orange",
    }, title='Distribution of all Token Borrowings (greater than 500)', nbins= 100))
#st.write(fig.update_xaxes(range = [500, 12000]))
st.write(fig.show())


# Comparative Token Distribution (greater than 100)
token_data2 = pandas.DataFrame(tmp)
token_data2['borrowings'] = token_data2['borrowings'].astype(float)
token_data2 = token_data2[token_data2['borrowings'] > 100]
fig = st.write(px.histogram(token_data2, x='borrowings', color='token', color_discrete_map= {
    "DAI": "red",
    "ETH": "blue", 
    "USDT": "purple",
    "USDC": "green",
    "wBTC": "orange",
    }, title='Distribution of all Token Borrowings (greater than 100)', nbins= 100))
#st.write(fig.update_xaxes(range = [100, 12000]))
st.write(fig.show())

# Comparative Token Distribution (between 1 and 500)
token_data3 = pandas.DataFrame(tmp)
token_data3['borrowings'] = token_data3['borrowings'].astype(float)
token_data3 = token_data3[token_data3['borrowings'] < 500]
token_data3= token_data3[token_data3['borrowings'] > 1]
fig = st.write(px.histogram(token_data3, x='borrowings', color='token', color_discrete_map= {
    "DAI": "red",
    "ETH": "blue", 
    "USDT": "purple",
    "USDC": "green",
    "wBTC": "orange",
    }, title='Distribution of all Token Borrowings (between 1 and 500)', nbins = 100))
st.write(fig.show())


# Comparative Token Distribution (between 100 and 500)
token_data4 = pandas.DataFrame(tmp)
token_data4['borrowings'] = token_data4['borrowings'].astype(float)
token_data4 = token_data4[token_data4['borrowings'] < 500] 
token_data4 = token_data4[token_data4['borrowings'] > 100]
fig = st.write(px.histogram(token_data4, x='borrowings', color='token', color_discrete_map= {
    "DAI": "red",
    "ETH": "blue", 
    "USDT": "purple",
    "USDC": "green",
    "wBTC": "orange",
    }, title='Distribution of all Token Borrowings (between 100 and 500)', nbins =100))
st.write(fig.show())

# Comparative Token Distribution (between 1 and 100) 
token_data5 = pandas.DataFrame(tmp)
token_data5['borrowings'] = token_data5['borrowings'].astype(float)
token_data5 = token_data5[token_data5['borrowings'] < 100] 
token_data5 = token_data5[token_data5['borrowings'] > 1] 
fig = st.write(px.histogram(token_data5, x='borrowings', color='token', color_discrete_map= {
    "DAI": "red",
    "ETH": "blue", 
    "USDT": "purple",
    "USDC": "green",
    "wBTC": "orange",
    }, title='Distribution of all Token Borrowings (between 1 and 100)', nbins = 100))
st.write(fig.show())

# Comparative Token Distribution (between 0 and 1)
token_data6 = pandas.DataFrame(tmp)
token_data6['borrowings'] = token_data6['borrowings'].astype(float)
token_data6 = token_data6[token_data6['borrowings'] < 1] 
token_data6 = token_data6[token_data6['borrowings'] > 0] 
fig = st.write(px.histogram(token_data6, x='borrowings', color='token', color_discrete_map= {
    "DAI": "red",
    "ETH": "blue", 
    "USDT": "purple",
    "USDC": "green",
    "wBTC": "orange",
    }, title='Distribution of all Token Borrowings (between 0 and 1)', nbins = 100))
st.write(fig.show())

