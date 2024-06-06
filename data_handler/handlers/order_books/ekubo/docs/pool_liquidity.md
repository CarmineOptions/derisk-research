# Get Pool Liquidity

### Class Method
Use this class method to retrieve liquidity data for each tick associated with a given pool key hash:
`Ekubo.api_connector.EkuboAPIConnector.get_pool_liquidity(key_hash)`
To get `key_hash`, use the `get_pools()` method. 

### Data Structure
This endpoint retrieves the liquidity delta for each tick for a specified pool key hash. The response includes an array of objects, each detailing specific liquidity information for a tick. Each object in the array contains:
- **tick**: The index of the tick within the pool's range.
  - Type: `int`
- **net_liquidity_delta_diff**: The net change in liquidity at this tick, expressed as a difference.
  - Type: `str`

### Parameters
- **key_hash**: The unique identifier of the pool, can be in hexadecimal or decimal format.
  - Type: `str`

### Return
- Returns an array of dictionaries, each providing details on the liquidity state for each tick.

### Example of Returned Data
```json
[
    {
        "tick": -88719042,
        "net_liquidity_delta_diff": "534939583228319557"
    }
]
```


