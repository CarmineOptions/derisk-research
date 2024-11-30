"""
This module contains the NostraTransformer class, 
which is used to transform Nostra events.
"""

import logging
from decimal import Decimal
from typing import Any, Callable, Dict, Tuple, Type

from data_handler.db.crud import NostraEventDBConnector
from data_handler.db.models.base import Base
from data_handler.db.models.nostra_events import (
    BearingCollateralBurnEventModel,
    BearingCollateralMintEventModel,
    DebtBurnEventModel,
    DebtMintEventModel,
    DebtTransferEventModel,
    InterestRateModelEventModel,
    NonInterestBearingCollateralBurnEventModel,
    NonInterestBearingCollateralMintEventModel,
)
from data_handler.handler_tools.api_connector import DeRiskAPIConnector
from data_handler.handler_tools.constants import ProtocolAddresses
from data_handler.handler_tools.data_parser.nostra import NostraDataParser
from data_handler.handler_tools.data_parser.serializers import (
    BearingCollateralBurnEventData,
    BearingCollateralMintEventData,
    DebtBurnEventData,
    DebtMintEventData,
    DebtTransferEventData,
    InterestRateModelEventData,
    NonInterestBearingCollateralBurnEventData,
    NonInterestBearingCollateralMintEventData,
)
from shared.constants import ProtocolIDs

logger = logging.getLogger(__name__)


