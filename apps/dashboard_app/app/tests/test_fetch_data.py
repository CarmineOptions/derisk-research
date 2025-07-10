import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from decimal import Decimal
import time
from typing import List, Optional, Any
from starknet_py.net.full_node_client import FullNodeClient
from starknet_py.hash.selector import get_selector_from_name
from dashboard_app.app.schemas.user_transaction import UserTransaction
from shared.constants import TOKEN_SETTINGS


from dashboard_app.app.services.fetch_data import (
    fetch_events_chunk,
    fetch_events,
    get_token_name_from_tx,
    process_trade_open,
    process_trade_close,
    get_events_by_hash,
)


@pytest.fixture
def mock_client() -> FullNodeClient:
    """Mock the FullNodeClient for testing"""
    return AsyncMock(spec=FullNodeClient)


@pytest.fixture
def sample_trade_open_event() -> MagicMock:
    """Mock a sample trade open event"""

    eth_address = int(TOKEN_SETTINGS["ETH"].address, 16)
    return MagicMock(
        transaction_hash="0xabc",
        block_number=1000,
        data=[0, eth_address, 500, 0],
        keys=[get_selector_from_name("TradeOpen")],
    )


@pytest.fixture
def sample_trade_close_event() -> MagicMock:
    """Mock a sample trade close event"""

    usdc_address = int(TOKEN_SETTINGS["USDC"].address, 16)
    return MagicMock(
        transaction_hash="0xdef",
        block_number=1001,
        data=[0, usdc_address, 300, 0],
        keys=[get_selector_from_name("TradeClose")],
    )


@pytest.mark.asyncio
async def test_fetch_events_chunk_success(mock_client: FullNodeClient) -> None:
    """Test successful event chunk fetching with pagination"""

    mock_response1 = MagicMock(
        events=["event1", "event2"], continuation_token="token123"
    )
    mock_response2 = MagicMock(events=["event3"], continuation_token=None)
    mock_client.get_events.side_effect = [mock_response1, mock_response2]

    with patch("app.services.fetch_data.client", mock_client):
        events: List[Any] = await fetch_events_chunk("0x123", 1000, 2000)
        assert len(events) == 3
        assert mock_client.get_events.call_count == 2

        assert events == ["event1", "event2", "event3"]


@pytest.mark.asyncio
async def test_fetch_events_chunk_no_continuation(mock_client: FullNodeClient) -> None:
    """Test event chunk fetching with no continuation token"""
    mock_response = MagicMock(events=["event1", "event2"], continuation_token=None)
    mock_client.get_events.return_value = mock_response

    with patch("app.services.fetch_data.client", mock_client):
        events: List[Any] = await fetch_events_chunk("0x123", 1000, 2000)
        assert len(events) == 2
        assert mock_client.get_events.call_count == 1


@pytest.mark.asyncio
async def test_fetch_events_concurrent(mock_client: FullNodeClient) -> None:
    """Test concurrent event fetching"""

    with patch(
        "app.services.fetch_data.fetch_events_chunk", new_callable=AsyncMock
    ) as mock_fetch:
        mock_fetch.side_effect = [["event1", "event2"], ["event3", "event4"], []]

        with patch("app.services.fetch_data.client", mock_client):
            events: List[Any] = await fetch_events(
                "0x123", 1000, 3000, concurrent_requests=3
            )

            assert len(events) == 4
            assert mock_fetch.call_count == 3

            assert sorted(events) == sorted(["event1", "event2", "event3", "event4"])


@pytest.mark.asyncio
async def test_fetch_events_single_block(mock_client: FullNodeClient) -> None:
    """Test handling of a single block range"""
    with patch(
        "app.services.fetch_data.fetch_events_chunk", new_callable=AsyncMock
    ) as mock_fetch:
        mock_fetch.return_value = ["event1"]

        with patch("app.services.fetch_data.client", mock_client):
            events: List[Any] = await fetch_events(
                "0x123", 1000, 1000, concurrent_requests=3
            )
            assert len(events) == 1

            assert mock_fetch.call_count == 1


