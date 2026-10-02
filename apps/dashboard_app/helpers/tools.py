import requests
import streamlit as st
from typing import List, Dict, Any

def get_prices(tokens: List[str]) -> Dict[str, Any]:
    """
    Fetch USD prices for a list of tokens.
    Handles timeouts and other request errors gracefully with Streamlit warnings.
    """
    if not tokens:
        return {}

    # Build request URL - keep original logic
    ids = ",".join(tokens)
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={ids}&vs_currencies=usd"

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.Timeout:
        st.warning("The price service is temporarily unavailable. Please try again later.")
        return {}
    except requests.exceptions.RequestException as e:
        st.warning(f"Unable to fetch prices at the moment. Please try again later.")
        return {}

    prices = {}
    for token in tokens:
        if token in data and "usd" in data[token]:
            prices[token] = data[token]["usd"]
        else:
            prices[token] = None
    return prices
