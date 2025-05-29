from datetime import date
from app.utils.api_request import api_request
from shared.constants import TOKEN_SETTINGS
from app.core.config import settings


class PriceHistoryManager:
    def __init__(self):
        """
        Initializes the TokenPrice service with necessary headers and base URL for API requests.
        Attributes:
            headers (dict): HTTP headers for the API requests, including the API key and content type.
            base_url (str): The base URL for the CoinGecko API, retrieved from the application settings.
        """
        self.headers = {
            "accept": "application/json",
            "x-cg-api-key": settings.coingecko_api_key,
        }
        self.base_url = settings.coingecko_api_url

    async def get_all_prices(self, date_obj: date):
        """
        Fetches the historical prices of all tokens for a given date.
        This asynchronous function iterates through the tokens defined in `TOKEN_SETTINGS`
        and retrieves their prices for the specified date using the `get_token_price` function.
        Args:
            date_obj (date): The date for which to fetch token prices.
        Returns:
            dict: A dictionary where the keys are token symbols and the values are their respective prices.
        """
        prices = {}
        for token in TOKEN_SETTINGS.values():
            prices[token.symbol] = await self.get_token_price(token.coin_id, date_obj)

        return prices

    async def get_token_price(self, coin_id: str, date_obj: date):
        """
        Fetches the historical price of a cryptocurrency in USD for a specific date.
        Args:
            coin_id (str): The unique identifier of the cryptocurrency (e.g., 'bitcoin', 'ethereum').
            date_obj (date): The date for which the price is requested.
        Returns:
            float: The price of the cryptocurrency in USD on the specified date.
        Raises:
            Exception: If the API request fails or the response does not contain the expected data.
        """
        # Format date as required by CoinGecko API (dd-mm-yyyy)
        formatted_date = date_obj.strftime("%d-%m-%Y")
        url = f"{self.base_url}/coins/{coin_id}/history?date={formatted_date}"
        return (
            (await api_request(url=url, headers=self.headers, key="market_data"))
            .get("current_price")
            .get("usd")
        )


price_history_manager = PriceHistoryManager()
