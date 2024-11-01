"""
This module contains the ZklendTransformer class, 
which is used to transform Zklend events.
"""
import logging
from pydantic import BaseModel
from data_handler.db.models.base import Base
from data_handler.handler_tools.api_connector import DeRiskAPIConnector
from typing import Dict, Any, Tuple, Type, Callable
from shared.constants import ProtocolIDs
from data_handler.handler_tools.data_parser.zklend import ZklendDataParser
from data_handler.db.models.zklend_events import (
    AccumulatorsSyncEventModel,
    LiquidationEventModel,
    RepaymentEventModel,
    BorrowingEventModel,
    DepositEventModel,
    WithdrawalEventModel,
    CollateralEnabledDisabledEventModel
)
from data_handler.db.crud import ZkLendEventDBConnector
from data_handler.handler_tools.constants import ProtocolAddresses




logger = logging.getLogger(__name__)

EVENT_MAPPING: Dict[str, Tuple[Callable, str, Type[Base]]] = {
    "AccumulatorsSync": (
        ZklendDataParser.parse_accumulators_sync_event,
        "save_accumulators_sync_event",
        AccumulatorsSyncEventModel
    ),
    "zklend::market::Market::AccumulatorsSync": (
        ZklendDataParser.parse_accumulators_sync_event,
        "save_accumulators_sync_event",
        AccumulatorsSyncEventModel
    ),
    "Liquidation": (
        ZklendDataParser.parse_liquidation_event,
        "save_liquidation_event",
        LiquidationEventModel
    ),
    "zklend::market::Market::Liquidation": (
        ZklendDataParser.parse_liquidation_event,
        "save_liquidation_event",
        LiquidationEventModel
    ),
    "Repayment": (
        ZklendDataParser.parse_repayment_event,
        "save_repayment_event",
        RepaymentEventModel
    ),
    "zklend::market::Market::Repayment": (
        ZklendDataParser.parse_repayment_event,
        "save_repayment_event",
        RepaymentEventModel
    ),
    "Borrowing": (
        ZklendDataParser.parse_borrowing_event,
        "save_borrowing_event",
        BorrowingEventModel
    ),
    "zklend::market::Market::Borrowing": (
        ZklendDataParser.parse_borrowing_event,
        "save_borrowing_event",
        BorrowingEventModel
    ),
    "Deposit": (
        ZklendDataParser.parse_deposit_event,
        "save_deposit_event",
        DepositEventModel
    ),
    "zklend::market::Market::Deposit": (
        ZklendDataParser.parse_deposit_event,
        "save_deposit_event",
        DepositEventModel
    ),
    "Withdrawal": (
        ZklendDataParser.parse_withdrawal_event,
        "save_withdrawal_event",
        WithdrawalEventModel
    ),
    "zklend::market::Market::Withdrawal": (
        ZklendDataParser.parse_withdrawal_event,
        "save_withdrawal_event",
        WithdrawalEventModel
    ),
    "CollateralEnabled": (
        ZklendDataParser.parse_collateral_enabled_disabled_event,
        "save_collateral_enabled_disabled_event",
        CollateralEnabledDisabledEventModel
    ),
    "zklend::market::Market::CollateralEnabled": (
        ZklendDataParser.parse_collateral_enabled_disabled_event,
        "save_collateral_enabled_disabled_event",
        CollateralEnabledDisabledEventModel
    ),
    "CollateralDisabled": (
        ZklendDataParser.parse_collateral_enabled_disabled_event,
        "save_collateral_enabled_disabled_event",
        CollateralEnabledDisabledEventModel
    ),
    "zklend::market::Market::CollateralDisabled": (
        ZklendDataParser.parse_collateral_enabled_disabled_event,
        "save_collateral_enabled_disabled_event",
        CollateralEnabledDisabledEventModel
    ),
}


