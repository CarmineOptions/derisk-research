from dashboard_app.app.utils.api_request import api_request
from shared.constants import TOKEN_SETTINGS
from dashboard_app.core.config import settings

headers = {
    "accept": "application/json",
    "x-cg-api-key": settings.coingecko_api_key
}

async def get_all_prices(date: str):
    prices = dict()
    for token in TOKEN_SETTINGS:
        prices[f'{token.symbol}'] = await get_token_price(coin_id=token.coind_id, date=date)

    return prices


async def get_token_price(coin_id: str, date: str):
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/history?date={date}"
    return (await api_request(url=url, headers = headers, key='market_data')).get("current_price").get("usd")

