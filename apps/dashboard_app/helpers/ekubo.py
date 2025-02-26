"""
A module that interacts with an API to fetch the latest
liquidity data and applies it to a dataframe.
"""

import logging
import time

import pandas
import requests


class EkuboLiquidity:
    """
    Fetches data from a liquidity API and send it to the dataframe which updates the
    liquidity of a token pair.
    """

    URL = "http://51.195.57.201/orderbook/"
    DEX = "Ekubo"
    LOWER_BOUND_VALUE = 0.95
    UPPER_BOUND_VALUE = 1.05

    def __init__(
        self,
        data: pandas.DataFrame,
        collateral_token: str,
        debt_token: str,
    ) -> None:
        self.data = data
        self.collateral_token = collateral_token
        self.debt_token = debt_token

        cleaned_collateral_token = self._remove_leading_zeros(collateral_token)
        cleaned_debt_token = self._remove_leading_zeros(debt_token)

        self.params_for_bids = {
            "base_token": cleaned_collateral_token,
            "quote_token": cleaned_debt_token,
            "dex": self.DEX,
        }
        self.params_for_asks = {
            "base_token": cleaned_debt_token,
            "quote_token": cleaned_collateral_token,
            "dex": self.DEX,
        }

    def apply_liquidity_to_dataframe(
        self, bids_or_asks: dict[str, str | list[float]]
    ) -> pandas.DataFrame:
        """
        Applying liquidity bids or asks data to dataframe, saving in object and returns data
        :param bids_or_asks: dict[str, Any]
        :return: pandas.DataFrame
        """

        liquidity = pandas.DataFrame(
            {
                "price": bids_or_asks["prices"],
                "quantity": bids_or_asks["quantities"],
            },
        ).astype(float)

        liquidity.sort_values(by="price", inplace=True)
        if self.data.empty:
            self.data = pandas.DataFrame(
                {
                    "price": [0],
                    "debt_token_supply": [0],
                    "collateral_token_price": [0],
                    "Ekubo_debt_token_supply": [0],
                }
            )
        price_diff = (
            self.data["collateral_token_price"].diff().max()
        )  # FIXME use Collateral

        self.data["Ekubo_debt_token_supply"] = self.data[
            "collateral_token_price"
        ].apply(
            lambda price: self._get_available_liquidity(
                data=liquidity,
                price=price,
                price_diff=price_diff,
                bids=bids_or_asks["type"] == "bids",
            ),
        )
        self.data["debt_token_supply"] += self.data["Ekubo_debt_token_supply"]

        return self.data

    def fetch_liquidity(self, bids: bool = True) -> dict[str, str | list[float]] | None:
        """
        Fetching liquidity from API endpoint and structuring data to comfortable format.
        Returns dictionary with the following struct:
        {
        'type': 'bids' or 'asks',
        'prices': list[float],
        'quantities': list[float]
        }
        :param bids: bool = True
        :return: dict[str, str | list[float]]
        """
        max_retries = 5
        retry_delay = 5 if not bids else 300

        params = self.params_for_bids if bids else self.params_for_asks
        attempt = 0

        while attempt < max_retries:
            response = requests.get(self.URL, params=params)

            if response.ok:
                liquidity = response.json()
                data = {
                    "type": "bids" if bids else "asks",
                }

                if data["type"] in liquidity:
                    try:
                        data["prices"], data["quantities"] = zip(
                            *liquidity[data["type"]]
                        )
                        return {
                            "type": data["type"],
                            "prices": data["prices"],
                            "quantities": data["quantities"],
                        }
                    except ValueError:
                        logging.warning("Invalid response format, retrying...")

            logging.warning(
                f"API request failed (attempt {attempt + 1}/{max_retries}), retrying in {retry_delay} seconds..."
            )
            time.sleep(retry_delay)
            attempt += 1

        logging.error("Max retries reached. Could not fetch liquidity.")
        return None

    def _get_available_liquidity(
        self, data: pandas.DataFrame, price: float, price_diff: float, bids: bool
    ) -> float:
        """
        Getting available liquidity from data, price, price_diff for bids or asks and returns float
        :param data: pandas.DataFrame
        :param price: float
        :param price_diff: float
        :param bids: bool
        :return: float
        """

        price_lower_bound = (
            max(self.LOWER_BOUND_VALUE * price, price - price_diff) if bids else price
        )
        price_upper_bound = (
            price if bids else min(self.UPPER_BOUND_VALUE * price, price + price_diff)
        )
        return data.loc[
            data["price"].between(
                price_lower_bound,
                price_upper_bound,
            ),
            "quantity",
        ].sum()

    @staticmethod
    def _remove_leading_zeros(address: str) -> str:
        """
        Removing leading zeros from address and returning cleaned string
        :param address: str
        :return: str
        """
        while address[2] == "0":
            address = f"0x{address[3:]}"
        return address
