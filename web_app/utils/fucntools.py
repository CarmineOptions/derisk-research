import logging
import pandas as pd
from fastapi import Request

from database.crud import DBConnector
from database.models import NotificationData
from utils.values import (
    CURRENTLY_AVAILABLE_PROTOCOLS,
    DEBT_USD_COLUMN_NAME,
    GS_BUCKET_NAME,
    RISK_ADJUSTED_COLLATERAL_USD_COLUMN_NAME,
    USER_COLUMN_NAME,
    ProtocolIDCodeNames,
)
from utils.zklend import ZkLendLoanEntity, ZkLendState


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


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


def fetch_user_loans(user_id: str = None, protocol_name: str = None) -> pd.DataFrame:
    """
    Fetches user loans data from `.parquet` file
    :param user_id: User wallet ID
    :param protocol_name: Protocol name
    :return: pd.DataFrame
    """
    if protocol_name.lower() not in CURRENTLY_AVAILABLE_PROTOCOLS:
        logger.error(f"Protocol {protocol_name} is not available")
        return None

    logger.info(f"Reading {protocol_name} data from local storage")
    file_url = f"https://storage.googleapis.com/{GS_BUCKET_NAME}/{protocol_name.lower()}_data/loans.parquet"
    try:

        logger.info(f"URL: {file_url}")
        df = pd.read_parquet(file_url)
        user_data = df[df[USER_COLUMN_NAME] == user_id]
        return user_data.to_dict()
    except Exception as e:
        logger.error(f"Error reading {protocol_name} data: {e}")
        return


def get_user_row_number(user: dict[str, dict[int, str]] = None) -> int | None:
    """
    Returns the user row number in the `.parquet` file.
    :param user: dict[str, dict[int, str]]
    :return: int
    """
    if user and USER_COLUMN_NAME in user:
        # Directly access the first key
        try:
            return list(user[USER_COLUMN_NAME].keys())[0]
        except IndexError:
            logger.error(f"User data: {user}")
            return None
    else:
        return None


def get_debt_usd(
    user_data: dict[str, dict[int, str]] = None, user_row_number: int = None
) -> float | None:
    """
    Returns debt usd value from user_data parameter
    :param user_data: dict[str, dict[int, str]] = None
    :param user_row_number: int = None
    :return: float | None
    """
    collateral_data = user_data.get(DEBT_USD_COLUMN_NAME, None)

    if collateral_data:
        return collateral_data.get(user_row_number, None)

    return None


def get_risk_adjusted_collateral_usd(
    user_data: dict[str, dict[int, str]] = None, user_row_number: int = None
) -> float | None:
    """
    Returns risk adjusted collateral usd value from user_data parameter
    :param user_data: dict[str, dict[int, str]] = None
    :param user_row_number: int = None
    :return: float | None
    """
    collateral_data = user_data.get(RISK_ADJUSTED_COLLATERAL_USD_COLUMN_NAME, None)

    if collateral_data:
        return collateral_data.get(user_row_number, None)

    return None


def get_all_activated_subscribers_from_db() -> list[NotificationData]:
    """
    Returns all activated subscribers from database
    :return: list[NotificationData]
    """
    return list(DBConnector().get_all_activated_subscribers(model=NotificationData))


def calculate_difference(a: float = None, b: float = None) -> float:
    """
    Calculates difference between two numbers
    """
    if a >= b:
        return a - b
    else:
        return b - a


def compute_health_ratio_level(
    user_id: str = None, protocol_name: str = None
) -> float | None:
    """
    Computes health ratio level based on user wallet ID and protocol name
    :param user_id: User wallet ID
    :param protocol_name: Protocol name
    :return: float
    """

    # Get only needed User from the whole file
    user_data = fetch_user_loans(user_id=user_id, protocol_name=protocol_name)
    if not user_data:
        return
    # Getting all data needed for the final calculation
    user_row_number = get_user_row_number(user_data)
    if user_row_number is None:
        return
    debt_usd = get_debt_usd(user_data, user_row_number)
    risk_adjusted_collateral_usd = get_risk_adjusted_collateral_usd(
        user_data, user_row_number
    )

    entity = ZkLendLoanEntity()
    state = ZkLendState()

    return entity.compute_health_factor(
        standardized=True,
        risk_adjusted_collateral_usd=risk_adjusted_collateral_usd,
        debt_usd=debt_usd,
        collateral_interest_rate_models=state.collateral_interest_rate_models,
        debt_interest_rate_models=state.debt_interest_rate_models,
    )
