"""
Test the zklend transformer
"""

import pytest
from typing import Dict, Any
from shared.constants import ProtocolIDs
from unittest.mock import MagicMock, patch
from data_handler.handlers.events.zklend.transform_events import ZklendTransformer
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


@pytest.fixture(scope="function")
def transformer():
    """
    Fixture to create a ZklendTransformer instance with mocked dependencies.
    """
    with patch('data_handler.handlers.events.zklend.transform_events.DeRiskAPIConnector') as mock_api, \
         patch('data_handler.handlers.events.zklend.transform_events.ZkLendEventDBConnector') as mock_db:
        
        # Configure mock DB
        mock_db_instance = mock_db.return_value
        mock_db_instance.get_last_block.return_value = 0
        
        # Configure mock API
        mock_api_instance = mock_api.return_value
        
        transformer = ZklendTransformer()
        transformer.api_connector = mock_api_instance
        transformer.db_connector = mock_db_instance
        
        return transformer

@pytest.fixture(scope="function")
def sample_borrowing_event_data() -> Dict[str, Any]:
    """
    Sample borrowing event data
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
            "0x1a0027d1bf86904d1051fe0ca94c39b659135f19504d663d66771a7424ca2eb",
            "0x49d36570d4e46f48e99674bd3fcc84644ddd6b96f7c741b1562b82f9e004dc7",
            "0x8ec920c39e9",
            "0x9184e72a000"
        ],
        "timestamp": 1712276824,
        "key_name": "zklend::market::Market::Borrowing"
    }


@pytest.fixture(scope="function")
def sample_repayment_event_data() -> Dict[str, Any]:
    """
    Sample repayment event data
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
            "0x7f121e44b3f446cdcaa28b230546956208d51e96894acc3b482947356bc10ed",
            "0x7f121e44b3f446cdcaa28b230546956208d51e96894acc3b482947356bc10ed",
            "0x3fe2b97c1fd336e750087d68b9b867997fd64a2661ff3ca5a7c771641e8e7ac",
            "0xd60",
            "0xdaf"
        ],
        "timestamp": 1712275350,
        "key_name": "zklend::market::Market::Repayment"
    }


@pytest.fixture(scope="function")
def sample_deposit_event_data() -> Dict[str, Any]:
    """
    Sample deposit event data
    """
    return {
        "id": "0x053217250e329e81d69d44a9f89bb65c4b97d07693f4a59ee32d898f5e0beef2_5",
        "block_hash": "0x07d1b221c40b6a19c0381d61ebbe8d048018b49314ae1bdc93938059e29febdf",
        "block_number": 630008,
        "transaction_hash": "0x053217250e329e81d69d44a9f89bb65c4b97d07693f4a59ee32d898f5e0beef2",
        "event_index": 5,
        "from_address": "0x04c0a5193d58f74fbace4b74dcf65481e734ed1714121bdc571da345540efa05",
        "keys": ["0x9149d2123147c5f43d258257fef0b7b969db78269369ebcf5ebb9eef8592f2"],
        "data": [
            "0x1cfa080d4bbddc206637afad05e5e1abb04da69630f40b2fd9dc578e618ec78",
            "0x585c32b625999e6e5e78645ff8df7a9001cf5cf3eb6b80ccdd16cb64bd3a34",
            "0x14839256fce60ba2c"
        ],
        "timestamp": 1712276824,
        "key_name": "zklend::market::Market::Deposit"
    }


@pytest.fixture(scope="function")
def sample_withdrawal_event_data() -> Dict[str, Any]:
    """
    Sample withdrawal event data
    """
    return {
        "id": "0x01e6bdd3a0cc5531b97ba28c135ceffd0d528aa648a8731e0dfb0ca293465991_3",
        "block_hash": "0x06eb8ae20d3e98d69025be79135523cded41257cfd694b1aea02ddec8e9196d9",
        "block_number": 630009,
        "transaction_hash": "0x01e6bdd3a0cc5531b97ba28c135ceffd0d528aa648a8731e0dfb0ca293465991",
        "event_index": 3,
        "from_address": "0x04c0a5193d58f74fbace4b74dcf65481e734ed1714121bdc571da345540efa05",
        "keys": ["0x2eed7e29b3502a726faf503ac4316b7101f3da813654e8df02c13449e03da8"],
        "data": [
            "0x49920f8f551060f726e3c8c2fe26e2b39376027450b7672634824bd60c64022",
            "0x585c32b625999e6e5e78645ff8df7a9001cf5cf3eb6b80ccdd16cb64bd3a34",
            "0x176b344f2a78c0000"
        ],
        "timestamp": 1712277188,
        "key_name": "zklend::market::Market::Withdrawal"
    }



