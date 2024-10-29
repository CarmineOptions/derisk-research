# Get List of Supported Tokens

### Class Method
Retrieve a list of tokens by using:
`haiko.api_connector.HaikoAPIConnector.get_supported_tokens()`

### Data Structure
This endpoint provides a list of tokens with detailed information. Each entry in the returned list is a dictionary containing:
- **address**: The address of the token on layer 2, in hexadecimal format.
  - Type: `str`
- **name**: The name of the token, such as "Wrapped BTC".
  - Type: `str`
- **symbol**: The abbreviated symbol of the token, such as "WBTC".
  - Type: `int`
- **decimals**: The number of decimal places the token is divided into.
  - Type: `str`
- **rank**: The rank of the token on the market.
  - Type: `int`

### Return
The method returns a list of dictionaries, each containing detailed information about a token.

### Example of Returned Data
```json
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
```
