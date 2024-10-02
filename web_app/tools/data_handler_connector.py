import os
from typing import Dict, List, Optional

import requests
from pydantic import BaseModel


class LoanStateResponse(BaseModel):
    protocol_id: str
    block: int
    timestamp: int
    user: Optional[str]
    collateral: Optional[Dict]
    debt: Optional[Dict]
    deposit: Optional[Dict]


class InterestRateModel(BaseModel):
    block: int
    timestamp: int
    debt: Dict[str, float]
    collateral: Dict[str, float]


class DataFetcherClient:
    """
    A client for fetching data from the FastAPI endpoints.
    """
    def __init__(self):
        self.base_url = os.getenv("DATA_HANDLER_URL", "http://localhost:8000")
        self.session = requests.Session()

    def read_loan_states(
        self,
        protocol: Optional[str] = None,
        start_block: Optional[int] = None,
        end_block: Optional[int] = None,
        start_datetime: Optional[int] = None,
        end_datetime: Optional[int] = None,
        user: Optional[str] = None
    ) -> List[LoanStateResponse]:
        """
        Fetch loan states from the database with optional filtering.

        :param protocol: The protocol ID to filter by, defaults to None
        :type protocol: Optional[str], optional
        :param start_block: The starting block number to filter by, defaults to None
        :type start_block: Optional[int], optional
        :param end_block: The ending block number to filter by, defaults to None
        :type end_block: Optional[int], optional
        :param start_datetime: The starting timestamp (in UNIX epoch format) to filter by, defaults to None
        :type start_datetime: Optional[int], optional
        :param end_datetime: The ending timestamp (in UNIX epoch format) to filter by, defaults to None
        :type end_datetime: Optional[int], optional
        :param user: The user to filter by (optional), defaults to None
        :type user: Optional[str], optional
        :return: A list of loan states matching the filtering criteria.
        :rtype: List[LoanStateResponse]
        :raises HTTPError: If the request to the server fails.
        """
        params = {
            "protocol": protocol,
            "start_block": start_block,
            "end_block": end_block,
            "start_datetime": start_datetime,
            "end_datetime": end_datetime,
            "user": user
        }
        response = self.session.get(f"{self.base_url}/loan_states", params=params)
        response.raise_for_status()
        return [LoanStateResponse(**item) for item in response.json()]

    def get_last_interest_rate_by_block(
        self,
        protocol: str
    ) -> InterestRateModel:
        """
        Fetch the last interest rate record by block number and protocol.

        :param protocol: The protocol ID to filter by.
        :type protocol: str
        :return: The last interest rate record.
        :rtype: InterestRateModel
        :raises HTTPError: If the request to the server fails.
        """
        params = {"protocol": protocol}
        response = self.session.get(f"{self.base_url}/interest-rate/", params=params)
        response.raise_for_status()
        return InterestRateModel(**response.json())

    def close(self):
        """
        Close the session.
        """
        self.session.close()


if __name__ == "__main__":
    # DEBUG CODE
    client = DataFetcherClient()
    try:
        loan_states = client.read_loan_states(protocol="zkLend")
        print(loan_states)

        interest_rate = client.get_last_interest_rate_by_block(protocol="zkLend")
        print(interest_rate)
    finally:
        client.close()
