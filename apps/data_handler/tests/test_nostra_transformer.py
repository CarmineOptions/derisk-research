"""
Test the nostra transformer
"""

from decimal import Decimal
from typing import Any, Dict
from unittest.mock import MagicMock, patch

import pytest
from data_handler.handler_tools.data_parser.serializers import (
    BearingCollateralBurnEventData,
    DebtBurnEventData,
    DebtMintEventData,
    DebtTransferEventData,
)
from data_handler.handlers.events.nostra.transform_events import NostraTransformer
from shared.constants import ProtocolIDs


@pytest.fixture(scope="function")
def sample_debt_mint_event_data() -> Dict[str, Any]:
    """
    Sample debt mint event data
    """
    return {
        "id": "0x00a00637ed8fd6f3f83a1eb743a36c894c6fe5af5a87e8ab35697afb3422967e_3",
        "block_hash": "0x07d1b221c40b6a19c0381d61ebbe8d048018b49314ae1bdc93938059e29febdf",
        "block_number": 630008,
        "transaction_hash": "0x00a00637ed8fd6f3f83a1eb743a36c894c6fe5af5a87e8ab35697afb3422967e",
        "event_index": 3,
        "from_address": "0x04c0a5193d58f74fbace4b74dcf65481e734ed1714121bdc571da345540efa05",
        "keys": ["0xfa3f9acdb7b24dcf6d40d77ff2f87a87bca64a830a2169aebc9173db23ff41"],
        "data": [
            "0x1a0027d1bf86904d1051fe0ca94c39b659135f19504d663d66771a7424ca2eb",  # user
            "0x9184e72a000",  # amount in hex
        ],
        "timestamp": 1712276824,
        "key_name": "DebtMint",
    }


@pytest.fixture(scope="function")
def sample_debt_burn_event_data() -> Dict[str, Any]:
    """
    Sample debt burn event data
    """
    return {
        "id": "0x0216d505e065501a8f26be71516b6f624dedff0dee50c5ccbc33142f378d8028_5",
        "block_hash": "0x056914ef72facffc6e7fbb651d7ee91fa3a0bcc49de3058129ece5c706a72bd8",
        "block_number": 630004,
        "transaction_hash": "0x0216d505e065501a8f26be71516b6f624dedff0dee50c5ccbc33142f378d8028",
        "event_index": 5,
        "from_address": "0x04c0a5193d58f74fbace4b74dcf65481e734ed1714121bdc571da345540efa05",
        "keys": ["0x7ae0ab7952bbfc33a72035e5eccec7c8816723421c0acb315bd4690a71d46e"],
        "data": [
            "0x7f121e44b3f446cdcaa28b230546956208d51e96894acc3b482947356bc10ed",  # user
            "0x9184e72a000",  # amount in hex
        ],
        "timestamp": 1712275350,
        "key_name": "DebtBurn",
    }


@pytest.fixture(scope="function")
def sample_debt_transfer_event_data() -> Dict[str, Any]:
    """
    Sample debt transfer event data
    """
    return {
        "id": "0x04123456789abcdef0abcdef1234567890abcdef1234567890abcdef12345678_2",
        "block_hash": "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef",
        "block_number": 630010,
        "transaction_hash": "0x04123456789abcdef0abcdef1234567890abcdef1234567890abcdef12345678",
        "event_index": 2,
        "from_address": "0x04c0a5193d58f74fbace4b74dcf65481e734ed1714121bdc571da345540efa05",
        "keys": ["0xabcdefabcdefabcdefabcdefabcdefabcdefabcdefabcdefabcdefabcdefabcd"],
        "data": [
            "0xabcdef1234567890abcdef1234567890abcdef12",  # sender
            "0x1234567890abcdef1234567890abcdef12345678",  # recipient
            "0x1bc16d674ec80000",  # amount in hex (2e18)
        ],
        "timestamp": 1712278000,
        "key_name": "DebtTransfer",
    }


@pytest.fixture(scope="function")
def sample_bearing_collateral_burn_event_data() -> Dict[str, Any]:
    """
    Sample bearing collateral burn event data
    """
    return {
        "id": "0x07abcdefabcdefabcdefabcdefabcdefabcdefabcdefabcdefabcdefabcdefabcd_0",
        "block_hash": "0xabcdefabcdefabcdefabcdefabcdefabcdefabcdefabcdefabcdefabcdefabcd",
        "block_number": 630013,
        "transaction_hash": "0x07abcdefabcdefabcdefabcdefabcdefabcdefabcdefabcdefabcdefabcdefabcd",
        "event_index": 0,
        "from_address": "0x04c0a5193d58f74fbace4b74dcf65481e734ed1714121bdc571da345540efa05",
        "keys": ["0xabcdefabcdefabcdefabcdefabcdefabcdefabcdefabcdefabcdefabcdefabcd"],
        "data": [
            "0xabcdefabcdefabcdefabcdefabcdefabcdefabcdefabcdefabcdefabcdefabcd",  # user
            "0x2386f26fc10000",  # amount in hex (0.1e18)
        ],
        "timestamp": 1712278300,
        "key_name": "BearingCollateralBurn",
    }


