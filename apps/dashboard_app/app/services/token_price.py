from dashboard_app.app.utils.api_request import api_request
from shared.constants import TOKEN_SETTINGS
from dashboard_app.core.config import settings

headers = {
    "accept": "application/json",
    "x-cg-api-key": settings.coingecko_api_key
}

async def get_all_prices(date: str):
    """
    Fetches the historical prices of all tokens for a given date.
    This asynchronous function iterates through the tokens defined in `TOKEN_SETTINGS`
    and retrieves their prices for the specified date using the `get_token_price` function.
    Args:
        date (str): The date for which to fetch token prices, formatted as 'YYYY-MM-DD'.
    Returns:
        dict: A dictionary where the keys are token symbols and the values are their respective prices.
    """

    prices = dict()
    for token in TOKEN_SETTINGS:
        prices[f'{token.symbol}'] = await get_token_price(coin_id=token.coind_id, date=date)

    return prices


async def get_token_price(coin_id: str, date: str):
    """
    Fetches the historical price of a cryptocurrency in USD for a specific date.
    Args:
        coin_id (str): The unique identifier of the cryptocurrency (e.g., 'bitcoin', 'ethereum').
        date (str): The date for which the price is requested, in the format 'dd-mm-yyyy'.
    Returns:
        float: The price of the cryptocurrency in USD on the specified date.
    Raises:
        Exception: If the API request fails or the response does not contain the expected data.
    """

    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/history?date={date}"
    return (await api_request(url=url, headers = headers, key='market_data')).get("current_price").get("usd")

