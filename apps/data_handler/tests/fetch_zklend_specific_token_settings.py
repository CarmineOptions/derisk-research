""" Test the fetch_zklend_specific_token_settings.py """
import decimal

from data_handler.handlers.loan_states.zklend.fetch_zklend_specific_token_settings import (
    ZkLendSpecificTokenSettings,
    get_token_settings,
)
from shared.custom_types import TokenSettings


# Mock response for the on chain call (func_call)
class MockBlockchainCall:
    """Mock response for the on chain call (func_call)"""

    async def func_call(self, addr, selector, calldata):
        """ Mock response for the on chain call (func_call) """
        return [
            {
                "name": "enabled",
                "type": "core::bool",
                "value": "1"
            },
            {
                "name": "decimals",
                "type": "core::felt252",
                "value": "18"
            },
            {
                "name": "z_token_address",
                "type": "core::starknet::contract_address::ContractAddress",
                "value": "0x1b5bd713e72fdc5d63ffd83762f81297f6175a5e0a4771cdadbc1dd5fe72cb1",
            },
            {
                "name": "interest_rate_model",
                "type": "core::starknet::contract_address::ContractAddress",
                "value": "0x5e39a07355604e8b19586ea01e83396166977fefbcf4bcf914d0febc2e382fe",
            },
            {
                "name": "collateral_factor",
                "type": "core::felt252",
                "value": "800000000000000000000000000",
            },
            {
                "name": "borrow_factor",
                "type": "core::felt252",
                "value": "1000000000000000000000000000",
            },
            {
                "name": "reserve_factor",
                "type": "core::felt252",
                "value": "100000000000000000000000000",
            },
            {
                "name": "last_update_timestamp",
                "type": "core::felt252",
                "value": "1717117956",
            },
            {
                "name": "lending_accumulator",
                "type": "core::felt252",
                "value": "1004566796838649499220632413",
            },
            {
                "name": "debt_accumulator",
                "type": "core::felt252",
                "value": "1023091980725735432747405580",
            },
            {
                "name": "current_lending_rate",
                "type": "core::felt252",
                "value": "8818453132823305828258328",
            },
            {
                "name": "current_borrowing_rate",
                "type": "core::felt252",
                "value": "26045010053342575604645918",
            },
            {
                "name": "raw_total_debt",
                "type": "core::felt252",
                "value": "1473750388904731480172",
            },
            {
                "name": "flash_loan_fee",
                "type": "core::felt252",
                "value": "900000000000000000000000",
            },
            {
                "name": "liquidation_bonus",
                "type": "core::felt252",
                "value": "100000000000000000000000000",
            },
            {
                "name": "debt_limit",
                "type": "core::felt252",
                "value": "2500000000000000000000",
            },
        ]


class ProtocolAddresses:
    """ Protocol addresses for the ZkLend protocol. """

    def __init__(self):
        self.ZKLEND_MARKET_ADDRESSES = "0xMarketAddress"


src = type("src", (), {"blockchain_call": MockBlockchainCall()})

# Mock TOKEN_SETTINGS dict
TOKEN_SETTINGS: dict[str, TokenSettings] = {
    "ETH":
    TokenSettings(
        symbol="ETH",
        decimal_factor=decimal.Decimal("1e18"),
        address="0x049d36570d4e46f48e99674bd3fcc84644ddd6b96f7c741b1562b82f9e004dc7",
    ),
    "wBTC":
    TokenSettings(
        symbol="wBTC",
        decimal_factor=decimal.Decimal("1e8"),
        address="0x03fe2b97c1fd336e750087d68b9b867997fd64a2661ff3ca5a7c771641e8e7ac",
    ),
    "USDC":
    TokenSettings(
        symbol="USDC",
        decimal_factor=decimal.Decimal("1e6"),
        address="0x053c91253bc9682c04929ca02ed00b3e423f6710d2ee7e0d5ebb06f3ecf368a8",
    ),
    "DAI":
    TokenSettings(
        symbol="DAI",
        decimal_factor=decimal.Decimal("1e18"),
        address="0x00da114221cb83fa859dbdb4c44beeaa0bb37c7537ad5ae66fe5e0efd20e6eb3",
    ),
    "USDT":
    TokenSettings(
        symbol="USDT",
        decimal_factor=decimal.Decimal("1e6"),
        address="0x068f5c6a61780768455de69077e07e89787839bf8166decfbf92b645209c0fb8",
    ),
    "wstETH":
    TokenSettings(
        symbol="wstETH",
        decimal_factor=decimal.Decimal("1e18"),
        address="0x042b8f0484674ca266ac5d08e4ac6a3fe65bd3129795def2dca5c34ecc5f96d2",
    ),
    "LORDS":
    TokenSettings(
        symbol="LORDS",
        decimal_factor=decimal.Decimal("1e18"),
        address="0x0124aeb495b947201f5fac96fd1138e326ad86195b98df6dec9009158a533b49",
    ),
    "STRK":
    TokenSettings(
        symbol="STRK",
        decimal_factor=decimal.Decimal("1e18"),
        address="0x4718f5a0fc34cc1af16a1cdee98ffb20c31f5cd61d6ab07201858f4287c938d",
    ),
}


# Function to call the mock of func_call
async def get_token_reserve_data(token_setting_address: str):
    """ Get the reserve data for a token setting address """
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
    zklend_specific_token_settings: dict[str, ZkLendSpecificTokenSettings] = {}

    # TOKEN_SETTINGS from /derisk-research/data_handler/handlers/settings.py
    # For each tokenSetting in TOKEN_SETTINGS, get the data from zklend
    for symbol, token_setting in TOKEN_SETTINGS.items():
        reserve_data = await get_token_reserve_data(token_setting.address)
        zklend_specific_token_setting = get_token_settings(reserve_data)
        zklend_specific_token_settings[symbol] = zklend_specific_token_setting

    return zklend_specific_token_settings


# Test the functionality
async def main():
    """ Test the functionality """
    new_settings = await fetch_zklend_specific_token_settings()
    for symbol, settings in new_settings.items():
        print(f"{symbol}: {settings}")


if __name__ == "__main__":
    pass
    # FIXME this test cases are broken
    # asyncio.run(main())