@pytest.mark.asyncio
async def test_get_token_name_from_tx_found() -> None:
    """Test finding token in TOKEN_SETTINGS"""

    tx = MagicMock()
    eth_address = int(TOKEN_SETTINGS["ETH"].address, 16)
    tx.calldata = [0, eth_address]

    symbol: Optional[str]
    settings: Optional[Any]
    symbol, settings = await get_token_name_from_tx(tx)

    assert symbol == "ETH"
    assert settings.address == TOKEN_SETTINGS["ETH"].address
    assert settings.decimal_factor == Decimal("1e18")


@pytest.mark.asyncio
async def test_get_token_name_from_tx_not_found() -> None:
    """Test with an unknown token address"""
    tx = MagicMock()
    tx.calldata = [0, 0x999999]

    symbol: Optional[str]
    settings: Optional[Any]
    symbol, settings = await get_token_name_from_tx(tx)

    assert symbol is None
    assert settings is None


@pytest.mark.asyncio
async def test_process_trade_open_success(mock_client: FullNodeClient) -> None:
    """Test successful processing of a trade open event"""

    eth_address = int(TOKEN_SETTINGS["ETH"].address, 16)
    event = MagicMock(
        transaction_hash="0xabcdef123",
        block_number=1000,
        data=[0, eth_address, 1000000000000000000, 0],
        keys=[get_selector_from_name("TradeOpen")],
    )

    mock_tx = MagicMock(sender_address="0xuser123")
    mock_tx.calldata = [0, eth_address]

    mock_block = MagicMock(timestamp=1714500000)

    mock_client.get_transaction.return_value = mock_tx
    mock_client.get_block.return_value = mock_block

    with patch("app.services.fetch_data.client", mock_client):
        result: Optional[UserTransaction] = await process_trade_open(event)

        assert result is not None
        assert result.user_address == "0xuser123"
        assert result.token == "ETH"
        assert result.price == "price --"
        assert result.amount == Decimal("1")

        mock_client.get_transaction.assert_called_once_with(event.transaction_hash)
        mock_client.get_block.assert_called_once_with(block_number=event.block_number)


@pytest.mark.asyncio
async def test_process_trade_close_success(mock_client: FullNodeClient) -> None:
    """Test successful processing of a trade close event"""
    usdc_address = int(TOKEN_SETTINGS["USDC"].address, 16)
    event = MagicMock(
        transaction_hash="0xdef456789",
        block_number=1001,
        data=[0, usdc_address, 1000000, 0],
        keys=[get_selector_from_name("TradeClose")],
    )

    mock_tx = MagicMock(sender_address="0xuser456")
    mock_tx.calldata = [0, usdc_address]

    mock_block = MagicMock(timestamp=1714586400)

    mock_client.get_transaction.return_value = mock_tx
    mock_client.get_block.return_value = mock_block

    with patch("app.services.fetch_data.client", mock_client):
        result: Optional[UserTransaction] = await process_trade_close(event)

        assert result is not None
        assert result.user_address == "0xuser456"
        assert result.token == "USDC"
        assert result.price == "price --"
        assert result.amount == Decimal("1")

        mock_client.get_transaction.assert_called_once_with(event.transaction_hash)
        mock_client.get_block.assert_called_once_with(block_number=event.block_number)