class ZklendTransformer:
    """
    A class that is used to transform Zklend events into database models.
    """

    EVENT_MAPPING: Dict[str, Tuple[Callable, str, Type[Base]]] = EVENT_MAPPING
    PROTOCOL_ADDRESSES: str = ProtocolAddresses.ZKLEND_MARKET_ADDRESSES
    PROTOCOL_TYPE: ProtocolIDs = ProtocolIDs.ZKLEND
    PAGINATION_SIZE: int = 1000

    def __init__(self):
        """
        Initialize the ZklendTransformer instance.
        Initializes API and database connectors, and retrieves the last processed block number.
        """
        self.api_connector = DeRiskAPIConnector()
        self.db_connector = ZkLendEventDBConnector()
        self.last_block = self.db_connector.get_last_block(self.PROTOCOL_TYPE)
    
    def fetch_and_transform_events(self, from_address: str, min_block: int, max_block: int) -> None:
        """
        Fetch events from the DeRisk API and transform them into database models.
        """
        # Fetch events using the API connector
        response = self.api_connector.get_data(
            from_address=from_address,
            min_block_number=min_block,
            max_block_number=max_block
        )

        if "error" in response:
            raise ValueError(f"Error fetching events: {response['error']}")

        # Process each event based on its type
        for event in response:
            event_type = event.get("key_name")
            if event_type in self.EVENT_MAPPING:
                parser_func, save_to_db_method_name, model_class = self.EVENT_MAPPING[event_type]
                parsed_data = parser_func(event["data"])
                db_model = model_class(**parsed_data.model_dump())
                getattr(self, save_to_db_method_name)(db_model)
            else:
                logger.info(f"Event type {event_type} not supported, yet...")

    def save_accumulators_sync_event(self, event_model: AccumulatorsSyncEventModel) -> None:
        """
        Save an accumulators sync event to the database.
        """
        self.db_connector.create_accumulator_event(
            protocol_id=self.PROTOCOL_TYPE,
            event_name=event_model.event_name,
            block_number=event_model.block_number,
            event_data={
                "token": event_model.token,
                "lending_accumulator": event_model.lending_accumulator,
                "debt_accumulator": event_model.debt_accumulator
            }
        )

    def save_liquidation_event(self, event_model: LiquidationEventModel) -> None:
        """
        Save a liquidation event to the database.
        """
        self.db_connector.create_liquidation_event(
            protocol_id=self.PROTOCOL_TYPE,
            event_name=event_model.event_name,
            block_number=event_model.block_number,
            event_data={
                "liquidator": event_model.liquidator,
                "user": event_model.user,
                "debt_token": event_model.debt_token,
                "debt_raw_amount": event_model.debt_raw_amount,
                "debt_face_amount": event_model.debt_face_amount,
                "collateral_token": event_model.collateral_token,
                "collateral_amount": event_model.collateral_amount
            }
        )

    def save_borrowing_event(self, event_model: BorrowingEventModel) -> None:
        """
        Save a borrowing event to the database.
        """
        self.db_connector.create_borrowing_event(
            protocol_id=self.PROTOCOL_TYPE,
            event_name=event_model.event_name,
            block_number=event_model.block_number,
            event_data={
                "user": event_model.user,
                "token": event_model.token,
                "raw_amount": event_model.raw_amount,
                "face_amount": event_model.face_amount
            }
        )

    def save_deposit_event(self, event_model: DepositEventModel) -> None:
        """
        Save a deposit event to the database.
        """
        self.db_connector.create_deposit_event(
            protocol_id=self.PROTOCOL_TYPE,
            event_name=event_model.event_name,
            block_number=event_model.block_number,
            event_data={
                "user": event_model.user,
                "token": event_model.token,
                "face_amount": event_model.face_amount
            }
        )
    
    def save_withdrawal_event(self, event_model: WithdrawalEventModel) -> None:
        """
        Save a withdrawal event to the database.
        """
        self.db_connector.create_withdrawal_event(
            protocol_id=self.PROTOCOL_TYPE,
            event_name=event_model.event_name,
            block_number=event_model.block_number,
            event_data={
                "user": event_model.user,
                "token": event_model.token,
                "face_amount": event_model.face_amount
            }
        )
    
    def save_collateral_enabled_disabled_event(self, event_model: CollateralEnabledDisabledEventModel) -> None:
        """
        Save a collateral enabled/disabled event to the database.
        """
        self.db_connector.create_collateral_enabled_disabled_event(
            protocol_id=self.PROTOCOL_TYPE,
            event_name=event_model.event_name,
            block_number=event_model.block_number,
            event_data={
                "user": event_model.user,
                "token": event_model.token
            }
        )
    
    def save_repayment_event(self, event_model: RepaymentEventModel) -> None:
        """
        Save a repayment event to the database.
        """
        self.db_connector.create_repayment_event(
            protocol_id=self.PROTOCOL_TYPE,
            event_name=event_model.event_name,
            block_number=event_model.block_number,
            event_data={
                "repayer": event_model.repayer,
                "beneficiary": event_model.beneficiary,
                "token": event_model.token,
                "raw_amount": event_model.raw_amount,
                "face_amount": event_model.face_amount
            }
        )

    def run(self) -> None:
        """
        Run the ZklendTransformer class.
        """
        max_retries = 5
        retry = 0
        while retry < max_retries:
            self.fetch_and_transform_events(
                from_address=self.PROTOCOL_ADDRESSES,
                min_block=self.last_block,
                max_block=self.last_block + self.PAGINATION_SIZE
            )
            self.last_block += self.PAGINATION_SIZE
            retry += 1
        if retry == max_retries:
            logger.info(f"Reached max retries for address {self.PROTOCOL_ADDRESSES}")


if __name__ == "__main__":
    """
    This is the init function for when ZklendTransformer class is called directly.
    """
    transformer = ZklendTransformer()
    transformer.run()
