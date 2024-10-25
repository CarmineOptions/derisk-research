# tests/db_test/test_db_connector.py

import pytest
from uuid import uuid4
from db.crud import DBConnector
from db.models import LoanState, InterestRate, OrderBookModel, ZkLendCollateralDebt, HashtackCollateralDebt

class TestDBConnector:
    @pytest.fixture(autouse=True)
    def db_connector(self):
        return DBConnector(db_url="sqlite:///:memory:")

    def test_write_to_db(self, db_connector):
        loan_state = LoanState(
            id=uuid4(),
            protocol_id="test_protocol",
            user="test_user",
            collateral={"token": "100"},
            debt={"token": "50"},
            timestamp=1643723400,
            block=12345,
            deposit={"token": "25"}
        )
        db_connector.write_to_db(loan_state)
        
        retrieved_loan_state = db_connector.get_object(model=LoanState, obj_id=loan_state.id)
        assert retrieved_loan_state == loan_state
        #negative scenario
        with pytest.raises(Exception):
            incomplete_loan_state = LoanState(
                id=uuid4(),
                protocol_id="",
                user="",
                collateral={},
                debt={},
                timestamp=None,
                block=None,
                deposit={}
            )
            db_connector.write_to_db(incomplete_loan_state)

    def test_get_object(self, db_connector):
        loan_state = LoanState(
            id=uuid4(),
            protocol_id="test_protocol",
            user="test_user",
            collateral={"token": "100"},
            debt={"token": "50"},
            timestamp=1643723400,
            block=12345,
            deposit={"token": "25"}
        )
        db_connector.write_to_db(loan_state)
        
        retrieved_loan_state = db_connector.get_object(model=LoanState, obj_id=loan_state.id)
        assert retrieved_loan_state == loan_state
        # Negative scenario
        non_existent_id = uuid4()
        result = db_connector.get_object(model=LoanState, obj_id=non_existent_id)
        assert result is None

    def test_delete_object(self, db_connector):
        loan_state = LoanState(
            id=uuid4(),
            protocol_id="test_protocol",
            user="test_user",
            collateral={"token": "100"},
            debt={"token": "50"},
            timestamp=1643723400,
            block=12345,
            deposit={"token": "25"}
        )
        db_connector.write_to_db(loan_state)
        
        db_connector.delete_object(model=LoanState, obj_id=loan_state.id)
        
        retrieved_loan_state = db_connector.get_object(model=LoanState, obj_id=loan_state.id)
        assert retrieved_loan_state is None

        # Negative scenario: Attempt to delete a non-existent object
        with pytest.raises(Exception):
            db_connector.delete_object(model=LoanState, obj_id=uuid4())


    def test_get_latest_block(self, db_connector):
        loan_state1 = LoanState(
            id=uuid4(),
            protocol_id="test_protocol",
            user="test_user",
            collateral={"token": "100"},
            debt={"token": "50"},
            timestamp=1643723400,
            block=12345,
            deposit={"token": "25"}
        )
        loan_state2 = LoanState(
            id=uuid4(),
            protocol_id="test_protocol",
            user="test_user",
            collateral={"token": "150"},
            debt={"token": "75"},
            timestamp=1643723400,
            block=67890,
            deposit={"token": "37.5"}
        )
        
        db_connector.write_to_db(loan_state1)
        db_connector.write_to_db(loan_state2)
        
        latest_block = db_connector.get_last_block(protocol_id="test_protocol")
        assert latest_block == 67890

        # Negative scenario: No blocks for given protocol should return None
        non_existent_protocol = "non_existent_protocol"
        latest_block = db_connector.get_last_block(protocol_id=non_existent_protocol)
        assert latest_block is None

    def test_write_batch_to_db(self, db_connector):
        loan_states = [
            LoanState(
                id=uuid4(),
                protocol_id="test_protocol",
                user="user1",
                collateral={"token": "100"},
                debt={"token": "50"},
                timestamp=1643723400,
                block=12345,
                deposit={"token": "25"}
            ),
            LoanState(
                id=uuid4(),
                protocol_id="test_protocol",
                user="user2",
                collateral={"token": "150"},
                debt={"token": "75"},
                timestamp=1643723400,
                block=67890,
                deposit={"token": "37.5"}
            )
        ]
        db_connector.write_batch_to_db(loan_states)
        
        retrieved_loan_states = db_connector.get_object(model=LoanState)
        assert len(retrieved_loan_states) == 2
        assert any(ls.user == "user1" for ls in retrieved_loan_states)
        assert any(ls.user == "user2" for ls in retrieved_loan_states)

        # Negative scenario: Attempt to write an invalid batch with an incomplete LoanState
        invalid_loan_states = loan_states + [LoanState(id=uuid4())]  # Incomplete LoanState
        with pytest.raises(Exception):
            db_connector.write_batch_to_db(invalid_loan_states)


    def test_get_latest_order_book(self, db_connector):
        order_book = OrderBookModel(
            id=uuid4(),
            token_a="ETH",
            token_b="USDC",
            timestamp=1643723400,
            block=12345,
            dex="Uniswap",
            current_price=3000.0,
            asks=[{"price": 2999.0, "amount": 100}, {"price": 3000.0, "amount": 200}],
            bids=[{"price": 3001.0, "amount": 150}]
        )
        db_connector.write_to_db(order_book)
        
        retrieved_order_book = db_connector.get_latest_order_book(dex="Uniswap", token_a="ETH", token_b="USDC")
        assert retrieved_order_book == order_book

        # Negative scenario: Retrieve order book with non-existent token pair
        result = db_connector.get_latest_order_book(dex="Uniswap", token_a="BTC", token_b="ETH")
        assert result is None

    def test_get_unique_users_last_block_objects(self, db_connector):
        loan_state1 = LoanState(
            id=uuid4(),
            protocol_id="test_protocol",
            user="user1",
            collateral={"token": "100"},
            debt={"token": "50"},
            timestamp=1643723400,
            block=12345,
            deposit={"token": "25"}
        )
        loan_state2 = LoanState(
            id=uuid4(),
            protocol_id="test_protocol",
            user="user2",
            collateral={"token": "150"},
            debt={"token": "75"},
            timestamp=1643723400,
            block=67890,
            deposit={"token": "37.5"}
        )
        db_connector.write_to_db(loan_state1)
        db_connector.write_to_db(loan_state2)
        
        unique_users_last_blocks = db_connector.get_unique_users_last_block_objects(protocol_id="test_protocol")
        assert len(unique_users_last_blocks) == 2
        assert any(ls.user == "user1" for ls in unique_users_last_blocks)
        assert any(ls.user == "user2" for ls in unique_users_last_blocks)

    def test_get_last_interest_rate_record_by_protocol_id(self, db_connector):
        interest_rate = InterestRate(
            id=uuid4(),
            protocol_id="test_protocol",
            collateral={"token": "150"},
            debt={"token": "75"},
            timestamp=1643723400,
            block=67890
        )
        db_connector.write_to_db(interest_rate)
        
        last_interest_rate = db_connector.get_last_interest_rate_record_by_protocol_id("test_protocol")
        assert last_interest_rate == interest_rate

    def test_get_interest_rate_by_block(self, db_connector):
        interest_rate = InterestRate(
            id=uuid4(),
            protocol_id="test_protocol",
            collateral={"token": "150"},
            debt={"token": "75"},
            timestamp=1643723400,
            block=67890
        )
        db_connector.write_to_db(interest_rate)
        
        retrieved_interest_rate = db_connector.get_interest_rate_by_block(block_number=67890, protocol_id="test_protocol")
        assert retrieved_interest_rate == interest_rate

         # Negative scenario: Attempt to retrieve interest rate for non-existent block
        non_existent_block = 99999
        result = db_connector.get_interest_rate_by_block(block_number=non_existent_block, protocol_id="test_protocol")
        assert result is None

    def test_get_all_block_records(self, db_connector):
        loan_states = [
            LoanState(
                id=uuid4(),
                protocol_id="test_protocol",
                user="user1",
                collateral={"token": "100"},
                debt={"token": "50"},
                timestamp=1643723400,
                block=12345,
                deposit={"token": "25"}
            ),
            LoanState(
                id=uuid4(),
                protocol_id="test_protocol",
                user="user2",
                collateral={"token": "150"},
                debt={"token": "75"},
                timestamp=1643723400,
                block=67890,
                deposit={"token": "37.5"}
            )
        ]
        db_connector.write_batch_to_db(loan_states)
        
        all_block_records = db_connector.get_all_block_records(model=LoanState)
        assert len(all_block_records) == 2
        assert all_block_records[0].collateral == {"token": "100"}
        assert all_block_records[1].collateral == {"token": "150"}


def test_write_loan_states_to_db(self, db_connector):
    loan_states = [
        LoanState(
            id=uuid4(),
            protocol_id="test_protocol",
            user="user1",
            collateral={"token": "100"},
            debt={"token": "50"},
            timestamp=1643723400,
            block=12345,
            deposit={"token": "25"}
        ),
        LoanState(
            id=uuid4(),
            protocol_id="test_protocol",
            user="user2",
            collateral={"token": "200"},
            debt={"token": "100"},
            timestamp=1643723401,
            block=12346,
            deposit={"token": "50"}
        )
    ]
    db_connector.write_batch_to_db(loan_states)

    for loan_state in loan_states:
        retrieved_loan_state = db_connector.get_object(model=LoanState, obj_id=loan_state.id)
        assert retrieved_loan_state == loan_state

    # Negative Scenario: Attempt to write an invalid list (with incomplete LoanState object) and expect failure
    invalid_loan_states = loan_states + [
        LoanState(
            id=uuid4(),
            protocol_id="",
            user="",
            collateral={},
            debt={},
            timestamp=None,
            block=None,
            deposit={}
        )
    ]
    with pytest.raises(Exception):
        db_connector.write_batch_to_db(invalid_loan_states)
