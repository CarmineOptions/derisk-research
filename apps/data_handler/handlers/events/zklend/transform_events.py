"""
This module contains the ZklendTransformer class, 
which is used to transform Zklend events.
"""

from pydantic import BaseModel
from data_handler.db.models.base import Base
from handler_tools.api_connector import DeRiskAPIConnector
from typing import Dict, Any, Tuple, Type, Callable
from data_handler.handler_tools.data_parser.serializers import (
    AccumulatorsSyncEventData as AccumulatorsSyncSerializer,
    LiquidationEventData as LiquidationSerializer,
    ZkLendDataParser,
)
from data_handler.db.models.zklend_events import (
    AccumulatorsSyncEventData as AccumulatorsSyncModel,
    LiquidationEventData as LiquidationModel,
)
from data_handler.db.crud import ZkLendEventDBConnector

EVENT_MAPPING: Dict[str, Tuple[Callable, Type[BaseModel], Type[Base]]] = {
    "AccumulatorsSync": (
        ZkLendDataParser.parse_accumulators_sync_event,
        AccumulatorsSyncSerializer,
        AccumulatorsSyncModel
    ),
    "Liquidation": (
        ZkLendDataParser.parse_liquidation_event,
        LiquidationSerializer,
        LiquidationModel
    ),
}

class ZklendTransformer:
    """
    A class that is used to transform Zklend events into database models.
    """

    EVENT_MAPPING: Dict[str, Tuple[Callable, Type[BaseModel], Type[Base]]] = EVENT_MAPPING
    
    def __init__(self):
        self.api_connector = DeRiskAPIConnector()
        self.db_connector = ZkLendEventDBConnector()

    def save_accumulators_sync_event(self, event: Dict[str, Any]) -> None:
        """
        Save an accumulators sync event to the database.
        """
        parser_func, serializer_class, model_class = EVENT_MAPPING["AccumulatorsSync"]
        parsed_data = parser_func(event)
        db_model = model_class(**parsed_data.model_dump())
        self.db_connector.create_accumulator_event(db_model)

    def save_liquidation_event(self, event: Dict[str, Any]) -> None:
        """
        Save a liquidation event to the database.
        """
        parser_func, serializer_class, model_class = EVENT_MAPPING["Liquidation"]
        parsed_data = parser_func(event)
        db_model = model_class(**parsed_data.model_dump())
        
        self.db_connector.create_liquidation_event(db_model)