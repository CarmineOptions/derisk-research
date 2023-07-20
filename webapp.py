import asyncio
import decimal
import time
import pandas
import streamlit as st
import plotly.express as px

import classes
import db
import constants
from compute import (
    decimal_range,
    update_graph_data,
)

def visualization(): 
    state = st.session_state['state'] 
    prices = st.session_state['prices']
    
    tmp = [
        {'token': token, 'borrowings': user_state.token_states[token].borrowings * prices.prices[token] / 10**constants.get_decimals(token)}
        for user_state in state.user_states.values()
        for token in constants.symbol_decimals_map.keys()
        if token[0] is not "z"
    ]



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

