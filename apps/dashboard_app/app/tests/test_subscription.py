from fastapi import status
from main import app
from starlette.testclient import TestClient


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
