from shared.custom_types import BaseTokenParameters


class NostraAlphaCollateralTokenParameters(BaseTokenParameters):
    is_interest_bearing: bool
    collateral_factor: float
    liquidator_fee_beta: float
    liquidator_fee_max: float
    protocol_fee: float


class NostraMainnetCollateralTokenParameters(BaseTokenParameters):
    is_interest_bearing: bool  # TODO: remove if distinguished within the loan entity
    collateral_factor: float
    protocol_fee: float  # TODO: is this even needed?


class NostraDebtTokenParameters(BaseTokenParameters):
    debt_factor: float
