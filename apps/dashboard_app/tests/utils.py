"""
Tests for charts utils functions in dashboard_app.
"""

# pylint: disable=wrong-import-position, too-few-public-methods
import pandas as pd
import pytest

from dashboard_app.charts.utils import (
    get_data,
    get_protocol_data_mappings,
    transform_loans_data,
)


class DummyState:
    """Dummy state for testing purposes."""

    # No additional implementation required.


# -------------------------------
# Tests for get_data
# -------------------------------


def test_get_data_positive(monkeypatch):
    """
    Test get_data returns main chart data and loans data for a valid protocol.
    """
    state = DummyState()

    def dummy_get_prices(token_decimals):
        # Return a dummy price (100) for each token address.
        return {key: 100 for key in token_decimals}

    def dummy_get_main_chart_data(*_args, **_kwargs):
        # Return a dummy DataFrame for main chart data.
        return pd.DataFrame({"col": [1, 2, 3]})

    def dummy_get_loans_table_data(*_args, **_kwargs):
        # Return a dummy DataFrame for loans data.
        return pd.DataFrame(
            {
                "Collateral": ["TokenA: 1", "TokenB: 2"],
                "Debt": ["TokenA: 0.5", "TokenB: 1"],
            }
        )

    async def dummy_get_balance(_self):
        return None

    monkeypatch.setattr("apps.dashboard_app.charts.utils.get_prices", dummy_get_prices)
    monkeypatch.setattr(
        "apps.dashboard_app.charts.utils.get_main_chart_data", dummy_get_main_chart_data
    )
    monkeypatch.setattr(
        "apps.dashboard_app.charts.utils.get_loans_table_data",
        dummy_get_loans_table_data,
    )
    monkeypatch.setattr(
        "apps.dashboard_app.charts.utils.SwapAmm.get_balance", dummy_get_balance
    )

    main_chart_data, loans_data = get_data("DummyProtocol", state)

    assert isinstance(main_chart_data, dict)
    assert isinstance(loans_data, pd.DataFrame)
    # Verify that each value in main_chart_data is a DataFrame.
    for df in main_chart_data.values():
        assert isinstance(df, pd.DataFrame)


def test_get_data_negative(monkeypatch):
    """
    Test get_data handles errors properly when get_main_chart_data raises an exception.
    """
    state = DummyState()

    def dummy_get_prices(token_decimals):
        return {key: 100 for key in token_decimals}

    def dummy_get_main_chart_data(*_args, **_kwargs):
        raise ValueError("Dummy error")

    def dummy_get_loans_table_data(*_args, **_kwargs):
        return pd.DataFrame({"Collateral": ["TokenA: 1"], "Debt": ["TokenA: 0.5"]})

    async def dummy_get_balance(_self):
        return None

    monkeypatch.setattr("apps.dashboard_app.charts.utils.get_prices", dummy_get_prices)
    monkeypatch.setattr(
        "apps.dashboard_app.charts.utils.get_main_chart_data", dummy_get_main_chart_data
    )
    monkeypatch.setattr(
        "apps.dashboard_app.charts.utils.get_loans_table_data",
        dummy_get_loans_table_data,
    )
    monkeypatch.setattr(
        "apps.dashboard_app.charts.utils.SwapAmm.get_balance", dummy_get_balance
    )

    main_chart_data, _ = get_data("DummyProtocol", state)
    # Since get_main_chart_data raises an exception, each pair's DataFrame should be empty.
    for df in main_chart_data.values():
        assert df.empty


# -------------------------------
# Tests for get_protocol_data_mappings
# -------------------------------


def test_get_protocol_data_mappings_positive(monkeypatch):
    """
    Test get_protocol_data_mappings returns correct mappings for valid input.
    """
    state = DummyState()

    def dummy_get_data(_protocol_name, _state):
        # Return dummy main_chart_data and loans_data.
        main_chart = {"TestPair": pd.DataFrame({"col": [1]})}
        loans = pd.DataFrame({"Collateral": ["TokenA: 1"], "Debt": ["TokenA: 0.5"]})
        return main_chart, loans

    monkeypatch.setattr("apps.dashboard_app.charts.utils.get_data", dummy_get_data)

    protocols = ["DummyProtocol"]
    current_pair = "TestPair"
    stable_coin_pair = (
        "USDC-ETH"  # Different from current_pair to bypass stablecoin branch.
    )

    main_chart_mappings, loans_mappings = get_protocol_data_mappings(
        current_pair, stable_coin_pair, protocols, state
    )

    expected_df = pd.DataFrame({"col": [1]})
    pd.testing.assert_frame_equal(main_chart_mappings["DummyProtocol"], expected_df)

    expected_loans_df = pd.DataFrame(
        {"Collateral": ["TokenA: 1"], "Debt": ["TokenA: 0.5"]}
    )
    pd.testing.assert_frame_equal(loans_mappings["DummyProtocol"], expected_loans_df)


def test_get_protocol_data_mappings_negative(monkeypatch):
    """
    Test get_protocol_data_mappings handles empty protocols gracefully.
    """
    state = DummyState()

    def dummy_get_data(_protocol_name, _state):
        main_chart = {"TestPair": pd.DataFrame({"col": [1]})}
        loans = pd.DataFrame({"Collateral": ["TokenA: 1"], "Debt": ["TokenA: 0.5"]})
        return main_chart, loans

    monkeypatch.setattr("apps.dashboard_app.charts.utils.get_data", dummy_get_data)

    protocols = []
    current_pair = "TestPair"
    stable_coin_pair = "USDC-ETH"

    main_chart_mappings, loans_mappings = get_protocol_data_mappings(
        current_pair, stable_coin_pair, protocols, state
    )

    assert not main_chart_mappings
    assert not loans_mappings


# -------------------------------
# Tests for transform_loans_data
# -------------------------------


def test_transform_loans_data_positive():
    """
    Test transform_loans_data returns correctly transformed loans DataFrame.
    """
    df1 = pd.DataFrame({"Collateral": ["BTC: 1, ETH: 2"], "Debt": ["BTC: 0.5, ETH: 1"]})
    df2 = pd.DataFrame({"Collateral": ["BTC: 3"], "Debt": ["BTC: 1.5"]})
    mapping = {"Prot1": df1, "Prot2": df2}
    protocols = ["Prot1", "Prot2"]

    transformed_df = transform_loans_data(mapping, protocols)

    expected_record1 = {"BTC": 1.0, "ETH": 2.0}
    expected_record2 = {"BTC": 3.0}

    records = transformed_df.to_dict(orient="records")
    assert records[0]["Collateral"] == expected_record1
    assert records[0]["Debt"] == {"BTC": 0.5, "ETH": 1.0}
    assert records[1]["Collateral"] == expected_record2
    assert records[1]["Debt"] == {"BTC": 1.5}


def test_transform_loans_data_negative():
    """
    Test transform_loans_data raises KeyError when required columns are missing.
    """
    df = pd.DataFrame({"SomeColumn": ["data"]})
    mapping = {"Prot1": df}
    protocols = ["Prot1"]

    with pytest.raises(KeyError):
        transform_loans_data(mapping, protocols)
