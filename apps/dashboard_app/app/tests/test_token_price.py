import sys
from pathlib import Path

# sys.path.append(Path().resolve().parent.absolute().as_posix())
# print(sys.path)
from unittest.mock import AsyncMock, Mock, call, patch
from hashlib import md5
from shared.constants import TOKEN_SETTINGS
from app.core.config import settings
from datetime import datetime
import pytest
import string
import random
from app.services.token_price import price_history_manager


@pytest.mark.asyncio
async def test_get_token_price():
    mock_token_price = 123
    with patch(
        "app.services.token_price.api_request",
        new=AsyncMock(return_value={"current_price": {"usd": mock_token_price}}),
    ) as api_request_mock:
        coin_id = "".join(random.sample(string.ascii_uppercase, 3))
        date = datetime.now().strftime("%d-%m-%Y")
        res = await price_history_manager.get_token_price(coin_id, date)
        assert res == mock_token_price
        expected_url = (
            f"{settings.coingecko_api_url}/coins/{coin_id}/history?date={date}"
        )
        expected_headers = {
            "accept": "application/json",
            "x-cg-api-key": settings.coingecko_api_key,
        }

        api_request_mock.assert_awaited_once_with(
            url=expected_url,
            headers=expected_headers,
            key="market_data",
        )


@pytest.mark.asyncio
async def test_get_all_prices():
    def get_token_price_side_effect(coin_id, date):
        return md5((str(coin_id) + str(date)).encode()).hexdigest()

    with patch.object(
        price_history_manager,
        "get_token_price",
        new=AsyncMock(side_effect=get_token_price_side_effect),
    ) as get_token_price_mock:
        date = datetime.now().strftime("%d-%m-%Y")
        expected_prices = {
            token.symbol: get_token_price_side_effect(token.coin_id, date)
            for token in TOKEN_SETTINGS.values()
        }
        res = await price_history_manager.get_all_prices(date)
        assert res == expected_prices
        get_token_price_mock.assert_has_awaits(
            [call(token.coin_id, date) for token in TOKEN_SETTINGS.values()]
        )
