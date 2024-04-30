from unittest.mock import MagicMock

import pytest

from database.database import get_database
from main import app

mock_session = MagicMock()


def get_test_database() -> MagicMock | None:
    """
    Creates the test database session
    :return: MagicMock | None
    """
    try:
        yield mock_session
    finally:
        mock_session.reset_mock()


app.dependency_overrides[get_database] = get_test_database


@pytest.fixture
def mock_database_session() -> MagicMock:
    """
    Mocks the database session
    :return: MagicMock
    """
    return mock_session
