import json

from starlette.testclient import TestClient

from main import app
from tests.values import INVALID_DATA, VALID_DATA

from .conftest import mock_database_session

client = TestClient(app)

_HEADERS = {"accept": "application/json", "Content-Type": "application/json"}


def test_create_subscription_to_notifications_with_valid_data(
    mock_database_session,
) -> None:
    response = client.post(
        url="/create-notifications-subscription",
        headers=_HEADERS,
        data=json.dumps(VALID_DATA),
    )

    assert response.status_code == 200


def test_create_subscription_to_notifications_with_invalid_data(
    mock_database_session,
) -> None:
    response = client.post(
        url="/create-notifications-subscription",
        headers=_HEADERS,
        data=json.dumps(INVALID_DATA),
    )

    assert response.status_code == 422


def test_create_subscription_to_notifications_without_data(
    mock_database_session,
) -> None:
    response = client.post(url="/create-notifications-subscription", headers=_HEADERS)

    assert response.status_code == 422