@pytest.mark.asyncio
async def test_get_events_by_hash(
    mock_client: FullNodeClient,
    sample_trade_open_event: MagicMock,
    sample_trade_close_event: MagicMock,
) -> None:
    """Test main function that processes all events"""

    with patch(
        "app.services.fetch_data.fetch_events", new_callable=AsyncMock
    ) as mock_fetch:
        mock_fetch.return_value = [sample_trade_open_event, sample_trade_close_event]

        with patch(
            "app.services.fetch_data.process_trade_open", new_callable=AsyncMock
        ) as mock_open:
            with patch(
                "app.services.fetch_data.process_trade_close", new_callable=AsyncMock
            ) as mock_close:
                mock_open.return_value = UserTransaction(
                    user_address="0x1",
                    token="ETH",
                    amount=Decimal("100"),
                    is_sold=True,
                    price="price --",
                    timestamp="2025-04-27 12:00:00",
                )
                mock_close.return_value = UserTransaction(
                    user_address="0x2",
                    token="ETH",
                    amount=Decimal("50"),
                    is_sold=False,
                    price="price --",
                    timestamp="2025-04-27 12:00:00",
                )

                with patch("app.services.fetch_data.client", mock_client):
                    opens: List[UserTransaction]
                    closes: List[UserTransaction]
                    opens, closes = await get_events_by_hash()

                    assert len(opens) == 1
                    assert len(closes) == 1
                    assert opens[0].is_sold is True
                    assert closes[0].is_sold is False

                    mock_open.assert_called_once_with(sample_trade_open_event)

                    mock_close.assert_called_once_with(sample_trade_close_event)


@pytest.mark.asyncio
async def test_get_events_by_hash_mixed_events(mock_client: FullNodeClient) -> None:
    """Test handling of various event types including unknown ones"""
    open_event = MagicMock(keys=[get_selector_from_name("TradeOpen")])
    close_event = MagicMock(keys=[get_selector_from_name("TradeClose")])
    unknown_event = MagicMock(keys=[123456])

    with patch(
        "app.services.fetch_data.fetch_events", new_callable=AsyncMock
    ) as mock_fetch:
        mock_fetch.return_value = [open_event, close_event, unknown_event]

        with patch(
            "app.services.fetch_data.process_trade_open", new_callable=AsyncMock
        ) as mock_open:
            with patch(
                "app.services.fetch_data.process_trade_close", new_callable=AsyncMock
            ) as mock_close:
                mock_open.return_value = UserTransaction(
                    user_address="0x1",
                    token="ETH",
                    amount=Decimal("100"),
                    is_sold=True,
                    price="price --",
                    timestamp="2025-04-27 12:00:00",
                )
                mock_close.return_value = UserTransaction(
                    user_address="0x2",
                    token="ETH",
                    amount=Decimal("50"),
                    is_sold=False,
                    price="price --",
                    timestamp="2025-04-27 12:00:00",
                )

                with patch("app.services.fetch_data.client", mock_client):
                    opens: List[UserTransaction]
                    closes: List[UserTransaction]
                    opens, closes = await get_events_by_hash()

                    assert len(opens) == 1
                    assert len(closes) == 1
                    mock_open.assert_called_once_with(open_event)
                    mock_close.assert_called_once_with(close_event)


@pytest.mark.asyncio
async def test_fetch_events_empty_range(mock_client: FullNodeClient) -> None:
    """Test empty block range handling"""
    with patch(
        "app.services.fetch_data.fetch_events_chunk", new_callable=AsyncMock
    ) as mock_fetch:
        mock_fetch.return_value = []

        with patch("app.services.fetch_data.client", mock_client):
            events: List[Any] = await fetch_events("0x123", 2000, 1000)
            assert len(events) == 0

            assert mock_fetch.call_count == 0


@pytest.mark.asyncio
async def test_process_trade_invalid_token(mock_client: FullNodeClient) -> None:
    """Test handling of unknown token with TOKEN_SETTINGS"""
    event = MagicMock(
        transaction_hash="0xunknown",
        block_number=1000,
        data=[0, 0x999999, 100, 0],
        keys=[get_selector_from_name("TradeOpen")],
    )

    mock_tx = MagicMock()
    mock_tx.calldata = [0, 0x999999]
    mock_client.get_transaction.return_value = mock_tx

    with patch("app.services.fetch_data.client", mock_client):
        result: Optional[UserTransaction] = await process_trade_open(event)
        assert result is None


