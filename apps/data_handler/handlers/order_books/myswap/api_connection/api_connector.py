""" This module contains the MySwapAPIConnector class. """
from data_handler.handlers.order_books.abstractions import AbstractionAPIConnector


class MySwapAPIConnector(AbstractionAPIConnector):
    """ This module contains the MySwapAPIConnector class. """
    API_URL = "https://myswap-cl-charts.s3.amazonaws.com"

    @classmethod
    def get_pools_data(cls) -> dict[str, list[dict]]:
        """
        Get all myswap pools data.
        :return: dict - The pools' data.
        The dict structure is as follows:
        {
            "pools": [
                {
                    "poolkey": "0x69e3c70822347a8c2013c9b0af125f80b1f7cbf5ab05a6664dae7483226e375",
                    "token0": {
                        "symbol": "STRK",
                        "address": "0x4718f5a0fc34cc1af16a1cdee98ffb20c31f5cd61d6ab07201858f4287c938d"
                    },
                    "token1": {
                        "symbol": "USDC",
                        "address": "0x53c91253bc9682c04929ca02ed00b3e423f6710d2ee7e0d5ebb06f3ecf368a8"
                    },
                    "pool_fee": 0.05,
                "volume_24h": 0.38646873585,
                "tvl": 12944.7484419227
                }
            ]
        }
        """
        return cls.send_get_request("/data/pools/all.json")

    @classmethod
    def get_liquidity(cls, pool_id: str) -> list[dict[str, int]]:
        """
        Get liquidity data from MySwap for specific pool.
        :param pool_id: ID of the pool in hexadecimal.
        :return list[dict[str]] - The liquidity data.
        The structure of list is as follows:
        [
            {"tick": 0, "liq": 0}, ...
        ]
        """
        return cls.send_get_request(f"/data/pools/{pool_id}/liqmap.json.gz")  # type: ignore
