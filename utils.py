from typing import Any

import logging
import requests
import time

import pandas


class EkuboLiquidity:
    URL = "http://178.32.172.153/orderbook/"
    DEX = 'Ekubo'

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
            'base_token': cleaned_collateral_token,
            'quote_token': cleaned_debt_token,
            'dex': self.DEX,
        }
        self.params_for_asks = {
            'base_token': cleaned_debt_token,
            'quote_token': cleaned_collateral_token,
            'dex': self.DEX,
        }

    def apply_liquidity_to_dataframe(self, bids_or_asks: dict[str, Any]) -> pandas.DataFrame:
        liquidity_dataframe = pandas.DataFrame(
            {
                'price': bids_or_asks['prices'],
                'quantity': bids_or_asks['quantities'],
            },
        ).astype(float)
        liquidity_dataframe.sort_values(by='price', inplace=True)
        price_diff = self.data['collateral_token_price'].diff().max()
        self.data['Ekubo_debt_token_supply'] = self.data['collateral_token_price'].apply(
            lambda price: self._get_available_liquidity(
                data=self.data,
                price=price,
                price_diff=price_diff,
                bids=True if bids_or_asks['type'] == 'bids' else False,
            ),
        )
        self.data['debt_token_supply'] += self.data['Ekubo_debt_token_supply']
        return self.data

    def fetch_liquidity(self, bids: bool = True) -> dict[str, Any]:
        params = self.params_for_bids
        if not bids:
            params = self.params_for_asks
            logging.warning('Using collateral token as base token and debt token as quote token.')

        response = requests.get(self.URL, params=params)

        if response.status_code == 200:
            liquidity = response.json()
            data = {
                'type': 'bids' if bids else 'asks',
            }
            try:
                data['prices'], data['quantities'] = zip(*liquidity[data['type']])
            except ValueError:
                time.sleep(300 if bids else 5)
                self.fetch_liquidity()
            else:
                return data
        elif bids:
            self.fetch_liquidity(bids=False)
        else:
            self.fetch_liquidity()

    @staticmethod
    def _get_available_liquidity(
            data: pandas.DataFrame,
            price: float,
            price_diff: float,
            bids: bool
    ) -> float:
        price_lower_bound = max(0.95 * price, price - price_diff) if bids else price
        price_upper_bound = price if bids else min(1.05 * price, price + price_diff)
        return data.loc[
            data['price'].between(
                price_lower_bound,
                price_upper_bound,
            ),
            'quantity',
        ].sum()

    @staticmethod
    def _remove_leading_zeros(address: str) -> str:
        while address[2] == '0':
            address = f'0x{address[3:]}'
        return address
