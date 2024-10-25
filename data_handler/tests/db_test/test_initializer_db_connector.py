# tests/db_test/test_initializer_db_connector.py

import pytest
from uuid import uuid4
from db.crud import InitializerDBConnector
from db.models import ZkLendCollateralDebt, HashtackCollateralDebt

class TestInitializerDBConnector:
    @pytest.fixture(autouse=True)
    def initializer_db_connector(self):
        return InitializerDBConnector(db_url="sqlite:///:memory:")

    def test_get_zklend_by_user_ids(self, initializer_db_connector):
        user_id1 = str(uuid4())
        user_id2 = str(uuid4())

        initializer_db_connector.save_collateral_enabled_by_user(
            user_id=user_id1,
            collateral_enabled={"token": True},
            collateral={"token": 100},
            debt={"token": 50}
        )
        
        initializer_db_connector.save_collateral_enabled_by_user(
            user_id=user_id2,
            collateral_enabled={"token": False},
            collateral={"token": 200},
            debt={"token": 75}
        )

        retrieved_records = initializer_db_connector.get_zklend_by_user_ids([user_id1, user_id2])
        assert len(retrieved_records) == 2
        assert any(record.user_id == user_id1 for record in retrieved_records)
        assert any(record.user_id == user_id2 for record in retrieved_records)

    def test_save_debt_category(self, initializer_db_connector):
        loan_id = str(uuid4())
        user_id = str(uuid4())

        initializer_db_connector.save_debt_category(
            user_id=user_id,
            loan_id=loan_id,
            debt_category="test_category",
            collateral={"token": 150},
            debt={"token": 75},
            original_collateral={"token": 100},
            borrowed_collateral={"token": 50},
            version=1
        )

        retrieved_record = initializer_db_connector.get_hashtack_by_loan_ids([loan_id], version=1)[0]
        assert retrieved_record.loan_id == loan_id
        assert retrieved_record.debt_category == "test_category"
        assert retrieved_record.collateral == {"token": 150}
        assert retrieved_record.debt == {"token": 75}
        assert retrieved_record.original_collateral == {"token": 100}
        assert retrieved_record.borrowed_collateral == {"token": 50}


    def test_get_zklend_by_user_ids_empty_result(self, initializer_db_connector):
        retrieved_records = initializer_db_connector.get_zklend_by_user_ids(["nonexistent_user"])
        assert len(retrieved_records) == 0

    def test_save_debt_category_invalid_version(self, initializer_db_connector):
        loan_id = str(uuid4())
        user_id = str(uuid4())

        with pytest.raises(ValueError):
            initializer_db_connector.save_debt_category(
                user_id=user_id,
                loan_id=loan_id,
                debt_category="test_category",
                collateral={"token": 150},
                debt={"token": 75},
                original_collateral={"token": 100},
                borrowed_collateral={"token": 50},
                version=-1  # Invalid version
            )
            retrieved_new_entry = initializer_db_connector.get_hashtack_by_loan_ids([loan_id], version=-1)[0]
            assert retrieved_new_entry is None
