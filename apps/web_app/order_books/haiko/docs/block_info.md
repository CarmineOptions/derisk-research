# Get Block Information

### Class Method
Use this class method to retrieve information about block using Haiko project id:
`haiko.api_connector.HaikoBlastAPIConnector.get_block_info()`

### Data Structure
This endpoint retrieves information about the latest Haiko block. The response includes an object containing the following details: block number and timestamp.

### Return
- Returns dictionary with id, jsonrpc version and block information.

### Example of Returned Data
```json
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
        "transactions": ["0x6a19b22f4fe4018d4d60ff844770a5459534d0a69f850f3c9cdcf70a132df94", "0x5fb5b63f0226ef426c81168d0235269398b63aa145ca6a3c47294caa691cfdc"]
    },
    "id": 0
}
```
