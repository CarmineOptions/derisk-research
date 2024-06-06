# Get Pools

### Class Method
Use this class method to retrieve detailed information about various pools:
`Ekubo.api_connector.EkuboAPIConnector.get_pools()`

### Data Structure
This endpoint retrieves a list of dictionaries, each containing comprehensive details about a pool. The structure of each dictionary in the list is as follows:
- **key_hash**: The unique identifier of the pool in hexadecimal format.
  - Type: `str`
- **token0**: The address of the first token in the pool on the blockchain.
  - Type: `str`
- **token1**: The address of the second token in the pool on the blockchain.
  - Type: `str`
- **fee**: The fee associated with the pool transactions, in hexadecimal format.
  - Type: `str`
- **tick_spacing**: The minimum granularity of price movements in the pool.
  - Type: `int`
- **extension**: Additional information or features related to the pool, in hexadecimal format.
  - Type: `str`
- **sqrt_ratio**: The square root of the current price ratio between token0 and token1, in hexadecimal format.
  - Type: `str`
- **tick**: The current position of the pool in its price range.
  - Type: `int`
- **liquidity**: The total liquidity available in the pool.
  - Type: `str`
- **lastUpdate**: A dictionary containing details about the latest update event:
  - **event_id**: Identifier of the last update event.
    - Type: `str`

### Return
- The method returns a list of dictionaries. Each dictionary provides detailed information about a specific pool.

### Example of Returned Data
```json
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
```