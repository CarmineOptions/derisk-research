"""
This module contains a function for making asynchronous HTTP requests using the httpx library.
"""

from json import JSONDecodeError
from typing import Optional

import httpx
from loguru import logger


async def api_request(
    url: str,
    method: str = "GET",
    key: Optional[str] = None,
    convert_to_json: bool = False,
    **kwargs,
) -> Optional[str | httpx.Response]:
    """
    Makes an asynchronous HTTP request using the httpx library.
    Args:
        url (str): URL for request
        method (str, optional): HTTP method to use (default is "GET")
        key (str, optional): key to extract from the JSON response (default is None).
        convert_to_json (bool, optional): convertention the response to JSON (default is False).
        **kwargs: Additional arguments for request.
    Returns:
        str | httpx.Response | None: The response content based on the provided parameters.
    Raises:
        TypeError: If both `key` and `convert_to_json` are provided.
        httpx.HTTPStatusError: If the response contains an HTTP status code indicating an error.
    """
    if key and convert_to_json:
        raise TypeError("Can not have key and json convertation at the same time")

    try:
        async with httpx.AsyncClient() as client:
            request = client.build_request(method=method.upper(), url=url, **kwargs)
            response = await client.send(request=request)
            response.raise_for_status()

            if key:
                return response.json().get(key)
            if convert_to_json:
                return response.json()
            return response

    except httpx.HTTPStatusError as e:
        logger.error(f"API request error: {e}")
    except JSONDecodeError as e:
        logger.error(f"JSON decoding error: {e}")
