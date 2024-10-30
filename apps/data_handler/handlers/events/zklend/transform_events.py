"""
This module contains the ZklendTransformer class, 
which is used to transform Zklend events.
"""

from handler_tools.api_connector import DeRiskAPIConnector
from typing import List, Dict, Any, Tuple, Type
from data_handler.handler_tools.data_parser.serializers import (
    AccumulatorsSyncEventData as AccumulatorsSyncSerializer,
    LiquidationEventData as LiquidationSerializer,
    ZkLendDataParser,
)
from data_handler.db.models.zklend_events import (
    AccumulatorsSyncEventData as AccumulatorsSyncModel,
    LiquidationEventData as LiquidationModel,
)
from sqlalchemy.orm import Session


class ZklendTransformer:
    def __init__(self):
        self.api_connector = DeRiskAPIConnector()
        self.event_mapping = {
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

    def transform_events(self, events: List[Dict[str, Any]], db_session: Session) -> List[Dict[str, Any]]:
        """
        Transform a list of Zklend events into a list of database models.
        
        :param events: List of Zklend events.
        :param db_session: SQLAlchemy session.

        :return: List of database models.
        """
        transformed_events = []
        
        for event in events:
            event_name = event.get("name")
            if event_name not in self.event_mapping:
                continue

            parser_func, serializer_class, model_class = self.event_mapping[event_name]
            
            try:
                parsed_data = parser_func(event["data"])
                
                db_model = model_class(**parsed_data.model_dump())
                
                db_session.add(db_model)
                transformed_events.append(db_model)
                
            except Exception as e:
                print(f"Error processing {event_name} event: {str(e)}")
                continue
            
            db_session.commit()
        
        return transformed_events
