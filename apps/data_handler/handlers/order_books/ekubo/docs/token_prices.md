# Get Token Prices

### Usage Example
To get the `quote_token`, first retrieve the list of tokens using `get_list_tokens()`, and then use a specific token's details from the list to query `get_token_prices(quote_token)` for its current prices.

### Class Method
Use this class method to retrieve current token prices:
`Ekubo.api_connector.EkuboAPIConnector.get_token_prices(quote_token)`
`Quote token` can be fetched from `get_list_tokens` method. This field is `l2_token_address`

### Data Structure
This endpoint returns the current price of a token in terms of another token or currency. The response includes the following details:
- **timestamp**: Time at which the data was recorded, in milliseconds since the Unix epoch.
  - Type: `int`
- **prices**: A list of dictionaries detailing the price of each token.
  - Type: `list` of `dict`
  
Each dictionary in the `prices` list contains:
- **token**: The address of the token on the blockchain.
  - Type: `str`
- **price**: The current price of the token, expressed in another token or currency.
  - Type: `str`
- **k_volume**: Volume of transactions for the token within a specified period, expressed in smallest unit counts (e.g., wei for Ethereum).
  - Type: `str`