@pytest.fixture(scope="function")
def sample_collateral_enabled_event_data() -> Dict[str, Any]:
    """
    Sample collateral enabled event data
    """
    return {
        "id": "0x043e9faa1cb77136dcbfcd7d093583bd877d10e55b5ebe83c49c88853d46a744_0",
        "block_hash": "0x03a7d0eac98323ecf1c756e5c10668a1e82dd6a858ed2909f36797e471279853",
        "block_number": 630010,
        "transaction_hash": "0x043e9faa1cb77136dcbfcd7d093583bd877d10e55b5ebe83c49c88853d46a744",
        "event_index": 0,
        "from_address": "0x04c0a5193d58f74fbace4b74dcf65481e734ed1714121bdc571da345540efa05",
        "keys": ["0x2324062bde6ebb76ffd17d55fee62fee62a4877588eb02524b19c091983b365"],
        "data": [
            "0x54f9574d3029b81e0d64e3267a7b682ab920b57948644de4581f5ceb30351ea",
            "0xda114221cb83fa859dbdb4c44beeaa0bb37c7537ad5ae66fe5e0efd20e6eb3"
        ],
        "timestamp": 1712277561,
        "key_name": "zklend::market::Market::CollateralEnabled"
    }


@pytest.fixture(scope="function")
def sample_collateral_disabled_event_data() -> Dict[str, Any]:
    """
    Sample collateral disabled event data
    """
    return {
        "id": "0x03b10eded4321e6385993b392c8c9a07be54ae822c467b0d6e029886c7ddf62b_0",
        "block_hash": "0x022e7611bf432bfefe7743b69da8fb498834ffbc2bbe220c57dd8709c1247596",
        "block_number": 630028,
        "transaction_hash": "0x03b10eded4321e6385993b392c8c9a07be54ae822c467b0d6e029886c7ddf62b",
        "event_index": 0,
        "from_address": "0x04c0a5193d58f74fbace4b74dcf65481e734ed1714121bdc571da345540efa05",
        "keys": ["0xf999d0d33513a8215756ae6a9223180a439c134372b158bc84b9dd02f63856"],
        "data": [
            "0x237be5917e0f4ceba3067af8f11137cc7262b9444fce220183e7fdffe4c1a40",
            "0x4718f5a0fc34cc1af16a1cdee98ffb20c31f5cd61d6ab07201858f4287c938d"
        ],
        "timestamp": 1712284226,
        "key_name": "zklend::market::Market::CollateralDisabled"
    }


@pytest.fixture(scope="function")
def sample_accumulators_sync_event_data() -> Dict[str, Any]:
    """
    Sample accumulators sync event data
    """
    return {
        "id": "0x001dfdb09e48a91cf6297c9fd50878c25b91ab67cb826a50f05ef03bd74192c6_0",
        "block_hash": "0x0474f1553ebeba66a52163ad62172f27d797d6b139159c391b611f5c7ab58e96",
        "block_number": 630029,
        "transaction_hash": "0x001dfdb09e48a91cf6297c9fd50878c25b91ab67cb826a50f05ef03bd74192c6",
        "event_index": 0,
        "from_address": "0x04c0a5193d58f74fbace4b74dcf65481e734ed1714121bdc571da345540efa05",
        "keys": ["0x30c296ae369716818de77cb5b71ce9cda7cc2c0e8456f474e0abb1ae8d017da"],
        "data": ["0x53c91253bc9682c04929ca02ed00b3e423f6710d2ee7e0d5ebb06f3ecf368a8", "0x3583127bd9f4ef81d8d7b6e", "0x364c261a781ab91b6c39aca"],
        "timestamp": 1712284614,
        "key_name": "zklend::market::Market::AccumulatorsSync"
    }


