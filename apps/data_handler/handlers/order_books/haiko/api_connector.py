""" This module contains API connectors for Haiko and Blast APIs. """
from data_handler.handlers.order_books.abstractions import AbstractionAPIConnector


class HaikoAPIConnector(AbstractionAPIConnector):
    """ This module contains API connectors for Haiko and Blast APIs. """
    API_URL = "https://app.haiko.xyz/api/v1"

    @classmethod
    def get_supported_tokens(cls, existing_only: bool = True) -> list[dict]:
        """
        Get all tokens supported by Haiko.
        :param existing_only: If True, return only tokens that are currently available on Haiko.
        :return: List of all tokens supported by Haiko.
        The response list structure is as follows:
        [
            {
                "address": "0x49d36570d4e46f48e99674bd3fcc84644ddd6b96f7c741b1562b82f9e004dc7",
                "name": "Ether",
                "symbol": "ETH",
                "decimals": 18,
                "rank": 7,
                "coingeckoAddress": "0x049d36570d4e46f48e99674bd3fcc84644ddd6b96f7c741b1562b82f9e004dc7"
            }
        ]
        """
        if not isinstance(existing_only, bool):
            raise ValueError("Existing only parameter must be a bool")
        endpoint = f"/tokens?network=mainnet&existingOnly={existing_only}"
        return cls.send_get_request(endpoint)  # type: ignore

    @classmethod
    def get_market_depth(cls, market_id: str) -> list[dict]:
        """
        Get the market depth for a specific market.
        :param market_id: The market ID in hexadecimal.
        :return: List of market depth.
        The response list structure is as follows:
        [
            {
                "price": "1.2072265814306946",
                "liquidityCumulative": "4231256547876"
            },
            ...
        ]
        """
        endpoint = f"/depth?network=mainnet&id={market_id}"
        return cls.send_get_request(endpoint)  # type: ignore

    @classmethod
    def get_pair_markets(cls, token0: str, token1: str) -> list[dict]:
        """
        Get Haiko markets for provided token pair.
        :return: List of Haiko markets for a token pair.
        The response list structure is as follows:
        [
            {
                "marketId": "0x581defc9a9b4e77fcb3ec274983e18ea30115727f7647f2eb1d23858292d873",
                "baseToken": {
                    "address": "0x4718f5a0fc34cc1af16a1cdee98ffb20c31f5cd61d6ab07201858f4287c938d",
                    "name": "Starknet Token",
                    "symbol": "STRK",
                    "decimals": 18,
                    "rank": 10
                },
                "quoteToken": {
                    "address": "0x53c91253bc9682c04929ca02ed00b3e423f6710d2ee7e0d5ebb06f3ecf368a8",
                    "name": "USD Coin",
                    "symbol": "USDC",
                    "decimals": 6,
                    "rank": 2
                },
                "width": 200,
                "strategy": {
                    "address": "0x0",
                    "name": null,
                    "symbol": null,
                    "version": null
                },
                "swapFeeRate": 100,
                "feeController": "0x0",
                "controller": "0x0",
                "currLimit": -2744284,
                "currSqrtPrice": "1.0987386319915646",
                "currPrice": "1.2072265814306946",
                "tvl": "580.7339",
                "feeApy": 0.05661423233103435
            }
        ]
        """
        endpoint = f"/markets-by-pair?network=mainnet&token0={token0}&token1={token1}"
        return cls.send_get_request(endpoint)  # type: ignore

    @classmethod
    def get_usd_prices(cls, token_a_name, token_b_name) -> dict:
        """
        Get USD prices for the provided token pair.
        :return: USD prices for the provided token pair.
        The response dictionary structure is as follows:
        {
            "ETH": 3761.71,
            "USDC": 0.999003
        }
        """
        endpoint = f"/usd-prices?network=mainnet&tokens={token_a_name},{token_b_name}"
        return cls.send_get_request(endpoint)  # type: ignore


class HaikoBlastAPIConnector(AbstractionAPIConnector):
    """ This module contains API connectors for Haiko and Blast APIs. """
    API_URL = "https://starknet-mainnet.blastapi.io"
    PROJECT_ID = "a419bd5a-ec9e-40a7-93a4-d16467fb79b3"

    @classmethod
    def _post_request_builder(cls, call_method: str, params: dict) -> dict:
        """
        Build request body for Blast API POST request from common base.
        :param call_method: BlastAPI method to call.
        :param params: Parameters for the method.
        :return: Response from BlastAPI.
        """
        if not isinstance(call_method, str) or not isinstance(params, dict):
            raise ValueError("Call method must be a string and params must be a dict.")
        body = {"jsonrpc": "2.0", "method": call_method, "params": params, "id": 0}
        endpoint = f"/{cls.PROJECT_ID}"
        return cls.send_post_request(endpoint, json=body)

    @classmethod
    def get_block_info(cls) -> dict:
        """
        Get information about the latest block.
        :return: Information about the latest block.
        The response dictionary structure is as follows:
        {
            "jsonrpc": "2.0",
            "result": {
                "status": "ACCEPTED_ON_L2",
                "block_hash": "0x18ec1a3931bb5a286f801a950e1153bd427d6d3811591cc01e6f074615a1f76",
                "parent_hash": "0x413229e9996b3025feb6b276a33249fb0ff0f92d8aeea284deb35ea4093dea2",
                "block_number": 4503,
                "new_root": "0xc95a878188acf408e285027bd5e7674a88529b8c65ef6c1999b3569aea8bc8",
                "timestamp": 1661246333,
                "sequencer_address": "0x5dcd266a80b8a5f29f04d779c6b166b80150c24f2180a75e82427242dab20a9",
                "transactions": ["0x6a19b22f4fe4018d4d60ff844770a5459534d0a69f850f3c9cdcf70a132df94", ...],
            },
            "id": 0
        }
        """
        return cls._post_request_builder(
            "starknet_getBlockWithTxHashes", params={"block_id": "latest"}
        )
