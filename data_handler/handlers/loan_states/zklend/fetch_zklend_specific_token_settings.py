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


def format_reserve_data_number(value_num: int):
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


def get_token_settings(reserve_data: list[int]):
    """
    Create and fill new ZkLend token setting.
    """
    collateral_factor = format_reserve_data_number(reserve_data[4])
    debt_factor = decimal.Decimal("1")
    liquidation_bonus = format_reserve_data_number(reserve_data[14])
    hexadecimal_without_prefix = hex(reserve_data[2])[2:].upper()
    # Add '0x0' prefix
    protocol_token_address = '0x0' + hexadecimal_without_prefix
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
        addr=next(iter(ProtocolAddresses().ZKLEND_MARKET_ADDRESSES)),
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


ZKLEND_SPECIFIC_TOKEN_SETTINGS = fetch_zklend_specific_token_settings()