"""
This module contains the logic to parse the nostra data to human-readable format.
"""
from decimal import Decimal
from typing import Any, List

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


class NostraDataParser:
    """
    Parses the nostra data to human-readable format.
    """

    @classmethod
    def parse_interest_rate_model_event(
        cls, event_data: List[Any]
    ) -> InterestRateModelEventData:
        """
        Parses the interest rate model event data into a human-readable format.
        The event data is fetched from on-chain logs and is structured in the following way:
        - event_data[0]: The debt token address (as a hexadecimal string).
        - event_data[1]: The lending interest rate index (as a hexadecimal in 18 decimal places).
        - event_data[2]: The borrow interest rate index (as a hexadecimal in 18 decimal places).
        Args:
            event_data (List[Any]): A list containing the raw event data.
                Expected order: [debt_token, lending_index, _, borrow_index, _]
        Returns:
            InterestRateModelEventData: A model with the parsed event data.
        """
        return InterestRateModelEventData(
            debt_token=event_data[0],
            lending_index=event_data[1],
            borrow_index=event_data[2],
        )

    @classmethod
    def parse_non_interest_bearing_collateral_mint_event(
        cls, event_data: list[Any]
    ) -> NonInterestBearingCollateralMintEventData:
        """
        Parses the non-interest bearing collateral mint event data into a human-readable format.

        The event data is structured as follows:
        - event_data[0]: sender address
        - event_data[1]: recipient address
        - event_data[2]: raw amount

        Args:
            event_data (list[Any]): A list containing the raw event data with 3 elements:
                sender, recipient, and raw amount.

        Returns:
            NonInterestBearingCollateralMintEventData: A model with the parsed event data.
        """
        return NonInterestBearingCollateralMintEventData(
            sender=event_data[0],
            recipient=event_data[1],
            raw_amount=event_data[2],
        )

    @classmethod
    def parse_non_interest_bearing_collateral_burn_event(
        cls, event_data: list[Any]
    ) -> NonInterestBearingCollateralBurnEventData:
        """
        Parses the non-interest bearing collateral burn event data into a human-readable format.

        The event data is structured as follows:
        - event_data[0]: user address
        - event_data[1]: face amount

        Args:
            event_data (list[Any]): A list containing the raw event data with 2 elements:
                user and face amount.

        Returns:
            NonInterestBearingCollateralBurnEventData: A model with the parsed event data.
        """
        return NonInterestBearingCollateralBurnEventData(
            user=event_data[0],
            face_amount=event_data[1],
        )

    def parse_interest_bearing_collateral_mint_event(
        self, event_data: list[Any]
    ) -> BearingCollateralMintEventData:
        """
        Parses the BearingCollateralMint event data into a human-readable format using the BearingCollateralMintEventData serializer.

        The event data is fetched from on-chain logs and is structured in the following way:
        - event_data[0]: The user address (as a hexadecimal string).
        - event_data[1]: Token amount

        Args:
            event_data (list[Any]): A list containing the raw event data, typically with 3 or more elements:
                user address, amount of tokens
        Returns:
            BearingCollateralMintEventData: A Pydantic model with the parsed and validated event data in a human-readable format.

        """
        return BearingCollateralMintEventData(
            user=event_data[0],
            amount=event_data[1],
        )

    def parse_interest_bearing_collateral_burn_event(
        self, event_data: list[Any]
    ) -> BearingCollateralBurnEventData:
        """
        Parses the BearingCollateralMint event data into a human-readable format using the BearingCollateralMintEventData serializer.

        The event data is fetched from on-chain logs and is structured in the following way:
        - event_data[0]: The user address (as a hexadecimal string).
        - event_data[1]: Token amount

        Args:
            event_data (list[Any]): A list containing the raw event data, typically with 3 or more elements:
                user address, amount of tokens
        Returns:
            BearingCollateralMintEventData: A Pydantic model with the parsed and validated event data in a human-readable format.

        """
        return BearingCollateralBurnEventData(
            user=event_data[0],
            amount=event_data[1],
        )

    def parse_debt_transfer_event(self, event_data: List[Any]) -> DebtTransferEventData:
        """
        Parses the debt transfer event data into a human-readable format using the
        DebtBurnEventData serializer.

        Args:
            event_data (List[Any]): A list containing the raw event data.
                Expected order: [sender, recipient, value, _]

        Returns:
            DebtTransferEventData: A model with the parsed event data.
        """
        return DebtTransferEventData(
            sender=event_data[0],
            recipient=event_data[1],
            amount=event_data[2],
        )

    @classmethod
    def parse_debt_mint_event(cls, event_data: list[Any]) -> DebtMintEventData:
        """
        Parses the debt mint event data into a human-readable format using the
        DebtMintEventData serializer.

        Args:
            event_data (List[Any]): A list containing the raw debt mint event data,
                                    typically with 2 elements: user and amount.

        Returns:
            DebtMintEventData: A Pydantic model with the parsed and validated event data in a human-readable format.
        """
        return DebtMintEventData(
            user=event_data[0],
            amount=event_data[1],
        )

    @classmethod
    def parse_debt_burn_event(cls, event_data: list[Any]) -> DebtBurnEventData:
        """
        Parses the debt burn event data into a human-readable format using the
        DebtBurnEventData serializer.

        Args:
            event_data (List[Any]): A list containing the raw debt burn event data,
                                    typically with 2 elements: user and amount.

        Returns:
            DebtBurnEventData: A Pydantic model with the parsed and validated event data in a human-readable format.
        """
        return DebtBurnEventData(
            user=event_data[0],
            amount=event_data[1],
        )
