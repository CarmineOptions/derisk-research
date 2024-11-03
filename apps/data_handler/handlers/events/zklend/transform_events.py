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

from data_handler.handler_tools.data_parser.serializers import (
    AccumulatorsSyncEventData,
    LiquidationEventData,
    WithdrawalEventData,
    BorrowingEventData,
    RepaymentEventData,
    DepositEventData,
    CollateralEnabledDisabledEventData,
)

from data_handler.db.crud import ZkLendEventDBConnector
from data_handler.handler_tools.constants import ProtocolAddresses


logger = logging.getLogger(__name__)

EVENT_MAPPING: Dict[str, Tuple[Callable, str]] = {
    "AccumulatorsSync": (
        ZklendDataParser.parse_accumulators_sync_event,
        "save_accumulators_sync_event"
    ),
    "zklend::market::Market::AccumulatorsSync": (
        ZklendDataParser.parse_accumulators_sync_event,
        "save_accumulators_sync_event"
    ),
    "Liquidation": (
        ZklendDataParser.parse_liquidation_event,
        "save_liquidation_event"
    ),
    "zklend::market::Market::Liquidation": (
        ZklendDataParser.parse_liquidation_event,
        "save_liquidation_event"
    ),
    "Repayment": (
        ZklendDataParser.parse_repayment_event,
        "save_repayment_event"
    ),
    "zklend::market::Market::Repayment": (
        ZklendDataParser.parse_repayment_event,
        "save_repayment_event"
    ),
    "Borrowing": (
        ZklendDataParser.parse_borrowing_event,
        "save_borrowing_event"
    ),
    "zklend::market::Market::Borrowing": (
        ZklendDataParser.parse_borrowing_event,
        "save_borrowing_event"
    ),
    "Deposit": (
        ZklendDataParser.parse_deposit_event,
        "save_deposit_event"
    ),
    "zklend::market::Market::Deposit": (
        ZklendDataParser.parse_deposit_event,
        "save_deposit_event"
    ),
    "Withdrawal": (
        ZklendDataParser.parse_withdrawal_event,
        "save_withdrawal_event"
    ),
    "zklend::market::Market::Withdrawal": (
        ZklendDataParser.parse_withdrawal_event,
        "save_withdrawal_event"
    ),
    "CollateralEnabled": (
        ZklendDataParser.parse_collateral_enabled_disabled_event,
        "save_collateral_enabled_disabled_event"
    ),
    "zklend::market::Market::CollateralEnabled": (
        ZklendDataParser.parse_collateral_enabled_disabled_event,
        "save_collateral_enabled_disabled_event"
    ),
    "CollateralDisabled": (
        ZklendDataParser.parse_collateral_enabled_disabled_event,
        "save_collateral_enabled_disabled_event"
    ),
    "zklend::market::Market::CollateralDisabled": (
        ZklendDataParser.parse_collateral_enabled_disabled_event,
        "save_collateral_enabled_disabled_event"
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
                parser_func, save_to_db_method_name = self.EVENT_MAPPING[event_type]
                parsed_data = parser_func(event["data"])

                getattr(self, save_to_db_method_name)(
                    event_name=event_type,
                    block_number=event.get("block_number"),
                    event_data=parsed_data
                )
            else:
                logger.info(f"Event type {event_type} not supported, yet...")

    def save_accumulators_sync_event(self, event_name: str, block_number: int, event_data: AccumulatorsSyncEventData) -> None:
        """
        Save an accumulators sync event to the database.
        """
        self.db_connector.create_accumulator_event(
            protocol_id=self.PROTOCOL_TYPE,
            event_name=event_name,
            block_number=block_number,
            event_data={
                "token": event_data.token,
                "lending_accumulator": event_data.lending_accumulator,
                "debt_accumulator": event_data.debt_accumulator
            }
        )

    def save_liquidation_event(self, event_name: str, block_number: int, event_data: LiquidationEventData) -> None:
        """
        Save a liquidation event to the database.
        """
        self.db_connector.create_liquidation_event(
            protocol_id=self.PROTOCOL_TYPE,
            event_name=event_name,
            block_number=block_number,
            event_data={
                "liquidator": event_data.liquidator,
                "user": event_data.user,
                "debt_token": event_data.debt_token,
                "debt_raw_amount": event_data.debt_raw_amount,
                "debt_face_amount": event_data.debt_face_amount,
                "collateral_token": event_data.collateral_token,
                "collateral_amount": event_data.collateral_amount
            }
        )

    def save_borrowing_event(self, event_name: str, block_number: int, event_data: BorrowingEventData) -> None:
        """
        Save a borrowing event to the database.
        """
        self.db_connector.create_borrowing_event(
            protocol_id=self.PROTOCOL_TYPE,
            event_name=event_name,
            block_number=block_number,
            event_data={
                "user": event_data.user,
                "token": event_data.token,
                "raw_amount": event_data.raw_amount,
                "face_amount": event_data.face_amount
            }
        )

    def save_deposit_event(self, event_name: str, block_number: int, event_data: DepositEventData) -> None:
        """
        Save a deposit event to the database.
        """
        self.db_connector.create_deposit_event(
            protocol_id=self.PROTOCOL_TYPE,
            event_name=event_name,
            block_number=block_number,
            event_data={
                "user": event_data.user,
                "token": event_data.token,
                "face_amount": event_data.face_amount
            }
        )
    
    def save_withdrawal_event(self, event_name: str, block_number: int, event_data: WithdrawalEventData) -> None:
        """
        Save a withdrawal event to the database.
        """
        self.db_connector.create_withdrawal_event(
            protocol_id=self.PROTOCOL_TYPE,
            event_name=event_name,
            block_number=block_number,
            event_data={
                "user": event_data.user,
                "token": event_data.token,
                "amount": event_data.amount
            }
        )
    
    def save_collateral_enabled_disabled_event(self, event_name: str, block_number: int, event_data: CollateralEnabledDisabledEventData) -> None:
        """
        Save a collateral enabled/disabled event to the database.
        """
        self.db_connector.create_collateral_enabled_disabled_event(
            protocol_id=self.PROTOCOL_TYPE,
            event_name=event_name,
            block_number=block_number,
            event_data={
                "user": event_data.user,
                "token": event_data.token
            }
        )
    
    def save_repayment_event(self, event_name: str, block_number: int, event_data: RepaymentEventData) -> None:
        """
        Save a repayment event to the database.
        """
        self.db_connector.create_repayment_event(
            protocol_id=self.PROTOCOL_TYPE,
            event_name=event_name,
            block_number=block_number,
            event_data={
                "repayer": event_data.repayer,
                "beneficiary": event_data.beneficiary,
                "token": event_data.token,
                "raw_amount": event_data.raw_amount,
                "face_amount": event_data.face_amount
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
    