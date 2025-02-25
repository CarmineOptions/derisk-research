import pytest
import pandas as pd
import logging

from dashboard_app.charts.utils import (
    transform_main_chart_data,
    infer_protocol_name
)

@pytest.fixture
def sample_protocol_data():
    """Fixture providing sample protocol data for testing."""
    df1 = pd.DataFrame({
        'collateral_token_price': [100, 200, 300],
        'liquidable_debt': [1000, 2000, 3000],
        'liquidable_debt_at_interval': [500, 1000, 1500]
    })
    
    df2 = pd.DataFrame({
        'collateral_token_price': [100, 200, 300],
        'liquidable_debt': [2000, 4000, 6000],
        'liquidable_debt_at_interval': [1000, 2000, 3000]
    })
    
    return {
        'protocol1': df1,
        'protocol2': df2
    }

def test_transform_main_chart_data_with_multiple_protocols(sample_protocol_data):
    """Tests if transform_main_chart_data correctly combines data from multiple protocols."""
    current_pair = "ETH-USDC"
    protocols = ["protocol1", "protocol2"]

    result = transform_main_chart_data(sample_protocol_data, current_pair, protocols)
    
    assert isinstance(result, pd.DataFrame)
    assert len(result) == 3
    assert 'liquidable_debt_protocol1' in result.columns
    assert 'liquidable_debt_protocol2' in result.columns
    assert 'liquidable_debt_at_interval_protocol1' in result.columns
    assert 'liquidable_debt_at_interval_protocol2' in result.columns

    assert result['liquidable_debt'].tolist() == [3000, 6000, 9000]
    assert result['liquidable_debt_at_interval'].tolist() == [1500, 3000, 4500]
    
    assert result['liquidable_debt_protocol1'].tolist() == [1000, 2000, 3000]
    assert result['liquidable_debt_protocol2'].tolist() == [2000, 4000, 6000]

def test_transform_main_chart_data_with_empty_data(sample_protocol_data, caplog):
    """Tests transform_main_chart_data with one protocol having empty data."""
    current_pair = "ETH-USDC"
    protocols = ["protocol1", "protocol2", "protocol3"]

    sample_protocol_data["protocol3"] = pd.DataFrame()
    
    with caplog.at_level(logging.WARNING):
        result = transform_main_chart_data(sample_protocol_data, current_pair, protocols)

    assert isinstance(result, pd.DataFrame)
    assert "No data for pair ETH-USDC from protocol3" in caplog.text
    assert len(result) == 3

    assert result['liquidable_debt'].tolist() == [3000, 6000, 9000]

@pytest.mark.parametrize("input_protocol, valid_protocols, expected", [
    ("protocol1", ["protocol1", "protocol2", "protocol3"], "protocol1"),
    ("protocl1", ["protocol1", "protocol2", "protocol3"], "protocol1"),  
    ("proto1", ["protocol1", "protocol2", "protocol3"], "protocol1"),   
    ("unknown", ["protocol1", "protocol2", "protocol3"], "unknown"),  
])
def test_infer_protocol_name(input_protocol, valid_protocols, expected):
    """Tests if infer_protocol_name correctly matches input to valid protocol names."""
    result = infer_protocol_name(input_protocol, valid_protocols)
    assert result == expected

def test_infer_protocol_name_with_empty_list():
    """Tests infer_protocol_name with an empty list of valid protocols."""
    input_protocol = "protocol1"
    valid_protocols = []
    result = infer_protocol_name(input_protocol, valid_protocols)
    assert result == input_protocol

def test_infer_protocol_name_with_very_similar_names():
    """Tests infer_protocol_name with very similar protocol names."""
    input_protocol = "protocol_v2"
    valid_protocols = ["protocol_v1", "protocol_v2", "protocol_v3"]
    result = infer_protocol_name(input_protocol, valid_protocols)
    assert result == "protocol_v2"

