"""
Tests for the process_liquidity function in helpers.tools module.
"""

import pandas as pd
import math
import pytest
from typing import Dict, Any, Tuple, Optional, DefaultDict, List, Union
from unittest.mock import patch
from dashboard_app.helpers.settings import TOKEN_SETTINGS, UNDERLYING_SYMBOLS_TO_UNDERLYING_ADDRESSES, COLLATERAL_TOKENS, DEBT_TOKENS, STABLECOIN_BUNDLE_NAME
from dashboard_app.helpers.ekubo import EkuboLiquidity
from collections import defaultdict
from dashboard_app.charts.utils import parse_token_amounts, create_stablecoin_bundle, process_liquidity

@pytest.fixture
def sample_token_amount_strings() -> Dict[str, str]:
    """
    Returns sample token amount strings for testing parse_token_amounts.
    """
    return {
        "empty": "",
        "single": "ETH: 10.5",
        "multiple": "ETH: 10.5, USDC: 1000.0, DAI: 500.25",
        "duplicates": "ETH: 5.0, ETH: 10.0, USDC: 100.0, USDC: 200.0"
    }

@pytest.fixture
def sample_stablecoin_data() -> Dict[str, pd.DataFrame]:
    """
    Returns sample data dictionary for testing create_stablecoin_bundle.
    """
    
    eth_usdc_df = pd.DataFrame({
        'collateral_token_price': [1900.0, 2000.0, 2100.0],
        'liquidable_debt': [50000.0, 60000.0, 70000.0],
        'liquidable_debt_at_interval': [50000.0, 10000.0, 10000.0],
        '10kSwap_debt_token_supply': [20000.0, 25000.0, 30000.0],
        'MySwap_debt_token_supply': [15000.0, 17000.0, 19000.0],
        'SithSwap_debt_token_supply': [10000.0, 12000.0, 14000.0],
        'JediSwap_debt_token_supply': [5000.0, 6000.0, 7000.0],
        'debt_token_supply': [50000.0, 60000.0, 70000.0]
    })
    
    
    eth_dai_df = pd.DataFrame({
        'collateral_token_price': [1900.0, 2000.0, 2100.0],
        'liquidable_debt': [40000.0, 45000.0, 50000.0],
        'liquidable_debt_at_interval': [40000.0, 5000.0, 5000.0],
        '10kSwap_debt_token_supply': [15000.0, 17000.0, 19000.0],
        'MySwap_debt_token_supply': [12000.0, 13000.0, 14000.0],
        'SithSwap_debt_token_supply': [8000.0, 9000.0, 10000.0],
        'JediSwap_debt_token_supply': [5000.0, 6000.0, 7000.0],
        'debt_token_supply': [40000.0, 45000.0, 50000.0]
    })
    
    
    btc_usdc_df = pd.DataFrame({
        'collateral_token_price': [45000.0, 47000.0, 49000.0],
        'liquidable_debt': [80000.0, 85000.0, 90000.0],
        'liquidable_debt_at_interval': [80000.0, 5000.0, 5000.0],
        '10kSwap_debt_token_supply': [30000.0, 32000.0, 34000.0],
        'MySwap_debt_token_supply': [20000.0, 22000.0, 24000.0],
        'SithSwap_debt_token_supply': [15000.0, 16000.0, 17000.0],
        'JediSwap_debt_token_supply': [15000.0, 15000.0, 15000.0],
        'debt_token_supply': [80000.0, 85000.0, 90000.0]
    })
    
    
    empty_df = pd.DataFrame()
    
    return {
        'ETH-USDC': eth_usdc_df,
        'ETH-DAI': eth_dai_df,
        'BTC-USDC': btc_usdc_df,
        'ETH-USDT': empty_df
    }

@pytest.fixture
def sample_chart_data() -> pd.DataFrame:
    """
    Returns a sample DataFrame for testing.
    """
    return pd.DataFrame({
        'collateral_token_price': [100.0, 200.0, 300.0],
        'liquidable_debt': [50.0, 75.0, 100.0],
        'liquidable_debt_at_interval': [50.0, 25.0, 25.0]
    })