def test_save_borrowing_event(transformer, sample_borrowing_event_data):
    """
    Test saving a borrowing event.
    """
    # Setup API response
    transformer.api_connector.get_data.return_value = [sample_borrowing_event_data]

    expected_parsed_data = BorrowingEventData(
        user=sample_borrowing_event_data['data'][0],
        token=sample_borrowing_event_data['data'][1],
        raw_amount=sample_borrowing_event_data['data'][2],
        face_amount=sample_borrowing_event_data['data'][3]
    )

    # Call the method
    transformer.fetch_and_transform_events(
        from_address=transformer.PROTOCOL_ADDRESSES,
        min_block=0,
        max_block=1000
    )

    # Verify DB connector was called with correct data
    transformer.db_connector.create_borrowing_event.assert_called_once_with(
        protocol_id=ProtocolIDs.ZKLEND,
        event_name=sample_borrowing_event_data['key_name'],
        block_number=sample_borrowing_event_data['block_number'],
        event_data={
            'user': expected_parsed_data.user,
            'token': expected_parsed_data.token,
            'raw_amount': expected_parsed_data.raw_amount,
            'face_amount': expected_parsed_data.face_amount
        }
    )


def test_save_repayment_event(transformer, sample_repayment_event_data):
    """
    Test saving a repayment event.
    """
    transformer.api_connector.get_data.return_value = [sample_repayment_event_data]

    expected_parsed_data = RepaymentEventData(
        repayer=sample_repayment_event_data['data'][0],
        beneficiary=sample_repayment_event_data['data'][1],
        token=sample_repayment_event_data['data'][2],
        raw_amount=sample_repayment_event_data['data'][3],
        face_amount=sample_repayment_event_data['data'][4]
    )

    transformer.fetch_and_transform_events(
        from_address=transformer.PROTOCOL_ADDRESSES,
        min_block=0,
        max_block=1000
    )

    transformer.db_connector.create_repayment_event.assert_called_once_with(
        protocol_id=ProtocolIDs.ZKLEND,
        event_name=sample_repayment_event_data['key_name'],
        block_number=sample_repayment_event_data['block_number'],
        event_data={
            'repayer': expected_parsed_data.repayer,
            'beneficiary': expected_parsed_data.beneficiary,
            'token': expected_parsed_data.token,
            'raw_amount': expected_parsed_data.raw_amount,
            'face_amount': expected_parsed_data.face_amount
        }
    )


def test_unsupported_event_type(transformer):
    """
    Test handling of unsupported event types.
    """
    unsupported_event = {
        'key_name': 'UnsupportedEvent',
        'data': [],
        'block_number': 1000
    }
    transformer.api_connector.get_data.return_value = [unsupported_event]

    # Should not raise an exception
    transformer.fetch_and_transform_events(
        from_address=transformer.PROTOCOL_ADDRESSES,
        min_block=0,
        max_block=1000
    )

    # Verify no DB calls were made
    transformer.db_connector.create_borrowing_event.assert_not_called()
    transformer.db_connector.create_repayment_event.assert_not_called()
    transformer.db_connector.create_deposit_event.assert_not_called()
    transformer.db_connector.create_withdrawal_event.assert_not_called()
    transformer.db_connector.create_collateral_enabled_event.assert_not_called()
    transformer.db_connector.create_collateral_disabled_event.assert_not_called()
    transformer.db_connector.create_accumulators_sync_event.assert_not_called()


def test_api_error_handling(transformer):
    """
    Test handling of API errors.
    """
    transformer.api_connector.get_data.return_value = {'error': 'API Error'}

    with pytest.raises(ValueError, match='Error fetching events: API Error'):
        transformer.fetch_and_transform_events(
            from_address=transformer.PROTOCOL_ADDRESSES,
            min_block=0,
            max_block=1000
        )


def test_save_deposit_event(transformer, sample_deposit_event_data):
    """
    Test saving a deposit event.
    """
    transformer.api_connector.get_data.return_value = [sample_deposit_event_data]

    expected_parsed_data = DepositEventData(
        user=sample_deposit_event_data['data'][0],
        token=sample_deposit_event_data['data'][1],
        face_amount=sample_deposit_event_data['data'][2]
    )

    transformer.fetch_and_transform_events(
        from_address=transformer.PROTOCOL_ADDRESSES,
        min_block=0,
        max_block=1000
    )

    transformer.db_connector.create_deposit_event.assert_called_once_with(
        protocol_id=ProtocolIDs.ZKLEND,
        event_name=sample_deposit_event_data['key_name'],
        block_number=sample_deposit_event_data['block_number'],
        event_data={
            'user': expected_parsed_data.user,
            'token': expected_parsed_data.token,
            'face_amount': expected_parsed_data.face_amount
        }
    )


