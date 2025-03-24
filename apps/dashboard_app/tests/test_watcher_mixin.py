from typing import Type
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy import Float, String
from sqlalchemy.orm import Mapped, Session
from sqlalchemy.testing.schema import mapped_column

from app.models.base import Base
from app.utils.values import CreateSubscriptionValues
from app.utils.watcher_mixin import WatcherMixin


class MockModel(Base):
    __tablename__ = "mock_table"
    test_attr: Mapped[str] = mapped_column(String, nullable=False)
    health_ratio_level: Mapped[float] = mapped_column(Float, nullable=False)

    def __repr__(self) -> str:
        """ """
        return f"<Mock(test_attr={self.test_attr}, health_ratio={self.health_ratio_level})>"


@pytest.fixture
def mock_db_session():
    return MagicMock()


@pytest.mark.parametrize(
    "health_ratio, expected",
    [
        (None, False),
        (-1.0, False),
        (0.0, True),
        (5.0, True),
        (10.0, True),
        (11.0, False),
    ],
)
def test_health_ratio_is_valid(health_ratio, expected):
    result = WatcherMixin.health_ratio_is_valid(health_ratio)
    assert result == expected


invalid_health_ratio_response = {
    "health_ratio_level": CreateSubscriptionValues.health_ratio_level_validation_message
}


@pytest.mark.parametrize(
    "health_ratio, expected",
    [
        (None, invalid_health_ratio_response),
        (-1.0, invalid_health_ratio_response),
        (0.0, None),
        (5.0, None),
        (10.0, None),
        (11.0, invalid_health_ratio_response),
    ],
)
def test_validate_health_ratio(health_ratio, expected):
    result = WatcherMixin.validate_health_ratio(health_ratio)
    assert result == expected


@pytest.mark.parametrize(
    "exists_in_db_value, fields_value, health_ratio_level, expected_dict",
    [
        (True, (), 5.0, {}),
        (True, ("test_attr"), 5.0, {"test_attr": "Current test attr is already taken"}),
        (False, ("test_attr"), 10.0, {}),
        (
            False,
            ("test_attr"),
            11.0,
            {"health_ratio_level": "Your health ratio level must be between 0 and 10"},
        ),
        (
            True,
            ("test_attr"),
            11.0,
            {
                "health_ratio_level": "Your health ratio level must be between 0 and 10",
                "test_attr": "Current test attr is already taken",
            },
        ),
    ],
)
def test_validate_fields(
    exists_in_db_value: bool,
    fields_value: tuple,
    health_ratio_level: float,
    expected_dict: dict,
    mock_db_session,
):
    with patch(
        "app.utils.watcher_mixin.WatcherMixin._exists_in_db",
        return_value=exists_in_db_value,
    ):
        mock_obj = MockModel(test_attr="test", health_ratio_level=health_ratio_level)
        with patch(
            "app.utils.values.NotificationValidationValues.unique_fields", fields_value
        ):
            result = WatcherMixin.validate_fields(
                db=mock_db_session, obj=mock_obj, model=MockModel
            )
            assert result == expected_dict