@pytest.fixture
def sample_token_info() -> Dict[str, str]:
    """
    Returns sample token information for testing.
    """
    return {
        "collateral_token": "ETH",
        "debt_token": "USDC"
    }

@pytest.fixture
def mock_prices() -> Dict[str, float]:
    """
    Returns mock prices for tokens.
    """
    return {
        UNDERLYING_SYMBOLS_TO_UNDERLYING_ADDRESSES["ETH"]: 2000.0,
        UNDERLYING_SYMBOLS_TO_UNDERLYING_ADDRESSES["USDC"]: 1.0
    }

@pytest.fixture
def mock_ekubo_liquidity() -> Dict[str, Union[str, List[float]]]:
    """
    Returns mock data for Ekubo liquidity.
    """
    return {"type": "bids", "prices": [1900.0, 1950.0, 2000.0], "quantities": [10.0, 15.0, 20.0]}

@patch('helpers.tools.get_prices')
def test_process_liquidity_successful_execution(
    mock_get_prices: Any, 
    sample_chart_data: pd.DataFrame, 
    sample_token_info: Dict[str, str], 
    mock_prices: Dict[str, float], 
    mock_ekubo_liquidity: Dict[str, Union[str, List[float]]]
) -> None:
    """
    Tests successful execution of process_liquidity function.
    """
    
    mock_get_prices.return_value = mock_prices
    
    
    with patch.object(EkuboLiquidity, 'fetch_liquidity', return_value=mock_ekubo_liquidity), \
         patch.object(EkuboLiquidity, 'apply_liquidity_to_dataframe', return_value=sample_chart_data):
        
        
        result_df, collateral_price = process_liquidity(
            sample_chart_data, 
            sample_token_info["collateral_token"], 
            sample_token_info["debt_token"]
        )
        
        
        assert collateral_price == 2000.0
        assert isinstance(result_df, pd.DataFrame)
        pd.testing.assert_frame_equal(result_df, sample_chart_data)
        
        
        expected_decimal_factor = int(math.log10(TOKEN_SETTINGS[sample_token_info["collateral_token"]].decimal_factor))
        mock_get_prices.assert_called_once_with(token_decimals={
            UNDERLYING_SYMBOLS_TO_UNDERLYING_ADDRESSES[sample_token_info["collateral_token"]]: expected_decimal_factor
        })

@patch('helpers.tools.get_prices')
def test_process_liquidity_with_empty_dataframe(
    mock_get_prices: Any, 
    sample_token_info: Dict[str, str], 
    mock_prices: Dict[str, float], 
    mock_ekubo_liquidity: Dict[str, Union[str, List[float]]]
) -> None:
    """
    Tests process_liquidity function with an empty DataFrame.
    """
    
    main_chart_data = pd.DataFrame()
    
    
    mock_get_prices.return_value = mock_prices
    
    
    expected_df = pd.DataFrame({
        'collateral_token_price': [100.0, 200.0, 300.0],
        'liquidable_debt': [50.0, 75.0, 100.0],
        'debt_token_supply': [10.0, 15.0, 20.0],
        'Ekubo_debt_token_supply': [5.0, 7.5, 10.0]
    })
    
    
    with patch.object(EkuboLiquidity, 'fetch_liquidity', return_value=mock_ekubo_liquidity), \
         patch.object(EkuboLiquidity, 'apply_liquidity_to_dataframe', return_value=expected_df):
        
        
        result_df, collateral_price = process_liquidity(
            main_chart_data, 
            sample_token_info["collateral_token"], 
            sample_token_info["debt_token"]
        )
        
        
        assert collateral_price == 2000.0
        assert not result_df.empty
        assert len(result_df) == 3

def test_process_liquidity_with_invalid_tokens(sample_chart_data: pd.DataFrame) -> None:
    """
    Tests process_liquidity function with invalid tokens.
    """
    
    with pytest.raises(KeyError):
        process_liquidity(sample_chart_data, "INVALID_TOKEN", "USDC")

