# tests/db_test/test_db_connector.py

import pytest
from uuid import uuid4
from db.crud import DBConnector
from db.models import LoanState, InterestRate, LiquidableDebt, OrderBookModel, HealthRatioLevel

class TestDBConnector:
    @pytest.fixture(autouse=True)
    def db_connector(self):
        return DBConnector(db_url="sqlite:///:memory:")

    def test_write_to_db_loan_state(self, db_connector):
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

    def test_write_to_db_interest_rate(self, db_connector):
        interest_rate = InterestRate(
            id=uuid4(),
            protocol_id="test_protocol",
            collateral={"token": "150"},
            debt={"token": "75"},
            timestamp=1643723400,
            block=67890
        )
        db_connector.write_to_db(interest_rate)
        
        retrieved_interest_rate = db_connector.get_object(model=InterestRate, obj_id=interest_rate.id)
        assert retrieved_interest_rate == interest_rate

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

    def test_write_to_db_liquidable_debt(self, db_connector):
        liquidable_debt = LiquidableDebt(
            id=uuid4(),
            liquidable_debt=100.0,
            protocol_name="TestProtocol",
            collateral_token_price=1.5,
            collateral_token="USDC",
            debt_token="DAI"
        )
        db_connector.write_to_db(liquidable_debt)
        
        retrieved_liquidable_debt = db_connector.get_object(model=LiquidableDebt, obj_id=liquidable_debt.id)
        assert retrieved_liquidable_debt == liquidable_debt

    def test_write_to_db_order_book_model(self, db_connector):
        order_book_model = OrderBookModel(
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
        db_connector.write_to_db(order_book_model)
        
        retrieved_order_book_model = db_connector.get_object(model=OrderBookModel, obj_id=order_book_model.id)
        assert retrieved_order_book_model == order_book_model

    def test_write_to_db_health_ratio_level(self, db_connector):
        health_ratio_level = HealthRatioLevel(
            id=uuid4(),
            timestamp=1643723400,
            user_id="test_user_1",
            value=1.5,
            protocol_id="TestProtocol"
        )
        db_connector.write_to_db(health_ratio_level)
        
        retrieved_health_ratio_level = db_connector.get_object(model=HealthRatioLevel, obj_id=health_ratio_level.id)
        assert retrieved_health_ratio_level == health_ratio_level

    # Add more test cases for other methods...
