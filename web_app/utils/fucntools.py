import dask.dataframe as dd
import pandas as pd
from fastapi import Request

from utils.state import InterestRateModels
from utils.values import GS_BUCKET_NAME, GS_BUCKET_URL, ProtocolIDCodeNames, USER_COLUMN_NAME, DEBT_USD_COLUMN_NAME, \
    RISK_ADJUSTED_COLLATERAL_USD_COLUMN_NAME
from utils.zklend import ZkLendLoanEntity, ZkLendState
from utils.exceptions import ProtocolExistenceError


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
    bucket_name: str | None = GS_BUCKET_NAME, protocol_name: str = None
) -> None:
    """
    Downloads parquet file to local storage from Google Cloud Storage
    :param bucket_name: Google Cloud Storage bucket name
    :param protocol_name: Protocol name
    :return: None
    """
    if protocol_name not in [item.value for item in ProtocolIDCodeNames]:
        raise ProtocolExistenceError(protocol=protocol_name)

    data = dd.read_parquet(
        GS_BUCKET_URL.format(protocol_name=protocol_name, bucket_name=bucket_name)
    )
    dd.to_parquet(df=data, path=f"loans/{protocol_name}_data/")


def fetch_user_loans(user_id: str = None, protcol_name: str = None) -> pd.DataFrame:
    """
    Fetches user loans data from `.parquet` file
    :param user_id: User wallet ID
    :param protcol_name: Protocol name
    :return: pd.DataFrame
    """
    data = pd.read_parquet(
        path=f"loans/{protcol_name}_data/part.0.parquet",
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


def compute_health_ratio_level(user_id: str = None, protocol_name: str = None) -> float:
    """
    Computes health ratio level based on user wallet ID and protocol name
    :param user_id: User wallet ID
    :param protocol_name: Protocol name
    :return: float
    """
    # TODO Downloading `.parquet` file directly inside this function is a temporary
    #  solution that will be adjusted in upcoming PR
    download_parquet_file(protocol_name=protocol_name)

    # Get only needed User from the whole file
    user_data = fetch_user_loans(user_id=user_id, protcol_name=protocol_name)

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
