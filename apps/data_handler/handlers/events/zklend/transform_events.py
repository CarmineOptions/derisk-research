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
)
from data_handler.db.crud import ZkLendEventDBConnector
from data_handler.handler_tools.constants import ProtocolAddresses




logger = logging.getLogger(__name__)

EVENT_MAPPING: Dict[str, Tuple[Callable, str, Type[Base]]] = {
    "AccumulatorsSync": (
        ZklendDataParser.parse_accumulators_sync_event,
        "create_accumulator_event",
        AccumulatorsSyncEventModel
    ),
    "Liquidation": (
        ZklendDataParser.parse_liquidation_event,
        "create_liquidation_event",
        LiquidationEventModel
    ),
    "zklend::market::Market::AccumulatorsSync": (
        ZklendDataParser.parse_accumulators_sync_event,
        "create_accumulator_event",
        AccumulatorsSyncEventModel
    ),
    "zklend::market::Market::Liquidation": (
        ZklendDataParser.parse_liquidation_event,
        "create_liquidation_event",
        LiquidationEventModel
    ),
}


class ZklendTransformer:
    """
    A class that is used to transform Zklend events into database models.
    """

    EVENT_MAPPING: Dict[str, Tuple[Callable, Type[BaseModel], Type[Base]]] = EVENT_MAPPING
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
                parser_func, method_name, model_class = self.EVENT_MAPPING[event_type]
                parsed_data = parser_func(event["data"])
                db_model = model_class(**parsed_data.model_dump())
                self.db_connector[method_name](db_model)
            else:
                logger.info(f"Event type {event_type} not supported, yet...")

    def save_accumulators_sync_event(self, event: Dict[str, Any]) -> None:
        """
        Save an accumulators sync event to the database.
        """
        parser_func, _, model_class = self.EVENT_MAPPING["zklend::market::Market::AccumulatorsSync"]
        parsed_data = parser_func(event)
        db_model = model_class(**parsed_data.model_dump())
        self.db_connector.create_accumulator_event(db_model)

    def save_liquidation_event(self, event: Dict[str, Any]) -> None:
        """
        Save a liquidation event to the database.
        """
        parser_func, _, model_class = self.EVENT_MAPPING["zklend::market::Market::Liquidation"]
        parsed_data = parser_func(event)
        db_model = model_class(**parsed_data.model_dump())
        
        self.db_connector.create_liquidation_event(db_model)

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