import os
import time
import shutil
import logging

import dask.dataframe as dd
import pandas as pd
from fastapi import Request

from database.crud import DBConnector
from database.models import NotificationData
from utils.exceptions import ProtocolExistenceError
from utils.values import (CURRENTLY_AVAILABLE_PROTOCOLS, DEBT_USD_COLUMN_NAME,
                          GS_BUCKET_NAME, GS_BUCKET_URL,
                          RISK_ADJUSTED_COLLATERAL_USD_COLUMN_NAME,
                          USER_COLUMN_NAME, ProtocolIDCodeNames)
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


def download_parquet_file(
    protocol_name: str = None,
    bucket_name: str | None = GS_BUCKET_NAME,
) -> None:
    """
    Downloads parquet file to local storage from Google Cloud Storage
    :param protocol_name: Protocol name
    :param bucket_name: Google Cloud Storage bucket name
    :return: None
    """
    if protocol_name not in [item.value for item in ProtocolIDCodeNames]:
        raise ProtocolExistenceError(protocol=protocol_name)

    logger.info(f"Downloading {protocol_name} data from Google Cloud Storage")
    data = dd.read_parquet(
        GS_BUCKET_URL.format(protocol_name=protocol_name, bucket_name=bucket_name)
    )
    dd.to_parquet(df=data, path=f"utils/loans/{protocol_name}_data/")
    logger.info(f"Downloaded {protocol_name} data from Google Cloud Storage")
    # check if file is downloaded
    folder_path = f"utils/loans/{protocol_name}_data/"
    if os.path.exists(folder_path):
        logger.info(f"File {protocol_name}_data downloaded successfully: {os.listdir(folder_path)}")
    else:
        logger.info(f"File {protocol_name}_data not downloaded: {os.listdir(folder_path)}")


def delete_parquet_file(protocol_name: str = None) -> None:
    """
    Deletes parquet file from local storage
    :param protocol_name: str = None
    :return: None
    """
    directory_path = f"utils/loans/{protocol_name}_data/"

    try:
        if os.path.exists(directory_path):
            shutil.rmtree(directory_path)
        else:
            logger.info(f"Directory {directory_path} does not exist, skipping deletion.")
    except FileNotFoundError:
        # This will handle cases where the directory is deleted between the check and the rmtree call.
        logger.info(f"Directory {directory_path} was not found, likely already deleted.")
    except Exception as e:
        # Handle other potential exceptions, like permission errors.
        logger.info(f"An error occurred while deleting {directory_path}: {e}")


def update_data(protocol_names: str = CURRENTLY_AVAILABLE_PROTOCOLS) -> None:
    """
    Updates loans data from Google Cloud Storage
    :param protocol_names: str = None
    :return: None
    """
    # Ensure the 'utils/loans/' directory exists
    loan_directory = "utils/loans/"
    if not os.path.exists(loan_directory):
        os.makedirs(loan_directory)

    for name in protocol_names:
        # Check if the specific subdirectory exists
        subdirectory_path = f"{loan_directory}{name}_data/"
        if os.path.exists(subdirectory_path):
            delete_parquet_file(name)
        else:
            os.mkdir(subdirectory_path)

    for protocol in CURRENTLY_AVAILABLE_PROTOCOLS:
        download_parquet_file(protocol_name=protocol)


def fetch_user_loans(user_id: str = None, protocol_name: str = None) -> pd.DataFrame:
    """
    Fetches user loans data from `.parquet` file
    :param user_id: User wallet ID
    :param protocol_name: Protocol name
    :return: pd.DataFrame
    """
    file_path = f"utils/loans/{protocol_name}_data/part.0.parquet"

    # Ensure the file exists
    if not os.path.exists(file_path):
        print(f"File does not exist: {file_path}")
        time.sleep(2)  # Wait for 1 second and check again
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

    data = pd.read_parquet(
        path=file_path,
    )
    user = data[data[USER_COLUMN_NAME] == user_id]
    return user.to_dict()


def get_user_row_number(user: dict[str, dict[int, str]] = None) -> int:
    """
    Returns user row number in `.parquet` file.
    According to type annotation for `user` parameter,
    the row stands for `int` python's data type.
    :param user: dict[str, dict[int, str]]
    :return: int
    """
    return next(iter(user[USER_COLUMN_NAME].keys()))


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


def compute_health_ratio_level(user_id: str = None, protocol_name: str = None) -> float:
    """
    Computes health ratio level based on user wallet ID and protocol name
    :param user_id: User wallet ID
    :param protocol_name: Protocol name
    :return: float
    """

    # Get only needed User from the whole file
    user_data = fetch_user_loans(user_id=user_id, protocol_name=protocol_name)

    # Getting all data needed for the final calculation
    user_row_number = get_user_row_number(user_data)
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