def test_save_withdrawal_event(transformer, sample_withdrawal_event_data):
    """
    Test saving a withdrawal event.
    """
    transformer.api_connector.get_data.return_value = [sample_withdrawal_event_data]

    expected_parsed_data = WithdrawalEventData(
        user=sample_withdrawal_event_data['data'][0],
        token=sample_withdrawal_event_data['data'][2],
        amount=sample_withdrawal_event_data['data'][1]
    )

    transformer.fetch_and_transform_events(
        from_address=transformer.PROTOCOL_ADDRESSES,
        min_block=0,
        max_block=1000
    )

    transformer.db_connector.create_withdrawal_event.assert_called_once_with(
        protocol_id=ProtocolIDs.ZKLEND,
        event_name=sample_withdrawal_event_data['key_name'],
        block_number=sample_withdrawal_event_data['block_number'],
        event_data={
            'user': expected_parsed_data.user,
            'token': expected_parsed_data.token,
            'amount': expected_parsed_data.amount
        }
    )


def test_save_collateral_enabled_event(transformer, sample_collateral_enabled_event_data):
    """
    Test saving a collateral enabled event.
    """
    transformer.api_connector.get_data.return_value = [sample_collateral_enabled_event_data]
    expected_parsed_data = CollateralEnabledDisabledEventData(
        user=sample_collateral_enabled_event_data['data'][0],
        token=sample_collateral_enabled_event_data['data'][1],
    )

    transformer.fetch_and_transform_events(
        from_address=transformer.PROTOCOL_ADDRESSES,
        min_block=0,
        max_block=1000
    )

    transformer.db_connector.create_collateral_enabled_disabled_event.assert_called_once_with(
        protocol_id=ProtocolIDs.ZKLEND,
        event_name=sample_collateral_enabled_event_data['key_name'],
        block_number=sample_collateral_enabled_event_data['block_number'],
        event_data={
            'user': expected_parsed_data.user,
            'token': expected_parsed_data.token
        }
    )


def test_save_collateral_disabled_event(transformer, sample_collateral_disabled_event_data):
    """
    Test saving a collateral disabled event.
    """
    transformer.api_connector.get_data.return_value = [sample_collateral_disabled_event_data]

    expected_parsed_data = CollateralEnabledDisabledEventData(
        user=sample_collateral_disabled_event_data['data'][0],
        token=sample_collateral_disabled_event_data['data'][1]
    )

    transformer.fetch_and_transform_events(
        from_address=transformer.PROTOCOL_ADDRESSES,
        min_block=0,
        max_block=1000
    )

    transformer.db_connector.create_collateral_enabled_disabled_event.assert_called_once_with(
        protocol_id=ProtocolIDs.ZKLEND,
        event_name=sample_collateral_disabled_event_data['key_name'],
        block_number=sample_collateral_disabled_event_data['block_number'],
        event_data={
            'user': expected_parsed_data.user,
            'token': expected_parsed_data.token
        }
    )

def test_save_accumulators_sync_event(transformer, sample_accumulators_sync_event_data):
    """
    Test saving an accumulators sync event.
    """
    transformer.api_connector.get_data.return_value = [sample_accumulators_sync_event_data]

    expected_parsed_data = AccumulatorsSyncEventData(
        token=sample_accumulators_sync_event_data['data'][0],
        lending_accumulator=sample_accumulators_sync_event_data['data'][1],
        debt_accumulator=sample_accumulators_sync_event_data['data'][2]
    )

    transformer.fetch_and_transform_events(
        from_address=transformer.PROTOCOL_ADDRESSES,
        min_block=0,
        max_block=1000
    )

    transformer.db_connector.create_accumulator_event.assert_called_once_with(
        protocol_id=ProtocolIDs.ZKLEND,
        event_name=sample_accumulators_sync_event_data['key_name'],
        block_number=sample_accumulators_sync_event_data['block_number'],
        event_data={
            'token': expected_parsed_data.token,
            'lending_accumulator': expected_parsed_data.lending_accumulator,
            'debt_accumulator': expected_parsed_data.debt_accumulator
        }
    )