@pytest.mark.asyncio
async def test_process_trade_missing_data(mock_client: FullNodeClient) -> None:
    """Test handling of malformed event data"""
    bad_event = MagicMock(data=[], keys=[])

    with patch("app.services.fetch_data.client", mock_client):
        result: Optional[UserTransaction] = await process_trade_open(bad_event)
        assert result is None


@pytest.mark.asyncio
async def test_process_trade_key_error(mock_client: FullNodeClient) -> None:
    """Test handling KeyError during processing"""
    event = MagicMock(
        transaction_hash="0xabc",
        block_number=1000,
        data=[],
    )

    mock_tx = MagicMock(sender_address="0xuser")
    mock_client.get_transaction.return_value = mock_tx

    with patch("app.services.fetch_data.client", mock_client):
        result: Optional[UserTransaction] = await process_trade_open(event)
        assert result is None


@pytest.mark.asyncio
async def test_network_failure_transaction(mock_client: FullNodeClient) -> None:
    """Test error handling when get_transaction fails"""
    event = MagicMock(
        transaction_hash="0xabc",
        block_number=1000,
        data=[0, int(TOKEN_SETTINGS["ETH"].address, 16), 100, 0],
    )

    mock_client.get_transaction.side_effect = Exception("Network error")

    with patch("app.services.fetch_data.client", mock_client):
        result: Optional[UserTransaction] = await process_trade_open(event)
        assert result is None


@pytest.mark.asyncio
async def test_network_failure_events(mock_client: FullNodeClient) -> None:
    """Test network error handling for events"""
    mock_client.get_events.side_effect = Exception("Network error")

    with patch("app.services.fetch_data.client", mock_client):
        with pytest.raises(Exception):
            await fetch_events_chunk("0x123", 1000, 2000)


@pytest.mark.asyncio
async def test_amount_calculation_large(mock_client: FullNodeClient) -> None:
    """Test proper amount calculation with large numbers using real TOKEN_SETTINGS"""
    eth_address = int(TOKEN_SETTINGS["ETH"].address, 16)
    event = MagicMock(
        transaction_hash="0xbig",
        block_number=1000,
        data=[
            0,
            eth_address,
            0xFFFFFFFF,
            0x1,
        ],
        keys=[get_selector_from_name("TradeOpen")],
    )

    mock_tx = MagicMock(sender_address="0xuser")
    mock_tx.calldata = [0, eth_address]
    mock_block = MagicMock(timestamp=time.time())
    mock_client.get_transaction.return_value = mock_tx
    mock_client.get_block.return_value = mock_block

    with patch("app.services.fetch_data.client", mock_client):
        result: Optional[UserTransaction] = await process_trade_open(event)

        expected_amount: Decimal = Decimal((1 << 128) + 0xFFFFFFFF) / Decimal("1e18")
        assert result is not None
        assert result.amount >= expected_amount


@pytest.mark.asyncio
async def test_empty_event_processing(mock_client: FullNodeClient) -> None:
    """Test handling of empty event list"""
    with patch(
        "app.services.fetch_data.fetch_events", new_callable=AsyncMock
    ) as mock_fetch:
        mock_fetch.return_value = []
        with patch("app.services.fetch_data.client", mock_client):
            opens: List[UserTransaction]
            closes: List[UserTransaction]
            opens, closes = await get_events_by_hash()
            assert len(opens) == 0
            assert len(closes) == 0


@pytest.mark.asyncio
async def test_all_tokens_can_be_processed() -> None:
    """Test that all tokens in TOKEN_SETTINGS can be properly processed"""
    for token_symbol, token_setting in TOKEN_SETTINGS.items():
        if token_symbol == "DAI":
            continue

        tx = MagicMock()
        token_address = int(token_setting.address, 16)
        tx.calldata = [0, token_address]

        symbol: Optional[str]
        settings: Optional[Any]
        symbol, settings = await get_token_name_from_tx(tx)

        assert symbol == token_symbol
        assert settings.address == token_setting.address
        assert settings.decimal_factor == token_setting.decimal_factor
