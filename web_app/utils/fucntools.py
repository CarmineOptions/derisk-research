from fastapi import Request


def get_client_ip(request: Request) -> str:
    """
    Returns the client IP address
    :param request: Request
    :return: str
    """
    x_forwarded_for = request.headers.get("x-forwarded-for", "")

    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[0]
    else:
        ip = request.client.host

    return ip
