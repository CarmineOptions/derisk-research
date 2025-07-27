from shared.data_parser.serializers.nostra import (
    DebtMintEventData,
    DebtBurnEventData,
    InterestRateModelEventData,
    DebtTransferEventData,
    BearingCollateralMintEventData,
    BearingCollateralBurnEventData,
    NonInterestBearingCollateralMintEventData,
    NonInterestBearingCollateralBurnEventData,
)

from shared.data_parser.serializers.zklend import (
    AccumulatorsSyncEventData,
    BorrowingEventData,
    RepaymentEventData,
    DepositEventData,
    LiquidationEventData,
    WithdrawalEventData,
    CollateralEnabledDisabledEventData,
)

__all__ = [
    # Nostra serializers
    "DebtMintEventData",
    "DebtBurnEventData",
    "InterestRateModelEventData",
    "DebtTransferEventData",
    "BearingCollateralMintEventData",
    "BearingCollateralBurnEventData",
    "NonInterestBearingCollateralMintEventData",
    "NonInterestBearingCollateralBurnEventData",
    # zkLend serializers
    "AccumulatorsSyncEventData",
    "BorrowingEventData",
    "RepaymentEventData",
    "DepositEventData",
    "LiquidationEventData",
    "WithdrawalEventData",
    "CollateralEnabledDisabledEventData",
]