@patch('helpers.tools.get_prices')
def test_process_liquidity_type_conversion(
    mock_get_prices: Any, 
    sample_token_info: Dict[str, str], 
    mock_prices: Dict[str, float], 
    mock_ekubo_liquidity: Dict[str, Union[str, List[float]]]
) -> None:
    """
    Tests type conversion in process_liquidity function.
    """
    
    main_chart_data = pd.DataFrame({
        'collateral_token_price': ['100.0', '200.0', '300.0'],
        'liquidable_debt': ['50.0', '75.0', '100.0']
    })
    
    
    mock_get_prices.return_value = mock_prices
    
    
    expected_df = pd.DataFrame({
        'collateral_token_price': [100.0, 200.0, 300.0],
        'liquidable_debt': [50.0, 75.0, 100.0]
    })
    
    
    with patch.object(EkuboLiquidity, 'fetch_liquidity', return_value=mock_ekubo_liquidity), \
         patch.object(EkuboLiquidity, '__init__', return_value=None), \
         patch.object(EkuboLiquidity, 'apply_liquidity_to_dataframe', return_value=expected_df.copy()):
        
        
        result_df, collateral_price = process_liquidity(
            main_chart_data, 
            sample_token_info["collateral_token"], 
            sample_token_info["debt_token"]
        )
        
        
        assert result_df['collateral_token_price'].dtype == float
        assert result_df['liquidable_debt'].dtype == float

@patch('helpers.tools.get_prices')
def test_process_liquidity_integration_with_ekubo(
    mock_get_prices: Any, 
    sample_chart_data: pd.DataFrame, 
    sample_token_info: Dict[str, str], 
    mock_prices: Dict[str, float]
) -> None:
    """
    Tests integration with EkuboLiquidity in process_liquidity function.
    """
    
    mock_get_prices.return_value = mock_prices
    
    
    def mock_init(self, data: pd.DataFrame, collateral_token: str, debt_token: str) -> None:
        self.data = data
        self.collateral_token = collateral_token
        self.debt_token = debt_token
        return None
    
    def mock_fetch_liquidity(self) -> Dict[str, Union[str, List[float]]]:
        return {"type": "bids", "prices": [1900.0, 1950.0, 2000.0], "quantities": [10.0, 15.0, 20.0]}
    
    def mock_apply_liquidity(self, bids_or_asks: str) -> pd.DataFrame:
        
        df = self.data.copy()
        df['Ekubo_debt_token_supply'] = [5.0, 7.5, 10.0]
        df['debt_token_supply'] = df.get('debt_token_supply', 0) + df['Ekubo_debt_token_supply']
        return df
    
    with patch('helpers.ekubo.EkuboLiquidity.__init__', mock_init), \
         patch('helpers.ekubo.EkuboLiquidity.fetch_liquidity', mock_fetch_liquidity), \
         patch('helpers.ekubo.EkuboLiquidity.apply_liquidity_to_dataframe', mock_apply_liquidity):
        
        
        result_df, collateral_price = process_liquidity(
            sample_chart_data, 
            sample_token_info["collateral_token"], 
            sample_token_info["debt_token"]
        )
        
        
        assert collateral_price == 2000.0
        assert 'Ekubo_debt_token_supply' in result_df.columns
        assert 'debt_token_supply' in result_df.columns

@patch('helpers.tools.get_prices', side_effect=Exception("API error"))
def test_process_liquidity_error_handling(
    mock_get_prices: Any, 
    sample_chart_data: pd.DataFrame, 
    sample_token_info: Dict[str, str]
) -> None:
    """
    Tests error handling in process_liquidity function.
    """
    
    with pytest.raises(Exception) as exc_info:
        process_liquidity(
            sample_chart_data, 
            sample_token_info["collateral_token"], 
            sample_token_info["debt_token"]
        )
    
    assert str(exc_info.value) == "API error"



