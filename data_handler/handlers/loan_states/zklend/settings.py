import decimal
import src.blockchain_call
from dataclasses import dataclass

from handlers.settings import TOKEN_SETTINGS, TokenSettings
from tools.constants import ProtocolAddresses


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


def convert_string_to_decimal_1e27(string_big_num):
    """
    Method to convert big string number to decimal.
    Example:
    string_big_num = "800000000000000000000000000"
    return = 0.80
    """
    decimal_big_num = decimal.Decimal(string_big_num)
    scale_factor = decimal.Decimal("1e27")
    bigResult = decimal_big_num / scale_factor
    # Have to cast "0.800000000000000000000000000" to "800000000000000000000000000"
    formatted_number = "{:.2f}".format(bigResult)
    return formatted_number

def get_value_by_name(data_list, name):
    """
    Method to return a specific value in a list based on the name.
    """
    return next((item['value'] for item in data_list if item['name'] == name), None)

def create_and_fill_new_zklend_token_setting(reserve_data):
    """
    Create and fill new ZkLend token setting.
    """
    # Decimal Values
    collateral_factor = convert_string_to_decimal_1e27(get_value_by_name(reserve_data, 'collateral_factor'))
    debt_factor = decimal.Decimal("1")
    liquidation_bonus = convert_string_to_decimal_1e27(get_value_by_name(reserve_data, 'liquidation_bonus'))
    
    # STR value
    protocol_token_address = get_value_by_name(reserve_data, 'z_token_address')
    
    return ZkLendSpecificTokenSettings(
        collateral_factor,
        debt_factor,
        liquidation_bonus,
        protocol_token_address
    )

async def get_token_reserve_data(token_setting_address):
    """
    Make a call to ZKLEND_MARKET_ADDRESSES with the tokenSettingAddress (Address).
    """
    reserve_data = await src.blockchain_call.func_call(
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
    NEW_ZKLEND_SPECIFIC_TOKEN_SETTINGS: dict[str, ZkLendSpecificTokenSettings] = {}
    
    # TOKEN_SETTINGS from /derisk-research/data_handler/handlers/settings.py
    # For each tokenSetting in TOKEN_SETTINGS, get the data from zklend
    for symbol, token_setting in TOKEN_SETTINGS.items():
        reserve_data = await get_token_reserve_data(token_setting.address)
        new_zklend_specific_token_setting = create_and_fill_new_zklend_token_setting(reserve_data)
        NEW_ZKLEND_SPECIFIC_TOKEN_SETTINGS[symbol] = new_zklend_specific_token_setting
    
    return NEW_ZKLEND_SPECIFIC_TOKEN_SETTINGS