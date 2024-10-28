### Get depth of the market

### Class Method
Use this class method to retrieve market depth:
`haiko.api_connector.HaikoAPIConnector.get_market_depth(market_id)`

### Data Structure
This endpoint retrieves the liquidity for each price for a specified market.
The response includes an array of objects, each detailing liquidity information in a pool for a price.
Each object in the array contains:
- **price**: The index of the tick within the pool's range.
  - Type: `str`
- **liquidityCumulative**: The current liquidity in a pool.
  - Type: `str`

### Parameters
- **market_id**: The identifier of the market in hexadecimal format.
  - Type: `str`

### Return
- Returns an array of dictionaries, each providing details on the liquidity state for each price.

### Example of Returned Data
```json
[
    {
        "price": "3750.5342",
        "liquidityCumulative": "534939583228319557"
    }
]
```