def test_save_debt_mint_event(transformer, sample_debt_mint_event_data):
    """
    Test saving a debt mint event.
    """
    # Setup API response
    transformer.api_connector.get_data.return_value = [sample_debt_mint_event_data]

    expected_parsed_data = DebtMintEventData(
        user=sample_debt_mint_event_data["data"][0],
        amount=Decimal(int(sample_debt_mint_event_data["data"][1], 16)),
    )

    # Call the method
    transformer.fetch_and_transform_events(
        from_address=transformer.PROTOCOL_ADDRESSES, min_block=0, max_block=1000
    )

    # Verify DB connector was called with correct data
    transformer.db_connector.create_debt_mint_event.assert_called_once_with(
        protocol_id=ProtocolIDs.NOSTRA_ALPHA.value,
        event_name=sample_debt_mint_event_data["key_name"],
        block_number=sample_debt_mint_event_data["block_number"],
        event_data={
            "user": expected_parsed_data.user,
            "amount": expected_parsed_data.amount,
        },
    )


def test_save_debt_burn_event(transformer, sample_debt_burn_event_data):
    """
    Test saving a debt burn event.
    """
    transformer.api_connector.get_data.return_value = [sample_debt_burn_event_data]

    expected_parsed_data = DebtBurnEventData(
        user=sample_debt_burn_event_data["data"][0],
        amount=Decimal(int(sample_debt_burn_event_data["data"][1], 16)),
    )

    transformer.fetch_and_transform_events(
        from_address=transformer.PROTOCOL_ADDRESSES, min_block=0, max_block=1000
    )

    transformer.db_connector.create_debt_burn_event.assert_called_once_with(
        protocol_id=ProtocolIDs.NOSTRA_ALPHA.value,
        event_name=sample_debt_burn_event_data["key_name"],
        block_number=sample_debt_burn_event_data["block_number"],
        event_data={
            "user": expected_parsed_data.user,
            "amount": expected_parsed_data.amount,
        },
    )


def test_save_debt_transfer_event(transformer, sample_debt_transfer_event_data):
    """
    Test saving a debt transfer event.
    """
    transformer.api_connector.get_data.return_value = [sample_debt_transfer_event_data]

    expected_parsed_data = DebtTransferEventData(
        sender=sample_debt_transfer_event_data["data"][0],
        recipient=sample_debt_transfer_event_data["data"][1],
        amount=Decimal(int(sample_debt_transfer_event_data["data"][2], 16)),
    )

    transformer.fetch_and_transform_events(
        from_address=transformer.PROTOCOL_ADDRESSES, min_block=0, max_block=1000
    )

    transformer.db_connector.create_debt_transfer_event.assert_called_once_with(
        protocol_id=ProtocolIDs.NOSTRA_ALPHA.value,
        event_name=sample_debt_transfer_event_data["key_name"],
        block_number=sample_debt_transfer_event_data["block_number"],
        event_data={
            "sender": expected_parsed_data.sender,
            "recipient": expected_parsed_data.recipient,
            "amount": expected_parsed_data.amount,
        },
    )


def test_save_bearing_collateral_burn_event(
    transformer, sample_bearing_collateral_burn_event_data
):
    """
    Test saving a bearing collateral burn event.
    """
    transformer.api_connector.get_data.return_value = [
        sample_bearing_collateral_burn_event_data
    ]

    expected_parsed_data = BearingCollateralBurnEventData(
        user=sample_bearing_collateral_burn_event_data["data"][0],
        amount=Decimal(int(sample_bearing_collateral_burn_event_data["data"][1], 16)),
    )

    transformer.fetch_and_transform_events(
        from_address=transformer.PROTOCOL_ADDRESSES, min_block=0, max_block=1000
    )

    transformer.db_connector.create_bearing_collateral_burn_event.assert_called_once_with(
        protocol_id=ProtocolIDs.NOSTRA_ALPHA.value,
        event_name=sample_bearing_collateral_burn_event_data["key_name"],
        block_number=sample_bearing_collateral_burn_event_data["block_number"],
        event_data={
            "user": expected_parsed_data.user,
            "amount": expected_parsed_data.amount,
        },
    )


def test_unsupported_event_type(transformer):
    """
    Test handling of unsupported event types.
    """
    unsupported_event = {
        "key_name": "UnsupportedEvent",
        "data": [],
        "block_number": 1000,
    }
    transformer.api_connector.get_data.return_value = [unsupported_event]

    # Should not raise an exception
    transformer.fetch_and_transform_events(
        from_address=transformer.PROTOCOL_ADDRESSES, min_block=0, max_block=1000
    )

    # Verify no DB calls were made for Nostra events
    transformer.db_connector.create_debt_mint_event.assert_not_called()
    transformer.db_connector.create_debt_burn_event.assert_not_called()
    transformer.db_connector.create_debt_transfer_event.assert_not_called()
    transformer.db_connector.create_bearing_collateral_burn_event.assert_not_called()


def test_api_error_handling(transformer):
    """
    Test handling of API errors.
    """
    transformer.api_connector.get_data.return_value = {"error": "API Error"}

    with pytest.raises(ValueError, match="Error fetching events: API Error"):
        transformer.fetch_and_transform_events(
            from_address=transformer.PROTOCOL_ADDRESSES, min_block=0, max_block=1000
        )
