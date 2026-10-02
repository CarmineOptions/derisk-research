from unittest.mock import MagicMock, patch
import pytest
import asyncio
import orjson as json

from apps.dashboard_app.state import DashboardState


@pytest.fixture
def state():
    return DashboardState()


@pytest.fixture
def mock_redis():
    return MagicMock()


def test_get_liquidable_debt_from_redis(state, mock_redis):
    """Test reading liquidable debt from Redis."""
    test_data = [
        {"user": "0x123", "is_liquidable": True, "collateral": "1000", "debt": "500"}
    ]
    mock_redis.get.return_value = json.dumps(test_data)

    with patch.object(state, '_get_redis', return_value=mock_redis):
        result = state.get_liquidable_debt_from_redis()
        assert len(result) == 1
        assert result[0]["is_liquidable"] is True


def test_get_collateral_price_from_redis(state, mock_redis):
    """Test reading collateral price from Redis."""
    mock_redis.get.return_value = b"1234.56"

    with patch.object(state, '_get_redis', return_value=mock_redis):
        result = state.get_collateral_price_from_redis()
        assert result == 1234.56


def test_get_debt_price_from_redis(state, mock_redis):
    """Test reading debt price from Redis."""
    mock_redis.get.return_value = b"1.00"

    with patch.object(state, '_get_redis', return_value=mock_redis):
        result = state.get_debt_price_from_redis()
        assert result == 1.00


def test_streamlit_dev_fill_with_test_data(state, mock_redis):
    """Test filling Redis with test data."""
    test_data = {
        "liquidable_debt": [{"user": "0x123", "is_liquidable": True}],
        "collateral_token_price": 1234.56,
        "debt_token_price": 1.00,
    }

    with patch.object(state, '_get_redis', return_value=mock_redis):
        state.streamlit_dev_fill_with_test_data(test_data)
        assert mock_redis.set.call_count == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
