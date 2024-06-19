# Get USD Prices

### Class Method
Use this class method to retrieve prices of tokens:
`haiko.api_connector.HaikoAPIConnector.get_usd_prices(token0_name, token1_name)`

### Data Structure
This endpoint retrieves a dictionary containing the prices of tokens. The keys of the dictionary are:
- **token0_name**: The price of the first token.
  - Type: `str`
- **token1_name**: The price of the second token.
  - Type: `str`

### Parameters
- **token0_name**: The name of the base token.
  - Type: `str`
- **token1_name**: The name of the quote token.
  - Type: `str`

### Return
- The method returns a dictionary containing the prices of the specified tokens.

### Example of Returned Data
```json
{
    "ETH": "232.54",
    "USDC": "0.867987"
}
```
