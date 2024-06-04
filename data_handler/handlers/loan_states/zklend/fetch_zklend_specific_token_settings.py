import decimal
from dataclasses import dataclass

from handlers.settings import TOKEN_SETTINGS, TokenSettings
from tools.constants import ProtocolAddresses
from src import blockchain_call

@dataclass
class ZkLendSpecificTokenSettings:
    # Source: https://zklend.gitbook.io/documentation/using-zklend/technical/asset-parameters.
    collateral_factor: decimal.Decimal
    # These are set to neutral values because zkLend doesn't use debt factors.
    debt_factor: decimal.Decimal
    # Source: https://zklend.gitbook.io/documentation/using-zklend/technical/asset-parameters.
    liquidation_bonus: decimal.Decimal
    protocol_token_address: str


@dataclass
class TokenSettings(ZkLendSpecificTokenSettings, TokenSettings):
    pass


def format_reserve_data_number(value_num: str):
    """
    Method to convert string number to decimal divided by the scale factor.
    Example:
    string_large_num = "800000000000000000000000000"
    return = 0.80
    """
    num = decimal.Decimal(value_num)
    SCALE_FACTOR = decimal.Decimal("1e27")
    # Example: cast 800000000000000000000000000 to 0.800000000000000000000000000
    decimal_large_num = num / SCALE_FACTOR
    # Example: convert 0.800000000000000000000000000 to 0.80
    formatted_number = round(decimal_large_num, 2)
    return formatted_number


def get_value_by_name(data_list: list[dict[str, str]], name: str):
    """
    Method to return a specific value in a list based on the name.
    """
    return next((item['value'] for item in data_list if item['name'] == name), None)


def get_token_settings(reserve_data: list[dict[str, str]]):
    """
    Create and fill new ZkLend token setting.
    """
    # Decimal Values
    collateral_factor = format_reserve_data_number(get_value_by_name(reserve_data, 'collateral_factor'))
    debt_factor = decimal.Decimal("1")
    liquidation_bonus = format_reserve_data_number(get_value_by_name(reserve_data, 'liquidation_bonus'))
    
    # STR value
    protocol_token_address = get_value_by_name(reserve_data, 'z_token_address')
    
    return ZkLendSpecificTokenSettings(
        collateral_factor,
        debt_factor,
        liquidation_bonus,
        protocol_token_address
    )


async def get_token_reserve_data(token_setting_address: str):
    """
    Make a call to ZKLEND_MARKET_ADDRESSES with the tokenSettingAddress (Address).
    """
    reserve_data = await blockchain_call.func_call(
        addr=ProtocolAddresses().ZKLEND_MARKET_ADDRESSES,
        selector="get_reserve_data",
        calldata=[token_setting_address],
    )
    return reserve_data


async def fetch_zklend_specific_token_settings():
    """
    Fetch ZkLend specific token settings.
    """
    # New dict to store ZkLendSpecificTokenSettings
    zklend_specific_token_settings: dict[str, ZkLendSpecificTokenSettings] = {}
    
    # TOKEN_SETTINGS from /derisk-research/data_handler/handlers/settings.py
    # For each tokenSetting in TOKEN_SETTINGS, get the data from zklend
    for symbol, token_setting in TOKEN_SETTINGS.items():
        reserve_data = await get_token_reserve_data(token_setting.address)
        zklend_specific_token_setting = get_token_settings(reserve_data)
        zklend_specific_token_settings[symbol] = zklend_specific_token_setting
    
    return zklend_specific_token_settings