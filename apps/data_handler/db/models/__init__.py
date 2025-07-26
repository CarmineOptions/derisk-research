"""This module contains all the models used in the database."""

from db.models.liquidable_debt import HealthRatioLevel, LiquidableDebt
from db.models.loan_states import InterestRate, LoanState, ZkLendCollateralDebt
from db.models.order_book import OrderBookModel
from db.models.vesu import VesuPosition
from db.models.zklend_events import (
    AccumulatorsSyncEventModel,
    BorrowingEventModel,
    CollateralEnabledDisabledEventModel,
    DepositEventModel,
    LiquidationEventModel,
    RepaymentEventModel,
    WithdrawalEventModel,
)
