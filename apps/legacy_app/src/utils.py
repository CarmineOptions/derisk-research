import logging
import time

import pandas
import requests


class EkuboLiquidity:
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
        price_diff = self.data["collateral_token_price"].diff().max()

        self.data["Ekubo_debt_token_supply"] = self.data[
            "collateral_token_price"
        ].apply(
            lambda price: self._get_available_liquidity(
                data=liquidity,
                price=price,
                price_diff=price_diff,
                bids=True if bids_or_asks["type"] == "bids" else False,
            ),
        )
        self.data["debt_token_supply"] += self.data["Ekubo_debt_token_supply"]

        return self.data

    def fetch_liquidity(self, bids: bool = True) -> dict[str, str | list[float]]:
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

        params = self.params_for_bids
        if not bids:
            params = self.params_for_asks
            logging.warning(
                "Using collateral token as base token and debt token as quote token."
            )

        response = requests.get(self.URL, params=params)

        if response.ok:
            liquidity = response.json()
            data = {
                "type": "bids" if bids else "asks",
            }
            try:
                data["prices"], data["quantities"] = zip(*liquidity[data["type"]])
            except ValueError:
                time.sleep(300 if bids else 5)
                self.fetch_liquidity(bids=True)
            else:
                return data
        else:
            time.sleep(300 if bids else 5)
            self.fetch_liquidity(
                bids=False if bids else True,
            )

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
