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

    def apply_liquidity_to_dataframe(self, bids_or_asks: ...) -> ...:
        ...

    def fetch_liquidity(self) -> ...:
        ...

    def _get_available_liquidity(self) -> ...:
        ...
