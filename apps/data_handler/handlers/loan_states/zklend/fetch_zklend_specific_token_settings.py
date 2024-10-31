""" Fetch ZkLend specific token settings. """
import asyncio
import decimal

from data_handler.handler_tools.constants import ProtocolAddresses
from data_handler.handlers import blockchain_call
from pydantic import BaseModel, field_validator

from data_handler.handlers.loan_states.zklend.settings import (
    ZkLendSpecificTokenSettings,
)
from shared.constants import TOKEN_SETTINGS
from data_handler.handlers.loan_states.zklend.settings import (
    ZkLendSpecificTokenSettings,
)

SCALE_FACTOR = decimal.Decimal("1e27")


class ContractData(BaseModel):
    """
    Data structure fetched from startscan, example for ETH:
    https://starkscan.co/contract/0x04c0a5193d58f74fbace4b74dcf65481e734ed1714121bdc571da345540efa05
    """

    decimals: int
    z_token_address: int
    collateral_factor: float
    liquidation_bonus: float

    @field_validator("collateral_factor", "liquidation_bonus", mode="before")
    def format_number(cls, value: str) -> float:
        """
        Method to convert string number to decimal divided by the scale factor.
        :param value: converted value
        :return: float
        """
        num = decimal.Decimal(value)
        decimal_large_num = num / SCALE_FACTOR

        return round(decimal_large_num, 2)


def get_token_settings(contract_data: ContractData) -> ZkLendSpecificTokenSettings:
    """
    Create and fill new ZkLend token setting.
    """
    # STR value
    hexadecimal_without_prefix = hex(contract_data.z_token_address)[2:]
    # Add '0x0' prefix
    protocol_token_address = "0x0" + hexadecimal_without_prefix
    return ZkLendSpecificTokenSettings(
        collateral_factor=contract_data.collateral_factor,
        debt_factor=decimal.Decimal("1"),
        liquidation_bonus=contract_data.liquidation_bonus,
        protocol_token_address=protocol_token_address,
    )


async def get_token_reserve_data(token_setting_address: str) -> list:
    """
    Make a call to ZKLEND_MARKET_ADDRESSES with the tokenSettingAddress (Address).
    :param token_setting_address: Address of the token setting.
    :return: List of reserve data.
    """
    reserve_data = await blockchain_call.func_call(
        addr=next(iter(ProtocolAddresses().ZKLEND_MARKET_ADDRESSES)),
        selector="get_reserve_data",
        calldata=[token_setting_address],
    )
    return reserve_data


async def fetch_zklend_specific_token_settings() -> (dict[str, ZkLendSpecificTokenSettings]):
    """
    Fetch ZkLend specific token settings.
    :return: Dict of ZkLend specific token settings.
    """
    # New dict to store ZkLendSpecificTokenSettings
    zklend_specific_token_settings: dict[str, ZkLendSpecificTokenSettings] = {}

    # TOKEN_SETTINGS from /derisk-research/data_handler/handlers/settings.py
    # For each tokenSetting in TOKEN_SETTINGS, get the data from zklend
    for symbol, token_setting in TOKEN_SETTINGS.items():
        reserve_data = await get_token_reserve_data(token_setting.address)
        contract_data = ContractData(
            **{
                "decimals": reserve_data[1],
                "z_token_address": reserve_data[2],
                "collateral_factor": reserve_data[4],
                "liquidation_bonus": reserve_data[14],
            }
        )
        zklend_specific_token_settings[symbol] = get_token_settings(contract_data)

    return zklend_specific_token_settings


if __name__ == "__main__":
    ZKLEND_SPECIFIC_TOKEN_SETTINGS = asyncio.run(fetch_zklend_specific_token_settings())
