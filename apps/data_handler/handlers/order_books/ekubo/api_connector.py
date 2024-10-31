""" This module contains the EkuboAPIConnector class, which is responsible for"""
import time

from data_handler.handlers.order_books.abstractions import AbstractionAPIConnector


class EkuboAPIConnector(AbstractionAPIConnector):
    """ A class that interacts with the Ekubo API to fetch data related to the Ekubo protocol. """
    API_URL = "https://mainnet-api.ekubo.org"

    @classmethod
    def get_token_prices(cls, quote_token: str) -> dict:
        """
        Get the prices of all other tokens in terms of the specified quote token.

        :param quote_token: The address of the quote token on StarkNet.
        :type quote_token: str
        :return: A dictionary containing the timestamp and a list 
                of dictionaries for each token with price details.
                Each token's dictionary includes its address, price, and trading volume.
        :rtype: dict

        The response dictionary structure is as follows:
        {
            'timestamp': int,  # Unix timestamp in milliseconds when the data was recorded
            'prices': [
                {
                    'token': str,   # The address of the token on the blockchain
                    'price': str,   # The current price of the token expressed 
                    in terms of the quote token
                    'k_volume': str # The trading volume for the 
                    token, expressed in the smallest unit counts
                }
            ]
        }

        Example:
        {
            'timestamp': 1715350510592,
            'prices': [
                {
                    'token': '0x49d36570d4e46f48e99674bd3fcc84644ddd6b96f7c741b1562b82f9e004dc7',
                    'price': '0.0481921',
                    'k_volume': '1176822712207290630680641242'
                }
            ]
        }
        """
        endpoint = f"/price/{quote_token}"
        return cls.send_get_request(endpoint)

    @classmethod
    def get_pool_liquidity(cls, key_hash: str) -> list:
        """
        Get the liquidity delta for each tick 
        for the given pool key hash. The response includes an array
        of objects, each containing details about the tick and the net liquidity delta difference.

        :param key_hash: The pool key hash in hexadecimal or decimal format.
        :type key_hash: str
        :return: An array of objects detailing the current liquidity chart for the pool. Each object
                 in the array includes the following:
                 - 'tick': The tick index as an integer.
                 - 'net_liquidity_delta_diff': The difference in net 
                    liquidity for the tick, represented as a string.
        :rtype: list

        Example of returned data:
        [
            {
                "tick": -88719042,
                "net_liquidity_delta_diff": "534939583228319557"
            }
        ]

        """
        endpoint = f"/pools/{key_hash}/liquidity"
        return cls.send_get_request(endpoint)

    def get_list_tokens(self) -> list:
        """
        Retrieves a list of tokens from the blockchain layer 2. Each token object
        in the list provides comprehensive details
        including its name, symbol, decimal precision, layer 2 address, and other attributes.

        :return: A list of dictionaries, each representing a token with the following attributes:
            - 'name' (str): The name of the token, e.g., "Wrapped BTC".
            - 'symbol' (str): The abbreviated symbol of the token, e.g., "WBTC".
            - 'decimals' (int): The number of decimal places the token is divided into, e.g., 8.
            - 'l2_token_address' (str): The address of the token on layer 2, in hexadecimal format.
            - 'sort_order' (int): 
            An integer specifying the order in which the token should be displayed
            relative to others; lower numbers appear first.
            - 'total_supply' (str): The total supply of the token, if known. This can be 'None'
            if the total supply is not set or unlimited.
            - 'logo_url' (str): A URL to the token's logo image.

        Example of returned data:
        [
            {
                "name": "Wrapped BTC",
                "symbol": "WBTC",
                "decimals": 8,
                "l2_token_address": "0x03fe2b97c1fd336e750087d68b9b867997fd64a2661ff3ca5a7c771641e8e7ac",
                "sort_order": 0,
                "total_supply": "None",
                "logo_url": "https://imagedelivery.net/0xPAQaDtnQhBs8IzYRIlNg/7dcb2db2-a7a7-44af-660b-8262e057a100/logo"
            }
        ]

        """
        endpoint = "/tokens"
        return self.send_get_request(endpoint)

    def get_pools(self) -> list:
        """
        Retrieves a list of detailed information about various pools. Each entry in the 
        list is a dictionary
        that provides comprehensive details about a pool, including the tokens involved, fees,
        and other relevant metrics.

        :return: A list of dictionaries, each containing detailed information about a pool. 
        The structure of
         each dictionary is as follows:
            - 'key_hash': The unique identifier of the pool in hexadecimal format. (str)
            - 'token0': The address of the first token in the pool on the blockchain. (str)
            - 'token1': The address of the second token in the pool on the blockchain. (str)
            - 'fee': The fee associated with the pool transactions, in hexadecimal format. (str)
            - 'tick_spacing': The minimum granularity of price movements in the pool. (int)
            - 'extension': Additional information or 
            features related to the pool, in hexadecimal format. (str)
            - 'sqrt_ratio': The square root of the current price ratio between token0 and token1,
             in hexadecimal format. (str)
            - 'tick': The current position of the pool in its price range. (int)
            - 'liquidity': The total liquidity available in the pool. (str)
            - 'lastUpdate': Dictionary containing details about the latest update event:
                - 'event_id': Identifier of the last update event. (str)
        :rtype: list

        Example of returned data:
        [
            {
                "key_hash": "0x34756a876aa3288b724dc967d43ee72d9b9cf390023775f0934305233767156",
                "token0": "0xda114221cb83fa859dbdb4c44beeaa0bb37c7537ad5ae66fe5e0efd20e6eb3",
                "token1": "0x49210ffc442172463f3177147c1aeaa36c51d152c1b0630f2364c300d4f48ee",
                "fee": "0x20c49ba5e353f80000000000000000",
                "tick_spacing": 1000,
                "extension": "0x0",
                "sqrt_ratio": "0x5c358a19c219f31e027d5ac98e8d5656",
                "tick": -2042238,
                "liquidity": "35067659406163360487",
                "lastUpdate": {
                    "event_id": "2747597966999556"
                }
            }
        ]
        """
        endpoint = "/pools"
        response = self.send_get_request(endpoint)
        if isinstance(response, dict) and response.get("error"):
            # handling too many requests
            time.sleep(2)
            response = self.send_get_request(endpoint)
        return response

    def get_pool_states(self) -> list:
        """
        Fetches the current state of all pools.

        The method sends a GET request to the endpoint "/pools" and retrieves a list of pool states.
        Each pool state is represented as a dictionary with the following keys:

        - key_hash (str): A unique hash identifier for the pool.
        - token0 (str): The address of the first token in the pool.
        - token1 (str): The address of the second token in the pool.
        - fee (str): The fee tier of the pool.
        - tick_spacing (int): The tick spacing for the pool.
        - extension (str): Extension field (details unspecified).
        - sqrt_ratio (str): The square root of the price ratio (Q64.96 format).
        - tick (int): The current tick of the pool.
        - liquidity (str): The current liquidity in the pool.
        - lastUpdate (dict): A dictionary containing the last update information:
            - event_id (str): The event identifier for the last update.

        Returns:
            list: A list of dictionaries, each representing the state of a pool.
        """
        endpoint = "/pools"
        return self.send_get_request(endpoint)

    def get_pair_liquidity(self, tokenA: str, tokenB: str) -> dict:
        """
        Fetches the liquidity information for a specified token pair.

        The method sends a GET request to the endpoint "/tokens/{tokenA}/{tokenB}/liquidity"
        to retrieve the liquidity data for the given token pair. The response is a dictionary
        containing the following keys:

        - net_liquidity_delta_diff (str): The net liquidity delta difference for the token pair.
        - tick (int): The current tick for the liquidity of the token pair.

        Args:
            tokenA (str): The address of the first token.
            tokenB (str): The address of the second token.

        Returns:
            dict: A dictionary containing the liquidity information for the token pair.
        """
        endpoint = f"/tokens/{tokenA}/{tokenB}/liquidity"
        return self.send_get_request(endpoint)

    def get_pair_states(self, tokenA: str, tokenB: str) -> dict:
        """
        Fetches the state information for a specified token pair.

        The method sends a GET request to the endpoint "/pair/{tokenA}/{tokenB}"
        to retrieve the state data for the given token pair. The response is a dictionary
        containing the following keys:

        - timestamp (int): The timestamp of the data.
        - tvlByToken (list): A list of dictionaries containing 
        the total value locked (TVL) by token:
            - token (str): The address of the token.
            - balance (str): The balance of the token in the pool.
        - volumeByToken (list): A list of dictionaries containing the volume by token:
            - token (str): The address of the token.
            - volume (str): The trading volume of the token.
            - fees (str): The fees generated by the token.
        - revenueByToken (list): A list of dictionaries containing the revenue by token:
            - token (str): The address of the token.
            - revenue (str): The revenue generated by the token.
        - tvlDeltaByTokenByDate (list): A list of dictionaries containing the 
        TVL delta by token by date:
            - token (str): The address of the token.
            - date (str): The date of the TVL delta.
            - delta (str): The change in TVL for the token.
        - volumeByTokenByDate (list): A list of dictionaries containing the volume by token by date:
            - token (str): The address of the token.
            - date (str): The date of the volume data.
            - volume (str): The trading volume of the token.
            - fees (str): The fees generated by the token.
        - revenueByTokenByDate (list): A list of dictionaries containing the revenue by 
        token by date:
            - token (str): The address of the token.
            - date (str): The date of the revenue data.
            - revenue (str): The revenue generated by the token.
        - topPools (list): A list of dictionaries containing the top pools:
            - fee (str): The fee tier of the pool.
            - tick_spacing (int): The tick spacing of the pool.
            - extension (str): Extension field (details unspecified).
            - volume0_24h (str): The 24-hour trading volume of token0.
            - volume1_24h (str): The 24-hour trading volume of token1.
            - fees0_24h (str): The 24-hour trading fees for token0.
            - fees1_24h (str): The 24-hour trading fees for token1.
            - tvl0_total (str): The total TVL of token0.
            - tvl1_total (str): The total TVL of token1.
            - tvl0_delta_24h (str): The 24-hour delta in TVL for token0.
            - tvl1_delta_24h (str): The 24-hour delta in TVL for token1.

        Args:
            tokenA (str): The address of the first token.
            tokenB (str): The address of the second token.

        Returns:
            dict: A dictionary containing the state information for the token pair.
        """
        endpoint = f"/pair/{tokenA}/{tokenB}"
        return self.send_get_request(endpoint)

    def get_pair_price(self, base_token: str, quote_token: str) -> dict:
        """
        Fetches the price information for a specified token pair.
        :param base_token: Base token address
        :param quote_token: Quote token address
        :return:
        {'price': '0.9528189037', 'timestamp': '2024-05-18T10:41:37.091Z'}
        """
        endpoint = f"/price/{base_token}/{quote_token}"
        return self.send_get_request(endpoint)