"""
Tests for the parse_token_amounts and create_stablecoin_bundle functions in helpers.tools module.
"""



def test_parse_token_amounts_empty_string(sample_token_amount_strings: Dict[str, str]) -> None:
    """
    Tests parse_token_amounts with an empty string.
    """
    result = parse_token_amounts(sample_token_amount_strings["empty"])
    assert isinstance(result, dict)
    assert len(result) == 0
    
    
    assert isinstance(result, defaultdict)
    assert result["NONEXISTENT"] == 0  

def test_parse_token_amounts_single_token(sample_token_amount_strings: Dict[str, str]) -> None:
    """
    Tests parse_token_amounts with a single token amount.
    """
    result = parse_token_amounts(sample_token_amount_strings["single"])
    assert len(result) == 1
    assert result["ETH"] == 10.5

def test_parse_token_amounts_multiple_tokens(sample_token_amount_strings: Dict[str, str]) -> None:
    """
    Tests parse_token_amounts with multiple token amounts.
    """
    result = parse_token_amounts(sample_token_amount_strings["multiple"])
    assert len(result) == 3
    assert result["ETH"] == 10.5
    assert result["USDC"] == 1000.0
    assert result["DAI"] == 500.25

def test_parse_token_amounts_with_duplicates(sample_token_amount_strings: Dict[str, str]) -> None:
    """
    Tests parse_token_amounts with duplicate tokens that should be summed.
    """
    result = parse_token_amounts(sample_token_amount_strings["duplicates"])
    assert len(result) == 2
    assert result["ETH"] == 15.0  
    assert result["USDC"] == 300.0  

def test_parse_token_amounts_with_malformed_input() -> None:
    """
    Tests parse_token_amounts with malformed input strings.
    """
    
    with pytest.raises(ValueError):
        parse_token_amounts("ETH: ")
    
    
    with pytest.raises(ValueError):
        parse_token_amounts("ETH 10.5")
    
    
    with pytest.raises(ValueError):
        parse_token_amounts("ETH: abc")

@patch('helpers.tools.COLLATERAL_TOKENS', ['ETH', 'BTC'])
@patch('helpers.tools.DEBT_TOKENS', ['USDC', 'DAI', 'USDT', 'STABLECOIN_BUNDLE'])
@patch('helpers.tools.STABLECOIN_BUNDLE_NAME', 'STABLECOIN_BUNDLE')
def test_create_stablecoin_bundle_successful(sample_stablecoin_data: Dict[str, pd.DataFrame]) -> None:
    """
    Tests successful execution of create_stablecoin_bundle function.
    """
    
    result = create_stablecoin_bundle(sample_stablecoin_data)
    
    
    assert 'ETH-STABLECOIN_BUNDLE' in result
    assert 'BTC-STABLECOIN_BUNDLE' in result
    
    
    eth_bundle = result['ETH-STABLECOIN_BUNDLE']
    
    
    assert list(eth_bundle['collateral_token_price']) == [1900.0, 2000.0, 2100.0]
    
    
    assert list(eth_bundle['liquidable_debt']) == [90000.0, 105000.0, 120000.0]  
    assert list(eth_bundle['liquidable_debt_at_interval']) == [90000.0, 15000.0, 15000.0]  
    
    
    assert list(eth_bundle['10kSwap_debt_token_supply']) == [35000.0, 42000.0, 49000.0]  
    assert list(eth_bundle['debt_token_supply']) == [90000.0, 105000.0, 120000.0]  

def test_create_stablecoin_bundle_with_empty_dataframe(sample_stablecoin_data: Dict[str, pd.DataFrame]) -> None:
    """
    Tests create_stablecoin_bundle function when one of the DataFrames is empty.
    """
    
    with patch('helpers.tools.logging.warning') as mock_warning:
        result = create_stablecoin_bundle(sample_stablecoin_data)
        
        
        mock_warning.assert_called_with("Empty DataFrame for pair: %s", "ETH-USDT")
    
    
    assert 'ETH-STABLECOIN_BUNDLE' in result
    assert 'BTC-STABLECOIN_BUNDLE' in result