class NostraTransformer:
    """
    A class that is used to transform Nostra events into database models.
    """

    PROTOCOL_ADDRESSES: str = ProtocolAddresses().NOSTRA_ALPHA_ADDRESSES
    PROTOCOL_TYPE: ProtocolIDs = ProtocolIDs.NOSTRA_ALPHA
    PAGINATION_SIZE: int = 1000

    def __init__(self):
        """
        Initialize the NostraTransformer instance.
        Initializes API and database connectors, and retrieves the last processed block number.
        """
        self.api_connector = DeRiskAPIConnector()
        self.db_connector = NostraEventDBConnector()
        self.last_block = self.db_connector.get_last_block(self.PROTOCOL_TYPE)
        self.data_parser = NostraDataParser()

        self.EVENT_MAPPING: Dict[str, Tuple[Callable, str]] = {
            "BearingCollateralBurn": (
                self.data_parser.parse_interest_bearing_collateral_burn_event,
                "save_bearing_collateral_burn_event",
            ),
            "BearingCollateralMint": (
                self.data_parser.parse_interest_bearing_collateral_mint_event,
                "save_bearing_collateral_mint_event",
            ),
            "DebtBurn": (
                self.data_parser.parse_debt_burn_event,
                "save_debt_burn_event",
            ),
            "DebtMint": (
                self.data_parser.parse_debt_mint_event,
                "save_debt_mint_event",
            ),
            "DebtTransfer": (
                self.data_parser.parse_debt_transfer_event,
                "save_debt_transfer_event",
            ),
            "InterestRateModel": (
                self.data_parser.parse_interest_rate_model_event,
                "save_interest_rate_model_event",
            ),
            "NonInterestBearingCollateralBurn": (
                self.data_parser.parse_non_interest_bearing_collateral_burn_event,
                "save_non_interest_bearing_collateral_burn_event",
            ),
            "NonInterestBearingCollateralMint": (
                self.data_parser.parse_non_interest_bearing_collateral_mint_event,
                "save_non_interest_bearing_collateral_mint_event",
            ),
        }

    def fetch_and_transform_events(
        self, from_address: str, min_block: int, max_block: int
    ) -> None:
        """
        Fetch events from the DeRisk API and transform them into database models.
        """
        # Fetch events using the API connector
        response = self.api_connector.get_data(
            from_address=from_address,
            min_block_number=min_block,
            max_block_number=max_block,
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
                    event_data=parsed_data,
                )
            else:
                logger.info(f"Event type {event_type} not supported, yet...")

    def save_bearing_collateral_burn_event(
        self,
        event_name: str,
        block_number: int,
        event_data: BearingCollateralBurnEventData,
    ) -> None:
        """
        Save a BearingCollateralBurn event to the database.
        """
        self.db_connector.create_bearing_collateral_burn_event(
            protocol_id=self.PROTOCOL_TYPE.value,
            event_name=event_name,
            block_number=block_number,
            event_data={
                "user": event_data.user,
                "amount": Decimal(event_data.amount),
            },
        )
        logger.info(
            f"Saved BearingCollateralBurn event: User={event_data.user}, Amount={event_data.amount}"
        )

    def save_bearing_collateral_mint_event(
        self,
        event_name: str,
        block_number: int,
        event_data: BearingCollateralMintEventData,
    ) -> None:
        """
        Save a BearingCollateralMint event to the database.
        """
        self.db_connector.create_bearing_collateral_mint_event(
            protocol_id=self.PROTOCOL_TYPE.value,
            event_name=event_name,
            block_number=block_number,
            event_data={
                "user": event_data.user,
                "amount": Decimal(event_data.amount),
            },
        )
        logger.info(
            f"Saved BearingCollateralMint event: User={event_data.user}, Amount={event_data.amount}"
        )

    def save_debt_mint_event(
        self, event_name: str, block_number: int, event_data: DebtMintEventData
    ) -> None:
        """
        Save a DebtMint event to the database.
        """
        self.db_connector.create_debt_mint_event(
            protocol_id=self.PROTOCOL_TYPE.value,
            event_name=event_name,
            block_number=block_number,
            event_data={
                "user": event_data.user,
                "amount": Decimal(event_data.amount),
            },
        )
        logger.info(
            f"Saved DebtMint event: User={event_data.user}, Amount={event_data.amount}"
        )

    def save_debt_burn_event(
        self, event_name: str, block_number: int, event_data: DebtBurnEventData
    ) -> None:
        """
        Save a DebtBurn event to the database.
        """
        self.db_connector.create_debt_burn_event(
            protocol_id=self.PROTOCOL_TYPE.value,
            event_name=event_name,
            block_number=block_number,
            event_data={
                "user": event_data.user,
                "amount": Decimal(event_data.amount),
            },
        )
        logger.info(
            f"Saved DebtBurn event: User={event_data.user}, Amount={event_data.amount}"
        )

    def save_debt_transfer_event(
        self, event_name: str, block_number: int, event_data: DebtTransferEventData
    ) -> None:
        """
        Save a DebtTransfer event to the database.
        """
        self.db_connector.create_debt_transfer_event(
            protocol_id=self.PROTOCOL_TYPE.value,
            event_name=event_name,
            block_number=block_number,
            event_data={
                "sender": event_data.sender,
                "recipient": event_data.recipient,
                "amount": Decimal(event_data.amount),
            },
        )
        logger.info(
            f"Saved DebtTransfer event: Sender={event_data.sender}, Recipient={event_data.recipient}, Amount={event_data.amount}"
        )

    def save_interest_rate_model_event(
        self,
        event_name: str,
        block_number: int,
        event_data: InterestRateModelEventData,
    ) -> None:
        """
        Save an InterestRateModel event to the database.
        """
        self.db_connector.create_interest_rate_model_event(
            protocol_id=self.PROTOCOL_TYPE.value,
            event_name=event_name,
            block_number=block_number,
            event_data={
                "debt_token": event_data.debt_token,
                "lending_index": Decimal(event_data.lending_index),
                "borrow_index": Decimal(event_data.borrow_index),
            },
        )
        logger.info(
            f"Saved InterestRateModel event: DebtToken={event_data.debt_token}, LendingIndex={event_data.lending_index}, BorrowIndex={event_data.borrow_index}"
        )

    def save_non_interest_bearing_collateral_burn_event(
        self,
        event_name: str,
        block_number: int,
        event_data: NonInterestBearingCollateralBurnEventData,
    ) -> None:
        """
        Save a NonInterestBearingCollateralBurn event to the database.
        """
        self.db_connector.create_non_interest_bearing_collateral_burn_event(
            protocol_id=self.PROTOCOL_TYPE.value,
            event_name=event_name,
            block_number=block_number,
            event_data={
                "user": event_data.user,
                "amount": Decimal(event_data.face_amount),
            },
        )
        logger.info(
            f"Saved NonInterestBearingCollateralBurn event: User={event_data.user}, Amount={event_data.face_amount}"
        )

    def save_non_interest_bearing_collateral_mint_event(
        self,
        event_name: str,
        block_number: int,
        event_data: NonInterestBearingCollateralMintEventData,
    ) -> None:
        """
        Save a NonInterestBearingCollateralMint event to the database.
        """
        self.db_connector.create_non_interest_bearing_collateral_mint_event(
            protocol_id=self.PROTOCOL_TYPE.value,
            event_name=event_name,
            block_number=block_number,
            event_data={
                "sender": event_data.sender,
                "recipient": event_data.recipient,
                "amount": Decimal(event_data.raw_amount),
            },
        )
        logger.info(
            f"Saved NonInterestBearingCollateralMint event: Sender={event_data.sender}, Recipient={event_data.recipient}, Amount={event_data.raw_amount}"
        )

    def run(self) -> None:
        """
        Run the NostraTransformer class.
        """
        max_retries = 5
        retry = 0
        while retry < max_retries:
            try:
                self.fetch_and_transform_events(
                    from_address=self.PROTOCOL_ADDRESSES,
                    min_block=self.last_block,
                    max_block=self.last_block + self.PAGINATION_SIZE,
                )
                self.last_block += self.PAGINATION_SIZE
                retry += 1
            except Exception as e:
                logger.error(f"Error during fetching or saving events: {e}")
        if retry == max_retries:
            logger.info(f"Reached max retries for address {self.PROTOCOL_ADDRESSES}")


if __name__ == "__main__":
    """
    This is the init function for when NostraTransformer class is called directly.
    """
    transformer = NostraTransformer()
    transformer.run()
