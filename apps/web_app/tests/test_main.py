from copy import deepcopy
from urllib.parse import urlencode

from fastapi import status
from main import app
from starlette.testclient import TestClient
from tests.values import INVALID_DATA, VALID_DATA

from .conftest import mock_database_session

client = TestClient(app)

_HEADERS = {
    "accept": "application/json",
    "Content-Type": "application/x-www-form-urlencoded",
}


def test_create_subscription_to_notifications_get_http_method() -> None:
    response = client.get(
        url="http://127.0.0.1/liquidation-watcher",
        headers=_HEADERS,
    )

    assert response.status_code == status.HTTP_200_OK


# def test_create_subscription_to_notifications_with_valid_data(
#     mock_database_session,
# ) -> None:
#     response = client.post(
#         url="http://127.0.0.1/liquidation-watcher",
#         headers=_HEADERS,
#         data=urlencode(VALID_DATA),
#     )
#
#     assert response.status_code == status.HTTP_200_OK


def test_create_subscription_to_notifications_without_all_data_provided(
    mock_database_session,
) -> None:
    for invalid_data in INVALID_DATA:
        mock_data = deepcopy(INVALID_DATA)
        mock_data[invalid_data] = ""

        response = client.post(
            url="http://127.0.0.1/liquidation-watcher",
            headers=_HEADERS,
            data=urlencode(mock_data),
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

        del mock_data


def test_create_subscription_to_notifications_with_invalid_data(
    mock_database_session,
) -> None:
    response = client.post(
        url="http://127.0.0.1/liquidation-watcher",
        headers=_HEADERS,
        data=urlencode(INVALID_DATA),
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_create_subscription_to_notifications_without_data(
    mock_database_session,
) -> None:
    response = client.post(url="http://127.0.0.1/liquidation-watcher", headers=_HEADERS)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
