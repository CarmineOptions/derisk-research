import decimal
from dataclasses import dataclass

from handlers.settings import TOKEN_SETTINGS, TokenSettings
from handlers.loan_states.zklend.fetch_zklend_specific_token_settings import ZKLEND_SPECIFIC_TOKEN_SETTINGS


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


TOKEN_SETTINGS: dict[str, TokenSettings] = {
    token: TokenSettings(
        symbol=TOKEN_SETTINGS[token].symbol,
        decimal_factor=TOKEN_SETTINGS[token].decimal_factor,
        address=TOKEN_SETTINGS[token].address,
        collateral_factor=ZKLEND_SPECIFIC_TOKEN_SETTINGS[token].collateral_factor,
        debt_factor=ZKLEND_SPECIFIC_TOKEN_SETTINGS[token].debt_factor,
        liquidation_bonus=ZKLEND_SPECIFIC_TOKEN_SETTINGS[token].liquidation_bonus,
        protocol_token_address=ZKLEND_SPECIFIC_TOKEN_SETTINGS[
            token
        ].protocol_token_address,
    )
    for token in TOKEN_SETTINGS
}