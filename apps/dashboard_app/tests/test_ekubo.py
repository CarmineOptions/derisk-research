from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

pytest.importorskip("helper")
from helpers.ekubo import EkuboLiquidity


@pytest.fixture
def sample_data():
    """Fixture to initialize sample Dataframe."""
    return pd.DataFrame(
        {
            "price": [1.0, 1.1, 1.2],
            "debt_token_supply": [100, 200, 300],
            "collateral_token_price": [1.0, 1.1, 1.2],
            "Ekubo_debt_token_supply": [10, 20, 30],
        }
    )


@pytest.fixture
def liquidity_instance(sample_data):
    """Fixture for initializing EkuboLiquidity instance."""
    return EkuboLiquidity(
        data=sample_data,
        collateral_token="0x0000000000000000000000000000000000000001",
        debt_token="0x0000000000000000000000000000000000000002",
    )


@patch("requests.get")
def test_fetch_liquidity_bids(mock_get, liquidity_instance):
    """Test fetch_liquidity() correctly parses API response for bids."""
    mock_get.return_value.ok = True
    mock_get.return_value.json.return_value = {
        "bids": [[1.0, 50.0], [1.1, 40.0], [1.2, 30.0]]
    }

    result = liquidity_instance.fetch_liquidity(bids=True)

    assert result["type"] == "bids"
    assert result["prices"] == (1.0, 1.1, 1.2)
    assert result["quantities"] == (50.0, 40.0, 30.0)


@patch("requests.get")
def test_fetch_liquidity_asks(mock_get, liquidity_instance):
    """Test fetch_liquidity() correctly parses API response for asks."""
    mock_get.return_value.ok = True
    mock_get.return_value.json.return_value = {
        "asks": [[1.0, 20.0], [1.1, 15.0], [1.2, 10.0]]
    }

    result = liquidity_instance.fetch_liquidity(bids=False)

    assert result["type"] == "asks"
    assert result["prices"] == (1.0, 1.1, 1.2)
    assert result["quantities"] == (20.0, 15.0, 10.0)


def test_apply_liquidity_to_dataframe(liquidity_instance):
    """Test apply_liquidity_to_dataframe updates DataFrame correctly."""
    mock_bids_or_asks = {
        "type": "bids",
        "prices": [1.0, 1.1, 1.2],
        "quantities": [50.0, 40.0, 30.0],
    }

    updated_df = liquidity_instance.apply_liquidity_to_dataframe(mock_bids_or_asks)

    assert "Ekubo_debt_token_supply" in updated_df.columns
    assert "debt_token_supply" in updated_df.columns
    assert updated_df["debt_token_supply"].iloc[0] >= 100  # Supply should increase


def test_remove_leading_zeros():
    """Test _remove_leading_zeros correctly removes extra zeros."""
    assert (
        EkuboLiquidity._remove_leading_zeros(
            "0x0000000000000000000000000000000000001234"
        )
        == "0x1234"
    )
    assert (
        EkuboLiquidity._remove_leading_zeros(
            "0x000000000000000000000000000000000000abcd"
        )
        == "0xabcd"
    )


def test_get_available_liquidity(liquidity_instance):
    """Test _get_available_liquidity retrieves correct sum of liquidity."""
    data = pd.DataFrame({"price": [1.0, 1.1, 1.2], "quantity": [50.0, 40.0, 30.0]})
    result = liquidity_instance._get_available_liquidity(
        data, price=1.05, price_diff=0.1, bids=True
    )

    assert result == 50.0  # Only one price in range [0.95, 1.05]


@patch("requests.get")
def test_fetch_liquidity_fails(mock_get, liquidity_instance):
    """Test fetch_liquidity handles API failures gracefully."""
    mock_get.return_value.ok = False  # Simulate API failure

    with patch("time.sleep") as mock_sleep:
        result = liquidity_instance.fetch_liquidity(bids=True)
        mock_sleep.assert_called()  # Ensure sleep is triggered on failure

    assert result is None  # Should return None on failure
