# Get Markets

### Class Method
Use this class method to retrieve detailed information about all markets:
`haiko.api_connector.HaikoAPIConnector.get_token_markets()`

### Data Structure
This endpoint retrieves a list of dictionaries, each containing details about a market. The structure of each dictionary in the list is as follows(only used and known info):
- **marketId**: The unique identifier of the market in hexadecimal format.
  - Type: `str`
- **baseToken**: A dictionary containing details about the base token:
  - **address**: The address of the base token in hexadecimal format.
    - Type: `str`
  - **symbol**: The symbol of the base token.
    - Type: `str`
  - **decimals**: The number of decimal places used to represent the base token.
      - Type: `int`
  - **name**: The name of the base token.
    - Type: `str`
  - **rank**: The rank of the base token on the market.
    - Type: `int`
- **quoteToken**: A dictionary containing details about the quote token:
  - **address**: The address of the quote token in hexadecimal format.
    - Type: `str`
  - **symbol**: The symbol of the quote token.
    - Type: `str`
  - **decimals**: The number of decimal places used to represent the quote token.
    - Type: `int`
  - **name**: The name of the quote token.
    - Type: `str`
  - **rank**: The rank of the quote token on the market.
    - Type: `int`
- **width** The width of the tick on the market.
  - Type: `int`
- **currLimit**: The current tick on the market.
  - Type: `int`
- **currPrice**: The current price on the market.
  - Type: `str`
- **currSqrtPrice**: The square root of the current price on the market.
  - Type: `str`
- **tvl**: The total value locked in the market.
  - Type: `str`

### Return
- The method returns a list of dictionaries. Each dictionary provides detailed information about a specific market.

### Example of Returned Data
```json
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
```