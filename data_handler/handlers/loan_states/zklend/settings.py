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
    return decimal_big_num / scale_factor

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


# ZKLEND_SPECIFIC_TOKEN_SETTINGS: dict[str, ZkLendSpecificTokenSettings] = {
#     "ETH": ZkLendSpecificTokenSettings(
#         collateral_factor=decimal.Decimal("0.80"),
#         debt_factor=decimal.Decimal("1"),
#         liquidation_bonus=decimal.Decimal("0.10"),
#         protocol_token_address="0x01b5bd713e72fdc5d63ffd83762f81297f6175a5e0a4771cdadbc1dd5fe72cb1",
#     ),
#     "wBTC": ZkLendSpecificTokenSettings(
#         collateral_factor=decimal.Decimal("0.70"),
#         debt_factor=decimal.Decimal("1"),
#         liquidation_bonus=decimal.Decimal("0.15"),
#         protocol_token_address="0x02b9ea3acdb23da566cee8e8beae3125a1458e720dea68c4a9a7a2d8eb5bbb4a",
#     ),
#     "USDC": ZkLendSpecificTokenSettings(
#         collateral_factor=decimal.Decimal("0.80"),
#         debt_factor=decimal.Decimal("1"),
#         liquidation_bonus=decimal.Decimal("0.10"),
#         protocol_token_address="0x047ad51726d891f972e74e4ad858a261b43869f7126ce7436ee0b2529a98f486",
#     ),
#     "DAI": ZkLendSpecificTokenSettings(
#         collateral_factor=decimal.Decimal("0.70"),
#         debt_factor=decimal.Decimal("1"),
#         liquidation_bonus=decimal.Decimal("0.10"),
#         protocol_token_address="0x062fa7afe1ca2992f8d8015385a279f49fad36299754fb1e9866f4f052289376",
#     ),
#     "USDT": ZkLendSpecificTokenSettings(
#         collateral_factor=decimal.Decimal("0.80"),
#         debt_factor=decimal.Decimal("1"),
#         liquidation_bonus=decimal.Decimal("0.10"),
#         protocol_token_address="0x00811d8da5dc8a2206ea7fd0b28627c2d77280a515126e62baa4d78e22714c4a",
#     ),
#     "wstETH": ZkLendSpecificTokenSettings(
#         collateral_factor=decimal.Decimal("0.80"),
#         debt_factor=decimal.Decimal("1"),
#         liquidation_bonus=decimal.Decimal("0.10"),
#         protocol_token_address="0x0536aa7e01ecc0235ca3e29da7b5ad5b12cb881e29034d87a4290edbb20b7c28",
#     ),
#     # TODO: Add LORDS.
#     "LORDS": ZkLendSpecificTokenSettings(
#         collateral_factor=decimal.Decimal("1"),
#         debt_factor=decimal.Decimal("1"),
#         liquidation_bonus=decimal.Decimal("0"),
#         protocol_token_address="",
#     ),
#     # TODO: Update STRK settings.
#     "STRK": ZkLendSpecificTokenSettings(
#         collateral_factor=decimal.Decimal("0.50"),
#         debt_factor=decimal.Decimal("1"),
#         liquidation_bonus=decimal.Decimal("0.15"),
#         protocol_token_address="0x06d8fa671ef84f791b7f601fa79fea8f6ceb70b5fa84189e3159d532162efc21",
#     ),
# }

# TOKEN_SETTINGS: dict[str, TokenSettings] = {
#     token: TokenSettings(
#         symbol=TOKEN_SETTINGS[token].symbol,
#         decimal_factor=TOKEN_SETTINGS[token].decimal_factor,
#         address=TOKEN_SETTINGS[token].address,
#         collateral_factor=ZKLEND_SPECIFIC_TOKEN_SETTINGS[token].collateral_factor,
#         debt_factor=ZKLEND_SPECIFIC_TOKEN_SETTINGS[token].debt_factor,
#         liquidation_bonus=ZKLEND_SPECIFIC_TOKEN_SETTINGS[token].liquidation_bonus,
#         protocol_token_address=ZKLEND_SPECIFIC_TOKEN_SETTINGS[
#             token
#         ].protocol_token_address,
#     )
#     for token in TOKEN_SETTINGS
# }