def test_create_stablecoin_bundle_with_no_relevant_pairs() -> None:
    """
    Tests create_stablecoin_bundle function when there are no relevant pairs for bundling.
    """
    
    data = {
        'SOL-USDC': pd.DataFrame({
            'collateral_token_price': [100.0, 110.0, 120.0],
            'liquidable_debt': [10000.0, 11000.0, 12000.0]
        })
    }
    
    
    with patch('helpers.tools.COLLATERAL_TOKENS', ['ETH', 'BTC']):
        result = create_stablecoin_bundle(data)
        
        
        assert 'ETH-STABLECOIN_BUNDLE' not in result
        assert 'BTC-STABLECOIN_BUNDLE' not in result
        assert 'SOL-USDC' in result
        assert len(result) == 1

def test_create_stablecoin_bundle_with_missing_columns() -> None:
    """
    Tests create_stablecoin_bundle function with DataFrames missing some columns.
    """
    
    data = {
        'ETH-USDC': pd.DataFrame({
            'collateral_token_price': [1900.0, 2000.0, 2100.0],
            'liquidable_debt': [50000.0, 60000.0, 70000.0],
            
        }),
        'ETH-DAI': pd.DataFrame({
            'collateral_token_price': [1900.0, 2000.0, 2100.0],
            'liquidable_debt': [40000.0, 45000.0, 50000.0],
            
        })
    }
    
    
    with patch('helpers.tools.COLLATERAL_TOKENS', ['ETH']), \
         patch('helpers.tools.DEBT_TOKENS', ['USDC', 'DAI', 'STABLECOIN_BUNDLE']), \
         patch('helpers.tools.STABLECOIN_BUNDLE_NAME', 'STABLECOIN_BUNDLE'):
        
        result = create_stablecoin_bundle(data)
        
        
        assert 'ETH-STABLECOIN_BUNDLE' in result
        
        
        eth_bundle = result['ETH-STABLECOIN_BUNDLE']
        assert list(eth_bundle['liquidable_debt']) == [90000.0, 105000.0, 120000.0]
        
        
        assert '10kSwap_debt_token_supply' not in eth_bundle.columns

@patch('helpers.tools.COLLATERAL_TOKENS', ['ETH', 'BTC'])
@patch('helpers.tools.DEBT_TOKENS', ['USDC', 'DAI', 'USDT', 'STABLECOIN_BUNDLE'])
@patch('helpers.tools.STABLECOIN_BUNDLE_NAME', 'STABLECOIN_BUNDLE')
def test_create_stablecoin_bundle_with_different_price_ranges(sample_stablecoin_data: Dict[str, pd.DataFrame]) -> None:
    """
    Tests create_stablecoin_bundle function with DataFrames having different price ranges.
    """
    
    modified_data = sample_stablecoin_data.copy()
    modified_data['ETH-DAI'] = pd.DataFrame({
        'collateral_token_price': [1850.0, 1950.0, 2050.0, 2150.0],  
        'liquidable_debt': [38000.0, 40000.0, 45000.0, 50000.0],
        'liquidable_debt_at_interval': [38000.0, 2000.0, 5000.0, 5000.0],
        '10kSwap_debt_token_supply': [14000.0, 15000.0, 17000.0, 19000.0],
        'MySwap_debt_token_supply': [11000.0, 12000.0, 13000.0, 14000.0],
        'SithSwap_debt_token_supply': [7000.0, 8000.0, 9000.0, 10000.0],
        'JediSwap_debt_token_supply': [6000.0, 5000.0, 6000.0, 7000.0],
        'debt_token_supply': [38000.0, 40000.0, 45000.0, 50000.0]
    })
    
    
    result = create_stablecoin_bundle(modified_data)

    eth_bundle = result['ETH-STABLECOIN_BUNDLE']
    
    assert len(eth_bundle) == 0